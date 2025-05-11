from typing import List
from bs4 import BeautifulSoup
from loguru import logger
from .base_scraper import BaseScraper
from ..models.proxy import Proxy, ProxyProtocol, ProxyStatus

class FreeProxyListScraper(BaseScraper):
    """Scraper for free-proxy-list.net"""
    
    name = "free_proxy_list"
    url = "https://free-proxy-list.net/"
    
    async def scrape(self) -> List[Proxy]:
        """Scrape proxies from free-proxy-list.net"""
        proxies = []
        
        try:
            response = await self.make_request(self.url)
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find the table with proxies
            table = soup.find('table', {'id': 'proxylisttable'})
            if not table:
                logger.warning(f"No proxy table found on {self.url}")
                return []
            
            # Extract proxies from table rows
            tbody = table.find('tbody')
            rows = tbody.find_all('tr')
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 8:
                    try:
                        ip = cells[0].text.strip()
                        port = int(cells[1].text.strip())
                        country = cells[2].text.strip()
                        anonymity = cells[4].text.strip().lower()
                        https = cells[6].text.strip().lower() == 'yes'
                        
                        protocol = ProxyProtocol.HTTPS if https else ProxyProtocol.HTTP
                        
                        proxy = Proxy(
                            ip=ip,
                            port=port,
                            protocol=protocol,
                            country=country,
                            anonymity=anonymity,
                            status=ProxyStatus.UNKNOWN,
                            score=50,  # Default score until validated
                            source=self.name
                        )
                        
                        proxies.append(proxy)
                    except Exception as e:
                        logger.warning(f"Error parsing proxy row: {e}")
                        continue
            
            self.log_result(proxies)
            return proxies
        
        except Exception as e:
            logger.error(f"Error scraping {self.name}: {e}")
            return []