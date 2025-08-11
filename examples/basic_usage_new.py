#!/usr/bin/env python3
"""
新的基本使用示例，展示 ripgrep-python 的新接口
"""
import pyripgrep
import time

def main():
    print(f"=== ripgrep-python v{pyripgrep.__version__} 新接口演示 ===\n")

    # 创建 Grep 实例
    grep = pyripgrep.Grep()

    # 1. 基本搜索 - 查找包含模式的文件
    print("1. 基本搜索 - 查找包含 'use' 的文件:")
    files = grep.search("use", path="src")
    for file in files:
        print(f"   {file}")
    print(f"   共找到 {len(files)} 个文件\n")

    # 2. 内容搜索 - 显示匹配的行
    print("2. 内容搜索 - 显示包含 'fn' 的行 (前5个):")
    content = grep.search("fn", path="src", output_mode="content", head_limit=5)
    for line in content:
        print(f"   {line}")
    print()

    # 3. 带行号的内容搜索
    print("3. 带行号的内容搜索:")
    content_with_lines = grep.search("struct", path="src",
                                   output_mode="content",
                                   line_numbers=True,
                                   head_limit=3)
    for line in content_with_lines:
        print(f"   {line}")
    print()

    # 4. 统计模式 - 计算每个文件的匹配数
    print("4. 统计模式 - 每个文件的匹配计数:")
    counts = grep.search("fn", path="src", output_mode="count")
    if isinstance(counts, dict):
        for file, count in counts.items():
            print(f"   {file}: {count} 次匹配")
    print()

    # 5. 文件类型过滤
    print("5. 文件类型过滤 - 只在 Rust 文件中搜索:")
    rust_files = grep.search("impl", file_type="rust", path=".")
    for file in rust_files:
        print(f"   {file}")
    print()

    # 6. 不区分大小写搜索
    print("6. 不区分大小写搜索 'STRUCT':")
    case_insensitive_results = grep.search("STRUCT",
                                         case_insensitive=True,
                                         path="src",
                                         head_limit=3)
    for file in case_insensitive_results:
        print(f"   {file}")
    print()

    # 7. Glob 模式过滤
    print("7. Glob 模式过滤 - 搜索 *.rs 文件:")
    glob_results = grep.search("pub", glob="*.rs", path=".", head_limit=3)
    for file in glob_results:
        print(f"   {file}")
    print()

    # 8. 正则表达式搜索
    print("8. 正则表达式搜索 - 查找函数定义:")
    regex_results = grep.search(r"fn\s+\w+",
                               path="src",
                               output_mode="content",
                               head_limit=3)
    for line in regex_results:
        print(f"   {line}")
    print()

    # 9. 上下文搜索
    print("9. 上下文搜索 - 显示匹配行前后的上下文:")
    context_results = grep.search("impl Grep",
                                 path="src",
                                 output_mode="content",
                                 context=1,
                                 line_numbers=True)
    for line in context_results[:5]:  # 只显示前5行
        print(f"   {line}")
    print()

    # 10. 性能测试
    print("10. 性能测试:")
    start_time = time.time()
    all_files = grep.search(".", path=".", head_limit=100)
    end_time = time.time()
    print(f"    搜索 100 个文件用时: {end_time - start_time:.3f} 秒")
    print(f"    总共找到: {len(all_files)} 个文件")

    print("\n=== 演示完成 ===")
    print("更多详细用法请参考: docs/NEW_INTERFACE.md")

if __name__ == "__main__":
    main()
