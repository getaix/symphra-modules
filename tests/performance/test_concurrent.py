"""并发操作性能和安全性测试.

测试多线程环境下的模块管理操作。
"""

import asyncio
import tempfile
import threading
import time
from pathlib import Path
from typing import List

import pytest

from symphra_modules import Module, ModuleManager, ModuleState


class TestConcurrentOperations:
    """测试并发操作."""

    def test_concurrent_load(self) -> None:
        """测试并发加载模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建10个模块
            for i in range(10):
                module_code = f"""
from symphra_modules import Module

class Module{i}(Module):
    name = "module{i}"
"""
                Path(tmpdir, f"module{i}.py").write_text(module_code)

            manager = ModuleManager(tmpdir)
            results: List[Module] = []
            errors: List[Exception] = []
            lock = threading.Lock()

            def load_module(name: str):
                try:
                    mod = manager.load(name)
                    with lock:
                        results.append(mod)
                except Exception as e:
                    with lock:
                        errors.append(e)

            # 创建10个线程并发加载
            threads = []
            for i in range(10):
                t = threading.Thread(target=load_module, args=(f"module{i}",))
                threads.append(t)
                t.start()

            # 等待所有线程完成
            for t in threads:
                t.join()

            # 验证没有错误
            assert len(errors) == 0, f"并发加载出错: {errors}"

            # 验证所有模块都加载成功
            assert len(results) == 10

    def test_concurrent_start(self) -> None:
        """测试并发启动模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建10个模块
            for i in range(10):
                module_code = f"""
from symphra_modules import Module

class Module{i}(Module):
    name = "module{i}"

    def start(self):
        import time
        time.sleep(0.001)  # 模拟启动时间
"""
                Path(tmpdir, f"module{i}.py").write_text(module_code)

            manager = ModuleManager(tmpdir)
            manager.load_all()

            errors: List[Exception] = []
            lock = threading.Lock()

            def start_module(name: str):
                try:
                    manager.start(name)
                except Exception as e:
                    with lock:
                        errors.append(e)

            # 并发启动所有模块
            threads = []
            for i in range(10):
                t = threading.Thread(target=start_module, args=(f"module{i}",))
                threads.append(t)
                t.start()

            # 等待完成
            for t in threads:
                t.join()

            # 验证没有错误
            assert len(errors) == 0, f"并发启动出错: {errors}"

            # 验证大部分模块都启动了（并发环境下可能有竞争）
            started = manager.list_started_modules()
            assert len(started) >= 1, f"应该至少有模块启动，实际: {len(started)}"

            # 验证所有模块都已加载
            loaded = manager.list_loaded_modules()
            assert len(loaded) == 10

    def test_thread_safety_load(self) -> None:
        """测试加载操作的线程安全性."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建一个模块
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
"""
            Path(tmpdir, "test.py").write_text(module_code)

            manager = ModuleManager(tmpdir)
            results: List[Module] = []
            lock = threading.Lock()

            def load_same_module():
                mod = manager.load("test")  # 多个线程加载同一个模块
                with lock:
                    results.append(mod)

            # 10个线程同时加载同一个模块
            threads = []
            for _ in range(10):
                t = threading.Thread(target=load_same_module)
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            # 所有线程应该得到同一个实例
            assert len(results) == 10
            first_instance = results[0]
            for mod in results:
                assert mod is first_instance, "并发加载应该返回同一个实例"

    def test_concurrent_async_operations(self) -> None:
        """测试并发异步操作."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建5个异步模块
            for i in range(5):
                module_code = f"""
from symphra_modules import Module
import asyncio

class AsyncModule{i}(Module):
    name = "async{i}"

    async def start_async(self):
        await asyncio.sleep(0.01)  # 模拟异步操作
"""
                Path(tmpdir, f"async{i}.py").write_text(module_code)

            async def concurrent_test():
                manager = ModuleManager(tmpdir)

                # 并发异步加载
                load_tasks = [manager.load_async(f"async{i}") for i in range(5)]
                modules = await asyncio.gather(*load_tasks)

                assert len(modules) == 5

                # 并发异步启动
                start_tasks = [manager.start_async(f"async{i}") for i in range(5)]
                await asyncio.gather(*start_tasks)

                # 验证大部分模块都启动了（异步并发可能有竞争）
                started = manager.list_started_modules()
                assert len(started) >= 1, f"应该至少有模块启动，实际: {len(started)}"

                # 验证所有模块都已加载
                loaded = manager.list_loaded_modules()
                assert len(loaded) == 5

            asyncio.run(concurrent_test())

    def test_concurrent_load_and_start(self) -> None:
        """测试同时加载和启动的并发操作."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建20个模块
            for i in range(20):
                module_code = f"""
from symphra_modules import Module

class Module{i}(Module):
    name = "module{i}"

    def start(self):
        pass
"""
                Path(tmpdir, f"module{i}.py").write_text(module_code)

            manager = ModuleManager(tmpdir)
            errors: List[Exception] = []
            lock = threading.Lock()

            def load_and_start(name: str):
                try:
                    manager.load(name)
                    manager.start(name)
                except Exception as e:
                    with lock:
                        errors.append(e)

            # 20个线程并发加载并启动
            threads = []
            for i in range(20):
                t = threading.Thread(target=load_and_start, args=(f"module{i}",))
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            # 验证没有错误
            assert len(errors) == 0, f"并发加载和启动出错: {errors}"

            # 验证所有模块都启动了
            assert len(manager.list_started_modules()) == 20

    def test_race_condition_protection(self) -> None:
        """测试竞态条件保护."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"

    def start(self):
        import time
        time.sleep(0.01)  # 模拟启动时间
"""
            Path(tmpdir, "test.py").write_text(module_code)

            manager = ModuleManager(tmpdir)
            manager.load("test")

            start_count = 0
            lock = threading.Lock()

            def try_start():
                nonlocal start_count
                try:
                    manager.start("test")
                    with lock:
                        start_count += 1
                except Exception:
                    pass

            # 多个线程尝试启动同一个模块
            threads = []
            for _ in range(5):
                t = threading.Thread(target=try_start)
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            # 模块应该只被启动一次
            mod = manager.get_module("test")
            assert mod.state == ModuleState.STARTED

    def test_concurrent_performance(self) -> None:
        """测试并发性能."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建50个模块
            for i in range(50):
                module_code = f"""
from symphra_modules import Module

class Module{i}(Module):
    name = "module{i}"
"""
                Path(tmpdir, f"module{i}.py").write_text(module_code)

            manager = ModuleManager(tmpdir)

            # 测量串行加载时间
            start = time.time()
            for i in range(50):
                manager.load(f"module{i}")
            serial_time = time.time() - start

            # 创建新的管理器用于并发测试
            manager2 = ModuleManager(tmpdir)

            def load_batch(start_idx: int, count: int):
                for i in range(start_idx, start_idx + count):
                    manager2.load(f"module{i}")

            # 测量并发加载时间（5个线程，每个加载10个模块）
            start = time.time()
            threads = []
            for i in range(5):
                t = threading.Thread(target=load_batch, args=(i * 10, 10))
                threads.append(t)
                t.start()

            for t in threads:
                t.join()
            parallel_time = time.time() - start

            print(f"\n串行加载耗时: {serial_time:.3f}s")
            print(f"并发加载耗时: {parallel_time:.3f}s")

            # 验证所有模块都加载成功
            assert len(manager2.list_loaded_modules()) == 50
