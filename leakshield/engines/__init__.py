"""检测引擎模块"""
from leakshield.engines.base import BaseEngine
from leakshield.engines.hash_engine import HashEngine
from leakshield.engines.mdf_engine import MDFEngine

# ImageEngine 是可选的，需要 Pillow
try:
    from leakshield.engines.image_engine import ImageEngine
    __all__ = ["BaseEngine", "HashEngine", "MDFEngine", "ImageEngine"]
except ImportError:
    __all__ = ["BaseEngine", "HashEngine", "MDFEngine"]
