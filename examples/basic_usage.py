import pyripgrep

def main():
    # 创建 RipGrep 实例
    rg = pyripgrep.RipGrep()

    print(f"使用 ripgrep v{pyripgrep.__version__}\n")

    # 基本搜索
    print("1. 基本搜索 - 在当前目录查找 'use' 关键字:")
    results = rg.search("use", ["."])
    for result in results[:5]:  # 显示前5个结果
        print(f"{result['path']}:{result['line_number']}")
        print(f"  {result['content']}")
    print(f"共找到 {len(results)} 个匹配\n")

    # 使用搜索选项 - gitignore-style 过滤
    print("2. 高级搜索 - 查找 'fn' 但包含隐藏文件，忽略 git 文件:")
    options = pyripgrep.SearchOptions()
    options.case_sensitive = False  # 不区分大小写
    options.include_hidden = True   # 包含隐藏文件
    options.ignore_vcs = True       # 忽略 VCS 文件 (默认)
    options.max_depth = 2           # 限制搜索深度
    results = rg.search("fn", ["."], options)

    for result in results[:3]:
        print(f"{result['path']}:{result['line_number']}")
        print(f"  {result['content']}")
    print(f"共找到 {len(results)} 个匹配\n")

    # 只获取包含匹配的文件
    print("3. 查找包含 'struct' 的文件:")
    files = rg.search_files("struct", ["src"])
    for file in files:
        print(f"  {file}")

    # 统计匹配数量
    print("\n4. 统计每个文件中的匹配数量:")
    counts = rg.count_matches("search", ["src"])
    for file, count in counts.items():
        print(f"  {file}: {count} 处匹配")

    # 展示 gitignore 功能
    print("\n5. 演示 gitignore-style 过滤:")
    print("搜索 'target' 关键字 (应该自动忽略 target/ 目录):")
    options_with_ignore = pyripgrep.SearchOptions()
    options_with_ignore.ignore_vcs = True  # 启用 gitignore 过滤
    results = rg.search("target", ["."], options_with_ignore)

    print(f"找到 {len(results)} 个匹配 (自动忽略了 target/ 目录)")
    for result in results[:3]:
        print(f"{result['path']}:{result['line_number']}")
        print(f"  {result['content']}")

if __name__ == "__main__":
    main()