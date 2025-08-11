#!/usr/bin/env python3
"""
演示 ripgrep-python 的 gitignore-style 过滤功能
"""

import pyripgrep
import os

def demonstrate_gitignore():
    """演示 gitignore 过滤功能"""
    rg = pyripgrep.RipGrep()

    print("=== ripgrep-python gitignore 功能演示 ===\n")

    # 1. 默认启用 gitignore 过滤
    print("1. 默认搜索 (启用 gitignore 过滤):")
    options_default = pyripgrep.SearchOptions()
    print(f"   ignore_vcs: {options_default.ignore_vcs}")
    print(f"   ignore_global: {options_default.ignore_global}")
    print(f"   ignore_parent: {options_default.ignore_parent}")

    results = rg.search("target", ["."], options_default)
    files = set(result["path"] for result in results)

    print(f"   找到 {len(results)} 个匹配，涉及 {len(files)} 个文件")
    print("   文件列表:")
    for f in sorted(files):
        print(f"     {f}")

    print()

    # 2. 禁用 gitignore 过滤
    print("2. 禁用 gitignore 过滤:")
    options_no_ignore = pyripgrep.SearchOptions()
    options_no_ignore.ignore_vcs = False
    options_no_ignore.ignore_global = False
    options_no_ignore.ignore_parent = False

    results = rg.search("target", ["."], options_no_ignore)
    files = set(result["path"] for result in results)

    print(f"   找到 {len(results)} 个匹配，涉及 {len(files)} 个文件")
    print("   新增的文件 (被 gitignore 过滤的):")
    for f in sorted(files):
        if "target/" in f:
            print(f"     {f}")

    print()

    # 3. 搜索隐藏文件
    print("3. 包含隐藏文件的搜索:")
    options_with_hidden = pyripgrep.SearchOptions()
    options_with_hidden.include_hidden = True

    results = rg.search("ripgrep", ["."], options_with_hidden)
    files = set(result["path"] for result in results)

    hidden_files = [f for f in files if any(part.startswith('.') for part in f.split('/'))]
    print(f"   找到 {len(results)} 个匹配，其中隐藏文件:")
    for f in sorted(hidden_files):
        print(f"     {f}")

    print()

    # 4. 限制搜索深度
    print("4. 限制搜索深度为 1:")
    options_shallow = pyripgrep.SearchOptions()
    options_shallow.max_depth = 1

    results = rg.search("pyripgrep", ["."], options_shallow)
    files = set(result["path"] for result in results)

    print(f"   找到 {len(results)} 个匹配，涉及 {len(files)} 个文件")
    for f in sorted(files):
        depth = len([part for part in f.split('/') if part]) - 1
        print(f"     {f} (深度: {depth})")


def test_performance():
    """测试性能"""
    import time

    print("\n=== 性能测试 ===")
    rg = pyripgrep.RipGrep()

    # 测试大范围搜索
    start_time = time.time()
    results = rg.search("use", ["."])
    end_time = time.time()

    print(f"搜索 'use' 关键字:")
    print(f"  耗时: {end_time - start_time:.3f}s")
    print(f"  结果数量: {len(results)}")
    print(f"  涉及文件数: {len(set(r['path'] for r in results))}")


if __name__ == "__main__":
    demonstrate_gitignore()
    test_performance()
