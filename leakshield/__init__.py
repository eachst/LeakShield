"""LeakShield - 轻量级机器学习数据泄露检测库"""
from typing import Optional

import pandas as pd

from leakshield.config import DetectionConfig
from leakshield.engines import HashEngine, MDFEngine
from leakshield.result import LeakageItem, LeakageResult

__version__ = "0.2.0"

__all__ = ["check", "LeakageResult", "LeakageItem", "DetectionConfig", "__version__"]


def check(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    config: Optional[DetectionConfig] = None,
) -> LeakageResult:
    """
    执行数据泄露检测

    这是 LeakShield 的主入口函数，三行代码即可完成检测：

    ```python
    import leakshield as ls
    result = ls.check(train_df, test_df)
    result.report()
    ```

    Args:
        train_df: 训练集 DataFrame
        test_df: 测试集 DataFrame
        config: 检测配置，默认使用 DetectionConfig()

    Returns:
        LeakageResult 对象，包含所有检测结果

    Raises:
        TypeError: 如果输入不是 DataFrame
        ValueError: 如果 DataFrame 为空或列不匹配
    """
    # 参数验证
    if not isinstance(train_df, pd.DataFrame):
        raise TypeError(f"train_df 必须是 pandas.DataFrame，当前类型: {type(train_df)}")
    if not isinstance(test_df, pd.DataFrame):
        raise TypeError(f"test_df 必须是 pandas.DataFrame，当前类型: {type(test_df)}")

    if train_df.empty:
        raise ValueError("train_df 不能为空")
    if test_df.empty:
        raise ValueError("test_df 不能为空")

    # 使用默认配置
    if config is None:
        config = DetectionConfig()

    # 收集所有检测项
    all_items = []
    engine_versions = {}

    # 运行 Hash 引擎
    if config.enable_hash:
        hash_engine = HashEngine()
        hash_items = hash_engine.detect(train_df, test_df, config)
        all_items.extend(hash_items)
        engine_versions[hash_engine.name] = hash_engine.version

    # 运行 MDF 引擎
    if config.enable_mdf:
        mdf_engine = MDFEngine()
        mdf_items = mdf_engine.detect(train_df, test_df, config)
        all_items.extend(mdf_items)
        engine_versions[mdf_engine.name] = mdf_engine.version

    # 构建结果
    result = LeakageResult(
        items=all_items,
        train_shape=train_df.shape,
        test_shape=test_df.shape,
        engine_versions=engine_versions,
    )

    return result
