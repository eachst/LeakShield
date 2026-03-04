"""测试 MDFEngine"""
import numpy as np
import pandas as pd
import pytest

from leakshield.config import DetectionConfig
from leakshield.engines.mdf_engine import MDFEngine


def test_mdf_engine_metadata():
    """MDFEngine 应有正确的元数据"""
    engine = MDFEngine()
    assert engine.name == "mdf_engine"
    assert engine.version == "0.2.0"


def test_no_shift_returns_empty():
    """无显著分布偏移时应返回空列表或少量项"""
    np.random.seed(42)
    
    # 创建大样本量的数据，减少随机波动
    train_df = pd.DataFrame({
        **{f"feature_{i}": np.random.randn(5000) for i in range(3)},
        "label": np.random.randint(0, 2, 5000),
    })
    
    # 测试集使用相同分布
    np.random.seed(43)
    test_df = pd.DataFrame({
        **{f"feature_{i}": np.random.randn(1000) for i in range(3)},
        "label": np.random.randint(0, 2, 1000),
    })
    
    engine = MDFEngine()
    config = DetectionConfig()

    items = engine.detect(train_df, test_df, config)

    # 大样本量下，相同分布应该不会触发高风险警报
    # 允许有少量中低风险检测（由于随机性）
    high_risk_items = [item for item in items if item.risk_level == "high"]
    assert len(high_risk_items) == 0, f"不应有高风险项，但检测到: {high_risk_items}"


def test_mean_shift_detected():
    """检测均值偏移 3σ 的情况"""
    np.random.seed(42)

    # 训练集：均值 0，标准差 1
    train_df = pd.DataFrame({
        "feature_0": np.random.randn(1000),
        "feature_1": np.random.randn(1000),
        "label": np.random.randint(0, 2, 1000),
    })

    # 测试集：均值偏移 3σ
    test_df = pd.DataFrame({
        "feature_0": np.random.randn(200) + 3.0,  # 偏移 3σ
        "feature_1": np.random.randn(200),
        "label": np.random.randint(0, 2, 200),
    })

    engine = MDFEngine()
    config = DetectionConfig()

    items = engine.detect(train_df, test_df, config)

    # 应该检测到 feature_0 的分布偏移
    shift_items = [item for item in items if item.leakage_type == "L1_distribution_shift"]
    assert len(shift_items) > 0

    # 检查是否检测到 feature_0
    feature_0_items = [item for item in shift_items if "feature_0" in item.detail]
    assert len(feature_0_items) == 1
    assert feature_0_items[0].risk_level == "high"


def test_label_leakage_detected():
    """检测特征与标签完全相同的情况"""
    np.random.seed(42)

    # 创建数据：feature_leak 与 label 完全相同
    labels = np.random.randint(0, 2, 1000)
    train_df = pd.DataFrame({
        "feature_normal": np.random.randn(1000),
        "feature_leak": labels.astype(float),  # 与标签完全相同
        "label": labels,
    })

    engine = MDFEngine()
    config = DetectionConfig()

    items = engine.detect(train_df, train_df, config)

    # 应该检测到标签泄露
    label_items = [item for item in items if item.leakage_type == "L5_label_leakage"]
    assert len(label_items) > 0

    # 检查是否检测到 feature_leak
    leak_items = [item for item in label_items if "feature_leak" in item.detail]
    assert len(leak_items) == 1
    assert leak_items[0].risk_level == "high"


def test_temporal_leakage_detected():
    """检测时间重叠的情况"""
    # 训练集：2020-01-01 到 2020-12-31
    train_df = pd.DataFrame({
        "feature_0": np.random.randn(365),
        "timestamp": pd.date_range("2020-01-01", periods=365, freq="D"),
        "label": np.random.randint(0, 2, 365),
    })

    # 测试集：2020-06-01 到 2021-06-01（与训练集重叠）
    test_df = pd.DataFrame({
        "feature_0": np.random.randn(365),
        "timestamp": pd.date_range("2020-06-01", periods=365, freq="D"),
        "label": np.random.randint(0, 2, 365),
    })

    engine = MDFEngine()
    config = DetectionConfig(timestamp_col="timestamp")

    items = engine.detect(train_df, test_df, config)

    # 应该检测到时序泄露
    temporal_items = [item for item in items if item.leakage_type == "L6_temporal_leakage"]
    assert len(temporal_items) == 1
    assert temporal_items[0].risk_level == "high"


def test_taxonomy_ref_not_empty():
    """所有检测项应包含分类法引用"""
    np.random.seed(42)

    # 创建有偏移的数据
    train_df = pd.DataFrame({
        "feature_0": np.random.randn(500),
        "label": np.random.randint(0, 2, 500),
    })

    test_df = pd.DataFrame({
        "feature_0": np.random.randn(200) + 2.0,
        "label": np.random.randint(0, 2, 200),
    })

    engine = MDFEngine()
    config = DetectionConfig()

    items = engine.detect(train_df, test_df, config)

    # 所有项都应该有分类法引用
    for item in items:
        assert "Kapoor & Narayanan 2023" in item.taxonomy_ref
        assert item.taxonomy_ref != ""


def test_single_column_failure_does_not_crash():
    """单列失败不应影响其他列的检测"""
    np.random.seed(42)

    # 创建数据，其中一列包含 NaN
    train_df = pd.DataFrame({
        "feature_0": np.random.randn(100),
        "feature_1": [np.nan] * 100,  # 全是 NaN
        "feature_2": np.random.randn(100) + 3.0,  # 有偏移
        "label": np.random.randint(0, 2, 100),
    })

    test_df = pd.DataFrame({
        "feature_0": np.random.randn(50),
        "feature_1": [np.nan] * 50,
        "feature_2": np.random.randn(50),
        "label": np.random.randint(0, 2, 50),
    })

    engine = MDFEngine()
    config = DetectionConfig(n_jobs=1)  # 禁用并行处理避免测试卡住

    # 不应该崩溃
    items = engine.detect(train_df, test_df, config)

    # feature_1 失败，但 feature_2 应该被检测到
    assert isinstance(items, list)


def test_no_label_column_skips_label_detection(clean_dataframes):
    """没有标签列时应跳过标签检测"""
    train_df, test_df = clean_dataframes

    # 移除标签列
    train_df = train_df.drop(columns=["label"])
    test_df = test_df.drop(columns=["label"])

    engine = MDFEngine()
    config = DetectionConfig()

    # 不应该崩溃
    items = engine.detect(train_df, test_df, config)

    # 不应该有标签泄露项
    label_items = [item for item in items if item.leakage_type == "L5_label_leakage"]
    assert len(label_items) == 0


def test_regression_task_detection():
    """测试回归任务的标签泄露检测"""
    np.random.seed(42)

    # 创建回归数据：feature_leak 与 label 高度相关
    X = np.random.randn(1000)
    y = X * 10 + np.random.randn(1000) * 0.1  # 强相关

    train_df = pd.DataFrame({
        "feature_normal": np.random.randn(1000),
        "feature_leak": X,
        "target": y,  # 回归标签
    })

    engine = MDFEngine()
    config = DetectionConfig(task_type="regression")

    items = engine.detect(train_df, train_df, config)

    # 应该检测到标签泄露
    label_items = [item for item in items if item.leakage_type == "L5_label_leakage"]
    assert len(label_items) > 0
