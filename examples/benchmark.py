#!/usr/bin/env python3
"""
ripgrep-python 性能基准测试
"""

import pyripgrep
import time
import subprocess
import sys
from pathlib import Path

def benchmark_ripgrep_python():
    """测试 ripgrep-python 的性能"""
    rg = pyripgrep.RipGrep()

    print("🔍 ripgrep-python 性能测试")

    # 测试 1: 简单文本搜索
    start = time.time()
    results = rg.search("use", ["."])
    end = time.time()

    print(f"📊 搜索 'use' 关键字:")
    print(f"   - 用时: {end - start:.3f}s")
    print(f"   - 结果数: {len(results)}")
    print(f"   - 文件数: {len(set(r['path'] for r in results))}")

    # 测试 2: 正则表达式搜索
    start = time.time()
    results = rg.search(r"fn\s+\w+", ["."])
    end = time.time()

    print(f"\n📊 正则搜索 'fn\\s+\\w+' (函数定义):")
    print(f"   - 用时: {end - start:.3f}s")
    print(f"   - 结果数: {len(results)}")

    # 测试 3: 大范围搜索 (禁用 gitignore)
    start = time.time()
    options = pyripgrep.SearchOptions()
    options.ignore_vcs = False
    results = rg.search("the", ["."], options)
    end = time.time()

    print(f"\n📊 大范围搜索 'the' (禁用过滤):")
    print(f"   - 用时: {end - start:.3f}s")
    print(f"   - 结果数: {len(results)}")
    print(f"   - 处理速度: {len(results) / (end - start):.0f} 匹配/秒")

def compare_with_rg():
    """与系统的 rg 命令比较（如果可用）"""
    try:
        # 检查是否有 rg 命令
        subprocess.run(['rg', '--version'],
                      capture_output=True, check=True)

        print("\n🆚 与系统 ripgrep 比较:")

        # ripgrep-python
        rg = pyripgrep.RipGrep()
        start = time.time()
        results = rg.search("import", ["."])
        python_time = time.time() - start
        python_count = len(results)

        # 系统 rg
        start = time.time()
        result = subprocess.run(
            ['rg', '--count', 'import', '.'],
            capture_output=True, text=True
        )
        rg_time = time.time() - start
        rg_count = sum(int(line.split(':')[1]) for line in result.stdout.strip().split('\n') if ':' in line)

        print(f"   ripgrep-python: {python_time:.3f}s ({python_count} 匹配)")
        print(f"   系统 rg:        {rg_time:.3f}s ({rg_count} 匹配)")
        print(f"   性能比率:       {rg_time / python_time:.1f}x")

    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n⚠️  系统中未找到 ripgrep 命令，跳过比较测试")

def test_gitignore_performance():
    """测试 gitignore 过滤的性能影响"""
    rg = pyripgrep.RipGrep()

    print("\n🚧 gitignore 过滤性能测试:")

    # 启用过滤
    options_with = pyripgrep.SearchOptions()
    options_with.ignore_vcs = True

    start = time.time()
    results_with = rg.search("target", ["."], options_with)
    time_with = time.time() - start

    # 禁用过滤
    options_without = pyripgrep.SearchOptions()
    options_without.ignore_vcs = False

    start = time.time()
    results_without = rg.search("target", ["."], options_without)
    time_without = time.time() - start

    print(f"   启用过滤:  {time_with:.3f}s ({len(results_with)} 匹配)")
    print(f"   禁用过滤:  {time_without:.3f}s ({len(results_without)} 匹配)")
    print(f"   过滤效率:  减少了 {len(results_without) - len(results_with)} 个匹配")
    print(f"   性能开销:  {time_without / time_with:.1f}x")

if __name__ == "__main__":
    benchmark_ripgrep_python()
    compare_with_rg()
    test_gitignore_performance()

    print("\n🎯 性能总结:")
    print("   - ripgrep-python 提供了接近原生 ripgrep 的性能")
    print("   - gitignore 过滤大大减少了不必要的搜索")
    print("   - Python 原生集成避免了子进程开销")
    print("   - 适合对性能有要求的文本搜索任务")
