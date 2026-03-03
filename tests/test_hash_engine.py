"""测试 HashEngine"""
import pytest

from leakshield.config import DetectionConfig
from leakshield.engines.hash_engine import HashEngine


def test_no_overlap_returns_clean(clean_dataframes):
    """无重叠时应返回空列表"""
    train_df, test_df = clean_dataframes
    engine = HashEngine()
    config = DetectionConfig()

    items = engine.detect(train_df, test_df, config)

    assert len(items) == 0


def test_10pct_overlap_returns_high(overlapping_dataframes):
    """10% 重叠应返回高风险"""
    train_df, test_df = overlapping_dataframes(overlap_ratio=0.1)
    engine = HashEngine()
    config = DetectionConfig()

    items = engine.detect(train_df, test_df, config)

    # 应该至少检测到精确重复
    assert len(items) > 0

    # 找到精确重复项
    exact_items = [item for item in items if item.leakage_type == "L4_exact_duplicate"]
    assert len(exact_items) == 1

    exact_item = exact_items[0]
    assert exact_item.risk_level == "high"
    assert exact_item.affected_count == 10
    assert exact_item.affected_ratio == 0.1


def test_1pct_overlap_returns_low(overlapping_dataframes):
    """1% 重叠应返回低风险"""
    train_df, test_df = overlapping_dataframes(overlap_ratio=0.01)
    engine = HashEngine()
    config = DetectionConfig()

    items = engine.detect(train_df, test_df, config)

    # 应该至少检测到精确重复
    assert len(items) > 0

    # 找到精确重复项
    exact_items = [item for item in items if item.leakage_type == "L4_exact_duplicate"]
    assert len(exact_items) == 1

    exact_item = exact_items[0]
    assert exact_item.risk_level == "low"
    assert exact_item.affected_count == 1
    assert exact_item.affected_ratio == 0.01


def test_result_has_taxonomy_ref(overlapping_dataframes):
    """检测结果应包含分类法引用"""
    train_df, test_df = overlapping_dataframes(overlap_ratio=0.05)
    engine = HashEngine()
    config = DetectionConfig()

    items = engine.detect(train_df, test_df, config)

    assert len(items) > 0
    for item in items:
        assert "Kapoor & Narayanan 2023" in item.taxonomy_ref
        assert "Type 4" in item.taxonomy_ref


def test_affected_ratio_correct(overlapping_dataframes):
    """affected_ratio 应该正确计算"""
    train_df, test_df = overlapping_dataframes(overlap_ratio=0.15)
    engine = HashEngine()
    config = DetectionConfig()

    items = engine.detect(train_df, test_df, config)

    exact_items = [item for item in items if item.leakage_type == "L4_exact_duplicate"]
    assert len(exact_items) == 1

    exact_item = exact_items[0]
    assert exact_item.affected_count == 15
    assert abs(exact_item.affected_ratio - 0.15) < 0.01


def test_engine_metadata():
    """引擎应有正确的元数据"""
    engine = HashEngine()
    assert engine.name == "hash_engine"
    assert engine.version == "0.1.0"


def test_excludes_label_columns(overlapping_dataframes):
    """应该排除标签列进行哈希计算"""
    train_df, test_df = overlapping_dataframes(overlap_ratio=0.1)

    # 修改标签列，但特征列保持不变
    test_df_modified = test_df.copy()
    test_df_modified["label"] = 1 - test_df_modified["label"]

    engine = HashEngine()
    config = DetectionConfig()

    items = engine.detect(train_df, test_df_modified, config)

    # 即使标签不同，特征相同仍应检测到重叠
    exact_items = [item for item in items if item.leakage_type == "L4_exact_duplicate"]
    assert len(exact_items) == 1
    assert exact_items[0].affected_count == 10
