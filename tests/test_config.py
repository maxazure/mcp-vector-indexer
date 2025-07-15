import pytest
import tempfile
import os
from pathlib import Path
from config import Config


class TestConfig:
    def test_default_config_values(self):
        """Test default configuration values"""
        config = Config()
        assert config.model_name == "intfloat/e5-small-v2"
        assert config.cache_db_path.endswith("cache.db")
        assert config.chroma_db_path.endswith("chroma_store")
        assert config.supported_extensions == [".cs", ".sql", ".vb", ".aspx"]
        assert config.ignored_folders == [".git", "node_modules", "bin", "obj", ".vs"]
        assert config.chunk_size == 1000
        assert config.chunk_overlap == 100

    def test_custom_config_values(self):
        """Test custom configuration values"""
        config = Config(
            model_name="custom-model",
            cache_db_path="custom_cache.db",
            chroma_db_path="custom_chroma",
            supported_extensions=[".py", ".js"],
            ignored_folders=[".git", "node_modules"]
        )
        assert config.model_name == "custom-model"
        assert config.cache_db_path.endswith("custom_cache.db")
        assert config.chroma_db_path.endswith("custom_chroma")
        assert config.supported_extensions == [".py", ".js"]
        assert config.ignored_folders == [".git", "node_modules"]

    def test_target_directory_validation(self):
        """Test target directory validation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config(target_directory=temp_dir)
            assert config.target_directory == temp_dir
            
        # Test with non-existent directory
        with pytest.raises(ValueError, match="Target directory does not exist"):
            Config(target_directory="/non/existent/path")

    def test_file_should_be_ignored(self):
        """Test file filtering based on ignored folders"""
        config = Config()
        
        # Test ignored folders
        assert config.should_ignore_file(Path("/project/.git/config")) == True
        assert config.should_ignore_file(Path("/project/node_modules/package.json")) == True
        assert config.should_ignore_file(Path("/project/bin/debug.exe")) == True
        assert config.should_ignore_file(Path("/project/obj/temp.obj")) == True
        
        # Test non-ignored files
        assert config.should_ignore_file(Path("/project/src/main.cs")) == False
        assert config.should_ignore_file(Path("/project/data/schema.sql")) == False

    def test_is_supported_file(self):
        """Test file extension support"""
        config = Config()
        
        # Test supported extensions
        assert config.is_supported_file("test.cs") == True
        assert config.is_supported_file("query.sql") == True
        assert config.is_supported_file("form.aspx") == True
        assert config.is_supported_file("module.vb") == True
        
        # Test unsupported extensions
        assert config.is_supported_file("readme.txt") == False
        assert config.is_supported_file("config.json") == False
        assert config.is_supported_file("image.png") == False

    def test_config_paths_are_absolute(self):
        """Test that relative paths are converted to absolute"""
        config = Config()
        assert os.path.isabs(config.cache_db_path)
        assert os.path.isabs(config.chroma_db_path)