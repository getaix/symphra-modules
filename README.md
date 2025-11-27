# Symphra Modules

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](https://opensource.org/licenses/MIT)

优雅简洁的 Python 模块化框架 - 单文件实现，支持异步操作和热重载。

## ✨ 核心特性

- 🎯 **极简设计** - 单文件实现,约 440 行代码
- 🔗 **自动依赖解析** - Kahn 算法拓扑排序
- 🛡️ **循环检测** - 自动检测并阻止循环依赖
- 📦 **零依赖** - 仅使用 Python 标准库
- 🔒 **类型安全** - 完整类型注解,mypy strict 通过
- 🚀 **易于使用** - 声明式 API,清晰直观
- ⚡ **异步支持** - 原生支持同步/异步模块
- 🔥 **热重载** - 文件修改时自动重载模块

## 架构优势

**v2.0 重大改进**:
- ✅ 从多文件架构重构为单文件 (~440 行)
- ✅ 保留所有核心功能 (依赖解析、循环检测、生命周期管理)
- ✅ 零外部依赖,部署更简单
- ✅ 代码更易阅读和维护
- ✅ 新增异步支持和热重载功能

## 安装

```bash
# 基础安装
pip install symphra-modules

# 包含热重载功能
pip install symphra-modules[hot-reload]
```

或使用 uv:

```bash
# 基础安装
uv add symphra-modules

# 包含热重载功能
uv add symphra-modules[hot-reload]
```

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
from symphra_modules import Module, ModuleManager

# 1. 定义模块
class DatabaseModule(Module):
    name = "database"
    
    def start(self) -> None:
        print("数据库已连接")

# 2. 使用管理器
manager = ModuleManager("./modules")
db = manager.load("database")
manager.start("database")
```

## ⚡ 异步使用

```python
import asyncio
from symphra_modules import Module, ModuleManager

class AsyncModule(Module):
    name = "async_module"
    
    async def start_async(self) -> None:
        await asyncio.sleep(0.1)  # 模拟异步操作
        print("异步模块已启动!")

async def main():
    manager = ModuleManager("./modules")
    await manager.load_async("async_module")
    await manager.start_async("async_module")

# asyncio.run(main())
```

## 🔥 热重载使用

```python
from symphra_modules import ModuleManager

# 启用热重载
manager = ModuleManager("./modules", enable_hot_reload=True)
manager.enable_hot_reload_monitoring()

# 加载模块
manager.load("my_module")
manager.start("my_module")

# 修改模块文件时，系统会自动重载
```

## 📚 核心概念

### 模块定义

```python
class UserModule(Module):
    name = "user"
    version = "1.0.0"
    dependencies = ["database", "cache"]
    
    def start(self) -> None:
        # 启动逻辑
        pass
```

### 异步模块

异步模块支持完整的 async/await 模式：

```python
class AsyncDatabaseModule(Module):
    name = "async_database"
    
    async def start_async(self) -> None:
        # 异步启动逻辑
        await connect_to_database()
    
    async def stop_async(self) -> None:
        # 异步停止逻辑
        await disconnect_from_database()
```

### 热重载

热重载功能允许在开发过程中自动重载修改的模块：

1. 启用热重载监控
2. 修改模块文件时自动检测变化
3. 自动停止、重新加载并启动模块

### 依赖管理

模块管理器自动:
1. 解析依赖关系
2. 拓扑排序
3. 按正确顺序加载
4. 检测循环依赖

### 模块生命周期

```
LOADED → STARTED ⇄ STOPPED
```

- **LOADED**: 模块类已实例化
- **STARTED**: 模块运行中
- **STOPPED**: 模块已停止

异步模块支持相同的生命周期状态，但使用异步方法进行状态转换。

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
uv run pytest tests/test_all.py
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
