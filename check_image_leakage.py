"""图像数据集泄露检测工具

用法：
    python check_image_leakage.py <数据集根目录> [--output <输出文件>]
    
示例：
    python check_image_leakage.py ./my_dataset
    python check_image_leakage.py ./my_dataset --output report.md
    
数据集结构：
    my_dataset/
    ├── train/
    │   ├── class1/
    │   └── class2/
    ├── val/
    │   ├── class1/
    │   └── class2/
    └── test/
        ├── class1/
        └── class2/
"""

import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

from PIL import Image
from rich.console import Console
from rich.progress import track
from rich.table import Table

console = Console()


def compute_file_hash(file_path: Path) -> str:
    """计算文件的 MD5 哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def compute_perceptual_hash(image_path: Path, hash_size: int = 8) -> str:
    """
    计算图像的感知哈希（pHash）
    
    感知哈希对图像的微小变化（如压缩、缩放）不敏感
    """
    try:
        img = Image.open(image_path).convert('L')  # 转为灰度图
        img = img.resize((hash_size, hash_size), Image.Resampling.LANCZOS)
        
        # 计算 DCT（离散余弦变换）的简化版本：平均值哈希
        pixels = list(img.getdata())
        avg = sum(pixels) / len(pixels)
        
        # 生成哈希
        bits = ''.join('1' if pixel > avg else '0' for pixel in pixels)
        return hex(int(bits, 2))[2:].zfill(16)
    except Exception as e:
        console.print(f"[yellow]警告: 无法处理图像 {image_path}: {e}[/yellow]")
        return ""


def hamming_distance(hash1: str, hash2: str) -> int:
    """计算两个哈希值的汉明距离"""
    if len(hash1) != len(hash2):
        return -1
    
    # 转换为二进制并计算差异位数
    try:
        int1 = int(hash1, 16)
        int2 = int(hash2, 16)
        xor = int1 ^ int2
        return bin(xor).count('1')
    except:
        return -1


def scan_images(root_dir: Path, split: str) -> Dict[str, Path]:
    """
    扫描指定分割的所有图像
    
    Returns:
        {相对路径: 绝对路径}
    """
    split_dir = root_dir / split
    if not split_dir.exists():
        return {}
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
    images = {}
    
    for file_path in split_dir.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            rel_path = str(file_path.relative_to(split_dir))
            images[rel_path] = file_path
    
    return images


def check_exact_duplicates(
    train_images: Dict[str, Path],
    val_images: Dict[str, Path],
    test_images: Dict[str, Path]
) -> Tuple[List[Tuple[str, str, str]], int]:
    """
    检查完全相同的图片（基于文件哈希）
    
    Returns:
        (重复列表, 总重复数)
    """
    console.print("\n[cyan]正在计算文件哈希...[/cyan]")
    
    # 计算所有图像的哈希
    train_hashes = {}
    for rel_path, abs_path in track(train_images.items(), description="训练集"):
        train_hashes[rel_path] = compute_file_hash(abs_path)
    
    val_hashes = {}
    for rel_path, abs_path in track(val_images.items(), description="验证集"):
        val_hashes[rel_path] = compute_file_hash(abs_path)
    
    test_hashes = {}
    for rel_path, abs_path in track(test_images.items(), description="测试集"):
        test_hashes[rel_path] = compute_file_hash(abs_path)
    
    # 构建哈希到文件的映射
    hash_to_files = defaultdict(list)
    for rel_path, file_hash in train_hashes.items():
        hash_to_files[file_hash].append(('train', rel_path))
    for rel_path, file_hash in val_hashes.items():
        hash_to_files[file_hash].append(('val', rel_path))
    for rel_path, file_hash in test_hashes.items():
        hash_to_files[file_hash].append(('test', rel_path))
    
    # 找出跨分割的重复
    duplicates = []
    for file_hash, files in hash_to_files.items():
        if len(files) > 1:
            splits = {split for split, _ in files}
            if len(splits) > 1:  # 跨分割重复
                for split, rel_path in files:
                    duplicates.append((split, rel_path, file_hash))
    
    return duplicates, len(duplicates)


def check_similar_images(
    train_images: Dict[str, Path],
    test_images: Dict[str, Path],
    threshold: int = 5
) -> List[Tuple[str, str, int]]:
    """
    检查视觉相似的图片（基于感知哈希）
    
    Args:
        threshold: 汉明距离阈值，越小越相似（0-64）
    
    Returns:
        [(train_path, test_path, distance)]
    """
    console.print("\n[cyan]正在计算感知哈希（这可能需要一些时间）...[/cyan]")
    
    # 计算训练集的感知哈希
    train_phashes = {}
    for rel_path, abs_path in track(train_images.items(), description="训练集感知哈希"):
        phash = compute_perceptual_hash(abs_path)
        if phash:
            train_phashes[rel_path] = phash
    
    # 计算测试集的感知哈希并比较
    similar_pairs = []
    for test_rel, test_abs in track(test_images.items(), description="检测相似图像"):
        test_phash = compute_perceptual_hash(test_abs)
        if not test_phash:
            continue
        
        for train_rel, train_phash in train_phashes.items():
            distance = hamming_distance(test_phash, train_phash)
            if 0 <= distance <= threshold:
                similar_pairs.append((train_rel, test_rel, distance))
    
    return similar_pairs


def check_filename_leakage(images: Dict[str, Path]) -> List[str]:
    """
    检查文件名是否包含可能的标签信息
    
    常见问题：文件名包含类别、ID、标签等信息
    """
    suspicious_files = []
    
    # 常见的标签关键词
    label_keywords = ['label', 'class', 'category', 'type', 'id', 'target']
    
    for rel_path in images.keys():
        filename = Path(rel_path).stem.lower()
        
        # 检查是否包含标签关键词
        for keyword in label_keywords:
            if keyword in filename:
                suspicious_files.append(rel_path)
                break
    
    return suspicious_files


def export_report(
    root_dir: Path,
    train_count: int,
    val_count: int,
    test_count: int,
    duplicates: List[Tuple[str, str, str]],
    similar_pairs: List[Tuple[str, str, int]],
    suspicious_files: List[str],
    output_path: str
):
    """导出详细的检测报告到 Markdown 文件"""
    
    # 按哈希分组重复文件
    hash_groups = defaultdict(list)
    for split, rel_path, file_hash in duplicates:
        hash_groups[file_hash].append((split, rel_path))
    
    # 计算泄露率
    dup_count = len(duplicates)
    exact_leak_rate = (dup_count / test_count) * 100 if test_count > 0 else 0
    similar_leak_rate = (len(set(p[1] for p in similar_pairs)) / test_count) * 100 if test_count > 0 else 0
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 图像数据集泄露检测报告\n\n")
        f.write(f"**数据集路径**: `{root_dir}`\n\n")
        f.write(f"**检测时间**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 数据集概览
        f.write("## 数据集概览\n\n")
        f.write(f"- 训练集: {train_count} 张图像\n")
        f.write(f"- 验证集: {val_count} 张图像\n")
        f.write(f"- 测试集: {test_count} 张图像\n")
        f.write(f"- 总计: {train_count + val_count + test_count} 张图像\n\n")
        
        # 检测结果摘要
        f.write("## 检测结果摘要\n\n")
        f.write(f"| 检测项 | 数量 | 泄露率 | 风险等级 |\n")
        f.write(f"|--------|------|--------|----------|\n")
        f.write(f"| 完全重复图片 | {len(hash_groups)} 组 ({dup_count} 个文件) | {exact_leak_rate:.2f}% | {'🔴 严重' if exact_leak_rate > 1 else '🟡 警告'} |\n")
        f.write(f"| 高度相似图片 | {len(similar_pairs)} 对 | {similar_leak_rate:.2f}% | {'🟡 警告' if similar_leak_rate > 5 else '🟢 正常'} |\n")
        f.write(f"| 可疑文件名 | {len(suspicious_files)} 个 | - | {'🟡 警告' if len(suspicious_files) > 0 else '🟢 正常'} |\n\n")
        
        # 完全重复图片详情
        f.write("## 1. 完全重复图片（文件哈希）\n\n")
        if hash_groups:
            f.write(f"发现 **{len(hash_groups)}** 组重复图片，共 **{dup_count}** 个文件。\n\n")
            f.write("### 详细列表\n\n")
            
            for idx, (file_hash, files) in enumerate(hash_groups.items(), 1):
                f.write(f"#### 重复组 {idx}\n\n")
                f.write(f"**哈希值**: `{file_hash}`\n\n")
                f.write(f"**文件列表**:\n\n")
                for split, rel_path in files:
                    f.write(f"- [{split}] `{rel_path}`\n")
                f.write("\n")
        else:
            f.write("✅ 未发现完全重复的图片。\n\n")
        
        # 高度相似图片详情
        f.write("## 2. 高度相似图片（感知哈希，汉明距离≤2）\n\n")
        if similar_pairs:
            f.write(f"发现 **{len(similar_pairs)}** 对高度相似图片。\n\n")
            f.write("### 详细列表\n\n")
            
            # 按相似度排序
            similar_pairs_sorted = sorted(similar_pairs, key=lambda x: x[2])
            
            for idx, (train_path, test_path, distance) in enumerate(similar_pairs_sorted, 1):
                f.write(f"#### 相似对 {idx}\n\n")
                f.write(f"**汉明距离**: {distance}/64 (相似度: {64-distance}/64)\n\n")
                f.write(f"- **训练集**: `{train_path}`\n")
                f.write(f"- **测试集**: `{test_path}`\n\n")
        else:
            f.write("✅ 未发现高度相似的图片。\n\n")
        
        # 可疑文件名详情
        f.write("## 3. 文件名泄露检查\n\n")
        if suspicious_files:
            f.write(f"发现 **{len(suspicious_files)}** 个可疑文件名（包含标签关键词）。\n\n")
            f.write("### 详细列表\n\n")
            for file_path in suspicious_files:
                f.write(f"- `{file_path}`\n")
            f.write("\n")
        else:
            f.write("✅ 未发现可疑文件名。\n\n")
        
        # 修复建议
        f.write("## 修复建议\n\n")
        if len(hash_groups) > 0:
            f.write("### 1. 移除完全重复的图片（严重）\n\n")
            f.write("完全重复的图片会导致模型在测试集上获得虚高的性能指标。建议：\n\n")
            f.write("- 从测试集中移除所有重复的图片\n")
            f.write("- 或者从训练集中移除这些图片\n")
            f.write("- 确保训练集、验证集、测试集之间没有重叠\n\n")
        
        if len(similar_pairs) > 0:
            f.write("### 2. 检查相似图片（警告）\n\n")
            f.write("高度相似的图片可能是由于：\n\n")
            f.write("- 数据增强在分割前进行（错误做法）\n")
            f.write("- 同一场景的多次拍摄\n")
            f.write("- 视频帧提取时间间隔过短\n\n")
            f.write("建议：\n\n")
            f.write("- 确保数据增强在数据分割后进行\n")
            f.write("- 检查数据采集流程\n")
            f.write("- 考虑增加图片之间的差异性\n\n")
        
        if len(suspicious_files) > 0:
            f.write("### 3. 检查文件名（警告）\n\n")
            f.write("文件名包含标签信息可能导致信息泄露。建议：\n\n")
            f.write("- 重命名文件，移除标签信息\n")
            f.write("- 使用统一的命名规范（如：img_0001.jpg）\n\n")
        
        # 参考文献
        f.write("## 参考文献\n\n")
        f.write("- Kapoor, S., & Narayanan, A. (2023). Leakage and the reproducibility crisis in machine-learning-based science. Patterns, 4(9).\n")
        f.write("- LeakShield: https://github.com/yourusername/leakshield\n")
    
    console.print(f"\n[green]✓ 报告已导出到: {output_path}[/green]")


def main():
    # 解析命令行参数
    output_file = None
    dataset_path = None
    
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--output' and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 2
        else:
            dataset_path = sys.argv[i]
            i += 1
    
    if not dataset_path:
        console.print("[red]错误: 请提供数据集根目录[/red]")
        console.print("\n用法: python check_image_leakage.py <数据集根目录> [--output <输出文件>]")
        sys.exit(1)
    
    root_dir = Path(dataset_path)
    if not root_dir.exists():
        console.print(f"[red]错误: 目录不存在: {root_dir}[/red]")
        sys.exit(1)
    
    # 默认输出文件名
    if not output_file:
        output_file = f"leakage_report_{root_dir.name}.md"
    
    console.print("╔══════════════════════════════════════════╗")
    console.print("║      图像数据集泄露检测工具              ║")
    console.print("╚══════════════════════════════════════════╝")
    console.print(f"\n数据集路径: [cyan]{root_dir}[/cyan]\n")
    
    # 扫描图像
    console.print("[cyan]正在扫描图像文件...[/cyan]")
    train_images = scan_images(root_dir, 'train')
    val_images = scan_images(root_dir, 'val')
    test_images = scan_images(root_dir, 'test')
    
    console.print(f"训练集: {len(train_images)} 张图像")
    console.print(f"验证集: {len(val_images)} 张图像")
    console.print(f"测试集: {len(test_images)} 张图像")
    
    if not train_images and not val_images and not test_images:
        console.print("[red]错误: 未找到任何图像文件[/red]")
        sys.exit(1)
    
    # ========================================================================
    # 检测 1: 完全相同的图片
    # ========================================================================
    duplicates, dup_count = check_exact_duplicates(train_images, val_images, test_images)
    
    console.print("\n" + "=" * 70)
    console.print("[bold]检测结果 1: 完全相同的图片（文件哈希）[/bold]")
    console.print("=" * 70)
    
    if duplicates:
        # 按哈希分组
        hash_groups = defaultdict(list)
        for split, rel_path, file_hash in duplicates:
            hash_groups[file_hash].append((split, rel_path))
        
        console.print(f"\n[red]发现 {len(hash_groups)} 组重复图片，共 {dup_count} 个文件[/red]\n")
        
        for idx, (file_hash, files) in enumerate(hash_groups.items(), 1):
            console.print(f"[yellow]重复组 {idx}:[/yellow] (哈希: {file_hash[:16]}...)")
            for split, rel_path in files:
                console.print(f"  - [{split}] {rel_path}")
            console.print()
    else:
        console.print("\n[green]✓ 未发现完全相同的图片[/green]")
    
    # ========================================================================
    # 检测 2: 视觉相似的图片（仅检查 train vs test）
    # ========================================================================
    if train_images and test_images:
        similar_pairs = check_similar_images(train_images, test_images, threshold=2)
        
        console.print("\n" + "=" * 70)
        console.print("[bold]检测结果 2: 视觉相似的图片（感知哈希，汉明距离≤2）[/bold]")
        console.print("=" * 70)
        
        if similar_pairs:
            console.print(f"\n[red]发现 {len(similar_pairs)} 对高度相似图片[/red]\n")
            
            # 按相似度排序（距离越小越相似）
            similar_pairs_sorted = sorted(similar_pairs, key=lambda x: x[2])
            
            for train_path, test_path, distance in similar_pairs_sorted[:30]:  # 显示前 30 对
                console.print(f"[yellow]汉明距离: {distance}/64 (相似度: {64-distance}/64)[/yellow]")
                console.print(f"  训练集: {train_path}")
                console.print(f"  测试集: {test_path}")
                console.print()
            
            if len(similar_pairs) > 30:
                console.print(f"[dim]... 还有 {len(similar_pairs) - 30} 对相似图片未显示[/dim]")
        else:
            console.print("\n[green]✓ 未发现高度相似的图片（汉明距离≤2）[/green]")
    
    # ========================================================================
    # 检测 3: 文件名泄露
    # ========================================================================
    console.print("\n" + "=" * 70)
    console.print("[bold]检测结果 3: 文件名泄露检查[/bold]")
    console.print("=" * 70)
    
    all_images = {**train_images, **val_images, **test_images}
    suspicious_files = check_filename_leakage(all_images)
    
    if suspicious_files:
        console.print(f"\n[yellow]发现 {len(suspicious_files)} 个可疑文件名[/yellow]\n")
        for file_path in suspicious_files[:10]:
            console.print(f"  - {file_path}")
        if len(suspicious_files) > 10:
            console.print(f"[dim]... 还有 {len(suspicious_files) - 10} 个文件未显示[/dim]")
    else:
        console.print("\n[green]✓ 未发现可疑文件名[/green]")
    
    # ========================================================================
    # 总结
    # ========================================================================
    console.print("\n" + "=" * 70)
    console.print("[bold cyan]检测总结[/bold cyan]")
    console.print("=" * 70)
    
    # 统计问题数量
    num_dup_groups = len(hash_groups) if duplicates else 0
    num_similar = len(similar_pairs) if train_images and test_images else 0
    num_suspicious = len(suspicious_files)
    
    console.print(f"\n完全重复图片: [red]{num_dup_groups}[/red] 组" if num_dup_groups > 0 else "\n完全重复图片: [green]0[/green] 组")
    console.print(f"高度相似图片: [yellow]{num_similar}[/yellow] 对" if num_similar > 0 else f"高度相似图片: [green]0[/green] 对")
    console.print(f"可疑文件名: [yellow]{num_suspicious}[/yellow] 个" if num_suspicious > 0 else f"可疑文件名: [green]0[/green] 个")
    
    # 计算泄露率
    if test_images:
        exact_leak_rate = (dup_count / len(test_images)) * 100 if dup_count > 0 else 0
        similar_leak_rate = (len(set(p[1] for p in similar_pairs)) / len(test_images)) * 100 if num_similar > 0 else 0
        
        console.print(f"\n完全重复泄露率: [red]{exact_leak_rate:.2f}%[/red]" if exact_leak_rate > 1 else f"\n完全重复泄露率: [green]{exact_leak_rate:.2f}%[/green]")
        console.print(f"相似图片泄露率: [yellow]{similar_leak_rate:.2f}%[/yellow]" if similar_leak_rate > 5 else f"相似图片泄露率: [green]{similar_leak_rate:.2f}%[/green]")
    
    # 建议
    if num_dup_groups > 0 or num_similar > 0 or num_suspicious > 0:
        console.print("\n[bold]建议:[/bold]")
        if num_dup_groups > 0:
            console.print("  1. [red]严重[/red]: 移除完全重复的图片")
        if num_similar > 0:
            console.print("  2. [yellow]警告[/yellow]: 检查相似图片是否为数据增强导致的泄露")
        if num_suspicious > 0:
            console.print("  3. [yellow]警告[/yellow]: 检查文件名是否包含标签信息")
    else:
        console.print("\n[green]✓ 未发现明显的数据泄露问题[/green]")
    
    # ========================================================================
    # 导出报告
    # ========================================================================
    export_report(
        root_dir=root_dir,
        train_count=len(train_images),
        val_count=len(val_images),
        test_count=len(test_images),
        duplicates=duplicates,
        similar_pairs=similar_pairs if train_images and test_images else [],
        suspicious_files=suspicious_files,
        output_path=output_file
    )


if __name__ == "__main__":
    main()
