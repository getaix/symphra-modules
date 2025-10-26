"""目录加载器实现."""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any

from symphra_modules.abc import ModuleInterface
from symphra_modules.exceptions import ModuleLoadError
from symphra_modules.loader.base import ModuleLoader
from symphra_modules.utils import get_logger

logger = get_logger()


class DirectoryLoader(ModuleLoader):
    """从目录加载模块."""

    def __init__(self, base_path: Path | None = None) -> None:
        """初始化目录加载器.

        Args:
            base_path: 基础路径，默认为当前工作目录
        """
        self.base_path = base_path or Path.cwd()

    def _to_module_name(self, path: Path) -> str | None:
        """将文件或包路径转换为模块名（相对 base_path）.

        Args:
            path: 文件或包路径

        Returns:
            模块名，如果无法转换则返回 None
        """
        try:
            relative = path.relative_to(self.base_path)
        except ValueError:
            # 无法转换为相对路径时返回 None
            return None

        parts = list(relative.parts)
        if parts and parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]

        return ".".join(parts)

    def load(self, source: str) -> dict[str, type[ModuleInterface]]:
        """从指定目录加载所有模块.

        Args:
            source: 目录路径（相对于 base_path）

        Returns:
            模块名到模块类的映射字典

        Raises:
            ModuleLoadError: 目录不存在时抛出
        """
        modules: dict[str, type[ModuleInterface]] = {}
        module_dir = Path(self.base_path) / source

        if not module_dir.exists():
            raise ModuleLoadError(f"模块目录不存在: {module_dir}")

        # 查找所有 Python 文件
        for py_file in module_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            try:
                module_classes = self._load_from_file(py_file)
                modules.update(module_classes)
            except Exception as e:
                logger.warning(f"无法从 {py_file} 加载模块: {e}")

        # 查找包
        for package_dir in module_dir.iterdir():
            if package_dir.is_dir() and (package_dir / "__init__.py").exists():
                try:
                    module_classes = self._load_from_package(package_dir)
                    modules.update(module_classes)
                except Exception as e:
                    logger.error(f"无法从 {package_dir} 加载模块: {e}")

        return modules

    def discover(self, source: str) -> list[str]:
        """发现目录中的模块.

        Args:
            source: 目录路径

        Returns:
            模块名称列表
        """
        module_names: list[str] = []
        module_dir = Path(self.base_path) / source

        if not module_dir.exists():
            return module_names

        # Python 文件
        for py_file in module_dir.glob("*.py"):
            if not py_file.name.startswith("_"):
                module_names.append(py_file.stem)

        # 包
        for package_dir in module_dir.iterdir():
            if package_dir.is_dir() and (package_dir / "__init__.py").exists():
                module_names.append(package_dir.name)

        return module_names

    def _load_from_file(self, file_path: Path, package: str | None = None) -> dict[str, type[ModuleInterface]]:
        """从 Python 文件加载模块.

        Args:
            file_path: Python 文件路径
            package: 包名（可选）

        Returns:
            模块类字典

        Raises:
            ModuleLoadError: 加载失败时抛出
        """
        module_name: str
        if package is not None:
            module_name = f"{package}.{file_path.stem}"
        else:
            inferred = self._to_module_name(file_path)
            module_name = inferred or file_path.stem

        module: Any = None
        if "." in module_name:
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                module = None

        if module is None:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if not spec or not spec.loader:
                raise ModuleLoadError(f"无法从 {file_path} 创建模块规范")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

        return self._find_module_classes(module)

    def _load_from_package(self, package_dir: Path) -> dict[str, type[ModuleInterface]]:
        """从包加载模块.

        Args:
            package_dir: 包目录路径

        Returns:
            模块类字典

        Raises:
            ModuleLoadError: 加载失败时抛出
        """
        inferred_package = self._to_module_name(package_dir)
        package_name = inferred_package or package_dir.name

        # 将包路径添加到 sys.path，便于定位依赖
        parent_path = str(package_dir.parent)
        if parent_path not in sys.path:
            sys.path.insert(0, parent_path)

        modules: dict[str, type[ModuleInterface]] = {}

        # 优先加载显式的 module.py，再加载其他非私有 Python 文件
        candidate_files: list[Path] = []
        module_file = package_dir / "module.py"
        if module_file.exists():
            candidate_files.append(module_file)

        if not candidate_files:
            # 回退：若没有独立文件，则尝试加载包本身
            try:
                module = importlib.import_module(package_name)
                return self._find_module_classes(module)
            except ImportError as e:
                raise ModuleLoadError(f"无法从 {package_name} 加载模块: {e}") from e

        for py_file in candidate_files:
            try:
                module_classes = self._load_from_file(py_file, package=package_name)
                modules.update(module_classes)
            except Exception as e:
                logger.warning(f"无法从 {package_name} 的 {py_file.name} 加载模块: {e}")

        return modules
