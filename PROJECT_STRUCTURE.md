# LeakShield 项目结构

## 核心模块

```
LeakShield/
├── leakshield/                 # 核心库
│   ├── __init__.py            # 主入口，check() 函数
│   ├── config.py              # 配置参数
│   ├── result.py              # 结果数据结构
│   ├── report.py              # 报告生成
│   ├── cli.py                 # 命令行工具
│   └── engines/               # 检测引擎
│       ├── __init__.py
│       ├── base.py            # 引擎基类
│       ├── hash_engine.py     # L4 哈希检测
│       ├── mdf_engine.py      # L1/L5/L6 多维特征检测
│       └── image_engine.py    # L4 图像检测 (v0.3.0 新增)
│
├── tests/                      # 单元测试
│   ├── conftest.py
│   ├── test_hash_engine.py
│   ├── test_mdf_engine.py
│   ├── test_result.py
│   └── test_image_engine.py   # v0.3.0 新增
│
├── benchmarks/                 # 基准测试
│   ├── run_benchmark.py       # 基准测试脚本
│   └── results/
│       └── benchmark_results.json
│
├── examples/                   # 示例
│   └── basic_usage.ipynb
│
├── pyproject.toml             # 项目配置
├── README.md                  # 项目说明
├── BENCHMARK.md               # 基准测试报告
├── CHANGELOG.md               # 变更日志
├── FEATURES.md                # 功能列表
└── .gitignore                 # Git 忽略文件
```

## 模块说明

### 1. leakshield/__init__.py
- `check()`: 主入口函数，支持 DataFrame 和图像路径
- 自动检测输入类型并调用相应引擎

### 2. leakshield/engines/
- **base.py**: 引擎抽象基类
- **hash_engine.py**: L4 样本重复检测（SHA-256 + MinHash）
- **mdf_engine.py**: L1/L5/L6 检测（分布偏移、标签泄露、时序穿越）
- **image_engine.py**: L4 图像检测（文件哈希 + 感知哈希）

### 3. leakshield/result.py
- `LeakageItem`: 单个泄露项
- `LeakageResult`: 完整检测结果
- `overall_level`: 综合风险等级计算

### 4. tests/
- 33 个单元测试
- 71% 代码覆盖率
- 100% 测试通过率

### 5. benchmarks/
- 6 个基准测试用例
- 100% 检出率
- 自动生成 BENCHMARK.md

## 依赖关系

### 核心依赖
```
pandas>=1.5.0
numpy>=1.21.0
scikit-learn>=1.1.0
scipy>=1.9.0
datasketch>=1.5.0
click>=8.0.0
rich>=12.0.0
```

### 可选依赖
```
[image]
Pillow>=9.0.0
```

## 使用流程

```
用户输入 (DataFrame/图像路径)
    ↓
check() 函数
    ↓
检测输入类型
    ↓
    ├─→ DataFrame → HashEngine + MDFEngine
    └─→ 图像路径 → ImageEngine
    ↓
返回 LeakageResult
    ↓
result.report() 或 result.to_json()
```

## 检测类型

| 编号 | 泄露类型 | 引擎 | 状态 |
|------|---------|------|------|
| L1 | 预处理未先分割 | MDF | ✅ v0.2 |
| L4 | 样本重复 | Hash | ✅ v0.1 |
| L4 | 图像重复 | Image | ✅ v0.3 |
| L5 | 标签泄露 | MDF | ✅ v0.2 |
| L6 | 时序穿越 | MDF | ✅ v0.2 |

## 开发指南

### 运行测试
```bash
pytest tests/ -v
```

### 运行基准测试
```bash
python benchmarks/run_benchmark.py
```

### 代码覆盖率
```bash
pytest tests/ --cov=leakshield --cov-report=html
```

### 安装开发依赖
```bash
pip install -e ".[dev,image]"
```

## 版本历史

- **v0.3.0** (2024): 图像检测 + 100% 基准测试
- **v0.2.0** (2024): MDF 引擎 (L1/L5/L6)
- **v0.1.0** (2024): Hash 引擎 (L4)
