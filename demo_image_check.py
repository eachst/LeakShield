"""演示图像泄露检测工具的使用

这个脚本创建一个模拟数据集并运行检测
"""

import os
import shutil
from pathlib import Path

from PIL import Image, ImageDraw
from rich.console import Console

console = Console()


def create_demo_dataset():
    """创建一个包含泄露的演示数据集"""
    
    demo_dir = Path("demo_image_dataset")
    
    # 清理旧数据
    if demo_dir.exists():
        shutil.rmtree(demo_dir)
    
    # 创建目录结构
    for split in ['train', 'val', 'test']:
        for cls in ['cat', 'dog']:
            (demo_dir / split / cls).mkdir(parents=True, exist_ok=True)
    
    console.print("[cyan]正在创建演示数据集...[/cyan]")
    
    # 创建一些简单的图像
    def create_image(color, size=(64, 64)):
        img = Image.new('RGB', size, color)
        draw = ImageDraw.Draw(img)
        # 画一个圆
        draw.ellipse([10, 10, 54, 54], fill='white', outline='black')
        return img
    
    # 训练集
    train_cat_1 = create_image('red')
    train_cat_1.save(demo_dir / 'train' / 'cat' / 'cat_001.jpg')
    
    train_cat_2 = create_image('blue')
    train_cat_2.save(demo_dir / 'train' / 'cat' / 'cat_002.jpg')
    
    train_dog_1 = create_image('green')
    train_dog_1.save(demo_dir / 'train' / 'dog' / 'dog_001.jpg')
    
    # 验证集
    val_cat_1 = create_image('yellow')
    val_cat_1.save(demo_dir / 'val' / 'cat' / 'cat_003.jpg')
    
    # 测试集 - 包含泄露
    # 1. 完全相同的图片（复制训练集的图片）
    shutil.copy(
        demo_dir / 'train' / 'cat' / 'cat_001.jpg',
        demo_dir / 'test' / 'cat' / 'cat_001_duplicate.jpg'
    )
    
    # 2. 视觉相似的图片（轻微变换）
    train_cat_2_rotated = train_cat_2.rotate(10)
    train_cat_2_rotated.save(demo_dir / 'test' / 'cat' / 'cat_002_rotated.jpg')
    
    # 3. 文件名泄露
    test_dog_1 = create_image('purple')
    test_dog_1.save(demo_dir / 'test' / 'dog' / 'dog_label_5.jpg')  # 文件名包含 'label'
    
    console.print(f"[green]✓ 演示数据集已创建: {demo_dir}[/green]")
    console.print(f"  - 训练集: 3 张图像")
    console.print(f"  - 验证集: 1 张图像")
    console.print(f"  - 测试集: 3 张图像（包含泄露）")
    console.print()
    
    return demo_dir


def main():
    console.print("╔══════════════════════════════════════════╗")
    console.print("║    图像泄露检测工具演示                  ║")
    console.print("╚══════════════════════════════════════════╝")
    console.print()
    
    # 创建演示数据集
    demo_dir = create_demo_dataset()
    
    console.print("[cyan]演示数据集包含以下泄露：[/cyan]")
    console.print("  1. 完全相同的图片：cat_001.jpg 在 train 和 test 中")
    console.print("  2. 视觉相似的图片：cat_002.jpg 的旋转版本在 test 中")
    console.print("  3. 文件名泄露：dog_label_5.jpg 包含 'label' 关键词")
    console.print()
    
    console.print("[yellow]现在运行检测工具：[/yellow]")
    console.print(f"[dim]python check_image_leakage.py {demo_dir}[/dim]")
    console.print()
    
    # 运行检测
    import subprocess
    result = subprocess.run(
        ['python', 'check_image_leakage.py', str(demo_dir)],
        capture_output=False
    )
    
    console.print()
    console.print("[green]演示完成！[/green]")
    console.print(f"演示数据集保存在: {demo_dir}")
    console.print("你可以手动检查这些文件来验证检测结果")


if __name__ == "__main__":
    main()
