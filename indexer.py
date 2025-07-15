import os
import glob
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from tqdm import tqdm
from config import Config


class FileIndexer:
    def __init__(self, config: Config):
        self.config = config
    
    def scan_directory(self) -> List[str]:
        """Recursively scan directory for supported files"""
        if not self.config.target_directory:
            return []
        
        found_files = []
        
        # Walk through directory recursively
        for root, dirs, files in os.walk(self.config.target_directory):
            # Remove ignored directories from dirs list to prevent traversal
            dirs[:] = [d for d in dirs if d not in self.config.ignored_folders]
            
            # Check if current directory should be ignored
            current_path = Path(root)
            if self.config.should_ignore_file(current_path):
                continue
            
            # Process files in current directory
            for file in files:
                if self.config.is_supported_file(file):
                    file_path = os.path.join(root, file)
                    file_path_obj = Path(file_path)
                    
                    # Double-check if file should be ignored
                    if not self.config.should_ignore_file(file_path_obj):
                        found_files.append(file_path)
        
        return found_files
    
    def read_file_content(self, file_path: str) -> str:
        """Read file content with error handling"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Warning: File not found: {file_path}")
            return ""
        except UnicodeDecodeError:
            try:
                # Try with different encoding
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                print(f"Warning: Cannot read file {file_path}: {e}")
                return ""
        except Exception as e:
            print(f"Warning: Error reading file {file_path}: {e}")
            return ""
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file metadata"""
        try:
            stat = os.stat(file_path)
            return {
                'file_size': stat.st_size,
                'last_modified': datetime.fromtimestamp(stat.st_mtime),
                'file_type': os.path.splitext(file_path)[1].lower()
            }
        except Exception as e:
            print(f"Warning: Cannot get file info for {file_path}: {e}")
            return {
                'file_size': 0,
                'last_modified': datetime.now(),
                'file_type': os.path.splitext(file_path)[1].lower()
            }
    
    def process_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Process a single file and return its information"""
        content = self.read_file_content(file_path)
        
        if not content.strip():
            return None
        
        file_info = self.get_file_info(file_path)
        
        return {
            'file_path': file_path,
            'content': content,
            'file_type': file_info['file_type'],
            'file_size': file_info['file_size'],
            'last_modified': file_info['last_modified']
        }
    
    def process_all_files(self) -> List[Dict[str, Any]]:
        """Process all files in the target directory"""
        found_files = self.scan_directory()
        processed_files = []
        
        print(f"Found {len(found_files)} files to process")
        
        for file_path in tqdm(found_files, desc="Processing files"):
            result = self.process_file(file_path)
            if result:
                processed_files.append(result)
        
        return processed_files
    
    def get_file_stats(self) -> Dict[str, Any]:
        """Get statistics about files in the target directory"""
        found_files = self.scan_directory()
        
        stats = {
            'total_files': len(found_files),
            'file_types': {}
        }
        
        for file_path in found_files:
            file_ext = os.path.splitext(file_path)[1].lower()
            stats['file_types'][file_ext] = stats['file_types'].get(file_ext, 0) + 1
        
        return stats
    
    def get_files_by_type(self, file_type: str) -> List[str]:
        """Get all files of a specific type"""
        found_files = self.scan_directory()
        return [f for f in found_files if f.endswith(file_type)]
    
    def is_file_modified_since(self, file_path: str, since_datetime: datetime) -> bool:
        """Check if file was modified since given datetime"""
        try:
            stat = os.stat(file_path)
            file_mtime = datetime.fromtimestamp(stat.st_mtime)
            return file_mtime > since_datetime
        except Exception:
            return True  # Assume modified if we can't check