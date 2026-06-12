#!/usr/bin/env python3
"""OfficeMetaExtractor - 命令行批量测试工具
无需 GUI，直接扫描文件夹并输出解析结果。
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 确保项目根目录在路径中
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "src"))

from src.core.extractor_core import MetaExtractor
from src.parsers import SUPPORTED_EXT
from src.utils.logger import logger


def scan_directory(directory: str, recursive: bool = True) -> list:
    """扫描目录获取支持的文件列表。"""
    root = Path(directory)
    if not root.exists():
        print(f"错误: 目录不存在: {directory}")
        return []
    
    files = []
    if recursive:
        for ext in SUPPORTED_EXT:
            files.extend(root.rglob(f'*{ext}'))
    else:
        for ext in SUPPORTED_EXT:
            files.extend(root.glob(f'*{ext}'))
    
    return sorted(set(str(f) for f in files))


def test_single_file(extractor: MetaExtractor, filepath: str) -> dict:
    """测试单个文件，返回结果字典。"""
    try:
        result = extractor.extract(filepath)
        return result
    except Exception as e:
        return {
            'filepath': filepath,
            'filename': Path(filepath).name,
            'format': Path(filepath).suffix.upper()[1:] or 'UNKNOWN',
            'status': f'失败: {str(e)}'
        }


def print_results(results: list, verbose: bool = False):
    """打印解析结果表格。"""
    # 统计
    total = len(results)
    success = sum(1 for r in results if not str(r.get('status', '')).startswith('失败'))
    failed = total - success
    
    print(f"\n{'='*80}")
    print(f"  OfficeMetaExtractor 批量测试结果")
    print(f"  测试时间: {datetime.now().isoformat()}")
    print(f"{'='*80}")
    print(f"  总计: {total} | 成功: {success} | 失败: {failed}")
    print(f"{'='*80}\n")
    
    # 表头
    print(f"{'序号':<6} {'文件名':<30} {'格式':<6} {'作者':<15} {'状态':<30}")
    print("-" * 80)
    
    for i, result in enumerate(results, 1):
        filename = result.get('filename', '')[:28]
        fmt = result.get('format', '')[:6]
        author = result.get('author', '')[:14]
        status = result.get('status', '')[:28]
        
        is_failed = status.startswith('失败')
        status_icon = "❌" if is_failed else "✅"
        
        print(f"{i:<6} {filename:<30} {fmt:<6} {author:<15} {status_icon} {status:<30}")
        
        if verbose and is_failed:
            print(f"       完整路径: {result.get('filepath', '')}")
    
    print(f"\n{'='*80}\n")


def export_json(results: list, output_path: str):
    """导出结果为 JSON 文件。"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"结果已导出: {output_path}")


def run_audit_mode(extractor: MetaExtractor, directory: str, project_name: str, output_path: str):
    """运行招标审计模式并打印结果。"""
    result = extractor.audit(project_name, directory, output_excel=output_path)

    alerts = result['alerts']
    summary_table = result['summary_table']
    detail_table = result['detail_table']

    print(f"\n{'='*80}")
    print("  OfficeMetaExtractor 招标审计结果")
    print(f"{'='*80}")
    print(f"  项目: {project_name or '未指定'}")
    print(f"  目录: {Path(directory).absolute()}")
    print(f"  文件数: {len(result['results'])}")
    print(f"  告警数: {len(alerts)}")
    print(f"{'='*80}\n")

    if alerts:
        print(f"{'规则':<22} {'严重':<8} {'描述'}")
        print("-" * 80)
        for alert in alerts:
            print(f"{alert.rule_name:<22} {alert.severity:<8} {alert.description}")
            print(f"    涉及公司: {', '.join(alert.affected_companies)}")
        print()
    else:
        print("未发现跨公司异常。\n")

    if summary_table:
        print(f"{'='*80}")
        print("  公司风险汇总")
        print(f"{'='*80}")
        print(f"{'公司名':<20} {'文件数':<8} {'风险评分':<8} {'风险等级':<10}")
        print("-" * 60)
        for row in summary_table:
            print(f"{row['公司名称']:<20} {row['文件数量']:<8} {row['风险评分']:<8} {row['风险等级']:<10}")
        print()

    if result['output_excel']:
        print(f"审计报告已导出: {result['output_excel']}")
    elif output_path:
        print(f"警告: 审计报告导出失败: {output_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='OfficeMetaExtractor 命令行测试工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 测试当前目录
  python test_cli.py
  
  # 测试指定目录
  python test_cli.py /path/to/documents
  
  # 递归测试并导出 JSON
  python test_cli.py /path/to/documents --recursive --export results.json
  
  # 详细输出（显示失败详情）
  python test_cli.py /path/to/documents --verbose
        """
    )
    parser.add_argument('directory', nargs='?', default='.', help='要扫描的目录 (默认: 当前目录)')
    parser.add_argument('-r', '--recursive', action='store_true', default=True, help='递归扫描子目录')
    parser.add_argument('-n', '--no-recursive', action='store_true', help='不递归扫描')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    parser.add_argument('-e', '--export', help='导出结果为 JSON 文件')
    parser.add_argument('-t', '--timeout', type=int, default=30, help='单文件超时时间(秒)')
    parser.add_argument('--audit', action='store_true', help='启用审计模式（招标审计）')
    parser.add_argument('--project-name', default='', help='项目名称（审计模式使用）')
    parser.add_argument('--audit-output', default='audit_report.xlsx', help='审计报告输出路径')
    
    args = parser.parse_args()
    
    directory = args.directory
    recursive = not args.no_recursive if args.no_recursive else args.recursive
    
    print(f"扫描目录: {Path(directory).absolute()}")
    print(f"递归扫描: {'是' if recursive else '否'}")
    print(f"支持的格式: {', '.join(sorted(SUPPORTED_EXT))}")
    
    extractor = MetaExtractor()
    
    if args.audit:
        if not args.project_name:
            print("警告: 未指定项目名称，模板复用检测可能不够精确")
        run_audit_mode(extractor, directory, args.project_name, args.audit_output)
        return
    
    # 扫描文件
    files = scan_directory(directory, recursive)
    
    if not files:
        print("未找到支持的文件。")
        return
    
    print(f"找到 {len(files)} 个文件，开始解析...\n")
    
    # 解析
    results = []
    
    for i, filepath in enumerate(files, 1):
        print(f"  [{i}/{len(files)}] {Path(filepath).name} ...", end=' ', flush=True)
        
        result = test_single_file(extractor, filepath)
        results.append(result)
        
        status = result.get('status', '')
        if status.startswith('失败'):
            print(f"❌ {status[:50]}")
        else:
            print(f"✅ 成功")
    
    # 打印结果
    print_results(results, args.verbose)
    
    # 导出
    if args.export:
        export_json(results, args.export)
    
    # 返回退出码
    failed_count = sum(1 for r in results if str(r.get('status', '')).startswith('失败'))
    if failed_count > 0:
        print(f"注意: {failed_count} 个文件解析失败")
        sys.exit(1)
    else:
        print("所有文件解析成功！")
        sys.exit(0)


if __name__ == '__main__':
    main()
