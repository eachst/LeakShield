"""图像数据泄露检测引擎（L4 图像重复检测）"""
import hashlib
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from leakshield.config import DetectionConfig
from leakshield.engines.base import BaseEngine
from leakshield.result import LeakageItem

# 可选依赖
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    Image = None


class ImageEngine(BaseEngine):
    """图像数据泄露检测引擎
    
    检测功能：
    - L4: 完全相同的图像（文件哈希）
    - L4: 视觉相似的图像（感知哈希）
    - 文件名泄露检测
    
    注意：需要安装可选依赖 Pillow 和 imagehash
    """

    name = "image_engine"
    version = "0.1.0"

    def __init__(self):
        """初始化图像引擎"""
        if not PILLOW_AVAILABLE:
            raise ImportError(
                "ImageEngine 需要 Pillow 库。请安装：pip install leakshield[image]"
            )

    def detect(
        self,
        train_paths: List[Path],
        test_paths: List[Path],
        config: DetectionConfig,
    ) -> List[LeakageItem]:
        """
        执行图像泄露检测
        
        Args:
            train_paths: 训练集图像路径列表
            test_paths: 测试集图像路径列表
            config: 检测配置
        
        Returns:
            检测到的泄露项列表
        """
        results = []

        # 1. 完全相同的图像检测（文件哈希）
        exact_duplicates = self._check_exact_duplicates(train_paths, test_paths)
        if exact_duplicates:
            results.append(
                LeakageItem(
                    leakage_type="L4_exact_duplicate_image",
                    taxonomy_ref="Kapoor & Narayanan 2023, Type 4",
                    risk_level="high",
                    risk_score=0.95,
                    affected_count=len(exact_duplicates),
                    affected_ratio=len(exact_duplicates) / len(test_paths) if test_paths else 0,
                    detail=f"发现 {len(exact_duplicates)} 张测试集图像与训练集完全相同（文件哈希匹配）",
                    fix_hint="请从测试集中移除这些重复图像",
                )
            )

        # 2. 视觉相似的图像检测（感知哈希）
        similar_pairs = self._check_similar_images(
            train_paths, test_paths, threshold=config.image_similarity_threshold
        )
        if similar_pairs:
            unique_test_images = len(set(p[1] for p in similar_pairs))
            results.append(
                LeakageItem(
                    leakage_type="L4_similar_image",
                    taxonomy_ref="Kapoor & Narayanan 2023, Type 4",
                    risk_level="medium" if unique_test_images < len(test_paths) * 0.05 else "high",
                    risk_score=0.7 if unique_test_images < len(test_paths) * 0.05 else 0.85,
                    affected_count=unique_test_images,
                    affected_ratio=unique_test_images / len(test_paths) if test_paths else 0,
                    detail=f"发现 {unique_test_images} 张测试集图像与训练集视觉相似（感知哈希距离 <= {config.image_similarity_threshold}）",
                    fix_hint="请检查这些图像是否为同一场景的不同拍摄或轻微变换",
                )
            )

        # 3. 文件名泄露检测
        suspicious_files = self._check_filename_leakage(test_paths)
        if suspicious_files:
            results.append(
                LeakageItem(
                    leakage_type="L5_filename_leakage",
                    taxonomy_ref="Kapoor & Narayanan 2023, Type 5",
                    risk_level="low",
                    risk_score=0.3,
                    affected_count=len(suspicious_files),
                    affected_ratio=len(suspicious_files) / len(test_paths) if test_paths else 0,
                    detail=f"发现 {len(suspicious_files)} 个文件名包含可能的标签信息（如 'label', 'class', 'id'）",
                    fix_hint="请检查文件名是否泄露了标签或类别信息",
                )
            )

        return results

    def _check_exact_duplicates(
        self, train_paths: List[Path], test_paths: List[Path]
    ) -> List[Tuple[Path, Path]]:
        """检查完全相同的图像（基于文件哈希）
        
        Returns:
            [(train_path, test_path), ...]
        """
        # 计算训练集哈希
        train_hashes = {}
        for path in train_paths:
            try:
                file_hash = self._compute_file_hash(path)
                train_hashes[file_hash] = path
            except Exception as e:
                warnings.warn(f"无法计算文件哈希 {path}: {e}")

        # 检查测试集
        duplicates = []
        for test_path in test_paths:
            try:
                test_hash = self._compute_file_hash(test_path)
                if test_hash in train_hashes:
                    duplicates.append((train_hashes[test_hash], test_path))
            except Exception as e:
                warnings.warn(f"无法计算文件哈希 {test_path}: {e}")

        return duplicates

    def _check_similar_images(
        self, train_paths: List[Path], test_paths: List[Path], threshold: int = 5
    ) -> List[Tuple[Path, Path, int]]:
        """检查视觉相似的图像（基于感知哈希）
        
        Args:
            threshold: 汉明距离阈值，越小越相似（0-64）
        
        Returns:
            [(train_path, test_path, distance), ...]
        """
        # 计算训练集感知哈希
        train_phashes = {}
        for path in train_paths:
            try:
                phash = self._compute_perceptual_hash(path)
                if phash:
                    train_phashes[path] = phash
            except Exception as e:
                warnings.warn(f"无法计算感知哈希 {path}: {e}")

        # 检查测试集
        similar_pairs = []
        for test_path in test_paths:
            try:
                test_phash = self._compute_perceptual_hash(test_path)
                if not test_phash:
                    continue

                for train_path, train_phash in train_phashes.items():
                    distance = self._hamming_distance(test_phash, train_phash)
                    if 0 <= distance <= threshold:
                        similar_pairs.append((train_path, test_path, distance))
            except Exception as e:
                warnings.warn(f"无法计算感知哈希 {test_path}: {e}")

        return similar_pairs

    def _check_filename_leakage(self, paths: List[Path]) -> List[Path]:
        """检查文件名是否包含可能的标签信息
        
        Returns:
            包含标签信息的文件路径列表
        """
        suspicious_files = []
        label_keywords = ["label", "class", "category", "type", "id", "target"]

        for path in paths:
            filename = path.stem.lower()
            if any(keyword in filename for keyword in label_keywords):
                suspicious_files.append(path)

        return suspicious_files

    @staticmethod
    def _compute_file_hash(file_path: Path) -> str:
        """计算文件的 MD5 哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def _compute_perceptual_hash(image_path: Path, hash_size: int = 8) -> str:
        """计算图像的感知哈希（pHash）
        
        感知哈希对图像的微小变化（如压缩、缩放）不敏感
        """
        try:
            img = Image.open(image_path).convert("L")  # 转为灰度图
            img = img.resize((hash_size, hash_size), Image.Resampling.LANCZOS)

            # 计算平均值哈希
            pixels = list(img.getdata())
            avg = sum(pixels) / len(pixels)

            # 生成哈希
            bits = "".join("1" if pixel > avg else "0" for pixel in pixels)
            return hex(int(bits, 2))[2:].zfill(16)
        except Exception:
            return ""

    @staticmethod
    def _hamming_distance(hash1: str, hash2: str) -> int:
        """计算两个哈希值的汉明距离"""
        if len(hash1) != len(hash2):
            return -1

        try:
            int1 = int(hash1, 16)
            int2 = int(hash2, 16)
            xor = int1 ^ int2
            return bin(xor).count("1")
        except Exception:
            return -1
