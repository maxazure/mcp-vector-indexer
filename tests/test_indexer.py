import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from indexer import FileIndexer
from config import Config


class TestFileIndexer:
    def test_indexer_initialization(self):
        """Test file indexer initialization"""
        config = Config()
        indexer = FileIndexer(config)
        assert indexer.config == config

    def test_scan_directory_with_supported_files(self):
        """Test directory scanning with supported files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = [
                "test1.cs",
                "test2.sql",
                "test3.vb",
                "test4.aspx",
                "test5.txt"  # Should be ignored
            ]
            
            for file_name in test_files:
                file_path = os.path.join(temp_dir, file_name)
                with open(file_path, 'w') as f:
                    f.write(f"Content of {file_name}")
            
            config = Config(target_directory=temp_dir)
            indexer = FileIndexer(config)
            
            found_files = indexer.scan_directory()
            found_file_names = [os.path.basename(f) for f in found_files]
            
            assert "test1.cs" in found_file_names
            assert "test2.sql" in found_file_names
            assert "test3.vb" in found_file_names
            assert "test4.aspx" in found_file_names
            assert "test5.txt" not in found_file_names

    def test_scan_directory_with_ignored_folders(self):
        """Test directory scanning ignores specified folders"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create ignored folder structure
            git_dir = os.path.join(temp_dir, ".git")
            node_modules_dir = os.path.join(temp_dir, "node_modules")
            src_dir = os.path.join(temp_dir, "src")
            
            os.makedirs(git_dir)
            os.makedirs(node_modules_dir)
            os.makedirs(src_dir)
            
            # Create files in different directories
            with open(os.path.join(git_dir, "config.cs"), 'w') as f:
                f.write("Git config")
            with open(os.path.join(node_modules_dir, "package.cs"), 'w') as f:
                f.write("Node module")
            with open(os.path.join(src_dir, "main.cs"), 'w') as f:
                f.write("Main source")
            
            config = Config(target_directory=temp_dir)
            indexer = FileIndexer(config)
            
            found_files = indexer.scan_directory()
            found_file_names = [os.path.basename(f) for f in found_files]
            
            assert "config.cs" not in found_file_names
            assert "package.cs" not in found_file_names
            assert "main.cs" in found_file_names

    def test_scan_directory_recursive(self):
        """Test recursive directory scanning"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested structure
            nested_dir = os.path.join(temp_dir, "level1", "level2", "level3")
            os.makedirs(nested_dir)
            
            # Create files at different levels
            with open(os.path.join(temp_dir, "root.cs"), 'w') as f:
                f.write("Root file")
            with open(os.path.join(nested_dir, "nested.cs"), 'w') as f:
                f.write("Nested file")
            
            config = Config(target_directory=temp_dir)
            indexer = FileIndexer(config)
            
            found_files = indexer.scan_directory()
            found_file_names = [os.path.basename(f) for f in found_files]
            
            assert "root.cs" in found_file_names
            assert "nested.cs" in found_file_names

    def test_read_file_content(self):
        """Test reading file content"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.cs")
            test_content = "using System;\nnamespace Test { }"
            
            with open(file_path, 'w') as f:
                f.write(test_content)
            
            config = Config()
            indexer = FileIndexer(config)
            
            content = indexer.read_file_content(file_path)
            assert content == test_content

    def test_read_file_content_with_encoding_error(self):
        """Test handling of file encoding errors"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.cs")
            
            # Write binary content that might cause encoding issues
            with open(file_path, 'wb') as f:
                f.write(b'\xff\xfe\x00\x00')  # Invalid UTF-8
            
            config = Config()
            indexer = FileIndexer(config)
            
            content = indexer.read_file_content(file_path)
            # Should read content with fallback encoding
            assert isinstance(content, str)

    def test_read_file_content_file_not_found(self):
        """Test handling of non-existent files"""
        config = Config()
        indexer = FileIndexer(config)
        
        content = indexer.read_file_content("/non/existent/file.cs")
        assert content == ""

    @patch('indexer.FileIndexer.read_file_content')
    def test_process_file(self, mock_read_file):
        """Test processing a single file"""
        mock_read_file.return_value = "Test file content"
        
        config = Config()
        indexer = FileIndexer(config)
        
        result = indexer.process_file("/path/to/test.cs")
        
        assert result['file_path'] == "/path/to/test.cs"
        assert result['content'] == "Test file content"
        assert result['file_type'] == ".cs"
        assert 'file_size' in result
        assert 'last_modified' in result

    @patch('indexer.FileIndexer.read_file_content')
    def test_process_file_empty_content(self, mock_read_file):
        """Test processing file with empty content"""
        mock_read_file.return_value = ""
        
        config = Config()
        indexer = FileIndexer(config)
        
        result = indexer.process_file("/path/to/test.cs")
        assert result is None

    def test_get_file_info(self):
        """Test getting file information"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.cs")
            test_content = "Test content"
            
            with open(file_path, 'w') as f:
                f.write(test_content)
            
            config = Config()
            indexer = FileIndexer(config)
            
            info = indexer.get_file_info(file_path)
            
            assert info['file_size'] == len(test_content)
            assert 'last_modified' in info
            assert info['file_type'] == ".cs"

    def test_process_all_files(self):
        """Test processing all files in directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            files = ["file1.cs", "file2.sql", "file3.vb"]
            for file_name in files:
                file_path = os.path.join(temp_dir, file_name)
                with open(file_path, 'w') as f:
                    f.write(f"Content of {file_name}")
            
            config = Config(target_directory=temp_dir)
            indexer = FileIndexer(config)
            
            results = indexer.process_all_files()
            
            assert len(results) == 3
            assert all('file_path' in result for result in results)
            assert all('content' in result for result in results)

    def test_get_file_stats(self):
        """Test getting file statistics"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            files = ["file1.cs", "file2.sql", "file3.vb", "file4.aspx"]
            for file_name in files:
                file_path = os.path.join(temp_dir, file_name)
                with open(file_path, 'w') as f:
                    f.write(f"Content of {file_name}")
            
            config = Config(target_directory=temp_dir)
            indexer = FileIndexer(config)
            
            stats = indexer.get_file_stats()
            
            assert stats['total_files'] == 4
            assert stats['file_types']['.cs'] == 1
            assert stats['file_types']['.sql'] == 1
            assert stats['file_types']['.vb'] == 1
            assert stats['file_types']['.aspx'] == 1