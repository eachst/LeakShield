"""基于哈希的样本重叠检测引擎（L4）"""
import hashlib
from typing import List, Optional, Set

import numpy as np
import pandas as pd
from datasketch import MinHash, MinHashLSH

from leakshield.config import DetectionConfig
from leakshield.engines.base import BaseEngine
from leakshield.result import LeakageItem


class HashEngine(BaseEngine):
    """基于哈希的样本重叠检测引擎"""

    name = "hash_engine"
    version = "0.1.0"

    def detect(
        self, train_df: pd.DataFrame, test_df: pd.DataFrame, config: DetectionConfig
    ) -> List[LeakageItem]:
        """
        执行基于哈希的泄露检测

        Args:
            train_df: 训练集 DataFrame
            test_df: 测试集 DataFrame
            config: 检测配置

        Returns:
            检测到的泄露项列表
        """
        items = []

        # 自动识别特征列（排除常见标签列名）
        label_keywords = {"label", "target", "y", "output", "class", "outcome"}
        feature_cols = [
            col for col in train_df.columns if col.lower() not in label_keywords
        ]

        if not feature_cols:
            # 如果没有特征列，使用所有列
            feature_cols = list(train_df.columns)

        # 1. 精确哈希检测
        exact_item = self._exact_hash_detect(train_df, test_df, feature_cols)
        if exact_item:
            items.append(exact_item)

        # 2. MinHash 近似检测
        minhash_item = self._minhash_detect(train_df, test_df, feature_cols, config)
        if minhash_item:
            items.append(minhash_item)

        return items

    def _exact_hash_detect(
        self, train_df: pd.DataFrame, test_df: pd.DataFrame, feature_cols: List[str]
    ) -> Optional[LeakageItem]:
        """
        精确哈希检测：检测完全重复的样本

        Args:
            train_df: 训练集
            test_df: 测试集
            feature_cols: 特征列名列表

        Returns:
            检测结果，无重叠时返回 None
        """
        train_hashes = self._compute_row_hashes(train_df, feature_cols)
        test_hashes = self._compute_row_hashes(test_df, feature_cols)

        # 计算重叠
        overlap = train_hashes & test_hashes
        overlap_count = len(overlap)

        if overlap_count == 0:
            return None

        affected_ratio = overlap_count / len(test_df)

        # 确定风险等级
        if affected_ratio > 0.05:
            risk_level = "high"
            risk_score = min(0.9, 0.7 + affected_ratio * 0.5)
        elif affected_ratio > 0.01:
            risk_level = "medium"
            risk_score = 0.35 + affected_ratio * 2
        else:
            risk_level = "low"
            risk_score = affected_ratio * 10

        return LeakageItem(
            leakage_type="L4_exact_duplicate",
            taxonomy_ref="Kapoor & Narayanan 2023, Type 4",
            risk_level=risk_level,
            risk_score=risk_score,
            affected_count=overlap_count,
            affected_ratio=affected_ratio,
            detail=f"测试集中发现 {overlap_count} 个样本与训练集完全重复（基于特征列哈希）",
            fix_hint="使用 train_test_split 前请确认数据集无重复，或使用 drop_duplicates() 去重",
        )

    def _minhash_detect(
        self,
        train_df: pd.DataFrame,
        test_df: pd.DataFrame,
        feature_cols: List[str],
        config: DetectionConfig,
    ) -> Optional[LeakageItem]:
        """
        MinHash 近似检测：检测高度相似的样本

        Args:
            train_df: 训练集
            test_df: 测试集
            feature_cols: 特征列名列表
            config: 检测配置

        Returns:
            检测结果，无近似重叠时返回 None
        """
        # 只处理数值型列
        numeric_cols = train_df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()

        if not numeric_cols:
            return None

        threshold = config.hash_similarity_threshold

        # 构建 MinHash LSH 索引
        lsh = MinHashLSH(threshold=threshold, num_perm=128)

        # 为训练集样本创建 MinHash
        train_minhashes = {}
        for idx, row in train_df[numeric_cols].iterrows():
            mh = self._create_minhash(row)
            train_minhashes[idx] = mh
            lsh.insert(f"train_{idx}", mh)

        # 检测测试集中的近似样本
        similar_count = 0
        for idx, row in test_df[numeric_cols].iterrows():
            mh = self._create_minhash(row)
            result = lsh.query(mh)
            if result:
                similar_count += 1

        if similar_count == 0:
            return None

        affected_ratio = similar_count / len(test_df)

        # 确定风险等级
        if affected_ratio > 0.05:
            risk_level = "high"
            risk_score = min(0.85, 0.65 + affected_ratio * 0.5)
        elif affected_ratio > 0.01:
            risk_level = "medium"
            risk_score = 0.30 + affected_ratio * 2
        else:
            risk_level = "low"
            risk_score = affected_ratio * 8

        return LeakageItem(
            leakage_type="L4_near_duplicate",
            taxonomy_ref="Kapoor & Narayanan 2023, Type 4",
            risk_level=risk_level,
            risk_score=risk_score,
            affected_count=similar_count,
            affected_ratio=affected_ratio,
            detail=f"测试集中发现 {similar_count} 个样本与训练集高度相似（相似度 > {threshold:.2f}）",
            fix_hint=f"检查数据预处理流程，确保训练集和测试集分离前未进行数据增强或特征工程",
        )

    def _compute_row_hashes(self, df: pd.DataFrame, feature_cols: List[str]) -> Set[str]:
        """
        计算每行的 SHA-256 哈希值

        Args:
            df: DataFrame
            feature_cols: 特征列名列表

        Returns:
            哈希值集合
        """
        hashes = set()

        for _, row in df[feature_cols].iterrows():
            # 按列名排序后拼接
            sorted_cols = sorted(feature_cols)
            row_str = ""

            for col in sorted_cols:
                val = row[col]
                if pd.isna(val):
                    row_str += "LEAKSHIELD_MISSING|"
                elif isinstance(val, (int, float)):
                    # 数值保留 6 位小数
                    row_str += f"{float(val):.6f}|"
                else:
                    row_str += f"{str(val)}|"

            # 计算 SHA-256 哈希
            hash_val = hashlib.sha256(row_str.encode("utf-8")).hexdigest()
            hashes.add(hash_val)

        return hashes

    def _create_minhash(self, row: pd.Series) -> MinHash:
        """
        为一行数据创建 MinHash

        Args:
            row: 数据行

        Returns:
            MinHash 对象
        """
        mh = MinHash(num_perm=128)

        for col, val in row.items():
            if pd.notna(val):
                # 将列名和值组合作为特征
                feature = f"{col}:{float(val):.6f}"
                mh.update(feature.encode("utf-8"))

        return mh
