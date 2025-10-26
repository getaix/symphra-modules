# 加载模块

## 加载方式

Symphra Modules 支持多种模块加载方式，满足不同的使用场景。

### 目录加载

从指定目录自动发现和加载模块：

```python
from symphra_modules import ModuleManager

# 创建管理器
manager = ModuleManager()

# 从目录加载模块
await manager.load_from_directory("./modules")
```

目录结构示例：

```
modules/
├── user_module.py
├── payment/
│   ├── __init__.py
│   └── payment_module.py
└── logging_module.py
```

### 包加载

从 Python 包导入模块：

```python
# 从包加载
await manager.load_from_package("my_app.modules")
```

### 自动加载

智能检测源类型并自动选择加载方式：

```python
# 自动检测并加载
await manager.auto_load("./modules")  # 目录
await manager.auto_load("my_app.modules")  # 包
```

## 模块发现

### 文件模式匹配

支持 glob 模式匹配模块文件：

```python
# 加载所有 .py 文件
await manager.load_from_directory("./modules", pattern="*.py")

# 加载特定命名模式
await manager.load_from_directory("./modules", pattern="*_module.py")
```

### 递归加载

自动递归加载子目录中的模块：

```python
# 递归加载所有子目录
await manager.load_from_directory("./modules", recursive=True)
```

## 加载选项

### 异步加载

支持异步模块加载：

```python
# 异步加载
await manager.load_from_directory("./modules", async_load=True)
```

### 条件加载

基于条件加载模块：

```python
# 仅在生产环境加载
await manager.load_from_directory(
    "./modules",
    condition=lambda: os.getenv("ENV") == "production"
)
```

### 配置传递

在加载时传递配置：

```python
config = {"database_url": "sqlite:///app.db"}
await manager.load_from_directory("./modules", config=config)
```

## 加载器接口

自定义加载器需要实现 `BaseLoader` 接口：

```python
from symphra_modules.loader.abc import BaseLoader

class CustomLoader(BaseLoader):
    async def load_modules(self, source: str, **options) -> list[BaseModule]:
        # 自定义加载逻辑
        modules = []
        # ... 加载模块 ...
        return modules

# 注册自定义加载器
manager.register_loader("custom", CustomLoader())

# 使用自定义加载器
await manager.load_with_loader("custom", "my_source")
```

## 错误处理

加载过程中的错误会被适当处理：

- **模块导入错误**: 记录错误但不中断加载过程
- **配置验证失败**: 抛出异常阻止模块加载
- **循环依赖**: 在依赖解析阶段检测并报告

```python
try:
    await manager.load_from_directory("./modules")
except ModuleLoadError as e:
    print(f"Failed to load modules: {e}")
```

## 缓存优化

模块加载结果会被缓存以提高性能：

- **模块实例缓存**: 避免重复创建实例
- **元数据缓存**: 缓存模块元数据信息
- **依赖图缓存**: 缓存解析后的依赖关系

```python
# 启用缓存
manager.enable_cache()

# 清除缓存
manager.clear_cache()
```