from typing import List
import json
from loguru import logger
from .base_scraper import BaseScraper
from ..models.proxy import Proxy, ProxyProtocol, ProxyStatus

class GeonodeScraper(BaseScraper):
    """Scraper for geonode.com free proxy API"""
    
    name = "geonode"
    url = "https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=lastChecked&sort_type=desc"
    
    async def scrape(self) -> List[Proxy]:
        """Scrape proxies from geonode.com API"""
        proxies = []
        
        try:
            response = await self.make_request(self.url)
            data = response.json()
            
            if "data" not in data:
                logger.warning(f"Unexpected response format from {self.url}")
                return []
            
            proxy_data = data["data"]
            
            for item in proxy_data:
                try:
                    ip = item.get("ip")
                    port = int(item.get("port"))
                    country = item.get("country")
                    city = item.get("city", None)
                    protocols = item.get("protocols", [])
                    anonymity = item.get("anonymityLevel", "").lower()
                    
                    # Use the first supported protocol, defaulting to HTTP
                    protocol = ProxyProtocol.HTTP
                    if "socks5" in protocols:
                        protocol = ProxyProtocol.SOCKS5
                    elif "socks4" in protocols:
                        protocol = ProxyProtocol.SOCKS4
                    elif "https" in protocols:
                        protocol = ProxyProtocol.HTTPS
                    
                    proxy = Proxy(
                        ip=ip,
                        port=port,
                        protocol=protocol,
                        country=country,
                        city=city,
                        anonymity=anonymity,
                        status=ProxyStatus.UNKNOWN,
                        score=50,  # Default score until validated
                        source=self.name
                    )
                    
                    proxies.append(proxy)
                except Exception as e:
                    logger.warning(f"Error parsing proxy item: {e}")
                    continue
            
            self.log_result(proxies)
            return proxies
        
        except Exception as e:
            logger.error(f"Error scraping {self.name}: {e}")
            return []