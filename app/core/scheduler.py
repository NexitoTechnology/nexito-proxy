import asyncio
import time
from datetime import datetime
from loguru import logger

from .config import settings
from ..services.scraper_service import ScraperService
from ..validators.proxy_validator import ProxyValidator

class Scheduler:
    """Task scheduler for periodic jobs"""
    
    @staticmethod
    async def scrape_job():
        """Periodic job to scrape proxies"""
        logger.info("Starting scheduled scraping job")
        await ScraperService.scrape_all()
    
    @staticmethod
    async def validate_job():
        """Periodic job to validate proxies"""
        logger.info("Starting scheduled validation job")
        await ProxyValidator.validate_all()
    
    @classmethod
    async def start(cls):
        """Start the scheduler"""
        logger.info("Starting scheduler")
        
        while True:
            try:
                # Run scraping job
                await cls.scrape_job()
                
                # Run validation job
                await cls.validate_job()
                
                # Sleep until next run
                logger.info(f"Sleeping for {settings.SCRAPING_INTERVAL} seconds until next job")
                await asyncio.sleep(settings.SCRAPING_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                # Sleep for a while before retrying
                await asyncio.sleep(60)