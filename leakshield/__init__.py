"""LeakShield - 轻量级机器学习数据泄露检测库"""
from pathlib import Path
from typing import List, Optional, Union

import pandas as pd

from leakshield.config import DetectionConfig
from leakshield.engines import HashEngine, MDFEngine
from leakshield.result import LeakageItem, LeakageResult

__version__ = "0.3.0"

__all__ = ["check", "LeakageResult", "LeakageItem", "DetectionConfig", "__version__"]


def check(
    train_data: Union[pd.DataFrame, str, Path, List[Path]],
    test_data: Union[pd.DataFrame, str, Path, List[Path]],
    config: Optional[DetectionConfig] = None,
) -> LeakageResult:
    """
    执行数据泄露检测
    
    支持两种输入模式：
    1. DataFrame 模式：检测表格数据泄露（L1/L4/L5/L6）
    2. 图像模式：检测图像数据泄露（L4 图像重复）

    DataFrame 模式示例：
    ```python
    import leakshield as ls
    result = ls.check(train_df, test_df)
    result.report()
    ```
    
    图像模式示例：
    ```python
    import leakshield as ls
    result = ls.check("dataset/train", "dataset/test")
    result.report()
    ```

    Args:
        train_data: 训练集数据
            - DataFrame: 表格数据
            - str/Path: 图像目录路径
            - List[Path]: 图像文件路径列表
        test_data: 测试集数据（格式同 train_data）
        config: 检测配置，默认使用 DetectionConfig()

    Returns:
        LeakageResult 对象，包含所有检测结果

    Raises:
        TypeError: 如果输入类型不支持
        ValueError: 如果数据为空或格式不匹配
        ImportError: 如果图像模式缺少必要依赖（Pillow）
    """
    # 使用默认配置
    if config is None:
        config = DetectionConfig()

    # 判断输入类型
    if isinstance(train_data, pd.DataFrame):
        # DataFrame 模式
        return _check_dataframes(train_data, test_data, config)
    elif isinstance(train_data, (str, Path, list)):
        # 图像模式
        return _check_images(train_data, test_data, config)
    else:
        raise TypeError(
            f"不支持的输入类型: {type(train_data)}。"
            f"支持的类型: pd.DataFrame, str, Path, List[Path]"
        )


def _check_dataframes(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    config: DetectionConfig,
) -> LeakageResult:
    """检测表格数据泄露"""
    # 参数验证
    if not isinstance(train_df, pd.DataFrame):
        raise TypeError(f"train_df 必须是 pandas.DataFrame，当前类型: {type(train_df)}")
    if not isinstance(test_df, pd.DataFrame):
        raise TypeError(f"test_df 必须是 pandas.DataFrame，当前类型: {type(test_df)}")

    if train_df.empty:
        raise ValueError("train_df 不能为空")
    if test_df.empty:
        raise ValueError("test_df 不能为空")

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


def _check_images(
    train_data: Union[str, Path, List[Path]],
    test_data: Union[str, Path, List[Path]],
    config: DetectionConfig,
) -> LeakageResult:
    """检测图像数据泄露"""
    # 导入图像引擎（延迟导入，避免强制依赖）
    try:
        from leakshield.engines.image_engine import ImageEngine
    except ImportError as e:
        raise ImportError(
            "图像检测需要安装 Pillow 库。请运行：pip install leakshield[image]"
        ) from e

    # 转换为路径列表
    train_paths = _resolve_image_paths(train_data)
    test_paths = _resolve_image_paths(test_data)

    if not train_paths:
        raise ValueError("训练集图像路径为空")
    if not test_paths:
        raise ValueError("测试集图像路径为空")

    # 收集所有检测项
    all_items = []
    engine_versions = {}

    # 运行图像引擎
    if config.enable_image:
        image_engine = ImageEngine()
        image_items = image_engine.detect(train_paths, test_paths, config)
        all_items.extend(image_items)
        engine_versions[image_engine.name] = image_engine.version

    # 构建结果
    result = LeakageResult(
        items=all_items,
        train_shape=(len(train_paths), 1),  # (样本数, 1)
        test_shape=(len(test_paths), 1),
        engine_versions=engine_versions,
    )

    return result


def _resolve_image_paths(data: Union[str, Path, List[Path]]) -> List[Path]:
    """解析图像路径
    
    Args:
        data: 图像目录路径、文件路径或路径列表
    
    Returns:
        图像文件路径列表
    """
    if isinstance(data, list):
        # 已经是路径列表
        return [Path(p) for p in data]
    
    # 转换为 Path 对象
    path = Path(data)
    
    if not path.exists():
        raise ValueError(f"路径不存在: {path}")
    
    if path.is_file():
        # 单个文件
        return [path]
    
    # 目录：扫描所有图像文件
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
    image_paths = []
    
    for file_path in path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            image_paths.append(file_path)
    
    return image_paths
