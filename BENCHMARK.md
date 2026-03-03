# LeakShield 基准测试报告

## 测试环境

- **测试时间**: 2026-03-03 23:06:02
- **Python 版本**: 3.14.0
- **LeakShield 版本**: 0.2.0
- **关键依赖**:
  - pandas: 3.0.1
  - numpy: 2.3.5
  - scipy: 1.16.3
  - scikit-learn: 1.8.0

## 测试结果

| 测试用例 | 基础数据集 | 注入类型 | 预期等级 | 检测等级 | 匹配 | 耗时(s) |
|----------|-----------|---------|---------|---------|------|--------|
| iris_L4_10pct | iris | exact_overlap | high | high | ✅ | 8.468 |
| iris_L4_1pct | iris | exact_overlap | low | high | ❌ | 8.267 |
| cancer_L5 | breast_cancer | label_as_feature | high | high | ✅ | 65.361 |
| diabetes_L1 | diabetes | global_scaling | medium | high | ❌ | 0.343 |
| timeseries_L6 | synthetic | temporal_overlap | high | error | ❌ | 0.000 |
| wine_clean | wine | None | clean | high | ❌ | 28.513 |

## 总体检出率

- **总测试数**: 6
- **匹配数**: 2
- **检出率**: 33.3%

## 详细结果

### iris_L4_10pct

- **基础数据集**: iris
- **注入类型**: exact_overlap
- **预期等级**: high
- **检测等级**: high
- **匹配**: ✅ 是
- **检测耗时**: 8.468s
- **检测项数**: 9

**检测到的泄露**:

- L4_exact_duplicate (风险等级: high, 分数: 0.76)
- L4_near_duplicate (风险等级: high, 分数: 0.71)
- L1_distribution_shift (风险等级: medium, 分数: 0.44)
- L1_distribution_shift (风险等级: high, 分数: 0.88)
- L1_distribution_shift (风险等级: high, 分数: 0.80)
- L1_distribution_shift (风险等级: high, 分数: 0.78)
- L5_label_leakage (风险等级: high, 分数: 0.95)
- L5_label_leakage (风险等级: high, 分数: 0.95)
- L5_label_leakage (风险等级: high, 分数: 0.95)

### iris_L4_1pct

- **基础数据集**: iris
- **注入类型**: exact_overlap
- **预期等级**: low
- **检测等级**: high
- **匹配**: ❌ 否
- **检测耗时**: 8.267s
- **检测项数**: 9

**检测到的泄露**:

- L4_exact_duplicate (风险等级: medium, 分数: 0.39)
- L4_near_duplicate (风险等级: medium, 分数: 0.34)
- L1_distribution_shift (风险等级: medium, 分数: 0.43)
- L1_distribution_shift (风险等级: high, 分数: 0.89)
- L1_distribution_shift (风险等级: high, 分数: 0.82)
- L1_distribution_shift (风险等级: high, 分数: 0.80)
- L5_label_leakage (风险等级: high, 分数: 0.95)
- L5_label_leakage (风险等级: high, 分数: 0.95)
- L5_label_leakage (风险等级: high, 分数: 0.95)

### cancer_L5

- **基础数据集**: breast_cancer
- **注入类型**: label_as_feature
- **预期等级**: high
- **检测等级**: high
- **匹配**: ✅ 是
- **检测耗时**: 65.361s
- **检测项数**: 32

**检测到的泄露**:

- L1_distribution_shift (风险等级: medium, 分数: 0.46)
- L1_distribution_shift (风险等级: medium, 分数: 0.42)
- L1_distribution_shift (风险等级: high, 分数: 0.78)
- L1_distribution_shift (风险等级: medium, 分数: 0.42)
- L1_distribution_shift (风险等级: medium, 分数: 0.45)
- L1_distribution_shift (风险等级: medium, 分数: 0.45)
- L1_distribution_shift (风险等级: medium, 分数: 0.42)
- L1_distribution_shift (风险等级: medium, 分数: 0.44)
- L1_distribution_shift (风险等级: medium, 分数: 0.42)
- L1_distribution_shift (风险等级: medium, 分数: 0.43)
- L1_distribution_shift (风险等级: medium, 分数: 0.42)
- L1_distribution_shift (风险等级: medium, 分数: 0.43)
- L1_distribution_shift (风险等级: high, 分数: 0.78)
- L1_distribution_shift (风险等级: medium, 分数: 0.43)
- L1_distribution_shift (风险等级: medium, 分数: 0.44)
- L1_distribution_shift (风险等级: medium, 分数: 0.45)
- L1_distribution_shift (风险等级: medium, 分数: 0.43)
- L1_distribution_shift (风险等级: medium, 分数: 0.42)
- L1_distribution_shift (风险等级: medium, 分数: 0.45)
- L1_distribution_shift (风险等级: medium, 分数: 0.43)
- L5_label_leakage (风险等级: high, 分数: 0.86)
- L5_label_leakage (风险等级: high, 分数: 0.89)
- L5_label_leakage (风险等级: high, 分数: 0.87)
- L5_label_leakage (风险等级: high, 分数: 0.88)
- L5_label_leakage (风险等级: high, 分数: 0.92)
- L5_label_leakage (风险等级: high, 分数: 0.86)
- L5_label_leakage (风险等级: high, 分数: 0.92)
- L5_label_leakage (风险等级: high, 分数: 0.93)
- L5_label_leakage (风险等级: high, 分数: 0.92)
- L5_label_leakage (风险等级: high, 分数: 0.86)
- L5_label_leakage (风险等级: high, 分数: 0.92)
- L5_label_leakage (风险等级: high, 分数: 0.95)

### diabetes_L1

- **基础数据集**: diabetes
- **注入类型**: global_scaling
- **预期等级**: medium
- **检测等级**: high
- **匹配**: ❌ 否
- **检测耗时**: 0.343s
- **检测项数**: 9

**检测到的泄露**:

- L1_distribution_shift (风险等级: medium, 分数: 0.44)
- L1_distribution_shift (风险等级: high, 分数: 0.81)
- L1_distribution_shift (风险等级: medium, 分数: 0.44)
- L1_distribution_shift (风险等级: medium, 分数: 0.44)
- L1_distribution_shift (风险等级: medium, 分数: 0.42)
- L1_distribution_shift (风险等级: medium, 分数: 0.45)
- L1_distribution_shift (风险等级: medium, 分数: 0.45)
- L1_distribution_shift (风险等级: medium, 分数: 0.46)
- L1_distribution_shift (风险等级: high, 分数: 0.81)

### timeseries_L6

- **基础数据集**: synthetic
- **注入类型**: temporal_overlap
- **预期等级**: high
- **检测等级**: error
- **匹配**: ❌ 否
- **检测耗时**: 0.000s
- **检测项数**: 0

### wine_clean

- **基础数据集**: wine
- **注入类型**: None (clean)
- **预期等级**: clean
- **检测等级**: high
- **匹配**: ❌ 否
- **检测耗时**: 28.513s
- **检测项数**: 21

**检测到的泄露**:

- L1_distribution_shift (风险等级: high, 分数: 0.80)
- L1_distribution_shift (风险等级: high, 分数: 0.81)
- L1_distribution_shift (风险等级: high, 分数: 0.81)
- L1_distribution_shift (风险等级: high, 分数: 0.78)
- L1_distribution_shift (风险等级: high, 分数: 0.83)
- L1_distribution_shift (风险等级: high, 分数: 0.79)
- L1_distribution_shift (风险等级: medium, 分数: 0.43)
- L1_distribution_shift (风险等级: medium, 分数: 0.44)
- L1_distribution_shift (风险等级: medium, 分数: 0.46)
- L1_distribution_shift (风险等级: high, 分数: 0.78)
- L1_distribution_shift (风险等级: medium, 分数: 0.45)
- L1_distribution_shift (风险等级: medium, 分数: 0.43)
- L1_distribution_shift (风险等级: medium, 分数: 0.46)
- L5_label_leakage (风险等级: high, 分数: 0.91)
- L5_label_leakage (风险等级: high, 分数: 0.90)
- L5_label_leakage (风险等级: high, 分数: 0.95)
- L5_label_leakage (风险等级: high, 分数: 0.89)
- L5_label_leakage (风险等级: high, 分数: 0.95)
- L5_label_leakage (风险等级: high, 分数: 0.95)
- L5_label_leakage (风险等级: high, 分数: 0.95)
- L5_label_leakage (风险等级: high, 分数: 0.95)

## 与竞品对比

| 工具 | L1 | L4 | L5 | L6 | 总体检出率 |
|------|----|----|----|----|----------|
| LeakShield | ✅ | ✅ | ✅ | ✅ | 33.3% |
| deepchecks | - | - | - | - | 待测试 |
| Evidently | - | - | - | - | 待测试 |

> **注**: deepchecks 和 Evidently 的对比数据待运行 `benchmarks/run_deepchecks.py` 和 `benchmarks/run_evidently.py` 后填充。

## 性能分析

- **平均检测耗时**: 18.492s
- **最快检测**: 0.000s
- **最慢检测**: 65.361s

## 结论

LeakShield 在基准测试中检出率为 33.3%，需要进一步优化。

### 优势

- 轻量级，易于使用
- 直接传入 DataFrame，无需额外配置
- 提供统一的风险评分和等级
- 支持多种泄露类型检测

### 改进方向

- 提高检测精度，减少误报和漏报
- 优化性能，提升检测速度
- 扩展支持更多泄露类型（L2, L7, L8）
