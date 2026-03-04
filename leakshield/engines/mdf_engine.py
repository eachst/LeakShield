"""多维特征分布检测引擎（L1/L3/L5/L6）"""
import warnings
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy import stats
from scipy.stats import chi2_contingency, pearsonr
from sklearn.feature_selection import mutual_info_classif

from leakshield.config import DetectionConfig
from leakshield.engines.base import BaseEngine
from leakshield.result import LeakageItem


class MDFEngine(BaseEngine):
    """多维特征分布检测引擎"""

    name = "mdf_engine"
    version = "0.2.0"

    def detect(
        self, train_df: pd.DataFrame, test_df: pd.DataFrame, config: DetectionConfig
    ) -> List[LeakageItem]:
        """
        执行多维特征分布检测

        实现功能：
        - L1: 特征分布偏移检测（Wasserstein 距离 + KS 检验）
        - L5: 预测目标泄露检测（互信息/相关系数）
        - L6: 时序数据泄露检测

        Args:
            train_df: 训练集 DataFrame
            test_df: 测试集 DataFrame
            config: 检测配置

        Returns:
            检测到的泄露项列表
        """
        results = []

        # 1. 分布偏移检测
        results.extend(self._distribution_shift_detect(train_df, test_df, config))

        # 2. 标签关联检测
        results.extend(self._label_leakage_detect(train_df, test_df, config))

        # 3. 时序泄露检测
        if config.timestamp_col:
            results.extend(self._temporal_leakage_detect(train_df, test_df, config))

        return results

    def _distribution_shift_detect(
        self, train_df: pd.DataFrame, test_df: pd.DataFrame, config: DetectionConfig
    ) -> List[LeakageItem]:
        """
        检测数值特征的分布偏移（L1）

        使用训练集统计量进行 Z-Score 归一化，然后计算 Wasserstein 距离和 KS 统计量

        Args:
            train_df: 训练集
            test_df: 测试集
            config: 检测配置

        Returns:
            检测到的分布偏移项列表
        """
        # 获取数值型列
        numeric_cols = train_df.select_dtypes(include=[np.number]).columns.tolist()

        # 排除标签列
        label_keywords = {"label", "target", "y", "output", "class", "outcome"}
        numeric_cols = [col for col in numeric_cols if col.lower() not in label_keywords]

        if not numeric_cols:
            return []

        # 并行处理每列
        def process_column(col: str) -> Optional[LeakageItem]:
            try:
                return self._check_single_column_shift(
                    train_df[col], test_df[col], col, config
                )
            except Exception as e:
                warnings.warn(f"检测列 '{col}' 时出错: {str(e)}")
                return None

        # 使用 threading backend 避免 Windows 中文路径问题
        items = Parallel(n_jobs=config.n_jobs, backend="threading")(
            delayed(process_column)(col) for col in numeric_cols
        )

        # 过滤 None 值
        return [item for item in items if item is not None]

    def _check_single_column_shift(
        self, train_col: pd.Series, test_col: pd.Series, col_name: str, config: DetectionConfig
    ) -> Optional[LeakageItem]:
        """
        检查单列的分布偏移

        Args:
            train_col: 训练集列
            test_col: 测试集列
            col_name: 列名
            config: 检测配置

        Returns:
            检测结果，无风险时返回 None
        """
        # 移除缺失值
        train_values = train_col.dropna().values
        test_values = test_col.dropna().values

        if len(train_values) < 10 or len(test_values) < 10:
            return None

        # 使用训练集统计量进行 Z-Score 归一化
        train_mean = train_values.mean()
        train_std = train_values.std()

        if train_std == 0:
            return None

        train_normalized = (train_values - train_mean) / train_std
        test_normalized = (test_values - train_mean) / train_std

        # 计算 Wasserstein 距离
        wd = stats.wasserstein_distance(train_normalized, test_normalized)

        # 计算 KS 统计量
        ks_stat, ks_pvalue = stats.ks_2samp(train_normalized, test_normalized)

        # 小样本量时放宽阈值（更激进）
        if len(test_values) < config.min_samples:
            threshold_multiplier = 2.0  # 从 1.5 提高到 2.0
        else:
            threshold_multiplier = 1.0

        # 风险判断
        risk_level = None
        risk_score = 0.0

        if wd > config.wasserstein_high * threshold_multiplier or (
            ks_stat > config.ks_high * threshold_multiplier and ks_pvalue < 0.001
        ):
            risk_level = "high"
            risk_score = min(0.9, 0.7 + wd * 0.5)
        elif wd > config.wasserstein_medium * threshold_multiplier or (
            ks_stat > config.ks_medium * threshold_multiplier and ks_pvalue < 0.01
        ):
            risk_level = "medium"
            risk_score = 0.35 + wd * 0.8

        if risk_level is None:
            return None

        return LeakageItem(
            leakage_type="L1_distribution_shift",
            taxonomy_ref="Kapoor & Narayanan 2023, Type 1",
            risk_level=risk_level,
            risk_score=risk_score,
            affected_count=len(test_values),
            affected_ratio=1.0,
            detail=f"特征 '{col_name}' 在训练集和测试集间存在显著分布偏移 "
            f"(Wasserstein={wd:.4f}, KS={ks_stat:.4f}, p={ks_pvalue:.4e})",
            fix_hint="请检查特征工程是否在分割前对全量数据 fit",
        )

    def _label_leakage_detect(
        self, train_df: pd.DataFrame, test_df: pd.DataFrame, config: DetectionConfig
    ) -> List[LeakageItem]:
        """
        检测标签关联泄露（L5）

        检查特征与标签的异常关联

        Args:
            train_df: 训练集
            test_df: 测试集
            config: 检测配置

        Returns:
            检测到的标签泄露项列表
        """
        # 识别标签列
        label_col = self._identify_label_column(train_df)
        if label_col is None:
            warnings.warn("未找到标签列，跳过标签关联检测")
            return []

        # 获取特征列
        feature_cols = [col for col in train_df.columns if col != label_col]
        numeric_features = train_df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()

        if not numeric_features:
            return []

        # 判断任务类型
        is_classification = self._is_classification_task(train_df[label_col], config)

        # 并行处理每个特征
        def process_feature(col: str) -> Optional[LeakageItem]:
            try:
                if is_classification:
                    return self._check_classification_leakage(
                        train_df, col, label_col, config
                    )
                else:
                    return self._check_regression_leakage(train_df, col, label_col, config)
            except Exception as e:
                warnings.warn(f"检测特征 '{col}' 与标签关联时出错: {str(e)}")
                return None

        # 使用 threading backend 避免 Windows 中文路径问题
        items = Parallel(n_jobs=config.n_jobs, backend="threading")(
            delayed(process_feature)(col) for col in numeric_features
        )

        return [item for item in items if item is not None]

    def _identify_label_column(self, df: pd.DataFrame) -> Optional[str]:
        """
        识别标签列

        Args:
            df: DataFrame

        Returns:
            标签列名，未找到返回 None
        """
        label_keywords = {"label", "target", "y", "output", "class", "outcome"}
        for col in df.columns:
            if col.lower() in label_keywords:
                return col
        return None

    def _is_classification_task(self, label_col: pd.Series, config: DetectionConfig) -> bool:
        """
        判断是否为分类任务

        Args:
            label_col: 标签列
            config: 检测配置

        Returns:
            是否为分类任务
        """
        if config.task_type == "classification":
            return True
        elif config.task_type == "regression":
            return False
        else:  # auto
            return label_col.nunique() <= 20

    def _check_classification_leakage(
        self, train_df: pd.DataFrame, feature_col: str, label_col: str, config: DetectionConfig
    ) -> Optional[LeakageItem]:
        """
        检查分类任务的标签泄露

        Args:
            train_df: 训练集
            feature_col: 特征列名
            label_col: 标签列名
            config: 检测配置

        Returns:
            检测结果，无风险时返回 None
        """
        X = train_df[[feature_col]].values
        y = train_df[label_col].values

        # 移除缺失值
        mask = ~(pd.isna(X).any(axis=1) | pd.isna(y))
        X = X[mask]
        y = y[mask]

        if len(X) < 10:
            return None

        # 计算互信息
        mi = mutual_info_classif(X, y, random_state=config.random_state)[0]

        # 计算 p-value
        if len(X) <= 10000:
            # 小数据集：置换检验
            p_value = self._permutation_test_mi(X, y, mi, config.random_state)
        else:
            # 大数据集：卡方检验近似
            p_value = self._chi2_test_mi(X, y)

        # 风险判断 - 只检测异常强的关联（可能是泄露）
        # 正常的特征-标签关联不应该被标记为泄露
        if mi > config.mi_high and p_value < config.p_value_threshold:
            # 额外检查：计算相关系数，只有非常强的关联才报告
            correlation = np.corrcoef(X.flatten(), y)[0, 1]
            
            # 只有相关系数 > 0.9 或 MI > 0.8 才认为是泄露
            if abs(correlation) > 0.9 or mi > 0.8:
                return LeakageItem(
                    leakage_type="L5_label_leakage",
                    taxonomy_ref="Kapoor & Narayanan 2023, Type 5",
                    risk_level="high",
                    risk_score=min(0.95, 0.7 + mi * 0.5),
                    affected_count=len(X),
                    affected_ratio=1.0,
                    detail=f"特征 '{feature_col}' 与标签存在异常强关联 "
                    f"(MI={mi:.4f}, corr={correlation:.4f}, p={p_value:.4e})",
                    fix_hint="请确认该特征在实际预测时是否可获得，或是否与标签完全相同",
                )

        return None

    def _permutation_test_mi(
        self, X: np.ndarray, y: np.ndarray, observed_mi: float, random_state: int
    ) -> float:
        """
        置换检验计算互信息的 p-value

        Args:
            X: 特征
            y: 标签
            observed_mi: 观测到的互信息
            random_state: 随机种子

        Returns:
            p-value
        """
        n_permutations = 1000
        rng = np.random.RandomState(random_state)

        count = 0
        for _ in range(n_permutations):
            y_permuted = rng.permutation(y)
            mi_permuted = mutual_info_classif(X, y_permuted, random_state=random_state)[0]
            if mi_permuted >= observed_mi:
                count += 1

        return (count + 1) / (n_permutations + 1)

    def _chi2_test_mi(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        使用卡方检验近似计算互信息的 p-value

        Args:
            X: 特征
            y: 标签

        Returns:
            p-value
        """
        try:
            # 将连续特征离散化
            X_binned = pd.cut(X.flatten(), bins=10, labels=False, duplicates="drop")
            contingency_table = pd.crosstab(X_binned, y)
            _, p_value, _, _ = chi2_contingency(contingency_table)
            return p_value
        except Exception:
            return 1.0

    def _check_regression_leakage(
        self, train_df: pd.DataFrame, feature_col: str, label_col: str, config: DetectionConfig
    ) -> Optional[LeakageItem]:
        """
        检查回归任务的标签泄露

        Args:
            train_df: 训练集
            feature_col: 特征列名
            label_col: 标签列名
            config: 检测配置

        Returns:
            检测结果，无风险时返回 None
        """
        X = train_df[feature_col].values
        y = train_df[label_col].values

        # 移除缺失值
        mask = ~(pd.isna(X) | pd.isna(y))
        X = X[mask]
        y = y[mask]

        if len(X) < 10:
            return None

        # 计算 Pearson 相关系数
        r, p_value = pearsonr(X, y)

        # 风险判断
        if abs(r) > 0.9 and p_value < config.p_value_threshold:
            return LeakageItem(
                leakage_type="L5_label_leakage",
                taxonomy_ref="Kapoor & Narayanan 2023, Type 5",
                risk_level="high",
                risk_score=min(0.95, 0.7 + abs(r) * 0.3),
                affected_count=len(X),
                affected_ratio=1.0,
                detail=f"特征 '{feature_col}' 与标签存在异常强相关 "
                f"(r={r:.4f}, p={p_value:.4e})",
                fix_hint="请确认该特征在实际预测时是否可获得",
            )

        return None

    def _temporal_leakage_detect(
        self, train_df: pd.DataFrame, test_df: pd.DataFrame, config: DetectionConfig
    ) -> List[LeakageItem]:
        """
        检测时序数据泄露（L6）

        检查训练集和测试集的时间范围是否重叠

        Args:
            train_df: 训练集
            test_df: 测试集
            config: 检测配置

        Returns:
            检测到的时序泄露项列表
        """
        timestamp_col = config.timestamp_col

        if timestamp_col not in train_df.columns or timestamp_col not in test_df.columns:
            warnings.warn(f"时间戳列 '{timestamp_col}' 不存在，跳过时序泄露检测")
            return []

        try:
            # 转换为 datetime
            train_times = pd.to_datetime(train_df[timestamp_col])
            test_times = pd.to_datetime(test_df[timestamp_col])

            train_max = train_times.max()
            test_min = test_times.min()

            # 检查时间重叠
            if train_max >= test_min:
                overlap_days = (train_max - test_min).days

                return [
                    LeakageItem(
                        leakage_type="L6_temporal_leakage",
                        taxonomy_ref="Kapoor & Narayanan 2023, Type 6",
                        risk_level="high",
                        risk_score=0.9,
                        affected_count=len(test_df),
                        affected_ratio=1.0,
                        detail=f"训练集最大时间 ({train_max}) >= 测试集最小时间 ({test_min})，"
                        f"重叠 {overlap_days} 天",
                        fix_hint="请按时间顺序划分数据集",
                    )
                ]

        except Exception as e:
            warnings.warn(f"时序泄露检测失败: {str(e)}")

        return []
