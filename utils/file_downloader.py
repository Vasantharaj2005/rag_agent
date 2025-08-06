
# utils/file_downloader.py
import aiohttp
import tempfile
import os
from typing import Optional
from urllib.parse import urlparse
import mimetypes
from loguru import logger

class FileDownloader:
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def download_from_url(self, url: str, target_dir: Optional[str] = None) -> str:
        """Download file from URL and return local file path"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            logger.info(f"Downloading file from: {url}")
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: Failed to download file")
                
                # Determine file extension
                file_extension = self._get_file_extension(url, response)
                
                # Create target file path
                if target_dir:
                    os.makedirs(target_dir, exist_ok=True)
                    target_file = tempfile.NamedTemporaryFile(
                        delete=False,
                        dir=target_dir,
                        suffix=file_extension
                    )
                else:
                    target_file = tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=file_extension
                    )
                
                # Download file in chunks
                total_size = 0
                async for chunk in response.content.iter_chunked(8192):
                    target_file.write(chunk)
                    total_size += len(chunk)
                
                target_file.close()
                
                logger.info(f"Downloaded {total_size} bytes to {target_file.name}")
                return target_file.name
                
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            raise
    
    def _get_file_extension(self, url: str, response) -> str:
        """Determine file extension from URL or content type"""
        # Try to get extension from URL
        parsed_url = urlparse(url)
        file_extension = os.path.splitext(parsed_url.path)[1]
        
        if file_extension:
            return file_extension
        
        # Try to get extension from content type
        content_type = response.headers.get('Content-Type', '').split(';')[0]
        extension = mimetypes.guess_extension(content_type)
        
        return extension or '.bin'
