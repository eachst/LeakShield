# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2024-03-03

### Added
- **MDF 引擎完整实现**
  - L1: 特征分布偏移检测（Wasserstein 距离 + KS 检验）
  - L3/L5: 标签泄露检测（互信息 + 相关系数）
  - L6: 时序数据泄露检测
- 并行处理支持（joblib threading backend）
- 9 个新的 MDF 引擎测试用例
- MDF 引擎演示脚本（demo_mdf.py）
- 分类和回归任务自动识别
- 置换检验和卡方检验用于 p-value 计算

### Changed
- 测试覆盖率从 59% 提升到 67%
- MDF 引擎版本从 0.0.1-placeholder 更新到 0.2.0
- 更新 README 和文档，标记 L1/L3/L5/L6 为已实现

### Fixed
- Windows 中文路径下 joblib 的编码问题（使用 threading backend）
- 单列检测失败不影响其他列的容错机制

## [0.1.0] - 2024-03-03

### Added
- 项目初始化和基础架构
- Hash 引擎实现
  - L4: 精确重复检测（SHA-256）
  - L4: 近似重复检测（MinHash LSH）
- 核心数据结构
  - LeakageResult
  - LeakageItem
  - DetectionConfig
- 格式化报告输出（rich 库）
- 命令行接口（click）
- 17 个单元测试
- CI/CD 配置（GitHub Actions）
- 基础演示脚本（demo.py）
- 完整的项目文档

### Technical Details
- Python >= 3.9 支持
- 自动特征列识别
- 标签列排除逻辑
- 缺失值处理
- 数值精度控制（6 位小数）

## [Unreleased]

### Planned for 0.3.0
- 性能基准测试
- 可视化报告（HTML/PDF）
- FastAPI 接口
- 批量检测支持
- 自定义检测规则
- CI/CD 工具链集成
