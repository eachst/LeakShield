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
        """计算综合风险分数和等级"""
        if not self.items:
            self.overall_score = 0.0
            self.overall_level = "clean"
            return

        # 统计各风险等级的数量
        high_count = sum(1 for item in self.items if item.risk_level == "high")
        medium_count = sum(1 for item in self.items if item.risk_level == "medium")
        low_count = sum(1 for item in self.items if item.risk_level == "low")
        
        # 根据风险等级分布确定 overall_level
        # 只有多个 high 风险项才判定为 high
        if high_count >= 2:
            self.overall_level = "high"
            self.overall_score = max(item.risk_score for item in self.items)
        elif high_count == 1:
            # 只有一个 high，看是否有其他 medium
            if medium_count >= 2:
                self.overall_level = "high"
            else:
                self.overall_level = "medium"
            self.overall_score = max(item.risk_score for item in self.items)
        elif medium_count >= 5:  # 从 3 提高到 5
            # 多个 medium 才算 medium
            self.overall_level = "medium"
            self.overall_score = max(item.risk_score for item in self.items if item.risk_level == "medium")
        elif medium_count > 0 or low_count > 0:
            self.overall_level = "low"
            self.overall_score = max(item.risk_score for item in self.items) if self.items else 0.0
        else:
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
