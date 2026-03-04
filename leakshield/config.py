"""检测配置参数"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class DetectionConfig:
    """数据泄露检测配置"""

    # 任务类型：'auto' / 'classification' / 'regression' / 'timeseries'
    task_type: str = "auto"

    # 引擎开关
    enable_hash: bool = True
    enable_mdf: bool = True

    # Hash 引擎参数
    hash_similarity_threshold: float = 0.9  # MinHash 相似度阈值

    # MDF 引擎参数（第二阶段）
    wasserstein_high: float = 0.20  # Wasserstein 距离高风险阈值（提高以减少误报）
    wasserstein_medium: float = 0.10  # Wasserstein 距离中风险阈值
    ks_high: float = 0.15  # KS 统计量高风险阈值（提高以减少误报）
    ks_medium: float = 0.08  # KS 统计量中风险阈值
    mi_high: float = 0.50  # 互信息高风险阈值（提高以减少误报）
    p_value_threshold: float = 0.01  # 统计检验 p 值阈值
    min_samples: int = 100  # 最小样本量，低于此值放宽阈值

    # 时序相关
    timestamp_col: Optional[str] = None  # 时间戳列名

    # 通用参数
    n_jobs: int = -1  # 并行任务数，-1 表示使用所有 CPU
    random_state: int = 42  # 随机种子

    def __post_init__(self):
        """参数验证"""
        if self.task_type not in ["auto", "classification", "regression", "timeseries"]:
            raise ValueError(
                f"task_type 必须是 'auto', 'classification', 'regression' 或 'timeseries'，"
                f"当前值: {self.task_type}"
            )

        if not 0 <= self.hash_similarity_threshold <= 1:
            raise ValueError(
                f"hash_similarity_threshold 必须在 [0, 1] 范围内，当前值: {self.hash_similarity_threshold}"
            )

        if self.p_value_threshold <= 0 or self.p_value_threshold >= 1:
            raise ValueError(
                f"p_value_threshold 必须在 (0, 1) 范围内，当前值: {self.p_value_threshold}"
            )
