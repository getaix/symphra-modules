# Basic Concepts

## Module

A module is the core concept of Symphra Modules, representing an independently loadable, configurable, and executable functional unit.

### Module Characteristics

- **Independence**: Each module is an independent functional unit
- **Configurable**: Supports runtime configuration
- **Lifecycle**: Complete start/stop flow
- **Dependency Management**: Declarative dependency relationships

## Module States

A module goes through multiple states during its lifecycle:

- `NOT_INSTALLED`: Not installed
- `LOADED`: Loaded (registered in registry)
- `INSTALLED`: Installed (configuration complete)
- `STARTED`: Started (running)
- `STOPPED`: Stopped
- `ERROR`: Error state

## Core Components

### ModuleManager

The module manager is the unified entry point, providing:

- Module loading and discovery
- Lifecycle management
- Batch operations

### ModuleRegistry

The module registry maintains the state and instances of all loaded modules.

### DependencyResolver

The dependency resolver is responsible for calculating the correct loading order of modules.

## Next Steps

- [Module Definition](module-definition.md)
- [Lifecycle](lifecycle.md)
