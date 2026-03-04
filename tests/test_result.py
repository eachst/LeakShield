"""测试 LeakageResult 数据结构"""
import pytest

from leakshield.result import LeakageItem, LeakageResult


def test_empty_result_is_falsy():
    """空结果应该返回 False"""
    result = LeakageResult()
    assert not result
    assert len(result) == 0


def test_result_with_items_is_truthy():
    """有检测项的结果应该返回 True"""
    item = LeakageItem(
        leakage_type="L4_exact_duplicate",
        taxonomy_ref="Kapoor & Narayanan 2023, Type 4",
        risk_level="high",
        risk_score=0.85,
        affected_count=10,
        affected_ratio=0.1,
        detail="测试详情",
        fix_hint="修复建议",
    )
    result = LeakageResult(items=[item])
    assert result
    assert len(result) == 1


def test_to_dict_contains_required_keys():
    """to_dict 应该包含所有必需的键"""
    result = LeakageResult(
        train_shape=(100, 10),
        test_shape=(50, 10),
        engine_versions={"hash_engine": "0.1.0"},
    )

    result_dict = result.to_dict()

    assert "items" in result_dict
    assert "overall_score" in result_dict
    assert "overall_level" in result_dict
    assert "train_shape" in result_dict
    assert "test_shape" in result_dict
    assert "engine_versions" in result_dict


def test_overall_level_clean_when_no_items():
    """无检测项时，综合等级应为 clean"""
    result = LeakageResult()
    assert result.overall_level == "clean"
    assert result.overall_score == 0.0


def test_overall_level_high():
    """多个高风险项（真正泄露）应设置综合等级为 high"""
    items = [
        LeakageItem(
            leakage_type="L4_exact_duplicate",
            taxonomy_ref="Kapoor & Narayanan 2023, Type 4",
            risk_level="high",
            risk_score=0.85,
            affected_count=10,
            affected_ratio=0.1,
            detail="测试1",
            fix_hint="修复1",
        ),
        LeakageItem(
            leakage_type="L4_near_duplicate",
            taxonomy_ref="Kapoor & Narayanan 2023, Type 4",
            risk_level="high",
            risk_score=0.80,
            affected_count=8,
            affected_ratio=0.08,
            detail="测试2",
            fix_hint="修复2",
        ),
    ]
    result = LeakageResult(items=items)
    assert result.overall_level == "high"
    assert result.overall_score == 0.85


def test_overall_level_medium():
    """单个高风险项应设置综合等级为 medium"""
    item = LeakageItem(
        leakage_type="L4_exact_duplicate",
        taxonomy_ref="Kapoor & Narayanan 2023, Type 4",
        risk_level="high",
        risk_score=0.85,
        affected_count=10,
        affected_ratio=0.1,
        detail="测试",
        fix_hint="修复",
    )
    result = LeakageResult(items=[item])
    assert result.overall_level == "medium"
    assert result.overall_score == 0.85


def test_overall_level_low():
    """少量 medium 级别真正泄露应设置综合等级为 low"""
    items = [
        LeakageItem(
            leakage_type="L4_exact_duplicate",
            taxonomy_ref="Kapoor & Narayanan 2023, Type 4",
            risk_level="medium",
            risk_score=0.5,
            affected_count=5,
            affected_ratio=0.05,
            detail="测试1",
            fix_hint="修复1",
        ),
        LeakageItem(
            leakage_type="L4_near_duplicate",
            taxonomy_ref="Kapoor & Narayanan 2023, Type 4",
            risk_level="medium",
            risk_score=0.45,
            affected_count=4,
            affected_ratio=0.04,
            detail="测试2",
            fix_hint="修复2",
        ),
    ]
    result = LeakageResult(items=items)
    assert result.overall_level == "low"
    assert result.overall_score == 0.5


def test_overall_level_clean_with_few_medium():
    """少量 medium（<=4）应判定为 clean（可能是随机波动）"""
    items = [
        LeakageItem(
            leakage_type="L1_distribution_shift",
            taxonomy_ref="Kapoor & Narayanan 2023, Type 1",
            risk_level="medium",
            risk_score=0.4,
            affected_count=3,
            affected_ratio=0.03,
            detail="测试",
            fix_hint="修复",
        ),
    ]
    result = LeakageResult(items=items)
    assert result.overall_level == "clean"
    assert result.overall_score == 0.4


def test_overall_score_is_max_of_items():
    """综合分数应为所有项中的最大值"""
    items = [
        LeakageItem(
            leakage_type="L4_exact_duplicate",
            taxonomy_ref="Kapoor & Narayanan 2023, Type 4",
            risk_level="high",
            risk_score=0.85,
            affected_count=10,
            affected_ratio=0.1,
            detail="测试1",
            fix_hint="修复1",
        ),
        LeakageItem(
            leakage_type="L4_near_duplicate",
            taxonomy_ref="Kapoor & Narayanan 2023, Type 4",
            risk_level="high",
            risk_score=0.80,
            affected_count=8,
            affected_ratio=0.08,
            detail="测试2",
            fix_hint="修复2",
        ),
    ]
    result = LeakageResult(items=items)
    assert result.overall_score == 0.85
    assert result.overall_level == "high"
