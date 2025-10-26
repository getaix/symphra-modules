# 示例

本章节提供 Symphra Modules 的完整使用示例。

## 基础示例

### 基本模块定义和使用

```python
from symphra_modules import BaseModule, ModuleManager, ModuleMetadata

class HelloModule(BaseModule):
    """示例模块 - Hello World."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="hello",
            version="1.0.0",
            description="一个简单的 Hello World 模块",
        )

    def start(self) -> None:
        print(f"Hello from {self.metadata.name}!")

    def stop(self) -> None:
        print(f"Goodbye from {self.metadata.name}!")

# 使用模块
manager = ModuleManager()
manager.registry.register("hello", HelloModule)

# 安装并启动模块
manager.install_module("hello")
manager.start_module("hello")

# 检查状态
print(f"已加载的模块: {manager.list_modules()}")
```

## 依赖管理示例

### 模块依赖解析

```python
from symphra_modules import DependencyResolver, ModuleMetadata

# 创建依赖解析器
resolver = DependencyResolver()

# 定义模块及其依赖
resolver.add_module(ModuleMetadata(name="database", dependencies=[]))
resolver.add_module(ModuleMetadata(name="cache", dependencies=["database"]))
resolver.add_module(ModuleMetadata(name="api", dependencies=["database", "cache"]))

# 解析依赖顺序
try:
    order = resolver.resolve_dependencies()
    print(f"加载顺序: {order}")
except CircularDependencyError as e:
    print(f"检测到循环依赖: {e}")
```

### 依赖注入

```python
class DatabaseModule(BaseModule):
    def start(self) -> None:
        self.connection = create_database_connection()

class APIModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="api",
            dependencies=["database"]
        )

    def start(self) -> None:
        # 获取依赖的数据库模块
        db_module = self.manager.get_module("database")
        self.db_connection = db_module.connection
```

## 事件系统示例

### 基本事件发布和订阅

```python
from symphra_modules import EventBus

# 创建事件总线
bus = EventBus()

# 定义事件处理器
@bus.subscribe("user.created")
def handle_user_created(user_id: int, email: str):
    print(f"New user created: {user_id} - {email}")

@bus.subscribe("user.*")  # 通配符订阅
def handle_all_user_events(event_type: str, **data):
    print(f"User event: {event_type}")

# 发布事件
bus.publish("user.created", user_id=123, email="user@example.com")
```

### 异步事件处理

```python
import asyncio

@bus.subscribe("data.process")
async def async_data_processor(data: dict):
    # 异步处理数据
    await process_data_async(data)
    # 发布处理完成事件
    await bus.publish("data.processed", data_id=data["id"])
```

## 目录加载示例

### 从目录自动加载模块

```python
# 项目结构
# modules/
# ├── user.py
# ├── payment.py
# └── notification.py

from symphra_modules import ModuleManager

manager = ModuleManager()

# 从目录加载所有模块
await manager.load_from_directory("./modules")

# 启动所有模块（按依赖顺序）
await manager.start_all()
```

### 条件加载

```python
# 仅在生产环境加载某些模块
await manager.load_from_directory(
    "./modules",
    condition=lambda: os.getenv("ENV") == "production"
)
```

## 异步模块示例

### 定义异步模块

```python
import asyncio

class AsyncDatabaseModule(BaseModule):
    async def start(self) -> None:
        self.pool = await create_connection_pool()
        print("Database pool created")

    async def stop(self) -> None:
        await self.pool.close()
        print("Database pool closed")

# 异步启动
manager = ModuleManager()
await manager.load_from_directory("./async_modules")
await manager.start_all()  # 自动处理异步模块
```

## 配置管理示例

### 模块配置

```python
class ConfigurableModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="configurable",
            config_schema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"}
                }
            }
        )

    def install(self, config: dict | None = None) -> None:
        super().install(config)
        self.host = self.get_config().get("host", "localhost")
        self.port = self.get_config().get("port", 8080)
```

### 配置验证

```python
def validate_config(self, config: dict | None = None) -> bool:
    if not config:
        return False
    required_fields = ["host", "port"]
    return all(field in config for field in required_fields)
```

## 热重载示例

### 运行时模块重载

```python
# 加载初始模块
await manager.load_from_directory("./modules")
await manager.start_all()

# 修改模块代码后重载
await manager.reload_module("user_module")

# 或者重载所有模块
await manager.reload_all()
```

## 完整应用示例

### Web 应用架构

```python
# modules/database.py
class DatabaseModule(BaseModule):
    def start(self) -> None:
        self.engine = create_engine("sqlite:///app.db")

# modules/cache.py
class CacheModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(dependencies=["database"])

    def start(self) -> None:
        db = self.manager.get_module("database")
        self.cache = RedisCache(db.engine)

# modules/api.py
class APIModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(dependencies=["database", "cache"])

    def start(self) -> None:
        self.app = FastAPI()
        # 使用依赖的模块
        self.db = self.manager.get_module("database").engine
        self.cache = self.manager.get_module("cache").cache

# 启动应用
manager = ModuleManager()
await manager.load_from_directory("./modules")
await manager.start_all()  # 自动按依赖顺序启动
```

## 测试示例

### 模块单元测试

```python
import pytest
from unittest.mock import Mock

def test_module_lifecycle():
    module = HelloModule()
    manager = Mock()
    module.manager = manager

    # 测试启动
    module.start()
    assert module.is_started

    # 测试停止
    module.stop()
    assert not module.is_started

def test_dependency_injection():
    db_module = Mock()
    db_module.connection = "mock_connection"

    api_module = APIModule()
    manager = Mock()
    manager.get_module.return_value = db_module
    api_module.manager = manager

    api_module.start()
    assert api_module.db_connection == "mock_connection"
```

## 运行示例

所有示例代码都可以在 `examples/` 目录中找到：

- `basic_example.py` - 基础使用示例
- `dependency_example.py` - 依赖解析示例
- `event_example.py` - 事件系统示例

运行示例：

```bash
# 运行基础示例
python examples/basic_example.py

# 运行依赖示例
python examples/dependency_example.py

# 运行事件示例
python examples/event_example.py
```
