from typing import Dict, List, Type
import asyncio
from loguru import logger

from ..models.proxy import Proxy
from ..scrapers.base_scraper import BaseScraper
from ..scrapers.free_proxy_list_scraper import FreeProxyListScraper
from ..scrapers.geonode_scraper import GeonodeScraper
from .proxy_service import ProxyService

class ScraperService:
    """Service for managing proxy scrapers"""
    
    _scrapers: Dict[str, Type[BaseScraper]] = {
    "free_proxy_list": FreeProxyListScraper,
    "geonode": GeonodeScraper
    }
    
    @classmethod
    async def scrape_all(cls) -> int:
        """
        Scrape proxies from all registered sources
        
        Returns:
            int: Total number of proxies scraped and added to database
        """
        total_added = 0
        
        logger.info(f"Starting scraping from {len(cls._scrapers)} sources")
        
        for scraper_name, scraper_class in cls._scrapers.items():
            try:
                logger.info(f"Scraping from {scraper_name}")
                scraper = scraper_class()
                proxies = await scraper.scrape()
                
                if proxies:
                    # Add all the proxies to the database
                    added = await ProxyService.add_proxies(proxies)
                    total_added += added
                    logger.info(f"Added {added} proxies from {scraper_name}")
                else:
                    logger.warning(f"No proxies scraped from {scraper_name}")
                    
            except Exception as e:
                logger.error(f"Error scraping from {scraper_name}: {e}")
        
        logger.info(f"Scraping completed. Added {total_added} proxies in total")
        return total_added
    
    @classmethod
    async def scrape_source(cls, source_name: str) -> int:
        """
        Scrape proxies from a specific source
        
        Args:
            source_name: Name of the source to scrape
            
        Returns:
            int: Number of proxies added to database
            
        Raises:
            ValueError: If source is not found
        """
        if source_name not in cls._scrapers:
            logger.error(f"Source {source_name} not found")
            raise ValueError(f"Source {source_name} not found")
        
        try:
            scraper_class = cls._scrapers[source_name]
            scraper = scraper_class()
            
            logger.info(f"Scraping from {source_name}")
            proxies = await scraper.scrape()
            
            if proxies:
                # Add all the proxies to the database
                added = await ProxyService.add_proxies(proxies)
                logger.info(f"Added {added} proxies from {source_name}")
                return added
            else:
                logger.warning(f"No proxies scraped from {source_name}")
                return 0
                
        except Exception as e:
            logger.error(f"Error scraping from {source_name}: {e}")
            return 0
    
    @classmethod
    def register_scraper(cls, name: str, scraper_class: Type[BaseScraper]) -> None:
        """
        Register a new scraper
        
        Args:
            name: Name of the scraper
            scraper_class: Scraper class
        """
        cls._scrapers[name] = scraper_class
        logger.info(f"Registered scraper: {name}")