#!/usr/bin/env python3
"""
示例：使用新的 Grep 接口，类似于 ripgrep 的原生命令行接口
"""
import pyripgrep

def demo_basic_usage():
    """基础使用示例"""
    print("=== 基础使用示例 ===\n")

    grep = pyripgrep.Grep()

    # 1. 默认模式：返回包含匹配的文件列表
    print("1. 查找包含 'use' 的文件:")
    files = grep.search("use", path="src")
    for file in files[:3]:  # 显示前3个
        print(f"   {file}")
    print(f"   ... (共 {len(files)} 个文件)\n")

    # 2. 内容模式：显示匹配的行内容
    print("2. 显示匹配的行内容:")
    content = grep.search("fn", path="src", output_mode="content", head_limit=5)
    for line in content:
        print(f"   {line}")
    print()

    # 3. 计数模式：显示每个文件的匹配数量
    print("3. 统计每个文件的匹配数量:")
    counts = grep.search("fn", path="src", output_mode="count")
    if isinstance(counts, dict):
        for file, count in counts.items():
            print(f"   {file}: {count} matches")
    print()

def demo_advanced_features():
    """高级功能示例"""
    print("=== 高级功能示例 ===\n")

    grep = pyripgrep.Grep()

    # 1. 不区分大小写搜索
    print("1. 不区分大小写搜索 'STRUCT':")
    files = grep.search("STRUCT", path="src", case_insensitive=True, head_limit=3)
    for file in files:
        print(f"   {file}")
    print()

    # 2. 文件类型过滤
    print("2. 只在 Rust 文件中搜索 'impl':")
    files = grep.search("impl", path=".", file_type="rust")
    for file in files:
        print(f"   {file}")
    print()

    # 3. Glob 模式过滤
    print("3. 使用 glob 模式 '*.rs' 搜索 'pub':")
    files = grep.search("pub", path=".", glob="*.rs", head_limit=3)
    for file in files:
        print(f"   {file}")
    print()

    # 4. 显示行号
    print("4. 显示行号的内容搜索:")
    content = grep.search("struct", path="src", output_mode="content",
                         line_numbers=True, head_limit=3)
    for line in content:
        print(f"   {line}")
    print()

def demo_context_and_limits():
    """上下文和限制示例"""
    print("=== 上下文和限制示例 ===\n")

    grep = pyripgrep.Grep()

    # 1. 上下文行
    print("1. 显示匹配行的上下文 (前后2行):")
    content = grep.search("impl Grep", path="src", output_mode="content",
                         context=2, line_numbers=True)
    for line in content[:5]:  # 只显示前5行避免输出太多
        print(f"   {line}")
    print()

    # 2. 限制输出数量
    print("2. 限制只显示前3个匹配文件:")
    files = grep.search("fn", path=".", head_limit=3)
    for file in files:
        print(f"   {file}")
    print()

def demo_regex_patterns():
    """正则表达式模式示例"""
    print("=== 正则表达式模式示例 ===\n")

    grep = pyripgrep.Grep()

    # 1. 简单正则表达式
    print("1. 使用正则表达式 'fn\\s+\\w+' 查找函数定义:")
    content = grep.search(r"fn\s+\w+", path="src", output_mode="content",
                         line_numbers=True, head_limit=5)
    for line in content:
        print(f"   {line}")
    print()

    # 2. 多行模式 (如果支持)
    print("2. 多行模式搜索:")
    try:
        content = grep.search("struct.*{", path="src", output_mode="content",
                             multiline=True, head_limit=3)
        for line in content:
            print(f"   {line}")
    except Exception as e:
        print(f"   多行模式可能还未完全实现: {e}")
    print()

def demo_performance_comparison():
    """性能对比示例"""
    print("=== 性能对比示例 ===\n")

    import time

    grep = pyripgrep.Grep()

    # 测试大规模搜索性能
    print("测试搜索性能 (搜索所有 'use' 关键字):")

    start_time = time.time()
    files = grep.search("use", path=".")
    end_time = time.time()

    print(f"   找到 {len(files)} 个文件")
    print(f"   耗时: {end_time - start_time:.3f} 秒")
    print()

def main():
    """主函数"""
    print("=== ripgrep-python 新接口演示 ===\n")
    print(f"使用 pyripgrep v{pyripgrep.__version__}\n")

    try:
        demo_basic_usage()
        demo_advanced_features()
        demo_context_and_limits()
        demo_regex_patterns()
        demo_performance_comparison()

        print("=== 演示完成 ===")

    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
