#!/usr/bin/env python3
"""
简单测试脚本，验证核心功能
"""

import os
import sys

# 设置单线程模式
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['VECLIB_MAXIMUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

from config import Config
from indexer import FileIndexer

def test_basic_functionality():
    """测试基本功能"""
    print("=== 测试基本功能 ===")
    
    # 1. 测试配置
    print("1. 测试配置模块...")
    config = Config(target_directory="./test_code")
    print(f"   支持文件类型: {config.supported_extensions}")
    print(f"   忽略文件夹: {config.ignored_folders}")
    
    # 2. 测试文件扫描
    print("\n2. 测试文件扫描...")
    indexer = FileIndexer(config)
    found_files = indexer.scan_directory()
    print(f"   找到文件: {found_files}")
    
    # 3. 测试文件处理
    print("\n3. 测试文件处理...")
    if found_files:
        first_file = found_files[0]
        content = indexer.read_file_content(first_file)
        print(f"   第一个文件内容长度: {len(content)} 字符")
        print(f"   文件预览: {content[:100]}...")
    
    # 4. 测试统计信息
    print("\n4. 测试统计信息...")
    stats = indexer.get_file_stats()
    print(f"   统计信息: {stats}")
    
    print("\n=== 基本功能测试完成 ===")

if __name__ == "__main__":
    test_basic_functionality()