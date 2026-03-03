# LeakShield

> 轻量级机器学习数据泄露检测库 - 三行代码，守护模型可信度

[![Tests](https://img.shields.io/badge/tests-24%20passed-success)](https://github.com/yourusername/leakshield/actions)
[![Coverage](https://img.shields.io/badge/coverage-67%25-yellow)](https://github.com/yourusername/leakshield)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
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

基于 [Kapoor & Narayanan (2023)](https://doi.org/10.1016/j.patter.2023.100804) 的八类数据泄露分类法：

| 编号 | 泄露类型 | 状态 | 引擎 | 说明 |
|------|---------|------|------|------|
| L1 | 预处理未先分割 | ✅ v0.2 | MDF | Wasserstein + KS 检验 |
| L2 | 使用不合法特征 | ⏳ 计划中 | - | 需要领域知识 |
| L3 | 特征工程穿越 | ✅ v0.2 | MDF | 通过 L1 分布偏移检测 |
| L4 | 样本重复 | ✅ v0.1 | Hash | SHA-256 + MinHash |
| L5 | 标签泄露 | ✅ v0.2 | MDF | 互信息 + 相关系数 |
| L6 | 时序穿越 | ✅ v0.2 | MDF | 时间范围校验 |
| L7 | 多重比较泄露 | ❌ 暂不支持 | - | 超出数据层范畴 |
| L8 | 概念漂移 | ❌ 暂不支持 | - | 需要代码分析 |

**当前版本 (v0.2.0) 支持**: L1, L3, L4, L5, L6

## 与竞品对比

| 工具 | 检测层次 | 使用方式 | 统一评分 | LeakShield 优势 |
|------|---------|---------|---------|----------------|
| **deepchecks** | 数据层 | Dataset 对象 | 无 | 专注泄露检测，更轻量 |
| **Evidently** | 数据层 | Report 对象 | 无 | 专注训练时泄露，非生产监控 |
| **LeakageDetector** | 代码层 | VS Code 插件 | 无 | 互补工具（数据层 vs 代码层） |
| **LeakShield** | 数据层 | 直接传 DataFrame | 有 | 三行代码，统一报告，分类法对齐 |

**注**: LeakageDetector 是互补工具而非竞品，建议同时使用以覆盖代码层和数据层。

### 详细对比

- **deepchecks**: 全面的数据验证框架，包含数据质量、模型评估等多个模块，但泄露检测不是核心功能
- **Evidently**: 专注于生产环境的模型监控和数据漂移检测，适合部署后使用
- **LeakageDetector**: 通过静态代码分析检测代码层泄露（如变量使用顺序错误），与 LeakShield 形成完美互补
- **LeakShield**: 专注于训练时的数据层泄露检测，轻量级，易于集成到训练流程中

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

## 性能基准测试

LeakShield 在标准数据集上的检测性能：

| 数据集 | 样本数 | 特征数 | 检测耗时 | 检出率 |
|--------|--------|--------|---------|--------|
| Iris | 150 | 4 | <1s | 100% |
| Breast Cancer | 569 | 30 | ~65s | 100% |
| Diabetes | 442 | 10 | <1s | 检测中 |
| Wine | 178 | 13 | ~29s | 检测中 |

详细基准测试报告见 [BENCHMARK.md](BENCHMARK.md)

**注**: 基准测试使用 sklearn 数据集并人工注入泄露，测试环境为 Python 3.14.0。

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

1. Kapoor, S., & Narayanan, A. (2023). Leakage and the Reproducibility Crisis in ML-based Science. *Patterns*, 4(9), 100804. [https://doi.org/10.1016/j.patter.2023.100804](https://doi.org/10.1016/j.patter.2023.100804) | [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10499856/)

2. Eljundi, M., Dhillon, A., Agarwal, A., & Chehab, A. (2025). Data leakage in deep learning studies of translational EEG. *PeerJ Computer Science*, 11, e2730. [https://doi.org/10.7717/peerj-cs.2730](https://doi.org/10.7717/peerj-cs.2730)

3. Hyun, M., Lee, S., & Ryu, D. (2025). LeakageDetector: Detecting Information Leakage Bugs in Machine Learning Pipelines. *IEEE SANER 2025*.

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
