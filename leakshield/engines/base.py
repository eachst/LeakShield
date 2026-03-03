"""检测引擎抽象基类"""
from abc import ABC, abstractmethod
from typing import List

import pandas as pd

from leakshield.config import DetectionConfig
from leakshield.result import LeakageItem


class BaseEngine(ABC):
    """数据泄露检测引擎基类"""

    name: str = "base_engine"
    version: str = "0.0.0"

    @abstractmethod
    def detect(
        self, train_df: pd.DataFrame, test_df: pd.DataFrame, config: DetectionConfig
    ) -> List[LeakageItem]:
        """
        执行泄露检测

        Args:
            train_df: 训练集 DataFrame
            test_df: 测试集 DataFrame
            config: 检测配置

        Returns:
            检测到的泄露项列表
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', version='{self.version}')"
