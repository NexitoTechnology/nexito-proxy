from datetime import datetime
from typing import List, Optional
import pymongo
from loguru import logger
from ..db.mongodb import proxy_collection
from ..models.proxy import Proxy, ProxyStatus, ProxyValidationResult

class ProxyService:
    @staticmethod
    async def get_proxies(
        status: Optional[ProxyStatus] = ProxyStatus.ACTIVE,
        min_score: int = 50,
        limit: int = 10
    ) -> List[Proxy]:
        """Get proxies filtered by status and minimum score"""
        query = {}
        
        if status:
            query["status"] = status
            
        if min_score > 0:
            query["score"] = {"$gte": min_score}
            
        cursor = proxy_collection.find(query).sort("score", pymongo.DESCENDING).limit(limit)
        proxies = await cursor.to_list(length=limit)
        
        return [Proxy(**proxy) for proxy in proxies]
    
    @staticmethod
    async def add_proxy(proxy: Proxy) -> bool:
        """Add a new proxy to the database"""
        try:
            proxy_dict = proxy.dict()
            
            # Use update_one with upsert to avoid duplicates
            result = await proxy_collection.update_one(
                {"ip": proxy.ip, "port": proxy.port},
                {"$set": proxy_dict},
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"Added new proxy: {proxy.ip}:{proxy.port}")
            else:
                logger.debug(f"Updated existing proxy: {proxy.ip}:{proxy.port}")
                
            return True
        except Exception as e:
            logger.error(f"Error adding proxy {proxy.ip}:{proxy.port}: {e}")
            return False
    
    @staticmethod
    async def add_proxies(proxies: List[Proxy]) -> int:
        """Add multiple proxies to the database"""
        success_count = 0
        
        for proxy in proxies:
            if await ProxyService.add_proxy(proxy):
                success_count += 1
                
        return success_count
    
    @staticmethod
    async def report_proxy_result(
        ip: str, 
        port: int, 
        success: bool, 
        latency_ms: Optional[int] = None,
        error: Optional[str] = None,
        blocked_by_google: bool = False
    ) -> bool:
        """Report proxy success/failure and update its stats"""
        try:
            # Create validation result
            validation_result = ProxyValidationResult(
                timestamp=datetime.utcnow(),
                success=success,
                latency_ms=latency_ms,
                error=error,
                blocked_by_google=blocked_by_google
            )
            
            # Increment success or fail count
            increment_field = "success_count" if success else "fail_count"
            
            # Calculate new status
            new_status = ProxyStatus.ACTIVE if success else ProxyStatus.INACTIVE
            if blocked_by_google:
                new_status = ProxyStatus.BLOCKED
            
            # Calculate new score
            proxy = await proxy_collection.find_one({"ip": ip, "port": port})
            new_score = 50  # Default score
            
            if proxy:
                success_count = proxy.get("success_count", 0) + (1 if success else 0)
                fail_count = proxy.get("fail_count", 0) + (0 if success else 1)
                total = success_count + fail_count
                
                if total > 0:
                    # Base score on success ratio
                    success_ratio = success_count / total
                    new_score = int(success_ratio * 100)
                    
                    # Adjust for latency if available
                    if latency_ms is not None and success:
                        latency_factor = max(0, min(1, (2000 - latency_ms) / 2000))
                        new_score = int(new_score * 0.7 + latency_factor * 100 * 0.3)
            
            # Update proxy in database
            result = await proxy_collection.update_one(
                {"ip": ip, "port": port},
                {
                    "$set": {
                        "status": new_status,
                        "score": new_score,
                        "last_checked": datetime.utcnow()
                    },
                    "$inc": {increment_field: 1},
                    "$push": {
                        "validation_history": {
                            "$each": [validation_result.dict()],
                            "$slice": -20  # Keep only the last 20 results
                        }
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.debug(f"Updated proxy status: {ip}:{port} -> {new_status}")
                return True
            else:
                logger.warning(f"Failed to update proxy: {ip}:{port}")
                return False
                
        except Exception as e:
            logger.error(f"Error reporting proxy result for {ip}:{port}: {e}")
            return False