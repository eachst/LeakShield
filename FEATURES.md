# LeakShield 功能详解

## 当前版本：v0.2.0

LeakShield 现已实现覆盖 L1/L3/L4/L5/L6 的完整数据层泄露检测能力。

---

## 检测能力矩阵

| 泄露类型 | 检测方法 | 风险等级判定 | 状态 |
|---------|---------|------------|------|
| **L1: 特征分布偏移** | Wasserstein 距离 + KS 检验 | high: wd>0.15 或 (ks>0.10 且 p<0.001)<br>medium: wd>0.08 或 (ks>0.06 且 p<0.01) | ✅ |
| **L3: 特征-标签关联** | 互信息（分类任务） | high: mi>0.30 且 p<0.01 | ✅ |
| **L4: 样本重叠（精确）** | SHA-256 哈希 | high: >5%<br>medium: >1%<br>low: ≤1% | ✅ |
| **L4: 样本重叠（近似）** | MinHash LSH | high: >5%<br>medium: >1%<br>low: ≤1% | ✅ |
| **L5: 预测目标泄露（分类）** | 互信息 + 置换检验/卡方检验 | high: mi>0.30 且 p<0.01 | ✅ |
| **L5: 预测目标泄露（回归）** | Pearson 相关系数 | high: \|r\|>0.9 且 p<0.01 | ✅ |
| **L6: 时序数据泄露** | 时间范围重叠检查 | high: 训练集最大时间 ≥ 测试集最小时间 | ✅ |

---

## 详细功能说明

### 1. L1 - 特征分布偏移检测

**检测原理：**
- 使用训练集的均值和标准差对训练集和测试集进行 Z-Score 归一化
- 计算 Wasserstein 距离（Earth Mover's Distance）
- 计算 KS 统计量（Kolmogorov-Smirnov test）

**适用场景：**
- 特征工程在数据分割前对全量数据进行 fit
- 数据预处理流程不一致
- 训练集和测试集来自不同分布

**示例：**
```python
# 训练集：标准正态分布
train_df = pd.DataFrame({
    "feature": np.random.randn(1000),
    "label": np.random.randint(0, 2, 1000)
})

# 测试集：均值偏移 3σ
test_df = pd.DataFrame({
    "feature": np.random.randn(200) + 3.0,
    "label": np.random.randint(0, 2, 200)
})

result = ls.check(train_df, test_df)
# 检测结果：L1_distribution_shift, HIGH
```

---

### 2. L3/L5 - 标签泄露检测

**分类任务（互信息）：**
- 小数据集（≤10000）：互信息 + 1000 次置换检验
- 大数据集（>10000）：互信息 + 卡方检验近似

**回归任务（相关系数）：**
- Pearson 相关系数 + p-value

**适用场景：**
- 特征包含未来信息（如使用了预测目标本身）
- 特征与标签存在因果倒置
- 数据泄露导致的异常高相关

**示例（分类）：**
```python
labels = np.random.randint(0, 2, 1000)
train_df = pd.DataFrame({
    "feature_normal": np.random.randn(1000),
    "feature_leak": labels.astype(float),  # 与标签完全相同
    "label": labels
})

result = ls.check(train_df, train_df)
# 检测结果：L5_label_leakage, HIGH, MI=0.69
```

**示例（回归）：**
```python
X = np.random.randn(1000)
y = X * 10 + np.random.randn(1000) * 0.1  # 强相关

train_df = pd.DataFrame({
    "feature_leak": X,
    "target": y
})

config = ls.DetectionConfig(task_type="regression")
result = ls.check(train_df, train_df, config)
# 检测结果：L5_label_leakage, HIGH, r=0.9999
```

---

### 3. L4 - 样本重叠检测

**精确重复（SHA-256）：**
- 对每行特征列按列名排序后拼接
- 数值保留 6 位小数
- 缺失值替换为 'LEAKSHIELD_MISSING'
- 计算 SHA-256 哈希

**近似重复（MinHash LSH）：**
- 仅处理数值型特征
- 使用 128 个置换的 MinHash
- 默认相似度阈值 0.9（可配置）

**适用场景：**
- train_test_split 前未去重
- 数据增强后的样本泄露
- 交叉验证时的数据泄露

**示例：**
```python
train_df = pd.DataFrame({...})  # 1000 行
test_df = train_df.iloc[:100]   # 直接复制 100 行

result = ls.check(train_df, test_df)
# 检测结果：
# - L4_exact_duplicate, 100/100 (100%), HIGH
# - L4_near_duplicate, 100/100 (100%), HIGH
```

---

### 4. L6 - 时序数据泄露检测

**检测原理：**
- 检查训练集最大时间是否 ≥ 测试集最小时间
- 自动转换时间戳列为 datetime 类型

**适用场景：**
- 时间序列数据未按时间顺序分割
- 训练集包含未来数据
- 滑动窗口划分错误

**示例：**
```python
# 训练集：2020-01-01 到 2020-12-31
train_df = pd.DataFrame({
    "feature": np.random.randn(365),
    "timestamp": pd.date_range("2020-01-01", periods=365, freq="D"),
    "label": np.random.randint(0, 2, 365)
})

# 测试集：2020-06-01 到 2021-06-01（重叠！）
test_df = pd.DataFrame({
    "feature": np.random.randn(365),
    "timestamp": pd.date_range("2020-06-01", periods=365, freq="D"),
    "label": np.random.randint(0, 2, 365)
})

config = ls.DetectionConfig(timestamp_col="timestamp")
result = ls.check(train_df, test_df, config)
# 检测结果：L6_temporal_leakage, HIGH, 重叠 212 天
```

---

## 配置参数

### DetectionConfig 完整参数

```python
config = ls.DetectionConfig(
    # 任务类型
    task_type="auto",  # 'auto' / 'classification' / 'regression' / 'timeseries'
    
    # 引擎开关
    enable_hash=True,   # 启用 Hash 引擎（L4）
    enable_mdf=True,    # 启用 MDF 引擎（L1/L3/L5/L6）
    
    # Hash 引擎参数
    hash_similarity_threshold=0.9,  # MinHash 相似度阈值
    
    # MDF 引擎参数
    wasserstein_high=0.15,    # Wasserstein 距离高风险阈值
    wasserstein_medium=0.08,  # Wasserstein 距离中风险阈值
    ks_high=0.10,             # KS 统计量高风险阈值
    ks_medium=0.06,           # KS 统计量中风险阈值
    mi_high=0.30,             # 互信息高风险阈值
    p_value_threshold=0.01,   # 统计检验 p 值阈值
    
    # 时序相关
    timestamp_col=None,  # 时间戳列名（启用 L6 检测）
    
    # 通用参数
    n_jobs=-1,          # 并行任务数（-1 表示使用所有 CPU）
    random_state=42     # 随机种子
)
```

---

## 性能特性

### 并行处理
- 使用 joblib threading backend
- 避免 Windows 中文路径编码问题
- 支持多核并行加速

### 容错机制
- 单列检测失败不影响其他列
- 自动跳过无效数据（全 NaN、样本量过小等）
- 友好的警告信息

### 自动化特性
- 自动识别标签列（label/target/y/output/class/outcome）
- 自动识别任务类型（分类/回归）
- 自动排除标签列进行特征检测

---

## 输出格式

### LeakageResult 对象

```python
result = ls.check(train_df, test_df)

# 属性
result.items              # List[LeakageItem]
result.overall_score      # float (0.0-1.0)
result.overall_level      # str ('clean'/'low'/'medium'/'high')
result.train_shape        # tuple
result.test_shape         # tuple
result.engine_versions    # dict

# 方法
result.report()           # 打印格式化报告
result.to_json(path)      # 保存为 JSON
result.to_dict()          # 转换为字典

# 魔术方法
len(result)               # 泄露项数量
bool(result)              # 是否有泄露
```

### LeakageItem 对象

```python
item = result.items[0]

item.leakage_type         # 'L1_distribution_shift'
item.taxonomy_ref         # 'Kapoor & Narayanan 2023, Type 1'
item.risk_level           # 'high' / 'medium' / 'low'
item.risk_score           # 0.85
item.affected_count       # 200
item.affected_ratio       # 1.0
item.detail               # 详细说明
item.fix_hint             # 修复建议
```

---

## 使用建议

### 1. 基础检测（推荐）
```python
result = ls.check(train_df, test_df)
result.report()
```

### 2. 仅检测样本重叠
```python
config = ls.DetectionConfig(enable_mdf=False)
result = ls.check(train_df, test_df, config)
```

### 3. 时序数据检测
```python
config = ls.DetectionConfig(timestamp_col="date")
result = ls.check(train_df, test_df, config)
```

### 4. 调整敏感度
```python
# 更严格的检测
config = ls.DetectionConfig(
    wasserstein_high=0.10,
    ks_high=0.08,
    mi_high=0.25
)

# 更宽松的检测
config = ls.DetectionConfig(
    wasserstein_high=0.20,
    ks_high=0.15,
    mi_high=0.40
)
```

---

## 限制和注意事项

### 不支持的检测类型
- **L2**: 预处理信息泄露（需要代码静态分析）
- **L7**: 模型迭代泄露（超出数据层范畴）
- **L8**: 评估流程泄露（需要代码静态分析）

### 性能考虑
- 大数据集（>100万行）建议采样后检测
- 互信息计算在大数据集上较慢（使用卡方近似）
- 并行处理可能增加内存占用

### 假阳性
- 小样本量可能导致分布检测过于敏感
- 建议训练集 ≥1000 行，测试集 ≥200 行
- 可通过调整阈值降低假阳性率

---

## 参考文献

Kapoor, S., & Narayanan, A. (2023). Leakage and the Reproducibility Crisis in ML-based Science. 
*Patterns*, 4(9), 100804. https://doi.org/10.1016/j.patter.2023.100804
