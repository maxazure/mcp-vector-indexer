# MCP Vector Indexer

A Python-based local semantic vector search tool designed for codebase indexing and searching. It supports recursive directory scanning, generates vector embeddings, and provides efficient semantic search functionality.

## Features

- **Recursive Directory Scanning**: Automatically scans all supported files in specified directories
- **Smart File Filtering**: Supports file type filtering and ignoring specific folders
- **Vector Embeddings**: Uses `intfloat/e5-small-v2` model to generate high-quality embeddings
- **SQLite Caching**: Avoids duplicate calculations, improves indexing efficiency
- **Persistent Storage**: Local vector database based on Chroma
- **Semantic Search**: Supports multi-keyword semantic search and similarity ranking
- **Test-Driven Development**: Complete TDD approach ensuring code quality

## Supported File Types

- `.cs` - C# source code
- `.sql` - SQL scripts
- `.vb` - Visual Basic code
- `.aspx` - ASP.NET pages

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/maxazure/mcp-vector-indexer.git
cd mcp-vector-indexer
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### ⚠️ Important Notice

The program is set to single-threaded mode to avoid system freezing due to multithreading:
- First run will download the model, please be patient
- Indexing process is slow but stable, do not interrupt
- Recommended to run when system resources are sufficient

### Basic Usage

#### 1. Index Code Directory

```bash
python main.py index /path/to/your/codebase
```

#### 2. Search Code

```bash
python main.py search "offmarket transfer" "transfer failed"
```

#### 3. View Statistics

```bash
python main.py stats
```

### Advanced Usage

#### Custom Configuration Indexing

```bash
python main.py index /path/to/codebase \
  --model intfloat/e5-small-v2 \
  --chunk-size 1000 \
  --chunk-overlap 100 \
  --extensions .cs .sql .py \
  --ignore .git node_modules bin obj
```

#### Precise Search

```bash
python main.py search "database connection" \
  --results 20 \
  --threshold 0.7
```

#### Custom Database Path

```bash
python main.py index /path/to/codebase \
  --cache-db ./my_cache.db \
  --chroma-db ./my_chroma_store
```

## Project Structure

```
mcp_vector_indexer/
├── config.py                # Configuration module
├── embedder.py              # Embedding generation and caching
├── indexer.py               # File indexing and scanning
├── search.py                # Vector search functionality
├── main.py                  # Main program entry
├── requirements.txt         # Dependency list
├── TODO.md                  # Task progress
├── README.md               # Usage documentation
├── tests/                   # Test directory
│   ├── test_config.py
│   ├── test_embedder.py
│   ├── test_indexer.py
│   └── test_search.py
├── venv/                    # Virtual environment
├── cache.db                 # SQLite cache database
└── chroma_store/            # Chroma vector database
```

## Technical Architecture

### Core Components

1. **Configuration Module (Config)**
   - Manages project configuration parameters
   - Supports file type and ignore rule definitions

2. **Embedder**
   - Uses sentence-transformers to generate vector embeddings
   - SQLite caching to avoid duplicate calculations
   - Supports text chunking processing

3. **File Indexer**
   - Recursively scans directory structure
   - Smart file filtering and content extraction
   - Error handling and encoding compatibility

4. **Vector Search**
   - Chroma vector database integration
   - Multi-keyword semantic search
   - Result ranking and deduplication

### Technology Stack

- **Python 3.11+**: Primary development language
- **sentence-transformers**: Embedding generation
- **chromadb**: Vector database
- **SQLite**: Embedding cache
- **pytest**: Testing framework
- **tqdm**: Progress display

## Development and Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific module tests
python -m pytest tests/test_config.py -v

# Run tests with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Development Mode

The project uses TDD (Test-Driven Development) methodology, with each module having corresponding test files.

## Configuration Options

### Command Line Arguments

- `--model`: Embedding model name (default: intfloat/e5-small-v2)
- `--chunk-size`: Text chunk size (default: 1000)
- `--chunk-overlap`: Chunk overlap size (default: 100)
- `--extensions`: Supported file extensions
- `--ignore`: List of folders to ignore
- `--cache-db`: SQLite cache database path
- `--chroma-db`: Chroma database path

### Configuration File

You can customize default configurations by modifying the `Config` class in `config.py`.

## Performance Optimization

1. **Caching Mechanism**: SQLite cache avoids duplicate embedding calculations
2. **Chunking Processing**: Long texts are automatically chunked for better search accuracy
3. **Single-threaded Mode**: Avoids system freezing due to multithreading, set to 1 thread
4. **Batch Processing**: Insert 100 document chunks in batches to avoid memory overflow
5. **Memory Management**: Lazy loading models to reduce memory usage
6. **Progress Display**: Real-time processing progress for monitoring

## Troubleshooting

### Common Issues

1. **Dependency Installation Failure**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Encoding Errors**
   The project supports automatic detection of UTF-8 and Latin-1 encoding

3. **Database Permission Issues**
   Ensure read/write permissions for the database directory

4. **Memory Insufficient**
   Can reduce the `chunk_size` parameter or process in batches

### Debug Mode

Use the `-v` parameter to view detailed output:

```bash
python main.py index /path/to/codebase -v
```

## Planned Features

- [ ] Function-level code analysis
- [ ] Code summary generation
- [ ] MCP interface integration
- [ ] Web UI interface
- [ ] Real-time file monitoring
- [ ] Multi-language support

## Custom Extensions

You can add new functionality by inheriting existing classes:

```python
from search import VectorSearch

class CustomSearch(VectorSearch):
    def custom_search_method(self, query):
        # Custom search logic
        pass
```

## Contributing

1. Fork the project
2. Create feature branch
3. Write tests
4. Implement functionality
5. Ensure tests pass
6. Submit Pull Request

## License

MIT License

## Contact

For questions or suggestions, please submit an Issue or Pull Request.

---

**Note**: The first run will automatically download the intfloat/e5-small-v2 model, which may take some time.