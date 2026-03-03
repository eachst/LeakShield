"""LeakShield 快速演示"""
import numpy as np
import pandas as pd
import leakshield as ls

print("=" * 60)
print("LeakShield 演示 - 数据泄露检测")
print("=" * 60)
print()

# 创建训练集
np.random.seed(42)
train_df = pd.DataFrame({
    **{f'feature_{i}': np.random.randn(100) for i in range(5)},
    'label': np.random.randint(0, 2, 100)
})

# 创建测试集（包含 10% 重叠样本）
overlap_df = train_df.iloc[:10].copy()
np.random.seed(123)
new_df = pd.DataFrame({
    **{f'feature_{i}': np.random.randn(90) for i in range(5)},
    'label': np.random.randint(0, 2, 90)
})
test_df = pd.concat([overlap_df, new_df], ignore_index=True)

print(f"训练集形状: {train_df.shape}")
print(f"测试集形状: {test_df.shape}")
print(f"实际重叠样本数: 10 (10%)")
print()

# 执行检测
print("正在执行泄露检测...")
print()
result = ls.check(train_df, test_df)

# 显示报告
result.report()
print()

# 显示详细信息
if result:
    print(f"检测到 {len(result)} 项泄露风险")
    print(f"综合风险分数: {result.overall_score:.2f}")
    print(f"综合风险等级: {result.overall_level.upper()}")
else:
    print("✓ 未检测到数据泄露")
