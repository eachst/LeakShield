"""LeakShield MDF 引擎演示 - 展示 L1/L5/L6 检测能力"""
import numpy as np
import pandas as pd
import leakshield as ls

print("=" * 70)
print("LeakShield MDF 引擎演示 - 多维特征分布检测")
print("=" * 70)
print()

# ============================================================================
# 场景 1：L1 - 特征分布偏移检测
# ============================================================================
print("【场景 1】L1 - 特征分布偏移检测")
print("-" * 70)

np.random.seed(42)

# 训练集：标准正态分布
train_df_1 = pd.DataFrame({
    "feature_normal": np.random.randn(1000),
    "feature_shifted": np.random.randn(1000),  # 训练集正常
    "label": np.random.randint(0, 2, 1000),
})

# 测试集：feature_shifted 发生了 3σ 偏移
test_df_1 = pd.DataFrame({
    "feature_normal": np.random.randn(200),
    "feature_shifted": np.random.randn(200) + 3.0,  # 偏移 3σ！
    "label": np.random.randint(0, 2, 200),
})

print(f"训练集形状: {train_df_1.shape}")
print(f"测试集形状: {test_df_1.shape}")
print(f"feature_shifted 在测试集中偏移了 3σ")
print()

result_1 = ls.check(train_df_1, test_df_1)
result_1.report()
print()
print()

# ============================================================================
# 场景 2：L5 - 标签泄露检测（分类任务）
# ============================================================================
print("【场景 2】L5 - 标签泄露检测（分类任务）")
print("-" * 70)

np.random.seed(42)

# 创建数据：feature_leak 与 label 完全相同（严重泄露）
labels = np.random.randint(0, 2, 1000)
train_df_2 = pd.DataFrame({
    "feature_normal": np.random.randn(1000),
    "feature_leak": labels.astype(float),  # 与标签完全相同！
    "label": labels,
})

print(f"训练集形状: {train_df_2.shape}")
print(f"feature_leak 与 label 完全相同（互信息极高）")
print()

result_2 = ls.check(train_df_2, train_df_2)
result_2.report()
print()
print()

# ============================================================================
# 场景 3：L5 - 标签泄露检测（回归任务）
# ============================================================================
print("【场景 3】L5 - 标签泄露检测（回归任务）")
print("-" * 70)

np.random.seed(42)

# 创建回归数据：feature_leak 与 target 高度相关（r > 0.9）
X = np.random.randn(1000)
y = X * 10 + np.random.randn(1000) * 0.1  # 强相关

train_df_3 = pd.DataFrame({
    "feature_normal": np.random.randn(1000),
    "feature_leak": X,  # 与 target 高度相关
    "target": y,
})

config_3 = ls.DetectionConfig(task_type="regression")

print(f"训练集形状: {train_df_3.shape}")
print(f"feature_leak 与 target 的相关系数 > 0.9")
print()

result_3 = ls.check(train_df_3, train_df_3, config_3)
result_3.report()
print()
print()

# ============================================================================
# 场景 4：L6 - 时序数据泄露检测
# ============================================================================
print("【场景 4】L6 - 时序数据泄露检测")
print("-" * 70)

# 训练集：2020-01-01 到 2020-12-31
train_df_4 = pd.DataFrame({
    "feature_0": np.random.randn(365),
    "timestamp": pd.date_range("2020-01-01", periods=365, freq="D"),
    "label": np.random.randint(0, 2, 365),
})

# 测试集：2020-06-01 到 2021-06-01（与训练集重叠！）
test_df_4 = pd.DataFrame({
    "feature_0": np.random.randn(365),
    "timestamp": pd.date_range("2020-06-01", periods=365, freq="D"),
    "label": np.random.randint(0, 2, 365),
})

config_4 = ls.DetectionConfig(timestamp_col="timestamp")

print(f"训练集时间范围: 2020-01-01 到 2020-12-31")
print(f"测试集时间范围: 2020-06-01 到 2021-06-01")
print(f"时间重叠: 2020-06-01 到 2020-12-31")
print()

result_4 = ls.check(train_df_4, test_df_4, config_4)
result_4.report()
print()
print()

# ============================================================================
# 场景 5：综合检测（L4 + L1 + L5）
# ============================================================================
print("【场景 5】综合检测 - 多种泄露同时存在")
print("-" * 70)

np.random.seed(42)

# 创建复杂场景
labels = np.random.randint(0, 2, 500)
train_df_5 = pd.DataFrame({
    "feature_normal": np.random.randn(500),
    "feature_shifted": np.random.randn(500),
    "feature_leak": labels.astype(float),  # L5: 标签泄露
    "label": labels,
})

# 测试集：包含重叠样本 + 分布偏移
overlap_df = train_df_5.iloc[:50].copy()  # L4: 样本重叠
test_new = pd.DataFrame({
    "feature_normal": np.random.randn(150),
    "feature_shifted": np.random.randn(150) + 2.5,  # L1: 分布偏移
    "feature_leak": np.random.randint(0, 2, 150).astype(float),
    "label": np.random.randint(0, 2, 150),
})
test_df_5 = pd.concat([overlap_df, test_new], ignore_index=True)

print(f"训练集形状: {train_df_5.shape}")
print(f"测试集形状: {test_df_5.shape}")
print(f"包含的泄露类型:")
print(f"  - L4: 50 个样本重叠 (25%)")
print(f"  - L1: feature_shifted 偏移 2.5σ")
print(f"  - L5: feature_leak 与 label 完全相同")
print()

result_5 = ls.check(train_df_5, test_df_5)
result_5.report()
print()

# 统计检测结果
print("=" * 70)
print("检测总结")
print("=" * 70)
print(f"共检测到 {len(result_5)} 项泄露风险")
print(f"综合风险等级: {result_5.overall_level.upper()}")
print(f"综合风险分数: {result_5.overall_score:.2f}")
print()

# 按类型分组
from collections import Counter
leakage_types = Counter(item.leakage_type for item in result_5.items)
print("泄露类型分布:")
for ltype, count in leakage_types.items():
    print(f"  - {ltype}: {count} 项")
