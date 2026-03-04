"""数据泄露检测结果数据结构"""
import json
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LeakageItem:
    """单个泄露检测项"""

    leakage_type: str  # 例如 'L4_sample_overlap'
    taxonomy_ref: str  # 'Kapoor & Narayanan 2023, Type 4'
    risk_level: str  # 'high' / 'medium' / 'low'
    risk_score: float  # 0.0 - 1.0
    affected_count: int
    affected_ratio: float
    detail: str
    fix_hint: str

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "leakage_type": self.leakage_type,
            "taxonomy_ref": self.taxonomy_ref,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "affected_count": self.affected_count,
            "affected_ratio": self.affected_ratio,
            "detail": self.detail,
            "fix_hint": self.fix_hint,
        }


@dataclass
class LeakageResult:
    """完整的泄露检测结果"""

    items: List[LeakageItem] = field(default_factory=list)
    overall_score: float = 0.0
    overall_level: str = "clean"
    train_shape: Optional[tuple] = None
    test_shape: Optional[tuple] = None
    engine_versions: dict = field(default_factory=dict)

    def __post_init__(self):
        """计算综合风险等级和分数"""
        self._calculate_overall()

    def _calculate_overall(self) -> None:
        """计算综合风险分数和等级
        
        判定逻辑（考虑泄露类型的严重性）：
        - L4/L5/L6 是"真正的泄露"（样本重复、标签泄露、时序穿越），权重更高
        - L1 是"分布偏移"（可能是预处理问题），权重较低，单独的 L1 不应触发 high
        
        - high: 有多个"真正泄露"的 high（>=2），或有 1 个真正泄露 high + 多个 medium（>=3）
        - medium: 有 1 个真正泄露 high，或有多个 L1 high（>=2），或有很多 medium（>=6）
        - low: 有少量 medium（5 个），或有真正泄露的 medium（>=2）
        - clean: 无风险项，或只有极少量 medium（<=4 个，可能是随机波动）
        """
        if not self.items:
            self.overall_score = 0.0
            self.overall_level = "clean"
            return

        # 统计各风险等级的数量
        high_count = sum(1 for item in self.items if item.risk_level == "high")
        medium_count = sum(1 for item in self.items if item.risk_level == "medium")
        low_count = sum(1 for item in self.items if item.risk_level == "low")
        
        # 统计"真正的泄露"（L4/L5/L6）vs "分布偏移"（L1）
        serious_leakage_types = {"L4_exact_duplicate", "L4_near_duplicate", "L5_label_leakage", "L6_temporal_leakage"}
        serious_high = sum(1 for item in self.items if item.risk_level == "high" and item.leakage_type in serious_leakage_types)
        serious_medium = sum(1 for item in self.items if item.risk_level == "medium" and item.leakage_type in serious_leakage_types)
        l1_high = sum(1 for item in self.items if item.risk_level == "high" and item.leakage_type == "L1_distribution_shift")
        
        # 根据风险等级分布确定 overall_level
        if serious_high >= 2:
            # 多个真正泄露的 high → high
            self.overall_level = "high"
            self.overall_score = max(item.risk_score for item in self.items)
        elif serious_high == 1:
            # 只有一个真正泄露的 high
            if medium_count >= 3:
                # 1 个真正泄露 high + 多个 medium → high
                self.overall_level = "high"
            else:
                # 1 个真正泄露 high + 少量 medium → medium
                self.overall_level = "medium"
            self.overall_score = max(item.risk_score for item in self.items)
        elif l1_high >= 2:
            # 多个 L1 high（但没有真正泄露）→ medium（预处理问题）
            self.overall_level = "medium"
            self.overall_score = max(item.risk_score for item in self.items if item.risk_level == "high")
        elif serious_medium >= 2:
            # 有多个 medium 级别的真正泄露（L4/L5/L6）→ low（有问题但不严重）
            self.overall_level = "low"
            self.overall_score = max(item.risk_score for item in self.items if item.risk_level == "medium")
        elif medium_count >= 6:
            # 很多 medium（>=6）→ medium
            self.overall_level = "medium"
            self.overall_score = max(item.risk_score for item in self.items if item.risk_level == "medium")
        elif medium_count == 5:
            # 5 个 medium → low（可能有问题但不严重）
            self.overall_level = "low"
            self.overall_score = max(item.risk_score for item in self.items if item.risk_level == "medium")
        elif medium_count >= 1 and medium_count <= 4:
            # 少量 medium（1-4 个）→ clean（可能是随机波动）
            self.overall_level = "clean"
            self.overall_score = max(item.risk_score for item in self.items if item.risk_level == "medium")
        elif low_count > 0:
            # 只有 low 风险项 → clean（风险很低）
            self.overall_level = "clean"
            self.overall_score = max(item.risk_score for item in self.items)
        else:
            # 无风险项 → clean
            self.overall_level = "clean"
            self.overall_score = 0.0

    def report(self) -> None:
        """打印格式化报告"""
        from leakshield.report import format_report
        from rich.console import Console

        console = Console()
        report_text = format_report(self)
        console.print(report_text)

    def to_json(self, path: str) -> None:
        """保存为 JSON 文件"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "items": [item.to_dict() for item in self.items],
            "overall_score": self.overall_score,
            "overall_level": self.overall_level,
            "train_shape": self.train_shape,
            "test_shape": self.test_shape,
            "engine_versions": self.engine_versions,
        }

    def __len__(self) -> int:
        """返回检测到的泄露项数量"""
        return len(self.items)

    def __bool__(self) -> bool:
        """无 items 时返回 False"""
        return len(self.items) > 0
