# Symphra Modules 测试文档

本目录包含 Symphra Modules 项目的所有测试，按照测试类型进行组织。

## 📁 目录结构

```
tests/
├── unit/                  # 单元测试 - 测试单个类或函数
│   ├── test_core_module.py          # Module 基类测试
│   ├── test_state.py                # 状态机测试
│   ├── test_dependency_graph.py      # 依赖图测试
│   ├── test_dependency_resolver.py   # 依赖解析器测试
│   ├── test_persistence.py           # 状态持久化测试
│   └── test_loader.py                # 模块加载器测试
├── integration/           # 集成测试 - 测试多个组件协作
│   ├── test_module_manager.py        # ModuleManager 核心功能
│   ├── test_lifecycle.py             # 生命周期管理
│   ├── test_async.py                 # 异步操作
│   ├── test_error_handling.py        # 错误处理
│   └── test_load_with_dependencies.py
├── performance/           # 性能测试 - 负载、并发、大规模
│   ├── test_load_performance.py      # 加载性能测试
│   └── test_concurrent.py            # 并发操作测试
├── fixtures/              # 测试固件和数据
├── test_all.py            # 完整测试集（包含所有测试）
├── conftest.py            # pytest 配置和共享 fixtures
├── TEST_STRUCTURE.md      # 详细的测试结构文档
└── README.md              # 本文件
```

## 🧪 测试类型

### 单元测试 (Unit Tests)

**目的**: 测试单个类、函数的行为，确保每个组件独立工作正常。

**特点**:
- 快速执行（每个测试 < 100ms）
- 不依赖文件系统或网络
- 使用 mock 和 stub 隔离依赖
- 高度聚焦于单一功能

**运行**:
```bash
# 运行所有单元测试
uv run pytest tests/unit/ -v

# 运行特定单元测试文件
uv run pytest tests/unit/test_core_module.py -v

# 快速运行（跳过慢速测试）
uv run pytest tests/unit/ -v -m "not slow"
```

### 集成测试 (Integration Tests)

**目的**: 测试多个组件之间的协作，确保系统整体功能正常。

**特点**:
- 测试真实场景
- 可以使用临时文件系统
- 测试组件间的交互
- 执行时间较长

**运行**:
```bash
# 运行所有集成测试
uv run pytest tests/integration/ -v

# 运行特定集成测试
uv run pytest tests/integration/test_module_manager.py -v
```

### 性能测试 (Performance Tests)

**目的**: 验证系统在高负载、大规模场景下的性能表现。

**特点**:
- 测试加载速度、内存使用等
- 验证并发安全性
- 设置性能基准
- 可能耗时较长

**运行**:
```bash
# 运行所有性能测试
uv run pytest tests/performance/ -v

# 运行特定性能测试
uv run pytest tests/performance/test_load_performance.py -v

# 跳过性能测试（用于快速验证）
uv run pytest -v -m "not performance"
```

## 🚀 常用测试命令

### 基本运行

```bash
# 运行所有测试
uv run pytest

# 运行所有测试并显示详细输出
uv run pytest -v

# 运行特定测试文件
uv run pytest tests/test_all.py -v

# 运行特定测试类
uv run pytest tests/unit/test_core_module.py::TestModule -v

# 运行特定测试方法
uv run pytest tests/unit/test_core_module.py::TestModule::test_module_basic -v
```

### 覆盖率报告

```bash
# 运行测试并生成覆盖率报告
uv run pytest --cov=symphra_modules --cov-report=html

# 查看未覆盖的代码行
uv run pytest --cov=symphra_modules --cov-report=term-missing

# 只看覆盖率摘要
uv run pytest --cov=symphra_modules --cov-report=term
```

### 调试测试

```bash
# 显示 print 输出
uv run pytest -s

# 在第一个失败处停止
uv run pytest -x

# 显示最慢的10个测试
uv run pytest --durations=10

# 运行失败的测试
uv run pytest --lf

# 只运行上次失败和新增的测试
uv run pytest --lf --ff
```

### 并行运行（需要 pytest-xdist）

```bash
# 使用多个CPU核心并行运行
uv run pytest -n auto

# 使用4个进程并行
uv run pytest -n 4
```

## 📊 测试覆盖率目标

- **总体覆盖率**: 80%+
- **核心模块**: 90%+
- **关键路径**: 100%

当前覆盖率: **80.15%** ✅

## 🎯 测试原则

### 单元测试原则
1. **FIRST 原则**:
   - **F**ast: 快速执行
   - **I**solated: 相互独立
   - **R**epeatable: 可重复
   - **S**elf-validating: 自我验证
   - **T**imely: 及时编写

2. **测试覆盖**:
   - 正常路径
   - 边界条件
   - 错误处理
   - 异常情况

### 集成测试原则
1. 测试真实使用场景
2. 验证组件间的契约
3. 测试端到端工作流
4. 使用实际的临时文件系统

### 性能测试原则
1. 设置明确的性能基准
2. 测试最坏情况
3. 验证线程安全
4. 监控资源使用

## 📝 编写测试指南

### 测试命名

```python
# 好的测试名称 ✅
def test_module_loads_with_valid_name():
    pass

def test_circular_dependency_raises_error():
    pass

# 不好的测试名称 ❌
def test1():
    pass

def test_stuff():
    pass
```

### 测试结构（AAA模式）

```python
def test_example():
    # Arrange - 准备测试数据
    module = SimpleModule()

    # Act - 执行测试操作
    module.start()

    # Assert - 验证结果
    assert module.state == ModuleState.STARTED
```

### Fixture 使用

```python
@pytest.fixture
def temp_module_dir():
    """创建临时模块目录."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_with_fixture(temp_module_dir):
    manager = ModuleManager(temp_module_dir)
    assert manager is not None
```

## 🏷️ 测试标记（Markers）

```python
# 标记慢速测试
@pytest.mark.slow
def test_large_scale_loading():
    pass

# 标记性能测试
@pytest.mark.performance
def test_concurrent_operations():
    pass

# 跳过特定测试
@pytest.mark.skip(reason="功能未实现")
def test_future_feature():
    pass

# 条件跳过
@pytest.mark.skipif(sys.platform == "win32", reason="Windows不支持")
def test_unix_specific():
    pass
```

运行特定标记的测试:
```bash
# 只运行慢速测试
uv run pytest -v -m slow

# 跳过慢速测试
uv run pytest -v -m "not slow"

# 跳过性能测试
uv run pytest -v -m "not performance"
```

## 🔧 持续集成

在 CI 环境中，通常运行:

```bash
# 完整测试套件（跳过性能测试）
uv run pytest tests/ -v -m "not performance" --cov=symphra_modules --cov-report=xml

# 或者只运行单元测试和集成测试
uv run pytest tests/unit/ tests/integration/ -v --cov=symphra_modules
```

## 📚 相关文档

- [TEST_STRUCTURE.md](./TEST_STRUCTURE.md) - 详细的测试结构说明
- [PyTest Documentation](https://docs.pytest.org/) - pytest 官方文档
- [Coverage.py](https://coverage.readthedocs.io/) - 覆盖率工具文档

## 🤝 贡献指南

添加新测试时:

1. 确定测试类型（单元/集成/性能）
2. 放入对应目录
3. 遵循命名约定
4. 使用适当的 fixtures
5. 添加必要的文档字符串
6. 确保测试可以独立运行
7. 运行 `uv run pytest` 确保所有测试通过

## 📈 测试统计

- 总测试数: 102+
- 单元测试: 40+
- 集成测试: 50+
- 性能测试: 12+

最后更新: 2025-11-28
