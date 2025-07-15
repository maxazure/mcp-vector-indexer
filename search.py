import os
import chromadb
import numpy as np
from typing import List, Dict, Any, Union, Optional
from config import Config
from embedder import Embedder


class VectorSearch:
    def __init__(self, config: Config):
        self.config = config
        self.chroma_db_path = config.chroma_db_path
        self.embedder = Embedder(config)
        self._client = None
        self._collection = None
        self.collection_name = "code_documents"
    
    @property
    def client(self):
        """Lazy initialization of Chroma client"""
        if self._client is None:
            self._client = chromadb.PersistentClient(path=self.chroma_db_path)
        return self._client
    
    def get_or_create_collection(self, collection_name: Optional[str] = None) -> chromadb.Collection:
        """Get or create a Chroma collection"""
        if collection_name is None:
            collection_name = self.collection_name
        
        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(self, documents: List[Dict[str, Any]], collection_name: Optional[str] = None) -> None:
        """Add documents to the vector database"""
        collection = self.get_or_create_collection(collection_name)
        
        all_ids = []
        all_embeddings = []
        all_metadatas = []
        all_documents = []
        
        print(f"处理 {len(documents)} 个文档...")
        
        for doc_idx, doc in enumerate(documents):
            file_path = doc['file_path']
            content = doc['content']
            file_type = doc.get('file_type', '')
            
            print(f"[{doc_idx+1}/{len(documents)}] 处理文件: {os.path.basename(file_path)}")
            
            # Get embeddings for chunks
            embeddings = self.embedder.get_embeddings_for_chunks(content)
            chunks = self.embedder.chunk_text(content)
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                doc_id = f"{file_path}_{i}"
                
                all_ids.append(doc_id)
                all_embeddings.append(embedding.tolist())
                all_metadatas.append({
                    'file_path': file_path,
                    'file_type': file_type,
                    'chunk_index': i,
                    'file_size': doc.get('file_size', 0),
                    'last_modified': doc.get('last_modified', '').isoformat() if doc.get('last_modified') else ''
                })
                all_documents.append(chunk)
            
            # 分批处理，避免内存溢出
            if len(all_ids) >= 100:  # 每100个文档块批量插入
                print(f"  插入 {len(all_ids)} 个文档块到数据库...")
                collection.add(
                    ids=all_ids,
                    embeddings=all_embeddings,
                    metadatas=all_metadatas,
                    documents=all_documents
                )
                all_ids = []
                all_embeddings = []
                all_metadatas = []
                all_documents = []
        
        # 处理剩余的文档块
        if all_ids:
            print(f"  插入最后 {len(all_ids)} 个文档块到数据库...")
            collection.add(
                ids=all_ids,
                embeddings=all_embeddings,
                metadatas=all_metadatas,
                documents=all_documents
            )
    
    def search(self, query: Union[str, List[str]], n_results: int = 10, 
               collection_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for documents using vector similarity"""
        collection = self.get_or_create_collection(collection_name)
        
        if isinstance(query, str):
            queries = [query]
        else:
            queries = query
        
        all_results = []
        
        for q in queries:
            # Get query embedding
            query_embedding = self.embedder.get_embedding(q)
            
            # Search in collection
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results
            )
            
            # Process results
            for i in range(len(results['ids'][0])):
                result = {
                    'file_path': results['metadatas'][0][i]['file_path'],
                    'content': results['documents'][0][i],
                    'similarity': 1.0 - results['distances'][0][i],  # Convert distance to similarity
                    'file_type': results['metadatas'][0][i].get('file_type', ''),
                    'chunk_index': results['metadatas'][0][i]['chunk_index'],
                    'query': q
                }
                all_results.append(result)
        
        # Sort by similarity and deduplicate
        sorted_results = self.sort_results_by_similarity(all_results)
        deduplicated_results = self.deduplicate_results(sorted_results)
        
        return deduplicated_results[:n_results]
    
    def search_with_filters(self, query: Union[str, List[str]], 
                           file_types: Optional[List[str]] = None,
                           similarity_threshold: float = 0.0,
                           n_results: int = 10,
                           collection_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search with additional filters"""
        # Get initial results
        results = self.search(query, n_results=n_results*2, collection_name=collection_name)
        
        # Apply file type filter
        if file_types:
            results = [r for r in results if r['file_type'] in file_types]
        
        # Apply similarity threshold
        results = self.filter_results_by_threshold(results, similarity_threshold)
        
        return results[:n_results]
    
    def deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results, keeping the highest similarity score"""
        seen_files = {}
        
        for result in results:
            file_path = result['file_path']
            if file_path not in seen_files or result['similarity'] > seen_files[file_path]['similarity']:
                seen_files[file_path] = result
        
        return list(seen_files.values())
    
    def sort_results_by_similarity(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort results by similarity score in descending order"""
        return sorted(results, key=lambda x: x['similarity'], reverse=True)
    
    def filter_results_by_threshold(self, results: List[Dict[str, Any]], 
                                  threshold: float) -> List[Dict[str, Any]]:
        """Filter results by minimum similarity threshold"""
        return [r for r in results if r['similarity'] >= threshold]
    
    def get_collection_info(self, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about the collection"""
        collection = self.get_or_create_collection(collection_name)
        
        return {
            'collection_name': collection_name or self.collection_name,
            'document_count': collection.count(),
            'database_path': self.chroma_db_path
        }
    
    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection"""
        self.client.delete_collection(collection_name)
    
    def list_collections(self) -> List[str]:
        """List all collections"""
        collections = self.client.list_collections()
        return [col.name for col in collections]
    
    def update_document(self, file_path: str, content: str, 
                       collection_name: Optional[str] = None) -> None:
        """Update a document in the collection"""
        collection = self.get_or_create_collection(collection_name)
        
        # First, delete existing chunks for this file
        try:
            # Get all document IDs for this file
            results = collection.get(where={"file_path": file_path})
            if results['ids']:
                collection.delete(ids=results['ids'])
        except Exception as e:
            print(f"Warning: Could not delete existing chunks for {file_path}: {e}")
        
        # Add the updated document
        doc = {
            'file_path': file_path,
            'content': content,
            'file_type': os.path.splitext(file_path)[1].lower()
        }
        self.add_documents([doc], collection_name)
    
    def get_document_by_path(self, file_path: str, 
                           collection_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all chunks for a specific document"""
        collection = self.get_or_create_collection(collection_name)
        
        results = collection.get(where={"file_path": file_path})
        
        documents = []
        for i in range(len(results['ids'])):
            documents.append({
                'id': results['ids'][i],
                'content': results['documents'][i],
                'metadata': results['metadatas'][i]
            })
        
        return documents