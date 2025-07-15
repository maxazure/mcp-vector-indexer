import hashlib
import sqlite3
import pickle
import numpy as np
from datetime import datetime
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from config import Config


class Embedder:
    def __init__(self, config: Config):
        self.config = config
        self.model_name = config.model_name
        self.cache_db_path = config.cache_db_path
        self.model = None
        self._init_cache_db()
    
    def _init_cache_db(self):
        """Initialize SQLite cache database"""
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                content_hash TEXT PRIMARY KEY,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def _load_model(self):
        """Lazy load the sentence transformer model with single thread"""
        if self.model is None:
            # 设置单线程模式，避免多线程导致的性能问题
            import torch
            torch.set_num_threads(1)
            self.model = SentenceTransformer(self.model_name)
        return self.model
    
    def get_content_hash(self, content: str) -> str:
        """Generate hash for content to use as cache key"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _get_cached_embedding(self, content_hash: str) -> Optional[np.ndarray]:
        """Get embedding from cache if exists"""
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT embedding FROM embeddings WHERE content_hash = ?', (content_hash,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return pickle.loads(result[0])
        return None
    
    def _cache_embedding(self, content_hash: str, embedding: np.ndarray):
        """Cache embedding in database"""
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO embeddings (content_hash, embedding, created_at)
            VALUES (?, ?, ?)
        ''', (content_hash, pickle.dumps(embedding), datetime.now()))
        conn.commit()
        conn.close()
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for given text using the model"""
        model = self._load_model()
        return model.encode(text)
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text, using cache if available"""
        content_hash = self.get_content_hash(text)
        
        # Try to get from cache first
        cached_embedding = self._get_cached_embedding(content_hash)
        if cached_embedding is not None:
            return cached_embedding
        
        # Generate new embedding and cache it
        embedding = self.generate_embedding(text)
        self._cache_embedding(content_hash, embedding)
        return embedding
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks based on configuration"""
        if not text:
            return []
        
        chunks = []
        chunk_size = self.config.chunk_size
        chunk_overlap = self.config.chunk_overlap
        
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end]
            chunks.append(chunk)
            
            # Move start position considering overlap
            start = end - chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
    def get_embeddings_for_chunks(self, text: str) -> List[np.ndarray]:
        """Get embeddings for all chunks of text"""
        chunks = self.chunk_text(text)
        embeddings = []
        
        for chunk in chunks:
            embedding = self.get_embedding(chunk)
            embeddings.append(embedding)
        
        return embeddings