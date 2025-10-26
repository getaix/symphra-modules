# 模块定义

## 基本模块

定义一个模块需要继承 `BaseModule` 并实现必要的方法:

```python
from symphra_modules.abc import BaseModule, ModuleMetadata

class MyModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="my_module",
            version="1.0.0",
            description="我的模块"
        )

    def start(self) -> None:
        print("模块启动")

    def stop(self) -> None:
        print("模块停止")
```

## 元数据配置

ModuleMetadata 支持以下字段:

- `name`: 模块名称(必需)
- `version`: 版本号
- `description`: 描述
- `dependencies`: 依赖模块列表
- `optional_dependencies`: 可选依赖
- `config_schema`: 配置schema

## 生命周期钩子

- `bootstrap()`: 模块注册时调用
- `install(config)`: 安装时调用
- `start()`: 启动时调用
- `stop()`: 停止时调用
- `uninstall()`: 卸载时调用
- `reload()`: 重载时调用

## 配置管理

```python
def install(self, config: dict | None = None) -> None:
    super().install(config)
    # 使用配置
    db_host = self.get_config().get("db_host", "localhost")
```

## 配置验证

```python
def validate_config(self, config: dict | None = None) -> bool:
    if not config:
        return False
    return "required_field" in config
```