import pytest
import tempfile
import os
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from search import VectorSearch
from config import Config
from embedder import Embedder


class TestVectorSearch:
    def test_search_initialization(self):
        """Test vector search initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config(chroma_db_path=temp_dir)
            search = VectorSearch(config)
            assert search.config == config
            assert search.chroma_db_path == temp_dir

    @patch('search.chromadb.PersistentClient')
    def test_chroma_client_initialization(self, mock_client):
        """Test Chroma client initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config(chroma_db_path=temp_dir)
            search = VectorSearch(config)
            
            # Access client property to trigger initialization
            client = search.client
            mock_client.assert_called_once_with(path=temp_dir)

    @patch('search.chromadb.PersistentClient')
    def test_get_or_create_collection(self, mock_client):
        """Test collection creation or retrieval"""
        mock_collection = Mock()
        mock_client_instance = Mock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance
        
        config = Config()
        search = VectorSearch(config)
        
        collection = search.get_or_create_collection("test_collection")
        
        assert collection == mock_collection
        mock_client_instance.get_or_create_collection.assert_called_once_with(
            name="test_collection",
            metadata={"hnsw:space": "cosine"}
        )

    @patch('search.chromadb.PersistentClient')
    @patch('search.Embedder')
    def test_add_documents(self, mock_embedder_class, mock_client):
        """Test adding documents to collection"""
        # Mock embedder
        mock_embedder = Mock()
        mock_embedder.get_embeddings_for_chunks.return_value = [
            np.array([0.1, 0.2, 0.3]),
            np.array([0.4, 0.5, 0.6])
        ]
        mock_embedder.chunk_text.return_value = ["chunk1", "chunk2"]
        mock_embedder_class.return_value = mock_embedder
        
        # Mock collection
        mock_collection = Mock()
        mock_client_instance = Mock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance
        
        config = Config()
        search = VectorSearch(config)
        
        documents = [
            {
                'file_path': '/path/to/file1.cs',
                'content': 'This is test content for file 1',
                'file_type': '.cs'
            },
            {
                'file_path': '/path/to/file2.sql',
                'content': 'This is test content for file 2',
                'file_type': '.sql'
            }
        ]
        
        search.add_documents(documents)
        
        # Verify embedder was called for each document
        assert mock_embedder.get_embeddings_for_chunks.call_count == 2
        
        # Verify collection add was called
        mock_collection.add.assert_called()

    @patch('search.chromadb.PersistentClient')
    @patch('search.Embedder')
    def test_search_single_query(self, mock_embedder_class, mock_client):
        """Test searching with single query"""
        # Mock embedder
        mock_embedder = Mock()
        mock_embedder.get_embedding.return_value = np.array([0.1, 0.2, 0.3])
        mock_embedder_class.return_value = mock_embedder
        
        # Mock collection
        mock_collection = Mock()
        mock_collection.query.return_value = {
            'ids': [['doc1_chunk1', 'doc2_chunk1']],
            'distances': [[0.1, 0.2]],
            'metadatas': [[
                {'file_path': '/path/to/file1.cs', 'chunk_index': 0, 'file_type': '.cs'},
                {'file_path': '/path/to/file2.sql', 'chunk_index': 0, 'file_type': '.sql'}
            ]],
            'documents': [['Content chunk 1', 'Content chunk 2']]
        }
        mock_client_instance = Mock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance
        
        config = Config()
        search = VectorSearch(config)
        
        results = search.search("test query", n_results=2)
        
        assert len(results) == 2
        assert results[0]['file_path'] == '/path/to/file1.cs'
        assert results[0]['content'] == 'Content chunk 1'
        assert results[0]['similarity'] == 0.9  # 1 - 0.1

    @patch('search.chromadb.PersistentClient')
    @patch('search.Embedder')
    def test_search_multiple_queries(self, mock_embedder_class, mock_client):
        """Test searching with multiple queries"""
        # Mock embedder
        mock_embedder = Mock()
        mock_embedder.get_embedding.side_effect = [
            np.array([0.1, 0.2, 0.3]),
            np.array([0.4, 0.5, 0.6])
        ]
        mock_embedder_class.return_value = mock_embedder
        
        # Mock collection
        mock_collection = Mock()
        mock_collection.query.side_effect = [
            {
                'ids': [['doc1_chunk1']],
                'distances': [[0.1]],
                'metadatas': [[{'file_path': '/path/to/file1.cs', 'chunk_index': 0, 'file_type': '.cs'}]],
                'documents': [['Content chunk 1']]
            },
            {
                'ids': [['doc2_chunk1']],
                'distances': [[0.2]],
                'metadatas': [[{'file_path': '/path/to/file2.sql', 'chunk_index': 0, 'file_type': '.sql'}]],
                'documents': [['Content chunk 2']]
            }
        ]
        mock_client_instance = Mock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance
        
        config = Config()
        search = VectorSearch(config)
        
        results = search.search(["query1", "query2"], n_results=1)
        
        assert len(results) == 2
        assert results[0]['file_path'] == '/path/to/file1.cs'
        assert results[1]['file_path'] == '/path/to/file2.sql'

    @patch('search.chromadb.PersistentClient')
    def test_get_collection_info(self, mock_client):
        """Test getting collection information"""
        mock_collection = Mock()
        mock_collection.count.return_value = 100
        mock_client_instance = Mock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance
        
        config = Config()
        search = VectorSearch(config)
        
        info = search.get_collection_info()
        
        assert info['document_count'] == 100
        assert 'collection_name' in info

    @patch('search.chromadb.PersistentClient')
    def test_delete_collection(self, mock_client):
        """Test deleting collection"""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        
        config = Config()
        search = VectorSearch(config)
        
        search.delete_collection("test_collection")
        
        mock_client_instance.delete_collection.assert_called_once_with("test_collection")

    @patch('search.chromadb.PersistentClient')
    def test_list_collections(self, mock_client):
        """Test listing collections"""
        mock_client_instance = Mock()
        mock_client_instance.list_collections.return_value = [
            Mock(name="collection1"),
            Mock(name="collection2")
        ]
        mock_client.return_value = mock_client_instance
        
        config = Config()
        search = VectorSearch(config)
        
        collections = search.list_collections()
        
        assert len(collections) == 2
        mock_client_instance.list_collections.assert_called_once()

    def test_deduplicate_results(self):
        """Test result deduplication"""
        config = Config()
        search = VectorSearch(config)
        
        results = [
            {'file_path': '/path/to/file1.cs', 'content': 'Content 1', 'similarity': 0.9},
            {'file_path': '/path/to/file2.sql', 'content': 'Content 2', 'similarity': 0.8},
            {'file_path': '/path/to/file1.cs', 'content': 'Content 3', 'similarity': 0.7},
            {'file_path': '/path/to/file3.vb', 'content': 'Content 4', 'similarity': 0.6}
        ]
        
        deduplicated = search.deduplicate_results(results)
        
        assert len(deduplicated) == 3
        file_paths = [r['file_path'] for r in deduplicated]
        assert '/path/to/file1.cs' in file_paths
        assert '/path/to/file2.sql' in file_paths
        assert '/path/to/file3.vb' in file_paths
        
        # Should keep the highest similarity score for duplicates
        file1_result = next(r for r in deduplicated if r['file_path'] == '/path/to/file1.cs')
        assert file1_result['similarity'] == 0.9

    def test_sort_results_by_similarity(self):
        """Test sorting results by similarity"""
        config = Config()
        search = VectorSearch(config)
        
        results = [
            {'file_path': '/path/to/file1.cs', 'similarity': 0.6},
            {'file_path': '/path/to/file2.sql', 'similarity': 0.9},
            {'file_path': '/path/to/file3.vb', 'similarity': 0.7}
        ]
        
        sorted_results = search.sort_results_by_similarity(results)
        
        assert sorted_results[0]['similarity'] == 0.9
        assert sorted_results[1]['similarity'] == 0.7
        assert sorted_results[2]['similarity'] == 0.6

    def test_filter_results_by_threshold(self):
        """Test filtering results by similarity threshold"""
        config = Config()
        search = VectorSearch(config)
        
        results = [
            {'file_path': '/path/to/file1.cs', 'similarity': 0.9},
            {'file_path': '/path/to/file2.sql', 'similarity': 0.5},
            {'file_path': '/path/to/file3.vb', 'similarity': 0.3}
        ]
        
        filtered = search.filter_results_by_threshold(results, threshold=0.6)
        
        assert len(filtered) == 1
        assert filtered[0]['similarity'] == 0.9