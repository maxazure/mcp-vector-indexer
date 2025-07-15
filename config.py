import os
from pathlib import Path
from typing import List, Optional


class Config:
    def __init__(
        self,
        model_name: str = "intfloat/e5-small-v2",
        cache_db_path: str = "cache.db",
        chroma_db_path: str = "chroma_store",
        supported_extensions: Optional[List[str]] = None,
        ignored_folders: Optional[List[str]] = None,
        target_directory: Optional[str] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 100
    ):
        self.model_name = model_name
        self.cache_db_path = os.path.abspath(cache_db_path)
        self.chroma_db_path = os.path.abspath(chroma_db_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        if supported_extensions is None:
            self.supported_extensions = [".cs", ".sql", ".vb", ".aspx"]
        else:
            self.supported_extensions = supported_extensions
            
        if ignored_folders is None:
            self.ignored_folders = [".git", "node_modules", "bin", "obj", ".vs"]
        else:
            self.ignored_folders = ignored_folders
            
        if target_directory is not None:
            if not os.path.exists(target_directory):
                raise ValueError(f"Target directory does not exist: {target_directory}")
            self.target_directory = os.path.abspath(target_directory)
        else:
            self.target_directory = None
    
    def should_ignore_file(self, file_path: Path) -> bool:
        """Check if a file should be ignored based on ignored folders"""
        path_parts = file_path.parts
        for ignored_folder in self.ignored_folders:
            if ignored_folder in path_parts:
                return True
        return False
    
    def is_supported_file(self, file_path: str) -> bool:
        """Check if a file has a supported extension"""
        file_extension = os.path.splitext(file_path)[1].lower()
        return file_extension in self.supported_extensions