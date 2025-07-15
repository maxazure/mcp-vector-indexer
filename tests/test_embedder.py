import pytest
import tempfile
import sqlite3
import os
from unittest.mock import Mock, patch
import numpy as np
from embedder import Embedder
from config import Config


class TestEmbedder:
    def test_embedder_initialization(self):
        """Test embedder initialization"""
        config = Config()
        embedder = Embedder(config)
        assert embedder.config == config
        assert embedder.model_name == config.model_name
        assert embedder.cache_db_path == config.cache_db_path

    def test_cache_database_creation(self):
        """Test cache database creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = os.path.join(temp_dir, "test_cache.db")
            config = Config(cache_db_path=cache_path)
            embedder = Embedder(config)
            
            # Database should be created
            assert os.path.exists(cache_path)
            
            # Check table structure
            conn = sqlite3.connect(cache_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            assert ("embeddings",) in tables
            conn.close()

    def test_cache_table_schema(self):
        """Test cache table has correct schema"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = os.path.join(temp_dir, "test_cache.db")
            config = Config(cache_db_path=cache_path)
            embedder = Embedder(config)
            
            conn = sqlite3.connect(cache_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(embeddings);")
            columns = cursor.fetchall()
            conn.close()
            
            column_names = [col[1] for col in columns]
            assert "content_hash" in column_names
            assert "embedding" in column_names
            assert "created_at" in column_names

    @patch('embedder.SentenceTransformer')
    def test_generate_embedding(self, mock_transformer):
        """Test embedding generation"""
        # Mock the transformer
        mock_model = Mock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_transformer.return_value = mock_model
        
        config = Config()
        embedder = Embedder(config)
        
        text = "This is a test text"
        embedding = embedder.generate_embedding(text)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (3,)
        mock_model.encode.assert_called_once_with(text)

    def test_get_content_hash(self):
        """Test content hash generation"""
        config = Config()
        embedder = Embedder(config)
        
        text = "This is a test text"
        hash1 = embedder.get_content_hash(text)
        hash2 = embedder.get_content_hash(text)
        
        # Same text should produce same hash
        assert hash1 == hash2
        
        # Different text should produce different hash
        hash3 = embedder.get_content_hash("Different text")
        assert hash1 != hash3

    @patch('embedder.SentenceTransformer')
    def test_cache_hit(self, mock_transformer):
        """Test cache hit scenario"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = os.path.join(temp_dir, "test_cache.db")
            config = Config(cache_db_path=cache_path)
            
            # Mock the transformer
            mock_model = Mock()
            mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
            mock_transformer.return_value = mock_model
            
            embedder = Embedder(config)
            
            text = "This is a test text"
            
            # First call should generate embedding
            embedding1 = embedder.get_embedding(text)
            assert mock_model.encode.call_count == 1
            
            # Second call should use cache
            embedding2 = embedder.get_embedding(text)
            assert mock_model.encode.call_count == 1  # Should not increase
            
            # Embeddings should be the same
            np.testing.assert_array_equal(embedding1, embedding2)

    @patch('embedder.SentenceTransformer')
    def test_cache_miss(self, mock_transformer):
        """Test cache miss scenario"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = os.path.join(temp_dir, "test_cache.db")
            config = Config(cache_db_path=cache_path)
            
            # Mock the transformer
            mock_model = Mock()
            mock_model.encode.side_effect = [
                np.array([0.1, 0.2, 0.3]),
                np.array([0.4, 0.5, 0.6])
            ]
            mock_transformer.return_value = mock_model
            
            embedder = Embedder(config)
            
            text1 = "This is a test text"
            text2 = "This is another test text"
            
            # Both calls should generate embeddings
            embedding1 = embedder.get_embedding(text1)
            embedding2 = embedder.get_embedding(text2)
            
            assert mock_model.encode.call_count == 2
            assert not np.array_equal(embedding1, embedding2)

    def test_chunk_text(self):
        """Test text chunking functionality"""
        config = Config(chunk_size=10, chunk_overlap=2)
        embedder = Embedder(config)
        
        text = "This is a very long text that should be chunked into smaller pieces"
        chunks = embedder.chunk_text(text)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= config.chunk_size + config.chunk_overlap for chunk in chunks)

    def test_empty_text_handling(self):
        """Test handling of empty or None text"""
        config = Config()
        embedder = Embedder(config)
        
        assert embedder.chunk_text("") == []
        assert embedder.chunk_text(None) == []

    @patch('embedder.SentenceTransformer')
    def test_get_embeddings_for_chunks(self, mock_transformer):
        """Test getting embeddings for text chunks"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = os.path.join(temp_dir, "test_cache.db")
            config = Config(cache_db_path=cache_path, chunk_size=10, chunk_overlap=2)
            
            # Mock the transformer
            mock_model = Mock()
            mock_model.encode.side_effect = [
                np.array([0.1, 0.2, 0.3]),
                np.array([0.4, 0.5, 0.6])
            ]
            mock_transformer.return_value = mock_model
            
            embedder = Embedder(config)
            
            text = "This is a long text that will be chunked"
            embeddings = embedder.get_embeddings_for_chunks(text)
            
            assert len(embeddings) > 0
            assert all(isinstance(emb, np.ndarray) for emb in embeddings)