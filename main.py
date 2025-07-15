#!/usr/bin/env python3
"""
MCP Vector Indexer - Main CLI Script
支持递归扫描代码目录，生成向量嵌入，并提供语义搜索功能
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# 设置单线程模式，避免多线程导致系统卡死
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['VECLIB_MAXIMUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

from config import Config
from indexer import FileIndexer
from search import VectorSearch


def index_directory(target_dir: str, config: Config) -> None:
    """索引指定目录的所有文件"""
    print(f"开始索引目录: {target_dir}")
    print("注意: 程序设置为单线程模式，避免系统卡死")
    
    # 更新配置中的目标目录
    config.target_directory = target_dir
    
    # 创建文件索引器
    indexer = FileIndexer(config)
    
    # 扫描并处理所有文件
    print("扫描文件中...")
    documents = indexer.process_all_files()
    
    if not documents:
        print("未找到任何支持的文件")
        return
    
    print(f"找到 {len(documents)} 个文件")
    
    # 创建向量搜索器并添加文档
    print("生成向量嵌入并存储到数据库...")
    print("首次运行时需要下载模型，请稍候...")
    search = VectorSearch(config)
    search.add_documents(documents)
    
    print("索引完成!")
    
    # 显示统计信息
    stats = indexer.get_file_stats()
    print(f"\n索引统计:")
    print(f"总文件数: {stats['total_files']}")
    print("文件类型分布:")
    for file_type, count in stats['file_types'].items():
        print(f"  {file_type}: {count} 个文件")
    
    # 显示数据库信息
    db_info = search.get_collection_info()
    print(f"\n数据库信息:")
    print(f"文档块数量: {db_info['document_count']}")
    print(f"数据库路径: {db_info['database_path']}")


def search_documents(queries: List[str], config: Config, n_results: int = 10) -> None:
    """搜索文档"""
    print(f"搜索关键词: {queries}")
    
    # 创建向量搜索器
    search = VectorSearch(config)
    
    # 检查数据库是否存在
    try:
        db_info = search.get_collection_info()
        if db_info['document_count'] == 0:
            print("数据库为空，请先运行索引命令")
            return
    except Exception as e:
        print(f"数据库错误: {e}")
        print("请先运行索引命令")
        return
    
    # 执行搜索
    results = search.search(queries, n_results=n_results)
    
    if not results:
        print("未找到相关结果")
        return
    
    print(f"\n找到 {len(results)} 个相关结果:\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. 文件: {result['file_path']}")
        print(f"   类型: {result['file_type']}")
        print(f"   相似度: {result['similarity']:.3f}")
        print(f"   内容预览: {result['content'][:200]}...")
        print("-" * 80)


def show_stats(config: Config) -> None:
    """显示索引统计信息"""
    search = VectorSearch(config)
    
    try:
        db_info = search.get_collection_info()
        print(f"数据库信息:")
        print(f"集合名称: {db_info['collection_name']}")
        print(f"文档块数量: {db_info['document_count']}")
        print(f"数据库路径: {db_info['database_path']}")
        
        # 列出所有集合
        collections = search.list_collections()
        print(f"\n所有集合:")
        for col in collections:
            print(f"  - {col}")
            
    except Exception as e:
        print(f"无法获取数据库信息: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="MCP Vector Indexer - 代码语义搜索工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 索引代码目录
  python main.py index /path/to/your/codebase

  # 搜索代码
  python main.py search "offmarket transfer" "transfer failed"
  
  # 显示统计信息
  python main.py stats
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 索引命令
    index_parser = subparsers.add_parser('index', help='索引代码目录')
    index_parser.add_argument('directory', help='要索引的目录路径')
    index_parser.add_argument('--model', default='intfloat/e5-small-v2', help='嵌入模型名称')
    index_parser.add_argument('--chunk-size', type=int, default=1000, help='文本分块大小')
    index_parser.add_argument('--chunk-overlap', type=int, default=100, help='分块重叠大小')
    
    # 搜索命令
    search_parser = subparsers.add_parser('search', help='搜索代码')
    search_parser.add_argument('queries', nargs='+', help='搜索关键词')
    search_parser.add_argument('-n', '--results', type=int, default=10, help='返回结果数量')
    search_parser.add_argument('--threshold', type=float, default=0.0, help='相似度阈值')
    
    # 统计命令
    stats_parser = subparsers.add_parser('stats', help='显示索引统计信息')
    
    # 配置选项
    parser.add_argument('--cache-db', default='cache.db', help='SQLite缓存数据库路径')
    parser.add_argument('--chroma-db', default='chroma_store', help='Chroma数据库路径')
    parser.add_argument('--extensions', nargs='+', default=['.cs', '.sql', '.vb', '.aspx'], 
                       help='支持的文件扩展名')
    parser.add_argument('--ignore', nargs='+', default=['.git', 'node_modules', 'bin', 'obj', '.vs'],
                       help='忽略的文件夹')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 创建配置
    config = Config(
        cache_db_path=args.cache_db,
        chroma_db_path=args.chroma_db,
        supported_extensions=args.extensions,
        ignored_folders=args.ignore
    )
    
    # 执行命令
    if args.command == 'index':
        if not os.path.exists(args.directory):
            print(f"错误: 目录不存在: {args.directory}")
            sys.exit(1)
        
        config.model_name = args.model
        config.chunk_size = args.chunk_size
        config.chunk_overlap = args.chunk_overlap
        
        index_directory(args.directory, config)
    
    elif args.command == 'search':
        search_documents(args.queries, config, args.results)
    
    elif args.command == 'stats':
        show_stats(config)


if __name__ == '__main__':
    main()