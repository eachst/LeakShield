# 贡献指南

感谢你对 LeakShield 的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 报告 Bug

如果你发现了 bug，请在 [GitHub Issues](https://github.com/eachst/LeakShield/issues) 中创建一个新的 issue，并包含：

- 清晰的标题和描述
- 重现步骤
- 预期行为和实际行为
- 你的环境信息（Python 版本、操作系统等）
- 如果可能，提供最小可复现示例

### 提出新功能

如果你有新功能的想法：

1. 先在 Issues 中讨论，确保这个功能符合项目方向
2. 等待维护者的反馈
3. 如果获得批准，可以开始实现

### 提交代码

1. **Fork 仓库**
   ```bash
   # 在 GitHub 上 fork 仓库
   git clone https://github.com/你的用户名/LeakShield.git
   cd LeakShield
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **安装开发依赖**
   ```bash
   pip install -e ".[dev,image]"
   ```

4. **编写代码**
   - 遵循现有的代码风格
   - 添加必要的测试
   - 更新文档

5. **运行测试**
   ```bash
   # 运行所有测试
   pytest tests/ -v
   
   # 检查覆盖率
   pytest tests/ --cov=leakshield --cov-report=html
   
   # 运行基准测试
   python benchmarks/run_benchmark.py
   ```

6. **代码格式化**
   ```bash
   # 使用 black 格式化代码
   black leakshield/ tests/
   
   # 使用 ruff 检查代码
   ruff check leakshield/ tests/
   ```

7. **提交更改**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   # 或
   git commit -m "fix: fix your bug description"
   ```

8. **推送到 GitHub**
   ```bash
   git push origin feature/your-feature-name
   ```

9. **创建 Pull Request**
   - 在 GitHub 上创建 Pull Request
   - 填写 PR 模板
   - 等待代码审查

## 代码规范

### 提交信息格式

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `test:` 测试相关
- `refactor:` 代码重构
- `perf:` 性能优化
- `chore:` 构建/工具相关

示例：
```
feat: add image similarity detection using perceptual hash
fix: correct L1 threshold calculation for small samples
docs: update README with image detection examples
```

### Python 代码风格

- 使用 [Black](https://black.readthedocs.io/) 进行代码格式化
- 使用 [Ruff](https://docs.astral.sh/ruff/) 进行代码检查
- 遵循 [PEP 8](https://pep8.org/) 规范
- 添加类型注解（Type Hints）
- 编写清晰的文档字符串（Docstrings）

### 测试要求

- 所有新功能必须包含测试
- 测试覆盖率应保持在 70% 以上
- 所有测试必须通过
- 基准测试检出率应保持在 80% 以上

## 开发流程

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/eachst/LeakShield.git
cd LeakShield

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -e ".[dev,image]"

# 运行测试
pytest tests/ -v

# 运行基准测试
python benchmarks/run_benchmark.py
```

### 添加新的检测引擎

如果你想添加新的检测引擎：

1. 在 `leakshield/engines/` 中创建新文件
2. 继承 `BaseEngine` 类
3. 实现 `detect()` 方法
4. 返回 `List[LeakageItem]`
5. 在 `leakshield/engines/__init__.py` 中导出
6. 添加测试文件 `tests/test_your_engine.py`
7. 更新文档

示例：
```python
from leakshield.engines.base import BaseEngine
from leakshield.result import LeakageItem

class YourEngine(BaseEngine):
    name = "your_engine"
    version = "0.1.0"
    
    def detect(self, train_df, test_df, config):
        # 实现检测逻辑
        items = []
        # ... 检测代码 ...
        return items
```

## 文档

- 更新 README.md（如果添加新功能）
- 更新 CHANGELOG.md
- 添加代码注释和文档字符串
- 如果需要，添加使用示例

## 问题和讨论

- 使用 [GitHub Issues](https://github.com/eachst/LeakShield/issues) 报告问题
- 使用 [GitHub Discussions](https://github.com/eachst/LeakShield/discussions) 进行讨论

## 行为准则

- 尊重所有贡献者
- 保持友好和专业
- 接受建设性的批评
- 关注项目的最佳利益

## 许可证

通过贡献代码，你同意你的贡献将在 MIT 许可证下发布。

---

感谢你的贡献！🎉
