from typing import List
import json
import asyncio
from loguru import logger
from .base_scraper import BaseScraper
from ..models.proxy import Proxy, ProxyProtocol, ProxyStatus

class GeonodeScraper(BaseScraper):
    """Scraper for geonode.com free proxy API"""
    
    name = "geonode"
    base_url = "https://proxylist.geonode.com/api/proxy-list?limit=50&sort_by=lastChecked&sort_type=desc"
    
    async def scrape(self) -> List[Proxy]:
        """Scrape proxies from geonode.com API with pagination"""
        all_proxies = []
        current_page = 1
        total_pages = 1  # Inicialmente desconocido, lo actualizaremos con la primera respuesta
        
        try:
            while current_page <= total_pages:
                # Construir URL para la página actual
                url = f"{self.base_url}&page={current_page}"
                logger.info(f"Scraping Geonode page {current_page}/{total_pages}")
                
                response = await self.make_request(url)
                data = response.json()
                
                if "data" not in data:
                    logger.warning(f"Unexpected response format from {url}")
                    break
                
                # Extraer información de paginación
                if current_page == 1 and "total" in data and "limit" in data:
                    total_items = data.get("total", 0)
                    items_per_page = data.get("limit", 50)
                    total_pages = (total_items + items_per_page - 1) // items_per_page
                    logger.info(f"Found {total_items} proxies in {total_pages} pages")
                
                proxy_data = data["data"]
                page_proxies = []
                
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
                        
                        page_proxies.append(proxy)
                    except Exception as e:
                        logger.warning(f"Error parsing proxy item: {e}")
                        continue
                
                logger.info(f"Scraped {len(page_proxies)} proxies from page {current_page}")
                all_proxies.extend(page_proxies)
                
                # Si no hay más datos o llegamos a una página vacía, salimos del bucle
                if not proxy_data:
                    logger.info(f"No more data on page {current_page}, stopping")
                    break
                
                # Pasar a la siguiente página
                current_page += 1
                
                # Para evitar sobrecarga de solicitudes, añadimos un pequeño retraso
                await asyncio.sleep(1)
            
            logger.info(f"Total proxies scraped from Geonode: {len(all_proxies)}")
            self.log_result(all_proxies)
            return all_proxies
        
        except Exception as e:
            logger.error(f"Error scraping {self.name}: {e}")
            return all_proxies  # Devolver los proxies que hayamos conseguido hasta el error