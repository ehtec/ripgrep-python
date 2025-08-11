#!/usr/bin/env python3
"""
示例：展示 pyripgrep 模块的类型注释使用

这个示例展示了如何正确使用类型注释来获得更好的 IDE 支持和类型检查。
"""

from typing import Dict, List
import pyripgrep

def demo_typed_usage() -> None:
    """演示带类型注释的 pyripgrep 使用"""
    print("=== 类型注释使用示例 ===\n")

    # 创建 Grep 实例
    grep: pyripgrep.Grep = pyripgrep.Grep()

    # 1. 文件匹配模式（默认）- 返回文件路径列表
    print("1. 查找包含 'use' 的文件:")
    files: List[str] = grep.search("use", path="src")
    for file in files[:3]:
        print(f"   {file}")
    print(f"   找到 {len(files)} 个文件\n")

    # 2. 内容模式 - 返回匹配行列表
    print("2. 获取匹配的行内容:")
    content: List[str] = grep.search(
        "fn",
        path="src",
        output_mode="content",
        n=True,  # 显示行号
        head_limit=5
    )
    for line in content:
        print(f"   {line}")
    print()

    # 3. 计数模式 - 返回文件到匹配数的映射
    print("3. 统计每个文件的匹配数量:")
    counts: Dict[str, int] = grep.search("fn", path="src", output_mode="count")
    for filepath, count in counts.items():
        print(f"   {filepath}: {count} matches")
    print()

def advanced_typed_search() -> None:
    """高级搜索功能的类型注释示例"""
    print("=== 高级类型化搜索 ===\n")

    grep: pyripgrep.Grep = pyripgrep.Grep()

    # 带上下文的内容搜索
    print("1. 带上下文的搜索结果:")
    context_results: List[str] = grep.search(
        "impl",
        path="src",
        output_mode="content",
        C=2,  # 前后2行上下文
        n=True,  # 显示行号
        i=True,  # 忽略大小写
        type="rust",  # 只搜索 Rust 文件
        head_limit=3
    )

    for result in context_results:
        print(f"   {result}")
    print()

    # Glob 模式过滤
    print("2. 使用 glob 模式搜索:")
    glob_results: List[str] = grep.search(
        "TODO",
        glob="*.py",
        output_mode="content",
        n=True
    )

    if glob_results:
        print(f"   在 Python 文件中找到 {len(glob_results)} 个 TODO:")
        for result in glob_results[:3]:
            print(f"   {result}")
    else:
        print("   未找到 TODO")
    print()

def demonstrate_type_safety() -> None:
    """演示类型安全的好处"""
    print("=== 类型安全演示 ===\n")

    grep: pyripgrep.Grep = pyripgrep.Grep()

    # 正确的类型注释可以帮助 IDE 提供更好的智能提示
    def process_file_list(files: List[str]) -> None:
        """处理文件列表"""
        print(f"处理 {len(files)} 个文件:")
        for i, file in enumerate(files, 1):
            if i <= 3:  # 只显示前3个
                print(f"  {i}. {file}")

    def process_counts(counts: Dict[str, int]) -> int:
        """处理计数结果"""
        total: int = sum(counts.values())
        print(f"总计找到 {total} 个匹配，分布在 {len(counts)} 个文件中")
        return total

    def process_content(content: List[str]) -> None:
        """处理内容结果"""
        print(f"匹配内容 ({len(content)} 行):")
        for line in content[:3]:
            # 类型检查器知道 line 是 str 类型
            parts = line.split(":", 2)
            if len(parts) >= 2:
                print(f"  文件: {parts[0]}")

    # 使用类型化的结果
    files = grep.search("use", path="src")
    process_file_list(files)

    counts = grep.search("fn", path="src", output_mode="count")
    total_matches = process_counts(counts)

    content = grep.search("impl", path="src", output_mode="content", n=True, head_limit=5)
    process_content(content)

    print(f"\n统计完成，共找到 {total_matches} 个函数定义")

def main() -> None:
    """主函数"""
    try:
        demo_typed_usage()
        advanced_typed_search()
        demonstrate_type_safety()

        print("\n=== 类型注释的好处 ===")
        print("1. IDE 智能提示：自动补全方法和参数")
        print("2. 静态类型检查：mypy、pyright 等工具可以检查类型错误")
        print("3. 更好的代码可读性：明确函数返回类型")
        print("4. 重构安全：类型检查器会发现类型不匹配的问题")
        print("5. 文档化：类型注释本身就是一种文档")

    except Exception as e:
        print(f"错误: {e}")
        return

if __name__ == "__main__":
    main()
