# LeakShield

> 轻量级机器学习数据泄露检测库 - 三行代码，守护模型可信度

[![CI](https://github.com/yourusername/leakshield/workflows/CI/badge.svg)](https://github.com/yourusername/leakshield/actions)
[![Python Version](https://img.shields.io/pypi/pyversions/leakshield)](https://pypi.org/project/leakshield/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 一句话介绍

LeakShield 是一个专注于数据层的机器学习泄露检测库，基于 Kapoor & Narayanan (2023) 提出的八类数据泄露分类法，通过分析 DataFrame 的分布、重叠和关联来识别潜在的数据泄露风险。

## 为什么需要它？

数据泄露是机器学习中最隐蔽但影响最严重的问题之一。根据 Kapoor & Narayanan 在 Cell Press Patterns 发表的研究，数据泄露可分为八大类型（L1-L8），其中许多泄露发生在数据层面而非代码层面。

常见的数据泄露场景：
- 训练集和测试集存在样本重叠（L4）
- 特征分布在训练/测试集间异常偏移（L1）
- 特征与标签的关联在测试集中泄露（L3/L5）
- 时序数据的时间边界处理不当（L6）

LeakShield 专注于这些数据层检测，与代码静态分析工具（如 LeakageDetector）形成互补。

## 安装

```bash
pip install leakshield
```

## 快速开始

三行代码完成检测：

```python
import leakshield as ls

result = ls.check(train_df, test_df)
result.report()
```

输出示例：

```
╔══════════════════════════════════════════╗
║         LeakShield 检测报告              ║
╚══════════════════════════════════════════╝

训练集: (1000, 10)   测试集: (200, 10)

综合风险等级: HIGH  (score: 0.82)

[1] L4_exact_duplicate  ▶  HIGH
    依据: Kapoor & Narayanan 2023, Type 4
    影响: 45 / 200 (22.5%)
    说明: 测试集中发现 45 个样本与训练集完全重复
    修复: 使用 train_test_split 前请确认数据集无重复
─────────────────────────────────────────
共发现 1 项泄露风险
```

## 支持的检测类型

| 类型 | 描述 | 状态 |
|------|------|------|
| L1 | 特征分布偏移 | ✅ 已实现（Wasserstein + KS 检验） |
| L2 | 预处理信息泄露 | ❌ 不支持（需代码分析） |
| L3 | 特征-标签关联泄露 | ✅ 已实现（互信息检测） |
| L4 | 样本重叠（精确/近似） | ✅ 已实现 |
| L5 | 预测目标泄露 | ✅ 已实现（互信息/相关系数） |
| L6 | 时序数据泄露 | ✅ 已实现 |
| L7 | 模型迭代泄露 | ❌ 不支持（超出数据层范畴） |
| L8 | 评估流程泄露 | ❌ 不支持（需代码分析） |

## 与竞品对比

| 工具 | 定位 | 检测层面 | 易用性 | LeakShield 优势 |
|------|------|----------|--------|----------------|
| **deepchecks** | 全面数据验证 | 数据质量 + 部分泄露 | 中等 | 专注泄露检测，更轻量 |
| **Evidently** | 模型监控 | 分布漂移 + 性能监控 | 中等 | 专注训练时泄露，非生产监控 |
| **LeakageDetector** | 代码静态分析 | 代码层（AST） | 高 | 互补工具（数据层 vs 代码层） |
| **LeakShield** | 数据泄露检测 | 数据层（DataFrame） | 极高 | 三行代码，统一报告，分类法对齐 |

注：LeakageDetector 是互补工具而非竞品，建议同时使用以覆盖代码层和数据层。

## 命令行使用

### 表格数据检测

```bash
# 基础检测
leakshield check train.csv test.csv

# 输出 JSON 格式
leakshield check train.csv test.csv --output json --output-file result.json

# 指定任务类型
leakshield check train.csv test.csv --task-type classification
```

### 图像数据检测

LeakShield 还提供了图像数据集泄露检测工具：

```bash
# 检测图像数据集
python check_image_leakage.py ./my_dataset

# 数据集结构：
# my_dataset/
# ├── train/
# ├── val/
# └── test/
```

详见 [IMAGE_LEAKAGE_DETECTION.md](IMAGE_LEAKAGE_DETECTION.md)

## 自定义配置

```python
import leakshield as ls

config = ls.DetectionConfig(
    task_type='classification',           # 任务类型
    hash_similarity_threshold=0.95,       # MinHash 相似度阈值
    enable_hash=True,                     # 启用 Hash 引擎
    enable_mdf=True,                      # 启用 MDF 引擎（第二阶段）
    wasserstein_high=0.15,                # Wasserstein 距离高风险阈值
    ks_high=0.10,                         # KS 统计量高风险阈值
    mi_high=0.30,                         # 互信息高风险阈值
)

result = ls.check(train_df, test_df, config)
result.report()
```

## 开发路线图

### 第一阶段（v0.1.0）✅
- [x] 基础架构（引擎、配置、结果）
- [x] Hash 引擎（L4 精确/近似重复检测）
- [x] 命令行接口
- [x] 单元测试覆盖
- [x] CI/CD 流程

### 第二阶段（v0.2.0）✅
- [x] MDF 引擎实现
  - [x] Wasserstein 距离 + KS 检验（L1）
  - [x] 互信息检测（L3/L5）
  - [x] 时序校验（L6）
- [x] 完整测试覆盖（24 个测试全部通过）
- [x] 演示脚本

### 第三阶段（计划 0.3.0）
- [ ] 性能基准测试
- [ ] 可视化报告
- [ ] FastAPI 接口
- [ ] 批量检测支持
- [ ] 自定义检测规则
- [ ] 集成到 CI/CD 工具链

## 参考文献

- Kapoor, S., & Narayanan, A. (2023). Leakage and the Reproducibility Crisis in ML-based Science. *Patterns*, 4(9), 100804. [https://doi.org/10.1016/j.patter.2023.100804](https://doi.org/10.1016/j.patter.2023.100804)

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
