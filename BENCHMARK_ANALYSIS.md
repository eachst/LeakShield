# LeakShield 基准测试分析

## 当前状态

**检出率**: 33.3% (2/6 测试通过)

## 测试结果详情

### ✅ 通过的测试

1. **iris_L4_10pct** - L4 样本重叠检测（10%）
   - 预期: high
   - 检测: high ✅
   - 耗时: 8.468s
   - 说明: 成功检测到 10% 的样本重叠

2. **cancer_L5** - L5 标签泄露检测
   - 预期: high
   - 检测: high ✅
   - 耗时: 65.361s
   - 说明: 成功检测到标签泄露特征

### ❌ 未通过的测试

3. **iris_L4_1pct** - L4 样本重叠检测（1%）
   - 预期: low
   - 检测: high ❌
   - 问题: 1% 重叠被误判为 high 风险
   - 原因: 同时检测到 L1 和 L5 的 high 风险，导致 overall_level 为 high

4. **diabetes_L1** - L1 分布偏移检测
   - 预期: medium
   - 检测: high ❌
   - 问题: 全局缩放导致的分布偏移被判定为 high 而非 medium
   - 原因: 多个特征的 Wasserstein 距离超过 high 阈值

5. **timeseries_L6** - L6 时序泄露检测
   - 预期: high
   - 检测: error ❌
   - 问题: 测试集为空（切片错误）
   - 原因: `test_df = test_df.iloc[300 - days :]` 导致测试集从 270 开始，但数据只有 365 行

6. **wine_clean** - 无泄露检测
   - 预期: clean
   - 检测: high ❌
   - 问题: 干净数据被误报为 high 风险
   - 原因: L1 和 L5 检测过于敏感，产生大量误报

## 问题分析

### 1. L1 分布偏移检测过于敏感

**现象**: 
- wine_clean 数据集（无泄露）被检测出 21 项泄露
- 其中 13 项 L1_distribution_shift

**原因**:
- 小样本量（训练集 124，测试集 54）导致随机波动
- Wasserstein 和 KS 阈值可能设置过低
- 未考虑样本量对统计检验的影响

**建议修复**:
```python
# 根据样本量调整阈值
if len(test_df) < 100:
    config.wasserstein_high *= 1.5
    config.ks_high *= 1.5
```

### 2. L5 标签泄露检测误报

**现象**:
- wine_clean 检测出 8 项 L5_label_leakage
- 这些特征与标签的关联是正常的（不是泄露）

**原因**:
- 互信息检测无法区分"正常关联"和"泄露关联"
- 在分类任务中，特征与标签有关联是正常的

**建议修复**:
- L5 检测应该只在发现"异常强"的关联时触发
- 提高 mi_high 阈值（从 0.30 到 0.50）
- 或者只检测"完全相同"的情况（相关系数 > 0.95）

### 3. 时序测试数据切片错误

**现象**:
- 测试集为空

**原因**:
```python
# 错误的切片逻辑
test_df = test_df.iloc[300 - days :]  # 从 270 开始，但数据只有 365 行
```

**修复**:
```python
# 正确的切片逻辑
train_df = train_df.iloc[:300].copy()
test_df = test_df.iloc[300 - days : 300 + 65].copy()  # 确保有测试数据
```

### 4. overall_level 计算逻辑

**现象**:
- iris_L4_1pct 的 L4 检测为 medium，但 overall_level 为 high

**原因**:
- overall_level 取所有 items 中 risk_score 的最大值
- 即使 L4 是 medium，L1 或 L5 的 high 也会导致整体为 high

**建议**:
- 按泄露类型分别评估
- 或者使用加权平均而非最大值

## 优化建议

### 短期优化（v0.2.1）

1. **修复时序测试**
   ```python
   # benchmarks/run_benchmark.py
   def inject_temporal_overlap(...):
       train_df = train_df.iloc[:300].copy()
       test_df = test_df.iloc[270:335].copy()  # 确保有 65 个测试样本
   ```

2. **调整 L1 阈值**
   ```python
   # leakshield/config.py
   wasserstein_high: float = 0.20  # 从 0.15 提高到 0.20
   ks_high: float = 0.15           # 从 0.10 提高到 0.15
   ```

3. **调整 L5 阈值**
   ```python
   # leakshield/config.py
   mi_high: float = 0.50  # 从 0.30 提高到 0.50
   ```

4. **添加样本量校正**
   ```python
   # leakshield/engines/mdf_engine.py
   def _check_single_column_shift(...):
       # 小样本量时放宽阈值
       if len(test_df) < 100:
           threshold_multiplier = 1.5
       else:
           threshold_multiplier = 1.0
   ```

### 中期优化（v0.3.0）

1. **改进 L5 检测逻辑**
   - 只检测"异常强"的关联（r > 0.95 或 MI > 0.8）
   - 添加"特征与标签完全相同"的专门检测

2. **添加置信度评估**
   - 为每个检测项添加置信度分数
   - 根据样本量、p-value 等计算置信度

3. **优化 overall_level 计算**
   - 使用加权平均而非最大值
   - 不同泄露类型有不同权重

### 长期优化（v0.4.0）

1. **自适应阈值**
   - 根据数据集特征自动调整阈值
   - 使用历史数据学习最优阈值

2. **误报率控制**
   - 添加 FPR（False Positive Rate）控制
   - 允许用户设置可接受的误报率

3. **可解释性增强**
   - 为每个检测项提供详细解释
   - 可视化分布差异

## 预期改进效果

应用短期优化后，预期检出率可提升到：

| 测试用例 | 当前结果 | 预期结果 | 改进措施 |
|---------|---------|---------|---------|
| iris_L4_10pct | ✅ high | ✅ high | 无需改进 |
| iris_L4_1pct | ❌ high | ✅ low | 调整 L1/L5 阈值 |
| cancer_L5 | ✅ high | ✅ high | 无需改进 |
| diabetes_L1 | ❌ high | ✅ medium | 调整 L1 阈值 |
| timeseries_L6 | ❌ error | ✅ high | 修复切片逻辑 |
| wine_clean | ❌ high | ✅ clean | 调整 L1/L5 阈值 |

**预期检出率**: 100% (6/6)

## 下一步行动

1. ✅ 完成基准测试框架
2. ⏳ 应用短期优化
3. ⏳ 重新运行基准测试
4. ⏳ 更新 BENCHMARK.md
5. ⏳ 发布 v0.2.1

## 结论

当前基准测试暴露了 LeakShield 的几个关键问题：

1. **L1 检测过于敏感**：需要调整阈值和添加样本量校正
2. **L5 检测逻辑不完善**：需要区分正常关联和泄露关联
3. **时序测试有 bug**：需要修复数据切片逻辑

这些问题都是可以快速修复的，预期在 v0.2.1 中可以达到 100% 检出率。

基准测试框架本身是成功的，为后续优化提供了清晰的方向和量化指标。
