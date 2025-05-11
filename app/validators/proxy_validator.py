import asyncio
from datetime import datetime
import httpx
from loguru import logger
from typing import Dict, Optional, Tuple

from ..models.proxy import Proxy, ProxyStatus
from ..services.proxy_service import ProxyService

class ProxyValidator:
    """Validator for checking if proxies are working"""
    
    @staticmethod
    async def validate_proxy(proxy: Proxy) -> Tuple[bool, Optional[int], Optional[str], bool]:
        """
        Validate if a proxy is working
        
        Args:
            proxy: Proxy to validate
            
        Returns:
            Tuple containing:
            - bool: Success (True if proxy works)
            - Optional[int]: Latency in milliseconds (None if proxy doesn't work)
            - Optional[str]: Error message (None if proxy works)
            - bool: Whether the proxy is blocked by Google
        """
        test_url = "https://www.google.com"
        
        # Setup proxy configuration for httpx
        proxy_url = f"{proxy.protocol}://{proxy.ip}:{proxy.port}"
        proxies = {
            "http://": proxy_url,
            "https://": proxy_url
        }
        
        # Use a short timeout
        timeout = httpx.Timeout(5.0)
        
        try:
            start_time = datetime.utcnow()
            
            async with httpx.AsyncClient(proxies=proxies, timeout=timeout, follow_redirects=True) as client:
                response = await client.get(test_url)
                
                # Calculate latency
                latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                # Check if the response is valid
                if response.status_code == 200:
                    # Check if Google is blocking the proxy (showing CAPTCHA or error page)
                    if "Our systems have detected unusual traffic" in response.text or \
                       "unusual traffic from your computer network" in response.text or \
                       "captcha" in response.text.lower():
                        logger.debug(f"Proxy {proxy.ip}:{proxy.port} is blocked by Google")
                        return False, latency_ms, "Blocked by Google", True
                    
                    logger.debug(f"Proxy {proxy.ip}:{proxy.port} is working (latency: {latency_ms}ms)")
                    return True, latency_ms, None, False
                else:
                    logger.debug(f"Proxy {proxy.ip}:{proxy.port} returned status code {response.status_code}")
                    return False, latency_ms, f"Invalid status code: {response.status_code}", False
                    
        except httpx.TimeoutException:
            logger.debug(f"Proxy {proxy.ip}:{proxy.port} timed out")
            return False, None, "Timeout", False
        except httpx.ProxyError as e:
            logger.debug(f"Proxy error for {proxy.ip}:{proxy.port}: {e}")
            return False, None, f"Proxy error: {str(e)}", False
        except Exception as e:
            logger.debug(f"Error validating proxy {proxy.ip}:{proxy.port}: {e}")
            return False, None, f"Error: {str(e)}", False
    
    @classmethod
    async def validate_and_update(cls, proxy: Proxy) -> bool:
        """
        Validate a proxy and update its status in the database
        
        Args:
            proxy: Proxy to validate
            
        Returns:
            bool: True if validation was successful, False otherwise
        """
        success, latency_ms, error, blocked_by_google = await cls.validate_proxy(proxy)
        
        # Update proxy in database
        result = await ProxyService.report_proxy_result(
            ip=proxy.ip,
            port=proxy.port,
            success=success,
            latency_ms=latency_ms,
            error=error,
            blocked_by_google=blocked_by_google
        )
        
        return result
    
    @classmethod
    async def validate_all(cls, batch_size: int = 10) -> Dict[str, int]:
        """
        Validate all proxies in the database
        
        Args:
            batch_size: Number of proxies to validate concurrently
            
        Returns:
            Dict containing counts of validation results
        """
        # Get all proxies
        proxies = await ProxyService.get_proxies(status=None, min_score=0, limit=1000)
        
        logger.info(f"Starting validation of {len(proxies)} proxies")
        
        # Initialize counters
        results = {
            "total": len(proxies),
            "success": 0,
            "fail": 0,
            "blocked": 0
        }
        
        # Process proxies in batches
        for i in range(0, len(proxies), batch_size):
            batch = proxies[i:i+batch_size]
            
            # Validate batch concurrently
            tasks = [cls.validate_and_update(proxy) for proxy in batch]
            await asyncio.gather(*tasks)
            
            # Log progress
            logger.info(f"Validated {i + len(batch)}/{len(proxies)} proxies")
        
        # Get updated statistics
        active_proxies = await ProxyService.get_proxies(status=ProxyStatus.ACTIVE, min_score=0, limit=1000)
        inactive_proxies = await ProxyService.get_proxies(status=ProxyStatus.INACTIVE, min_score=0, limit=1000)
        blocked_proxies = await ProxyService.get_proxies(status=ProxyStatus.BLOCKED, min_score=0, limit=1000)
        
        results["success"] = len(active_proxies)
        results["fail"] = len(inactive_proxies)
        results["blocked"] = len(blocked_proxies)
        
        logger.info(f"Validation completed: {results['success']} working, {results['fail']} failed, {results['blocked']} blocked")
        
        return results