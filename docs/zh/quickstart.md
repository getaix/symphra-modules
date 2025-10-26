# 快速开始

本指南将帮助您快速上手 Symphra Modules,从安装到编写第一个模块。

## 环境要求

- Python 3.11 或更高版本
- uv (推荐) 或 pip

## 安装

### 使用 uv (推荐)

```bash
# 创建新项目
uv init my-project
cd my-project

# 添加依赖
uv add symphra-modules
```

### 使用 pip

```bash
pip install symphra-modules
```

## 第一个模块

### 1. 创建模块目录

```bash
mkdir -p modules
```

### 2. 定义模块

创建文件 `modules/hello.py`:

```python
from symphra_modules.abc import BaseModule, ModuleMetadata

class HelloModule(BaseModule):
    """示例模块."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="hello",
            version="1.0.0",
            description="一个简单的问候模块"
        )

    def bootstrap(self) -> None:
        """模块引导,在注册时调用."""
        print("HelloModule: 引导完成")

    def install(self, config: dict | None = None) -> None:
        """安装模块."""
        super().install(config)
        print(f"HelloModule: 已安装,配置: {config}")

    def start(self) -> None:
        """启动模块."""
        print("HelloModule: 已启动")
        print(f"配置: {self.get_config()}")

    def stop(self) -> None:
        """停止模块."""
        print("HelloModule: 已停止")

    def uninstall(self) -> None:
        """卸载模块."""
        super().uninstall()
        print("HelloModule: 已卸载")
```

### 3. 使用模块管理器

创建文件 `main.py`:

```python
from symphra_modules import ModuleManager

def main():
    # 创建管理器
    manager = ModuleManager(module_dirs=["modules"])

    # 发现可用模块
    available = manager.discover_modules()
    print(f"可用模块: {available}")

    # 加载模块
    module = manager.load_module("hello")
    print(f"已加载: {module.metadata.name}")

    # 安装模块
    manager.install_module("hello", config={"greeting": "你好"})

    # 启动模块
    manager.start_module("hello")

    # 停止模块
    manager.stop_module("hello")

    # 卸载模块
    manager.uninstall_module("hello")

if __name__ == "__main__":
    main()
```

### 4. 运行

```bash
python main.py
```

输出:

```
可用模块: ['hello']
HelloModule: 引导完成
已加载: hello
HelloModule: 已安装,配置: {'greeting': '你好'}
HelloModule: 已启动
配置: {'greeting': '你好'}
HelloModule: 已停止
HelloModule: 已卸载
```

## 带依赖的模块

### 定义基础模块

`modules/database.py`:

```python
from symphra_modules.abc import BaseModule, ModuleMetadata

class DatabaseModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(name="database")

    def start(self) -> None:
        self.connection = "database_connected"  # type: ignore[attr-defined]
        print("数据库已连接")

    def stop(self) -> None:
        self.connection = None  # type: ignore[attr-defined]
        print("数据库已断开")
```

### 定义依赖模块

`modules/user_service.py`:

```python
from symphra_modules.abc import BaseModule, ModuleMetadata

class UserServiceModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="user_service",
            dependencies=["database"]  # 依赖 database 模块
        )

    def start(self) -> None:
        print("用户服务已启动,数据库可用")
```

### 使用依赖解析

```python
from symphra_modules import ModuleManager
from symphra_modules.resolver import DependencyResolver
from symphra_modules.config import ModuleMetadata

# 创建管理器
manager = ModuleManager(module_dirs=["modules"])

# 发现并加载所有模块
modules = manager.load_all_modules()

# 创建依赖解析器
resolver = DependencyResolver()
for module in modules.values():
    resolver.add_module(module.metadata)

# 获取加载顺序
load_order = resolver.resolve()
print(f"加载顺序: {load_order}")  # ['database', 'user_service']

# 按顺序启动
for name in load_order:
    manager.install_module(name)
    manager.start_module(name)
```

## 异步模块

### 定义异步模块

`modules/async_worker.py`:

```python
import asyncio
from symphra_modules.abc import BaseModule, ModuleMetadata

class AsyncWorkerModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(name="async_worker")

    async def start(self) -> None:
        """异步启动."""
        await asyncio.sleep(0.1)
        print("异步工作器已启动")
        self.running = True  # type: ignore[attr-defined]

    async def stop(self) -> None:
        """异步停止."""
        self.running = False  # type: ignore[attr-defined]
        await asyncio.sleep(0.1)
        print("异步工作器已停止")
```

### 使用异步模块

```python
import asyncio
from symphra_modules import ModuleManager
from symphra_modules.abc import call_module_method

async def main():
    manager = ModuleManager(module_dirs=["modules"])

    # 加载模块
    module = manager.load_module("async_worker")
    manager.install_module("async_worker")

    # 使用统一接口调用异步方法
    await call_module_method(module, "start")
    await call_module_method(module, "stop")

if __name__ == "__main__":
    asyncio.run(main())
```

## 事件订阅

### 订阅模块事件

```python
from symphra_modules import ModuleManager
from symphra_modules.events import EventBus, Event

# 创建事件总线
event_bus = EventBus()

# 订阅所有事件
@event_bus.subscribe("*")
def log_all_events(event: Event) -> None:
    print(f"[事件] {event.event_type}: {event.module_name}")

# 订阅特定事件
@event_bus.subscribe("module.started")
def on_started(event: Event) -> None:
    print(f"模块 {event.module_name} 已启动!")

# 创建管理器并注入事件总线
manager = ModuleManager()
manager.registry.event_bus = event_bus

# 操作模块会触发事件
manager.load_module("hello")
manager.install_module("hello")
manager.start_module("hello")
```

## 配置验证

### 定义带验证的模块

```python
from symphra_modules.abc import BaseModule, ModuleMetadata

class ConfigurableModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="configurable",
            config_schema={
                "host": str,
                "port": int,
                "enabled": bool
            }
        )

    def validate_config(self, config: dict | None = None) -> bool:
        """验证配置."""
        if config is None:
            return False

        required = {"host", "port"}
        if not required.issubset(config.keys()):
            return False

        if not isinstance(config["host"], str):
            return False
        if not isinstance(config["port"], int):
            return False

        return True

    def start(self) -> None:
        config = self.get_config()
        print(f"服务器启动: {config['host']}:{config['port']}")
```

### 使用配置验证

```python
from symphra_modules import ModuleManager
from symphra_modules.exceptions import ModuleConfigError

manager = ModuleManager(module_dirs=["modules"])
manager.load_module("configurable")

try:
    # 无效配置会失败
    manager.install_module("configurable", config={"invalid": "config"})
except ModuleConfigError as e:
    print(f"配置错误: {e}")

# 有效配置
manager.install_module("configurable", config={
    "host": "localhost",
    "port": 8080,
    "enabled": True
})
manager.start_module("configurable")
```

## 下一步

- [基本概念](guide/concepts.md) - 了解核心概念
- [模块定义](guide/module-definition.md) - 深入学习模块定义
- [生命周期](guide/lifecycle.md) - 掌握模块生命周期
- [API 参考](api/abc.md) - 查看完整 API 文档
