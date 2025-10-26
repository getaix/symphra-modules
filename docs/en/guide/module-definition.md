# Module Definition

## Basic Module

Defining a module requires inheriting from `BaseModule` and implementing necessary methods:

```python
from symphra_modules.abc import BaseModule, ModuleMetadata

class MyModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="my_module",
            version="1.0.0",
            description="My module"
        )

    def start(self) -> None:
        print("Module started")

    def stop(self) -> None:
        print("Module stopped")
```

## Metadata Configuration

ModuleMetadata supports the following fields:

- `name`: Module name (required)
- `version`: Version number
- `description`: Description
- `dependencies`: List of dependent modules
- `optional_dependencies`: Optional dependencies
- `config_schema`: Configuration schema

## Lifecycle Hooks

- `bootstrap()`: Called when module is registered
- `install(config)`: Called during installation
- `start()`: Called when starting
- `stop()`: Called when stopping
- `uninstall()`: Called during uninstallation
- `reload()`: Called when reloading

## Configuration Management

```python
def install(self, config: dict | None = None) -> None:
    super().install(config)
    # Use configuration
    db_host = self.get_config().get("db_host", "localhost")
```

## Configuration Validation

```python
def validate_config(self, config: dict | None = None) -> bool:
    if not config:
        return False
    return "required_field" in config
```
