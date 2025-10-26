"""包加载器实现."""

import importlib
from pathlib import Path

from symphra_modules.abc import ModuleInterface
from symphra_modules.exceptions import ModuleLoadError
from symphra_modules.loader.base import ModuleLoader


class PackageLoader(ModuleLoader):
    """从包名加载模块."""

    def load(self, source: str) -> dict[str, type[ModuleInterface]]:
        """从包名加载模块.

        Args:
            source: 包名（如 "my_package.modules"）

        Returns:
            模块类字典

        Raises:
            ModuleLoadError: 包未找到时抛出
        """
        try:
            module = importlib.import_module(source)
            return self._find_module_classes(module)
        except ImportError as e:
            raise ModuleLoadError(f"包未找到: {source}") from e

    def discover(self, source: str) -> list[str]:
        """发现包中的模块.

        Args:
            source: 包名

        Returns:
            模块名称列表
        """
        try:
            package = importlib.import_module(source)
            package_path = Path(package.__file__).parent if package.__file__ else Path.cwd() / source

            module_names: list[str] = []

            # 扫描包内的模块
            for item in package_path.iterdir():
                if item.is_file() and item.suffix == ".py" and not item.name.startswith("_"):
                    module_names.append(item.stem)
                elif item.is_dir() and (item / "__init__.py").exists():
                    module_names.append(item.name)

            return module_names

        except (ImportError, AttributeError):
            return []
