# Module Lifecycle

## Lifecycle Overview

A module goes through the following lifecycle stages:

```
NOT_INSTALLED → LOADED → INSTALLED → STARTED → STOPPED → INSTALLED → LOADED → NOT_INSTALLED
```

## Lifecycle States

### NOT_INSTALLED

The initial state before the module is loaded into the system.

### LOADED

The module class has been registered in the registry, and an instance has been created. The `bootstrap()` method is called at this stage.

```python
def bootstrap(self) -> None:
    """Called during module registration."""
    print("Module bootstrapped")
```

### INSTALLED

The module has been configured and installed. The `install()` method is called at this stage.

```python
def install(self, config: dict | None = None) -> None:
    """Called during module installation."""
    super().install(config)
    print(f"Module installed with config: {config}")
```

### STARTED

The module is running. The `start()` method is called at this stage.

```python
def start(self) -> None:
    """Called when module starts."""
    print("Module started")
    # Initialize resources, start services, etc.
```

### STOPPED

The module has been stopped but configuration is retained. The `stop()` method is called at this stage.

```python
def stop(self) -> None:
    """Called when module stops."""
    print("Module stopped")
    # Clean up resources, stop services, etc.
```

## Lifecycle Methods

### bootstrap()

Called during module registration, used for initialization work that doesn't require configuration.

```python
def bootstrap(self) -> None:
    """Module bootstrap."""
    # Register event handlers
    # Initialize logging
    pass
```

### install(config)

Called during module installation, receives configuration dictionary.

```python
def install(self, config: dict | None = None) -> None:
    """Install module."""
    super().install(config)
    # Validate configuration
    # Initialize database connections
    pass
```

### start()

Called when module starts, used to start services and allocate resources.

```python
def start(self) -> None:
    """Start module."""
    # Start background tasks
    # Open network connections
    pass
```

### stop()

Called when module stops, used to clean up resources and stop services.

```python
def stop(self) -> None:
    """Stop module."""
    # Stop background tasks
    # Close connections
    pass
```

### uninstall()

Called during module uninstallation, used to clean up all module state.

```python
def uninstall(self) -> None:
    """Uninstall module."""
    super().uninstall()
    # Clean up database
    # Delete temporary files
    pass
```

### reload()

Called when module reloads, used to refresh module state.

```python
def reload(self) -> None:
    """Reload module."""
    # Reload configuration
    # Refresh cached data
    pass
```

## Complete Example

```python
from symphra_modules.abc import BaseModule, ModuleMetadata

class CompleteModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(name="complete")

    def bootstrap(self) -> None:
        """Bootstrap phase."""
        print("1. Bootstrap: Module registered")
        self.initialized = False  # type: ignore[attr-defined]

    def install(self, config: dict | None = None) -> None:
        """Installation phase."""
        super().install(config)
        print(f"2. Install: Config = {config}")
        self.initialized = True  # type: ignore[attr-defined]

    def start(self) -> None:
        """Start phase."""
        print("3. Start: Module running")
        self.running = True  # type: ignore[attr-defined]

    def stop(self) -> None:
        """Stop phase."""
        print("4. Stop: Module stopped")
        self.running = False  # type: ignore[attr-defined]

    def uninstall(self) -> None:
        """Uninstall phase."""
        super().uninstall()
        print("5. Uninstall: Cleanup complete")
        self.initialized = False  # type: ignore[attr-defined]

    def reload(self) -> None:
        """Reload phase."""
        print("6. Reload: State refreshed")
```

## Usage Example

```python
from symphra_modules import ModuleManager

manager = ModuleManager(module_dirs=["modules"])

# Load → LOADED
module = manager.load_module("complete")  # Calls bootstrap()

# Install → INSTALLED
manager.install_module("complete", config={"key": "value"})  # Calls install()

# Start → STARTED
manager.start_module("complete")  # Calls start()

# Stop → STOPPED
manager.stop_module("complete")  # Calls stop()

# Uninstall → LOADED
manager.uninstall_module("complete")  # Calls uninstall()

# Unload → NOT_INSTALLED
manager.unload_module("complete")
```

## Async Lifecycle

For async modules, lifecycle methods can be defined as async:

```python
class AsyncModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(name="async")

    async def start(self) -> None:
        """Async start."""
        await self.connect_to_database()
        print("Async module started")

    async def stop(self) -> None:
        """Async stop."""
        await self.disconnect_from_database()
        print("Async module stopped")
```

## Next Steps

- [Async Support](async.md)
- [Dependency Management](dependencies.md)
- [Event System](events.md)
