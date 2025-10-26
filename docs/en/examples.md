# Examples

This chapter provides complete usage examples for Symphra Modules.

## Basic Example

### Basic Module Definition and Usage

```python
from symphra_modules import BaseModule, ModuleManager, ModuleMetadata

class HelloModule(BaseModule):
    """Example module - Hello World."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="hello",
            version="1.0.0",
            description="A simple Hello World module",
        )

    def start(self) -> None:
        print(f"Hello from {self.metadata.name}!")

    def stop(self) -> None:
        print(f"Goodbye from {self.metadata.name}!")

# Use module
manager = ModuleManager()
manager.registry.register("hello", HelloModule)

# Install and start module
manager.install_module("hello")
manager.start_module("hello")

# Check status
print(f"Loaded modules: {manager.list_modules()}")
```

## Dependency Management Example

### Module Dependency Resolution

```python
from symphra_modules import DependencyResolver, ModuleMetadata

# Create dependency resolver
resolver = DependencyResolver()

# Define modules and their dependencies
resolver.add_module(ModuleMetadata(name="database", dependencies=[]))
resolver.add_module(ModuleMetadata(name="cache", dependencies=["database"]))
resolver.add_module(ModuleMetadata(name="api", dependencies=["database", "cache"]))

# Resolve dependency order
try:
    order = resolver.resolve_dependencies()
    print(f"Loading order: {order}")
except CircularDependencyError as e:
    print(f"Circular dependency detected: {e}")
```

### Dependency Injection

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
        # Get dependent database module
        db_module = self.manager.get_module("database")
        self.db_connection = db_module.connection
```

## Event System Example

### Basic Event Publishing and Subscription

```python
from symphra_modules import EventBus

# Create event bus
bus = EventBus()

# Define event handler
@bus.subscribe("user.created")
def handle_user_created(user_id: int, email: str):
    print(f"New user created: {user_id} - {email}")

@bus.subscribe("user.*")  # Wildcard subscription
def handle_all_user_events(event_type: str, **data):
    print(f"User event: {event_type}")

# Publish event
bus.publish("user.created", user_id=123, email="user@example.com")
```

### Async Event Handling

```python
import asyncio

@bus.subscribe("data.process")
async def async_data_processor(data: dict):
    # Process data asynchronously
    await process_data_async(data)
    # Publish completion event
    await bus.publish("data.processed", data_id=data["id"])
```

## Directory Loading Example

### Auto Loading Modules from Directory

```python
# Project structure
# modules/
# ├── user.py
# ├── payment.py
# └── notification.py

from symphra_modules import ModuleManager

manager = ModuleManager()

# Load all modules from directory
await manager.load_from_directory("./modules")

# Start all modules (in dependency order)
await manager.start_all()
```

### Conditional Loading

```python
# Load only certain modules in production environment
await manager.load_from_directory(
    "./modules",
    condition=lambda: os.getenv("ENV") == "production"
)
```

## Async Module Example

### Defining Async Modules

```python
import asyncio

class AsyncDatabaseModule(BaseModule):
    async def start(self) -> None:
        self.pool = await create_connection_pool()
        print("Database pool created")

    async def stop(self) -> None:
        await self.pool.close()
        print("Database pool closed")

# Async startup
manager = ModuleManager()
await manager.load_from_directory("./async_modules")
await manager.start_all()  # Automatically handles async modules
```

## Configuration Management Example

### Module Configuration

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

### Configuration Validation

```python
def validate_config(self, config: dict | None = None) -> bool:
    if not config:
        return False
    required_fields = ["host", "port"]
    return all(field in config for field in required_fields)
```

## Hot Reload Example

### Runtime Module Reloading

```python
# Load initial modules
await manager.load_from_directory("./modules")
await manager.start_all()

# Reload after modifying module code
await manager.reload_module("user_module")

# Or reload all modules
await manager.reload_all()
```

## Complete Application Example

### Web Application Architecture

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
        # Use dependent modules
        self.db = self.manager.get_module("database").engine
        self.cache = self.manager.get_module("cache").cache

# Start application
manager = ModuleManager()
await manager.load_from_directory("./modules")
await manager.start_all()  # Automatically start in dependency order
```

## Testing Example

### Module Unit Testing

```python
import pytest
from unittest.mock import Mock

def test_module_lifecycle():
    module = HelloModule()
    manager = Mock()
    module.manager = manager

    # Test startup
    module.start()
    assert module.is_started

    # Test shutdown
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

## Running Examples

All example code can be found in the `examples/` directory:

- `basic_example.py` - Basic usage example
- `dependency_example.py` - Dependency resolution example
- `event_example.py` - Event system example

Run examples:

```bash
# Run basic example
python examples/basic_example.py

# Run dependency example
python examples/dependency_example.py

# Run event example
python examples/event_example.py
```