"""Pytest fixtures"""
import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def clean_dataframes():
    """
    生成无泄露的训练集和测试集

    返回:
        (train_df, test_df) 元组，各 100 行 10 列
    """
    np.random.seed(42)

    # 训练集：100 行，10 个特征 + 1 个标签
    train_data = {
        **{f"feature_{i}": np.random.randn(100) for i in range(10)},
        "label": np.random.randint(0, 2, 100),
    }
    train_df = pd.DataFrame(train_data)

    # 测试集：100 行，完全不同的数据
    np.random.seed(123)
    test_data = {
        **{f"feature_{i}": np.random.randn(100) for i in range(10)},
        "label": np.random.randint(0, 2, 100),
    }
    test_df = pd.DataFrame(test_data)

    return train_df, test_df


@pytest.fixture
def overlapping_dataframes():
    """
    生成带有重叠样本的训练集和测试集工厂函数

    返回:
        函数，接受 overlap_ratio 参数，返回 (train_df, test_df)
    """

    def _create_overlapping(overlap_ratio: float = 0.1):
        """
        创建带有指定重叠比例的数据集

        Args:
            overlap_ratio: 重叠比例，例如 0.1 表示 10% 的测试集样本与训练集重复

        Returns:
            (train_df, test_df) 元组
        """
        np.random.seed(42)

        # 训练集：100 行
        train_data = {
            **{f"feature_{i}": np.random.randn(100) for i in range(10)},
            "label": np.random.randint(0, 2, 100),
        }
        train_df = pd.DataFrame(train_data)

        # 测试集：部分来自训练集，部分是新数据
        overlap_count = int(100 * overlap_ratio)
        non_overlap_count = 100 - overlap_count

        # 重叠部分：直接从训练集复制
        overlap_df = train_df.iloc[:overlap_count].copy()

        # 非重叠部分：生成新数据
        np.random.seed(123)
        non_overlap_data = {
            **{f"feature_{i}": np.random.randn(non_overlap_count) for i in range(10)},
            "label": np.random.randint(0, 2, non_overlap_count),
        }
        non_overlap_df = pd.DataFrame(non_overlap_data)

        # 合并测试集
        test_df = pd.concat([overlap_df, non_overlap_df], ignore_index=True)

        # 打乱测试集顺序
        test_df = test_df.sample(frac=1, random_state=42).reset_index(drop=True)

        return train_df, test_df

    return _create_overlapping
