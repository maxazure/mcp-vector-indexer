# MCP Vector Indexer - TODO Progress

## Project Overview
建立一个Python项目，用于递归扫描代码目录，提取文件内容，生成向量嵌入，并支持语义搜索功能。

## 完成的任务 ✅

### 1. 项目环境设置
- [x] 创建虚拟环境 (venv)
- [x] 安装依赖包 (sentence-transformers, chromadb, pytest等)
- [x] 创建项目目录结构

### 2. 配置模块 (config.py)
- [x] 实现配置类，支持自定义参数
- [x] 支持文件类型过滤 (.cs, .sql, .vb, .aspx)
- [x] 支持忽略文件夹设置 (.git, node_modules等)
- [x] 完成单元测试 (test_config.py)

### 3. 嵌入生成模块 (embedder.py)
- [x] 实现intfloat/e5-small-v2模型嵌入生成
- [x] 实现SQLite缓存机制，避免重复计算
- [x] 支持文本分块处理 (chunk_text)
- [x] 完成单元测试 (test_embedder.py)

### 4. 文件索引模块 (indexer.py)
- [x] 实现递归目录扫描
- [x] 支持文件类型过滤
- [x] 支持忽略文件夹功能
- [x] 文件内容读取与错误处理
- [x] 完成单元测试 (test_indexer.py)

### 5. 向量搜索模块 (search.py)
- [x] 实现Chroma向量数据库集成
- [x] 支持文档添加和向量存储
- [x] 实现语义搜索功能
- [x] 支持多关键词搜索
- [x] 结果去重和相似度排序
- [x] 完成单元测试 (test_search.py)

### 6. 依赖管理
- [x] 创建requirements.txt
- [x] 安装所有必要的依赖包

## 正在进行的任务 🔄

### 7. 项目文档
- [x] 创建TODO.md文件
- [ ] 更新README.md使用说明

## 待完成的任务 📋

### 8. 测试完善
- [ ] 运行所有模块的完整测试套件
- [ ] 确保测试覆盖率达到要求
- [ ] 修复任何失败的测试

### 9. 主程序集成
- [ ] 创建main.py或CLI脚本
- [ ] 集成所有模块功能
- [ ] 实现完整的索引和搜索流程

### 10. 功能扩展 (可选)
- [ ] 支持按函数/语句段落切分
- [ ] 提供内容摘要功能
- [ ] 实现MCP接口集成
- [ ] 添加CLI命令行界面

## 技术栈
- Python 3.11
- sentence-transformers (intfloat/e5-small-v2)
- chromadb (向量数据库)
- SQLite (嵌入缓存)
- pytest (测试框架)
- tqdm (进度条)

## 项目结构
```
mcp_vector_indexer/
├── config.py                # 配置模块
├── embedder.py              # 嵌入生成模块
├── indexer.py               # 文件索引模块
├── search.py                # 向量搜索模块
├── requirements.txt         # 依赖包
├── TODO.md                  # 任务进度
├── tests/                   # 测试目录
│   ├── test_config.py
│   ├── test_embedder.py
│   ├── test_indexer.py
│   └── test_search.py
├── venv/                    # 虚拟环境
├── cache.db                 # SQLite缓存
└── chroma_store/            # Chroma数据库

```

## 性能优化记录

### 2025-07-14 - 单线程模式优化
- [x] 设置环境变量限制线程数为1，避免系统卡死
- [x] 在 embedder.py 中设置 torch.set_num_threads(1)
- [x] 在 main.py 启动时设置多个线程控制环境变量
- [x] 添加批处理机制，每100个文档块批量插入数据库
- [x] 增加进度显示，让用户看到处理状态
- [x] 更新 README.md 添加性能优化说明

### 环境变量设置
```python
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'  
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['VECLIB_MAXIMUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
```

### 关键优化点
1. **单线程模式**: 避免多线程竞争导致系统卡死
2. **批量处理**: 每100个文档块批量插入，减少内存压力
3. **进度显示**: 实时显示处理进度和文件名
4. **懒加载**: 模型按需加载，减少初始内存占用

## 最后更新
2025-07-14 - 完成核心模块开发、测试和性能优化