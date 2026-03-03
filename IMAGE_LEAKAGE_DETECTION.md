# 图像数据集泄露检测工具

## 概述

`check_image_leakage.py` 是一个专门用于检测图像数据集中数据泄露的工具，可以发现：

1. **完全相同的图片**（基于文件 MD5 哈希）
2. **视觉相似的图片**（基于感知哈希）
3. **文件名泄露**（文件名包含标签信息）

## 安装依赖

```bash
pip install Pillow rich
```

## 使用方法

### 基本用法

```bash
python check_image_leakage.py <数据集根目录>
```

### 数据集结构要求

工具支持标准的图像分类数据集结构：

```
my_dataset/
├── train/
│   ├── class1/
│   │   ├── img1.jpg
│   │   └── img2.jpg
│   └── class2/
│       ├── img3.jpg
│       └── img4.jpg
├── val/
│   ├── class1/
│   └── class2/
└── test/
    ├── class1/
    └── class2/
```

### 示例

```bash
# 检测 CIFAR-10 数据集
python check_image_leakage.py ./cifar10

# 检测自定义数据集
python check_image_leakage.py ./my_images
```

## 检测功能详解

### 1. 完全相同的图片检测

**原理：**
- 计算每张图片的 MD5 哈希值
- 比较 train/val/test 之间的哈希值
- 发现跨分割的重复文件

**适用场景：**
- 数据集分割前未去重
- 同一张图片被错误地放入多个分割
- 数据收集过程中的重复

**示例输出：**
```
发现 3 组重复图片，共 6 个文件

重复组 1: (哈希: a1b2c3d4e5f6...)
  - [train] cat/img_001.jpg
  - [test] cat/img_001.jpg

重复组 2: (哈希: f6e5d4c3b2a1...)
  - [train] dog/img_042.jpg
  - [val] dog/img_042.jpg
  - [test] dog/img_042.jpg
```

### 2. 视觉相似的图片检测

**原理：**
- 计算图像的感知哈希（Perceptual Hash）
- 使用汉明距离衡量相似度
- 默认阈值：汉明距离 ≤ 5（可调整）

**适用场景：**
- 数据增强后的图片泄露（旋转、翻转、裁剪等）
- 同一场景的不同拍摄
- 视频帧提取导致的相似帧

**相似度说明：**
- 汉明距离 0：完全相同
- 汉明距离 1-5：非常相似（可能是轻微变换）
- 汉明距离 6-10：相似
- 汉明距离 >10：不太相似

**示例输出：**
```
发现 12 对相似图片

相似度: 62/64
  训练集: cat/img_001.jpg
  测试集: cat/img_001_rotated.jpg

相似度: 60/64
  训练集: dog/img_042.jpg
  测试集: dog/img_042_flipped.jpg
```

### 3. 文件名泄露检查

**原理：**
- 检查文件名是否包含标签关键词
- 关键词：label, class, category, type, id, target

**适用场景：**
- 文件名包含类别信息（如 `cat_001.jpg`）
- 文件名包含标签 ID（如 `img_label_5.jpg`）
- 文件名包含目标值（如 `target_high.jpg`）

**示例输出：**
```
发现 25 个可疑文件名

  - cat/cat_001.jpg
  - dog/dog_label_5.jpg
  - bird/class_2_img.jpg
```

## 性能考虑

### 处理速度

- **文件哈希**：非常快（~1000 张/秒）
- **感知哈希**：较慢（~100 张/秒）
- **大数据集**：建议先运行文件哈希检测

### 内存占用

- 小数据集（<10000 张）：<500MB
- 中等数据集（10000-100000 张）：500MB-2GB
- 大数据集（>100000 张）：可能需要分批处理

### 优化建议

对于超大数据集（>100000 张），可以：

1. 先运行完全相同检测（快速）
2. 只对 train vs test 运行相似检测
3. 调整相似度阈值（降低到 3 以减少误报）

## 调整检测参数

如果需要调整相似度阈值，可以修改代码中的 `threshold` 参数：

```python
# 在 main() 函数中找到这一行：
similar_pairs = check_similar_images(train_images, test_images, threshold=5)

# 调整 threshold 值：
# - threshold=3: 更严格（只检测非常相似的图片）
# - threshold=10: 更宽松（检测更多相似图片，但可能有误报）
```

## 输出解读

### 风险等级

- **高风险**：完全相同的图片（文件哈希相同）
- **中风险**：视觉相似的图片（汉明距离 ≤ 5）
- **低风险**：文件名可疑（需要人工确认）

### 修复建议

1. **完全相同的图片**
   - 从测试集/验证集中移除重复图片
   - 或者从训练集中移除

2. **视觉相似的图片**
   - 检查是否为数据增强导致
   - 确认是否为同一场景的不同拍摄
   - 考虑移除或重新分配

3. **文件名泄露**
   - 重命名文件（移除标签信息）
   - 或确认文件名不会被模型使用

## 支持的图像格式

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- GIF (.gif)
- TIFF (.tiff)
- WebP (.webp)

## 限制和注意事项

### 不检测的内容

- **图像内容泄露**：图片中包含标签信息（如文字、水印）
- **元数据泄露**：EXIF 信息中的标签
- **语义相似**：不同物体但语义相关（需要深度学习模型）

### 假阳性

- 感知哈希可能将不同但视觉相似的图片标记为重复
- 建议人工确认相似图片检测结果

### 假阴性

- 经过大幅度变换的图片可能无法检测
- 不同分辨率、色彩空间的相同图片可能被遗漏

## 与 LeakShield 的关系

`check_image_leakage.py` 是 LeakShield 的补充工具：

- **LeakShield**：表格数据泄露检测（DataFrame）
- **check_image_leakage.py**：图像数据泄露检测

两者可以配合使用：
1. 使用 `check_image_leakage.py` 检测图像重复
2. 使用 LeakShield 检测图像特征（如果已提取）的分布偏移

## 示例：完整检测流程

```bash
# 1. 检测图像泄露
python check_image_leakage.py ./my_dataset

# 2. 如果有提取的特征（CSV 格式）
python -c "
import pandas as pd
import leakshield as ls

train_features = pd.read_csv('train_features.csv')
test_features = pd.read_csv('test_features.csv')

result = ls.check(train_features, test_features)
result.report()
"
```

## 常见问题

### Q: 检测需要多长时间？

A: 取决于数据集大小：
- 1000 张图片：~1 分钟
- 10000 张图片：~10 分钟
- 100000 张图片：~2 小时

### Q: 可以只检测特定分割吗？

A: 可以，修改代码中的扫描逻辑，或者临时移动不需要检测的文件夹。

### Q: 如何处理检测到的重复？

A: 建议：
1. 备份原始数据集
2. 从测试集/验证集中移除重复
3. 重新训练模型验证性能

### Q: 感知哈希的准确率如何？

A: 对于轻微变换（旋转、翻转、轻微裁剪）准确率很高（>95%），但对于大幅度变换可能失效。

## 参考资料

- [Perceptual Hashing](https://en.wikipedia.org/wiki/Perceptual_hashing)
- [Data Leakage in Machine Learning](https://machinelearningmastery.com/data-leakage-machine-learning/)
- Kapoor & Narayanan (2023). Leakage and the Reproducibility Crisis in ML-based Science.
