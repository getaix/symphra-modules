# 开发指南

## 开发环境设置

### 环境要求

- Python 3.11+
- uv (推荐) 或 pip
- Git

### 安装开发依赖

```bash
# 克隆项目
git clone https://github.com/getaix/symphra-modules.git
cd symphra-modules

# 使用 uv 安装（推荐）
uv sync --dev

# 或使用 pip
pip install -e .[dev]
```

### 开发工具

项目使用以下开发工具：

- **Black**: 代码格式化
- **isort**: 导入排序
- **mypy**: 静态类型检查
- **ruff**: 代码检查和修复
- **pytest**: 单元测试
- **coverage**: 测试覆盖率

## 代码规范

### 类型注解

项目要求 100% 类型覆盖，使用严格的 mypy 配置：

```python
from typing import Optional, Dict, List

def process_data(data: Dict[str, Any]) -> Optional[List[str]]:
    """处理数据并返回结果列表."""
    if not data:
        return None
    return [item.upper() for item in data.values()]
```

### 文档字符串

使用 Google 风格的文档字符串：

```python
def calculate_total(items: List[Dict[str, float]]) -> float:
    """计算商品总价.

    Args:
        items: 商品列表，每个商品包含价格信息

    Returns:
        总价

    Raises:
        ValueError: 当商品价格无效时

    Example:
        >>> calculate_total([{"price": 10.0}, {"price": 20.0}])
        30.0
    """
    return sum(item["price"] for item in items)
```

### 命名约定

- 类名: `PascalCase`
- 函数和变量: `snake_case`
- 常量: `UPPER_SNAKE_CASE`
- 私有成员: 前缀 `_`

## 项目结构

```
src/symphra_modules/
├── __init__.py          # 包初始化
├── abc.py              # 抽象基类
├── config.py           # 配置管理
├── events/             # 事件系统
├── exceptions.py       # 异常定义
├── loader/             # 模块加载器
├── manager.py          # 模块管理器
├── registry.py         # 模块注册表
├── resolver/           # 依赖解析器
└── utils/              # 工具函数

tests/                  # 测试文件
├── unit/              # 单元测试
├── integration/       # 集成测试
└── fixtures/          # 测试固件

docs/                  # 文档
├── guide/            # 用户指南
├── api/              # API 文档
└── examples/         # 示例

examples/              # 使用示例
```

## 开发工作流

### 1. 创建功能分支

```bash
git checkout -b feature/new-feature
```

### 2. 编写代码

遵循以下原则：

- **SOLID 原则**: 单一职责、开闭原则等
- **DRY 原则**: 不要重复自己
- **KISS 原则**: 保持简单

### 3. 编写测试

为新功能编写全面的测试：

```python
# tests/unit/test_new_feature.py
import pytest
from symphra_modules import NewFeature

class TestNewFeature:
    def test_basic_functionality(self):
        feature = NewFeature()
        result = feature.process("input")
        assert result == "expected_output"

    def test_edge_cases(self):
        feature = NewFeature()
        with pytest.raises(ValueError):
            feature.process(None)
```

### 4. 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_new_feature.py

# 带覆盖率报告
pytest --cov=symphra_modules --cov-report=html
```

### 5. 代码检查

```bash
# 格式化代码
black src/ tests/

# 排序导入
isort src/ tests/

# 类型检查
mypy src/

# 代码检查
ruff check src/ tests/

# 自动修复
ruff fix src/ tests/
```

### 6. 提交代码

```bash
git add .
git commit -m "feat: add new feature

- Add NewFeature class
- Implement process method
- Add comprehensive tests
- Update documentation"
```

## 贡献指南

### 提交信息格式

使用约定式提交格式：

```
type(scope): description

[optional body]

[optional footer]
```

类型：
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档更新
- `style`: 代码风格调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

### Pull Request 流程

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送分支
5. 创建 Pull Request
6. 等待代码审查
7. 合并更改

## 调试技巧

### 日志记录

使用结构化日志：

```python
import logging

logger = logging.getLogger(__name__)

def process_data(data):
    logger.debug("Processing data: %s", data)
    try:
        result = do_processing(data)
        logger.info("Data processed successfully")
        return result
    except Exception as e:
        logger.error("Failed to process data: %s", e)
        raise
```

### 调试异步代码

```python
import asyncio

async def debug_async_function():
    print("Starting async function")
    await asyncio.sleep(1)
    print("Async function completed")

# 使用调试模式运行
asyncio.run(debug_async_function(), debug=True)
```

## 性能优化

### 分析性能

```python
import cProfile
import pstats

def profile_function():
    # 要分析的代码
    pass

profiler = cProfile.Profile()
profiler.enable()
profile_function()
profiler.disable()

stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats()
```

### 内存优化

- 使用 `__slots__` 减少内存占用
- 避免循环引用
- 使用弱引用处理缓存

```python
class OptimizedClass:
    __slots__ = ('name', 'value')

    def __init__(self, name, value):
        self.name = name
        self.value = value
```

## 测试策略

### 单元测试

测试单个组件：

```python
def test_module_lifecycle():
    module = TestModule()
    assert module.state == ModuleState.NOT_INSTALLED

    module.install()
    assert module.state == ModuleState.INSTALLED

    module.start()
    assert module.state == ModuleState.STARTED
```

### 集成测试

测试组件间交互：

```python
def test_module_dependencies():
    manager = ModuleManager()

    # 加载有依赖关系的模块
    await manager.load_from_directory("./test_modules")

    # 验证依赖解析
    await manager.start_all()

    # 验证所有模块都正确启动
    assert all(module.is_started for module in manager.get_modules())
```

### 异步测试

```python
import pytest_asyncio

@pytest.mark.asyncio
async def test_async_module():
    module = AsyncModule()
    await module.start()
    assert module.is_started
    await module.stop()
    assert not module.is_started
```

## 发布流程

### 版本管理

使用语义化版本：

- `MAJOR.MINOR.PATCH`
- `MAJOR`: 不兼容的 API 更改
- `MINOR`: 向后兼容的功能添加
- `PATCH`: 向后兼容的修复

### 发布步骤

1. 更新版本号
2. 更新变更日志
3. 创建发布标签
4. 构建分发包
5. 上传到 PyPI

```bash
# 更新版本
uv version patch

# 构建
uv build

# 发布
uv publish
```

## 常见问题

### 导入错误

```python
# 错误：相对导入问题
from ..utils import helper  # 在可执行脚本中可能失败

# 正确：绝对导入
from symphra_modules.utils import helper
```

### 异步/同步混用

```python
# 错误：混用 async def 和 def
class MixedModule(BaseModule):
    async def start(self):  # async
        pass

    def stop(self):  # sync
        pass  # 这可能导致问题

# 正确：保持一致
class AsyncModule(BaseModule):
    async def start(self):
        pass

    async def stop(self):
        pass
```

### 依赖循环

```python
# 错误：循环依赖
# module_a.py 依赖 module_b
# module_b.py 依赖 module_a

# 正确：重构避免循环
# 使用事件系统或将共同代码提取到独立模块
```

## 资源链接

- [Python 官方文档](https://docs.python.org/3/)
- [Typing 模块文档](https://docs.python.org/3/library/typing.html)
- [AsyncIO 文档](https://docs.python.org/3/library/asyncio.html)
- [Pytest 文档](https://docs.pytest.org/)
- [MyPy 文档](https://mypy.readthedocs.io/)
