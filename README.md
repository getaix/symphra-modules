# Symphra Modules

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](https://opensource.org/licenses/MIT)
[![Test Coverage](https://img.shields.io/badge/coverage-80%25-yellowgreen)](./htmlcov/index.html)

高性能、高质量的 Python 模块管理库，支持动态加载、生命周期管理、依赖解析和异步操作。

## ✨ 核心特性

- 🚀 **高性能设计** - 智能缓存、内存优化(`__slots__`)、延迟加载
- 📦 **灵活加载** - 支持目录、包、自动加载多种方式
- 🔄 **生命周期管理** - 完整的状态机和钩子系统
- 🔗 **依赖解析** - Kahn算法拓扑排序,循环检测
- 📡 **事件驱动** - 发布订阅模式,通配符支持
- 🛡️ **类型安全** - mypy strict模式验证
- ⚡ **异步支持** - 原生支持同步/异步模块

## 📊 项目状态

- **测试**: 117 passed (100%)
- **覆盖率**: 79.78% (核心模块 80%+)
- **代码质量**: ruff + mypy strict
- **文档**: 中英双语 MkDocs

## 安装

```bash
pip install symphra-modules
```

或使用 uv:

```bash
uv add symphra-modules
```

## 🚀 快速开始

```python
from symphra_modules import ModuleManager
from symphra_modules.abc import BaseModule, ModuleMetadata

# 1. 定义模块
class MyModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(name="my_module", version="1.0.0")

    def start(self) -> None:
        print("模块已启动!")

# 2. 使用管理器
manager = ModuleManager()
manager.load_module("my_module", source="./modules")
manager.start_module("my_module")
```

## 📚 文档

### 在线文档

完整文档请访问: [Symphra Modules Documentation](https://symphra-modules.readthedocs.io)

### 本地预览

```bash
# 启动文档服务器
uv run mkdocs serve

# 访问 http://localhost:8000
```

### 构建文档

```bash
# 构建静态文档
uv run mkdocs build

# 文档生成在 site/ 目录
```

## 🧪 测试

```bash
# 运行所有测试
uv run pytest

# 运行测试并生成覆盖率报告
uv run pytest --cov=symphra_modules --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

## 开发

### 环境准备

```bash
# 克隆项目
git clone https://github.com/getaix/symphra-modules.git
cd symphra-modules

# 安装依赖
uv sync

# 安装 pre-commit hooks
pre-commit install
```

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行测试并显示覆盖率
uv run pytest --cov

# 运行特定测试
uv run pytest tests/unit/test_registry.py
```

### 代码质量检查

```bash
# 格式化代码
uv run ruff format .

# 代码检查
uv run ruff check .

# 类型检查
uv run mypy src
```

## 许可证

MIT License
