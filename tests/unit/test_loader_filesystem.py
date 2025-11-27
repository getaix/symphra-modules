"""测试文件系统加载器."""

from pathlib import Path

import pytest

from symphra_modules.core.exceptions import LoaderError
from symphra_modules.loader.filesystem import FileSystemLoader


def test_discover_empty_directory(tmp_path: Path) -> None:
    """测试发现空目录."""
    loader = FileSystemLoader([tmp_path])
    modules = loader.discover()

    assert modules == {}


def test_discover_nonexistent_directory(tmp_path: Path) -> None:
    """测试发现不存在的目录."""
    nonexistent = tmp_path / "nonexistent"
    loader = FileSystemLoader([nonexistent])

    # 不应该抛异常，只记录警告
    modules = loader.discover()
    assert modules == {}


def test_discover_file_instead_of_directory(tmp_path: Path) -> None:
    """测试路径是文件而不是目录."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test")

    loader = FileSystemLoader([test_file])

    # 不应该抛异常，只记录警告
    modules = loader.discover()
    assert modules == {}


def test_discover_skips_private_files(tmp_path: Path) -> None:
    """测试跳过私有文件（以_开头）."""
    # 创建私有模块文件
    private_file = tmp_path / "_private.py"
    private_file.write_text(
        """
from symphra_modules import Module

class PrivateModule(Module):
    name = "private"
    version = "1.0.0"
    dependencies = []
"""
    )

    # 创建正常模块文件
    public_file = tmp_path / "public.py"
    public_file.write_text(
        """
from symphra_modules import Module

class PublicModule(Module):
    name = "public"
    version = "1.0.0"
    dependencies = []
"""
    )

    loader = FileSystemLoader([tmp_path])
    modules = loader.discover()

    # 只应该发现公开模块
    assert "public" in modules
    assert "private" not in modules


def test_discover_invalid_python_file(tmp_path: Path) -> None:
    """测试发现包含语法错误的Python文件."""
    invalid_file = tmp_path / "invalid.py"
    invalid_file.write_text("this is { invalid python }")

    loader = FileSystemLoader([tmp_path])

    # 不应该抛异常，只记录错误
    modules = loader.discover()
    assert modules == {}


def test_discover_file_without_module(tmp_path: Path) -> None:
    """测试发现不包含Module子类的文件."""
    no_module_file = tmp_path / "nomodule.py"
    no_module_file.write_text(
        """
# 这个文件不包含Module子类
def some_function():
    pass

class SomeClass:
    pass
"""
    )

    loader = FileSystemLoader([tmp_path])
    modules = loader.discover()

    # 不应该发现任何模块
    assert modules == {}


def test_discover_multiple_modules_in_file(tmp_path: Path) -> None:
    """测试发现一个文件中的多个模块."""
    multi_file = tmp_path / "multi.py"
    multi_file.write_text(
        """
from symphra_modules import Module

class Module1(Module):
    name = "module1"
    version = "1.0.0"
    dependencies = []

class Module2(Module):
    name = "module2"
    version = "1.0.0"
    dependencies = []
"""
    )

    loader = FileSystemLoader([tmp_path])
    modules = loader.discover()

    # 应该发现两个模块
    assert len(modules) == 2
    assert "module1" in modules
    assert "module2" in modules


def test_load_class_from_cache(tmp_path: Path) -> None:
    """测试从缓存加载模块类."""
    module_file = tmp_path / "test.py"
    module_file.write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
    version = "1.0.0"
    dependencies = []
"""
    )

    loader = FileSystemLoader([tmp_path])
    loader.discover()  # 填充缓存

    # 从缓存加载
    module_class = loader.load_class("test")
    assert module_class.name == "test"


def test_load_class_nonexistent(tmp_path: Path) -> None:
    """测试加载不存在的模块类."""
    loader = FileSystemLoader([tmp_path])
    loader.discover()

    with pytest.raises(LoaderError, match="模块 'nonexistent' 未找到"):
        loader.load_class("nonexistent")


def test_load_class_auto_discover(tmp_path: Path) -> None:
    """测试加载时自动发现."""
    module_file = tmp_path / "test.py"
    module_file.write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
    version = "1.0.0"
    dependencies = []
"""
    )

    loader = FileSystemLoader([tmp_path])

    # 不先调用discover，直接load_class应该自动发现
    module_class = loader.load_class("test")
    assert module_class.name == "test"


def test_reload(tmp_path: Path) -> None:
    """测试重新加载."""
    module_file = tmp_path / "test.py"
    module_file.write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
    version = "1.0.0"
    dependencies = []
"""
    )

    loader = FileSystemLoader([tmp_path])
    modules1 = loader.discover()
    assert "test" in modules1

    # 清空缓存并重新加载
    loader.reload()

    # 验证重新发现了模块
    modules2 = loader.discover()
    assert "test" in modules2


def test_discover_multiple_directories(tmp_path: Path) -> None:
    """测试发现多个目录中的模块."""
    dir1 = tmp_path / "dir1"
    dir2 = tmp_path / "dir2"
    dir1.mkdir()
    dir2.mkdir()

    # 在第一个目录创建模块
    (dir1 / "module1.py").write_text(
        """
from symphra_modules import Module

class Module1(Module):
    name = "module1"
    version = "1.0.0"
    dependencies = []
"""
    )

    # 在第二个目录创建模块
    (dir2 / "module2.py").write_text(
        """
from symphra_modules import Module

class Module2(Module):
    name = "module2"
    version = "1.0.0"
    dependencies = []
"""
    )

    loader = FileSystemLoader([dir1, dir2])
    modules = loader.discover()

    # 应该发现两个目录中的所有模块
    assert len(modules) == 2
    assert "module1" in modules
    assert "module2" in modules


def test_module_without_name_attribute(tmp_path: Path) -> None:
    """测试没有name属性的Module子类."""
    no_name_file = tmp_path / "noname.py"
    no_name_file.write_text(
        """
from symphra_modules import Module

class NoNameModule(Module):
    # 没有定义name属性
    version = "1.0.0"
    dependencies = []
"""
    )

    loader = FileSystemLoader([tmp_path])
    modules = loader.discover()

    # 不应该发现这个模块（因为没有name属性）
    assert modules == {}
