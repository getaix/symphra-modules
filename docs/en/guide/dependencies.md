# Dependency Management

## Dependency Declaration

Modules can declare dependencies through metadata:

```python
from symphra_modules.abc import BaseModule, ModuleMetadata

class DatabaseModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="database",
            dependencies=[],  # No dependencies
        )

class UserModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="user",
            dependencies=["database"],  # Depends on database module
        )
```

## Dependency Types

### Required Dependencies

Dependencies required for normal module operation:

```python
ModuleMetadata(
    name="web_server",
    dependencies=["database", "cache", "logger"]
)
```

### Optional Dependencies

Dependencies that modules can choose to use:

```python
ModuleMetadata(
    name="metrics",
    optional_dependencies=["prometheus", "grafana"]
)
```

## Dependency Resolution

### Topological Sort

Symphra Modules uses Kahn's algorithm for dependency resolution:

```python
from symphra_modules.resolver import DependencyResolver

resolver = DependencyResolver()
modules = [db_module, user_module, web_module]

# Resolve dependency order
ordered_modules = resolver.resolve_dependencies(modules)
# Returns: [db_module, user_module, web_module]
```

### Cycle Detection

Automatically detect and report circular dependencies:

```python
# Circular dependency example (will throw exception)
# A depends on B, B depends on A

try:
    ordered_modules = resolver.resolve_dependencies(modules)
except CircularDependencyError as e:
    print(f"Circular dependency detected: {e}")
```

## Dependency Injection

Modules can access other modules through the manager:

```python
class UserModule(BaseModule):
    def start(self) -> None:
        # Get dependent database module
        db_module = self.manager.get_module("database")
        self.db_connection = db_module.get_connection()
```

## Lazy Dependencies

Support runtime dynamic dependency addition:

```python
# Add dependency at runtime
await manager.add_dependency("user_module", "cache_module")

# Re-resolve dependencies
await manager.resolve_all_dependencies()
```

## Version Constraints

Support version range dependency declarations:

```python
ModuleMetadata(
    name="api_client",
    dependencies=["database>=1.0.0,<2.0.0"]
)
```

## Dependency Validation

Validate all dependencies are satisfied before startup:

```python
# Validate dependencies
missing_deps = manager.validate_dependencies()
if missing_deps:
    print(f"Missing dependencies: {missing_deps}")
    # Handle missing dependencies
```

## Best Practices

### Dependency Layering

- **Foundation Layer**: Database, cache, configuration
- **Service Layer**: Business logic modules
- **Interface Layer**: API, web interface

### Avoid Circular Dependencies

- Use event system instead of direct dependencies
- Extract common interfaces to independent modules
- Use dependency injection pattern

### Optional Dependency Handling

```python
class MonitoringModule(BaseModule):
    def start(self) -> None:
        # Check optional dependencies
        if self.manager.has_module("prometheus"):
            prometheus = self.manager.get_module("prometheus")
            # Use prometheus module
        else:
            # Use fallback solution
            self.logger.warning("Prometheus not available, using basic monitoring")
```

### Dependency Testing

```python
# Dependency mocking in unit tests
import pytest
from unittest.mock import Mock

def test_user_module():
    mock_db = Mock()
    manager = Mock()
    manager.get_module.return_value = mock_db

    user_module = UserModule()
    user_module.manager = manager
    user_module.start()

    # Verify dependency calls
    manager.get_module.assert_called_with("database")
```