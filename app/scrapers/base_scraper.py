from abc import ABC, abstractmethod
from typing import List
import httpx
from loguru import logger
from ..models.proxy import Proxy

class BaseScraper(ABC):
    """Base class for all proxy scrapers"""
    
    name: str = "base_scraper"  # Should be overridden by subclasses
    
    @abstractmethod
    async def scrape(self) -> List[Proxy]:
        """
        Scrape proxies from the source
        
        Returns:
            List[Proxy]: List of proxy objects
        """
        pass
    
    async def make_request(self, url: str, headers=None, **kwargs) -> httpx.Response:
        """
        Make an HTTP request with error handling
        
        Args:
            url: URL to request
            headers: Optional request headers
            **kwargs: Additional parameters to pass to httpx.AsyncClient.get
            
        Returns:
            httpx.Response: Response object if successful
            
        Raises:
            Exception: If request fails
        """
        if headers is None:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
        try:
            timeout = httpx.Timeout(10.0)  # 10 seconds timeout
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=headers, **kwargs)
                response.raise_for_status()
                return response
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error while scraping {self.name}: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error while scraping {self.name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while scraping {self.name}: {e}")
            raise
    
    def log_result(self, proxies: List[Proxy]) -> None:
        """
        Log the result of scraping
        
        Args:
            proxies: List of scraped proxies
        """
        logger.info(f"Scraped {len(proxies)} proxies from {self.name}")
        