import pyripgrep
import os
import tempfile

def test_basic_search():
    # 创建临时文件进行测试
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试文件
        test_file = os.path.join(tmpdir, "test.py")
        with open(test_file, "w") as f:
            f.write("import os\n")
            f.write("def hello():\n")
            f.write("    print('hello world')\n")

        # 初始化搜索器
        rg = pyripgrep.Grep()

        # 测试基本搜索
        results = rg.search("import", [tmpdir])
        assert len(results) == 1
        assert results[0]["path"] == test_file
        assert results[0]["line_number"] == 1

        # 测试文件搜索
        files = rg.search_files("def", [tmpdir])
        assert len(files) == 1
        assert files[0] == test_file

        # 测试计数功能
        counts = rg.count_matches("print", [tmpdir])
        assert counts[test_file] == 1

def test_options():
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建多个测试文件
        file1 = os.path.join(tmpdir, "file1.txt")
        with open(file1, "w") as f:
            f.write("Hello World\n")
            f.write("hello again\n")

        file2 = os.path.join(tmpdir, "file2.txt")
        with open(file2, "w") as f:
            f.write("TEST content\n")

        rg = pyripgrep.RipGrep()
        options = pyripgrep.SearchOptions()

        # 测试大小写敏感
        options.case_sensitive = True
        results = rg.search("Hello", [tmpdir], options)
        assert len(results) == 1  # 只匹配"Hello World"

        # 测试大小写不敏感
        options.case_sensitive = False
        results = rg.search("hello", [tmpdir], options)
        assert len(results) == 2  # 匹配两个hello

        # 测试最大深度限制
        subdir = os.path.join(tmpdir, "subdir")
        os.makedirs(subdir)
        file3 = os.path.join(subdir, "file3.txt")
        with open(file3, "w") as f:
            f.write("deep content\n")

        options = pyripgrep.SearchOptions()
        options.max_depth = 1
        results = rg.search("deep", [tmpdir], options)
        assert len(results) == 0  # 超过深度限制

        options.max_depth = 2
        results = rg.search("deep", [tmpdir], options)
        assert len(results) == 1  # 在深度范围内


def test_gitignore_functionality():
    """测试 gitignore 风格过滤功能 - 在当前项目中测试"""
    rg = pyripgrep.RipGrep()

    # 在当前项目中测试 target 目录过滤
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 测试默认启用 gitignore 过滤
    options_with_ignore = pyripgrep.SearchOptions()
    options_with_ignore.ignore_vcs = True
    results = rg.search("target", [current_dir], options_with_ignore)
    target_files_filtered = [r["path"] for r in results if "target/" in r["path"]]

    # 测试禁用 gitignore 过滤
    options_no_ignore = pyripgrep.SearchOptions()
    options_no_ignore.ignore_vcs = False
    results_no_ignore = rg.search("target", [current_dir], options_no_ignore)
    target_files_unfiltered = [r["path"] for r in results_no_ignore if "target/" in r["path"]]

    # 禁用 gitignore 后应该找到更多 target/ 目录中的文件
    print(f"启用过滤: {len(target_files_filtered)} 个 target/ 文件")
    print(f"禁用过滤: {len(target_files_unfiltered)} 个 target/ 文件")

    # gitignore 应该过滤掉大部分 target/ 目录中的文件
    assert len(target_files_unfiltered) > len(target_files_filtered)

    # 启用过滤时，target/ 目录中的文件应该很少或为 0
    assert len(target_files_filtered) < 10  # 允许少量文件通过

    # 禁用过滤时应该找到大量 target/ 目录中的文件
    assert len(target_files_unfiltered) > 50


if __name__ == "__main__":
    test_basic_search()
    test_options()
    test_gitignore_functionality()
    print("所有测试通过！")