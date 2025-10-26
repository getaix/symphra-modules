# Module Loading

## Loading Strategies

Symphra Modules provides multiple loading strategies to meet different scenarios.

## Directory Loading

Load modules from a file system directory.

### Basic Usage

```python
from symphra_modules import ModuleManager

manager = ModuleManager(module_dirs=["modules"])
module = manager.load_module("my_module")
```

### Directory Structure

```
modules/
├── user/
│   └── user_module.py
├── auth/
│   └── auth_module.py
└── database.py
```

### DirectoryLoader

```python
from symphra_modules.loader import DirectoryLoader

loader = DirectoryLoader()

# Load all modules from a directory
modules = loader.load("modules")
print(modules)  # {'UserModule': <class>, 'AuthModule': <class>, ...}

# Discover available module names
names = loader.discover("modules")
print(names)  # ['user', 'auth', 'database']
```

## Package Loading

Load modules from Python packages.

### Basic Usage

```python
from symphra_modules.loader import PackageLoader

loader = PackageLoader()

# Load from a package
modules = loader.load("my_package.modules")
```

### Package Structure

```
my_package/
└── modules/
    ├── __init__.py
    ├── user.py
    └── auth.py
```

## Module Discovery

### Discover Available Modules

```python
manager = ModuleManager(module_dirs=["modules"])

# Discover all available modules
available = manager.discover_modules()
print(available)  # ['user', 'auth', 'database']

# Load all discovered modules
for name in available:
    manager.load_module(name)
```

### Discover from Specific Source

```python
# Discover from specific directory
names = manager.discover_modules(source="plugins", source_type="directory")

# Discover from specific package
names = manager.discover_modules(source="my_app.plugins", source_type="package")
```

## Module Naming Rules

### Class Name Matching

The loader uses flexible naming rules to match module classes:

```python
# These will all match module name "user":
class User(BaseModule): ...
class UserModule(BaseModule): ...
class user(BaseModule): ...
class userModule(BaseModule): ...
```

### Case Insensitivity

Module name matching is case-insensitive:

```python
# All of these can load the same module
manager.load_module("user")
manager.load_module("User")
manager.load_module("USER")
```

## Batch Loading

### Load All Modules

```python
manager = ModuleManager(module_dirs=["modules"])

# Load all available modules
modules = manager.load_all_modules()
print(modules)  # {'user': <instance>, 'auth': <instance>, ...}
```

### Handle Load Errors

```python
import logging

# Configure logging to see error messages
logging.basicConfig(level=logging.WARNING)

# Load all modules, errors will be logged
modules = manager.load_all_modules()
```

## Module Exclusion

### Exclude Specific Modules

```python
# Exclude "common" directory (typically used for shared utilities)
manager = ModuleManager(
    module_dirs=["modules"],
    exclude_modules={"common", "utils"}
)

# These modules won't be loaded
available = manager.discover_modules()  # "common" and "utils" excluded
```

## Loading from Multiple Directories

```python
manager = ModuleManager(module_dirs=[
    "core_modules",
    "plugins",
    "extensions"
])

# Will search all directories in order
module = manager.load_module("my_module")
```

## Caching

### Directory Cache

The manager caches loaded modules from directories to improve performance:

```python
manager = ModuleManager(module_dirs=["modules"])

# First load - reads from disk
module1 = manager.load_module("user")

# Second load - uses cache
module2 = manager.load_module("user")

# They're the same instance
assert module1 is module2
```

### Invalidate Cache

```python
# Invalidate specific directory cache
manager._invalidate_directory_cache("modules")

# Invalidate all caches
manager._invalidate_directory_cache()

# Now reload will read from disk again
manager.reload_module("user")
```

## Custom Loaders

### Extend ModuleLoader

```python
from symphra_modules.loader import ModuleLoader
from symphra_modules.abc import ModuleInterface

class CustomLoader(ModuleLoader):
    def load(self, source: str) -> dict[str, type[ModuleInterface]]:
        """Custom loading logic."""
        modules = {}
        # Your implementation
        return modules

    def discover(self, source: str) -> list[str]:
        """Custom discovery logic."""
        names = []
        # Your implementation
        return names
```

### Use Custom Loader

```python
class CustomManager(ModuleManager):
    def __init__(self):
        super().__init__()
        self._custom_loader = CustomLoader()

    def load_from_custom(self, source: str):
        modules = self._custom_loader.load(source)
        # Process modules
```

## Best Practices

### 1. Use Consistent Naming

```python
# Good: Consistent naming
class UserModule(BaseModule):  # File: user.py
    @property
    def metadata(self):
        return ModuleMetadata(name="user")
```

### 2. Organize by Feature

```
modules/
├── user/           # User management feature
│   ├── user.py
│   └── permissions.py
├── auth/           # Authentication feature
│   ├── login.py
│   └── session.py
└── common/         # Shared utilities (excluded)
    └── helpers.py
```

### 3. Handle Load Failures

```python
from symphra_modules.exceptions import ModuleNotFoundException, ModuleLoadError

try:
    module = manager.load_module("risky_module")
except ModuleNotFoundException:
    print("Module not found")
except ModuleLoadError as e:
    print(f"Failed to load module: {e}")
```

## Next Steps

- [Dependency Management](dependencies.md)
- [Configuration](../api/config.md)
