# Quick Start

This guide will help you get started with Symphra Modules quickly, from installation to writing your first module.

## Requirements

- Python 3.11 or higher
- uv (recommended) or pip

## Installation

### Using uv (Recommended)

```bash
# Create a new project
uv init my-project
cd my-project

# Add dependency
uv add symphra-modules
```

### Using pip

```bash
pip install symphra-modules
```

## Your First Module

### 1. Create Module Directory

```bash
mkdir -p modules
```

### 2. Define a Module

Create file `modules/hello.py`:

```python
from symphra_modules.abc import BaseModule, ModuleMetadata

class HelloModule(BaseModule):
    """Example module."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="hello",
            version="1.0.0",
            description="A simple greeting module"
        )

    def bootstrap(self) -> None:
        """Module bootstrap, called during registration."""
        print("HelloModule: Bootstrap complete")

    def install(self, config: dict | None = None) -> None:
        """Install the module."""
        super().install(config)
        print(f"HelloModule: Installed with config: {config}")

    def start(self) -> None:
        """Start the module."""
        print("HelloModule: Started")
        print(f"Config: {self.get_config()}")

    def stop(self) -> None:
        """Stop the module."""
        print("HelloModule: Stopped")

    def uninstall(self) -> None:
        """Uninstall the module."""
        super().uninstall()
        print("HelloModule: Uninstalled")
```

### 3. Use the Module Manager

Create file `main.py`:

```python
from symphra_modules import ModuleManager

def main():
    # Create manager
    manager = ModuleManager(module_dirs=["modules"])

    # Discover available modules
    available = manager.discover_modules()
    print(f"Available modules: {available}")

    # Load module
    module = manager.load_module("hello")
    print(f"Loaded: {module.metadata.name}")

    # Install module
    manager.install_module("hello", config={"greeting": "Hello"})

    # Start module
    manager.start_module("hello")

    # Stop module
    manager.stop_module("hello")

    # Uninstall module
    manager.uninstall_module("hello")

if __name__ == "__main__":
    main()
```

### 4. Run

```bash
python main.py
```

Output:

```
Available modules: ['hello']
HelloModule: Bootstrap complete
Loaded: hello
HelloModule: Installed with config: {'greeting': 'Hello'}
HelloModule: Started
Config: {'greeting': 'Hello'}
HelloModule: Stopped
HelloModule: Uninstalled
```

## Modules with Dependencies

### Define Base Module

`modules/database.py`:

```python
from symphra_modules.abc import BaseModule, ModuleMetadata

class DatabaseModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(name="database")

    def start(self) -> None:
        self.connection = "database_connected"  # type: ignore[attr-defined]
        print("Database connected")

    def stop(self) -> None:
        self.connection = None  # type: ignore[attr-defined]
        print("Database disconnected")
```

### Define Dependent Module

`modules/user_service.py`:

```python
from symphra_modules.abc import BaseModule, ModuleMetadata

class UserServiceModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="user_service",
            dependencies=["database"]  # Depends on database module
        )

    def start(self) -> None:
        print("User service started, database available")
```

### Using Dependency Resolution

```python
from symphra_modules import ModuleManager
from symphra_modules.resolver import DependencyResolver
from symphra_modules.config import ModuleMetadata

# Create manager
manager = ModuleManager(module_dirs=["modules"])

# Discover and load all modules
modules = manager.load_all_modules()

# Create dependency resolver
resolver = DependencyResolver()
for module in modules.values():
    resolver.add_module(module.metadata)

# Get loading order
load_order = resolver.resolve()
print(f"Loading order: {load_order}")  # ['database', 'user_service']

# Start in order
for name in load_order:
    manager.install_module(name)
    manager.start_module(name)
```

## Async Modules

### Define Async Module

`modules/async_worker.py`:

```python
import asyncio
from symphra_modules.abc import BaseModule, ModuleMetadata

class AsyncWorkerModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(name="async_worker")

    async def start(self) -> None:
        """Async start."""
        await asyncio.sleep(0.1)
        print("Async worker started")
        self.running = True  # type: ignore[attr-defined]

    async def stop(self) -> None:
        """Async stop."""
        self.running = False  # type: ignore[attr-defined]
        await asyncio.sleep(0.1)
        print("Async worker stopped")
```

### Using Async Modules

```python
import asyncio
from symphra_modules import ModuleManager
from symphra_modules.abc import call_module_method

async def main():
    manager = ModuleManager(module_dirs=["modules"])

    # Load module
    module = manager.load_module("async_worker")
    manager.install_module("async_worker")

    # Use unified interface to call async methods
    await call_module_method(module, "start")
    await call_module_method(module, "stop")

if __name__ == "__main__":
    asyncio.run(main())
```

## Event Subscription

### Subscribe to Module Events

```python
from symphra_modules import ModuleManager
from symphra_modules.events import EventBus, Event

# Create event bus
event_bus = EventBus()

# Subscribe to all events
@event_bus.subscribe("*")
def log_all_events(event: Event) -> None:
    print(f"[Event] {event.event_type}: {event.module_name}")

# Subscribe to specific event
@event_bus.subscribe("module.started")
def on_started(event: Event) -> None:
    print(f"Module {event.module_name} started!")

# Create manager and inject event bus
manager = ModuleManager()
manager.registry.event_bus = event_bus

# Module operations will trigger events
manager.load_module("hello")
manager.install_module("hello")
manager.start_module("hello")
```

## Configuration Validation

### Define Module with Validation

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
        """Validate configuration."""
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
        print(f"Server started: {config['host']}:{config['port']}")
```

### Using Configuration Validation

```python
from symphra_modules import ModuleManager
from symphra_modules.exceptions import ModuleConfigError

manager = ModuleManager(module_dirs=["modules"])
manager.load_module("configurable")

try:
    # Invalid config will fail
    manager.install_module("configurable", config={"invalid": "config"})
except ModuleConfigError as e:
    print(f"Config error: {e}")

# Valid config
manager.install_module("configurable", config={
    "host": "localhost",
    "port": 8080,
    "enabled": True
})
manager.start_module("configurable")
```

## Next Steps

- [Basic Concepts](guide/concepts.md) - Learn core concepts
- [Module Definition](guide/module-definition.md) - Deep dive into module definition
- [Lifecycle](guide/lifecycle.md) - Master module lifecycle
- [API Reference](api/abc.md) - View complete API documentation
