"""图像引擎测试"""
import tempfile
from pathlib import Path

import pytest

# 检查 Pillow 是否可用
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

pytestmark = pytest.mark.skipif(not PILLOW_AVAILABLE, reason="需要 Pillow 库")


@pytest.fixture
def temp_image_dataset():
    """创建临时图像数据集"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # 创建训练集图像
        train_dir = tmpdir / "train"
        train_dir.mkdir()
        
        train_images = []
        for i in range(5):
            img_path = train_dir / f"train_{i}.png"
            img = Image.new("RGB", (100, 100), color=(i * 50, i * 50, i * 50))
            img.save(img_path)
            train_images.append(img_path)
        
        # 创建测试集图像（包含 1 张重复）
        test_dir = tmpdir / "test"
        test_dir.mkdir()
        
        test_images = []
        for i in range(3):
            img_path = test_dir / f"test_{i}.png"
            img = Image.new("RGB", (100, 100), color=(i * 80, i * 80, i * 80))
            img.save(img_path)
            test_images.append(img_path)
        
        # 添加一张与训练集完全相同的图像
        duplicate_path = test_dir / "test_duplicate.png"
        img = Image.new("RGB", (100, 100), color=(0, 0, 0))  # 与 train_0 相同
        img.save(duplicate_path)
        test_images.append(duplicate_path)
        
        yield train_images, test_images


def test_image_engine_import():
    """测试图像引擎导入"""
    from leakshield.engines.image_engine import ImageEngine
    
    engine = ImageEngine()
    assert engine.name == "image_engine"
    assert engine.version == "0.1.0"


def test_image_engine_detect_exact_duplicates(temp_image_dataset):
    """测试完全相同图像检测"""
    from leakshield.config import DetectionConfig
    from leakshield.engines.image_engine import ImageEngine
    
    train_images, test_images = temp_image_dataset
    
    engine = ImageEngine()
    config = DetectionConfig()
    
    results = engine.detect(train_images, test_images, config)
    
    # 应该检测到至少 1 个完全相同的图像
    exact_dup_items = [item for item in results if item.leakage_type == "L4_exact_duplicate_image"]
    assert len(exact_dup_items) >= 1
    assert exact_dup_items[0].risk_level == "high"


def test_image_engine_with_check_function(temp_image_dataset):
    """测试通过 check() 函数使用图像引擎"""
    import leakshield as ls
    
    train_images, test_images = temp_image_dataset
    
    # 使用路径列表
    result = ls.check(train_images, test_images)
    
    assert result is not None
    assert len(result.items) > 0
    assert "image_engine" in result.engine_versions


def test_image_engine_with_directory_path(temp_image_dataset):
    """测试使用目录路径"""
    import leakshield as ls
    
    train_images, test_images = temp_image_dataset
    
    # 获取目录路径
    train_dir = train_images[0].parent
    test_dir = test_images[0].parent
    
    # 使用目录路径
    result = ls.check(str(train_dir), str(test_dir))
    
    assert result is not None
    assert len(result.items) > 0


def test_image_engine_file_hash():
    """测试文件哈希计算"""
    from leakshield.engines.image_engine import ImageEngine
    
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.png') as f:
        f.write(b"test data")
        temp_path = Path(f.name)
    
    try:
        hash1 = ImageEngine._compute_file_hash(temp_path)
        hash2 = ImageEngine._compute_file_hash(temp_path)
        
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 哈希长度
    finally:
        temp_path.unlink()


def test_image_engine_perceptual_hash():
    """测试感知哈希计算"""
    from leakshield.engines.image_engine import ImageEngine
    
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.png') as f:
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        img.save(f.name)
        temp_path = Path(f.name)
    
    try:
        phash = ImageEngine._compute_perceptual_hash(temp_path)
        
        assert phash != ""
        assert len(phash) == 16  # 64-bit 哈希的十六进制表示
    finally:
        temp_path.unlink()


def test_image_engine_hamming_distance():
    """测试汉明距离计算"""
    from leakshield.engines.image_engine import ImageEngine
    
    hash1 = "0000000000000000"
    hash2 = "0000000000000001"
    hash3 = "ffffffffffffffff"
    
    # 相同哈希
    assert ImageEngine._hamming_distance(hash1, hash1) == 0
    
    # 1 位不同
    assert ImageEngine._hamming_distance(hash1, hash2) == 1
    
    # 所有位不同
    assert ImageEngine._hamming_distance(hash1, hash3) == 64


def test_image_engine_filename_leakage():
    """测试文件名泄露检测"""
    from leakshield.engines.image_engine import ImageEngine
    
    paths = [
        Path("normal_image.png"),
        Path("photo_123.png"),
        Path("image_with_label_info.png"),  # 包含 'label'
        Path("class_1_sample.png"),  # 包含 'class'
        Path("target_data.png"),  # 包含 'target'
    ]
    
    engine = ImageEngine()
    suspicious = engine._check_filename_leakage(paths)
    
    assert len(suspicious) == 3
    assert Path("image_with_label_info.png") in suspicious
    assert Path("class_1_sample.png") in suspicious
    assert Path("target_data.png") in suspicious
