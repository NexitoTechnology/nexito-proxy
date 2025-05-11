import asyncio
from datetime import datetime, timedelta
import requests
from loguru import logger
from typing import Dict, Optional, Tuple
import concurrent.futures

from ..models.proxy import Proxy, ProxyStatus
from ..services.proxy_service import ProxyService
from ..db.mongodb import proxy_collection

class ProxyValidator:
    """Validator for checking if proxies are working"""
    
    @staticmethod
    def _validate_proxy_sync(proxy_dict) -> Tuple[bool, Optional[int], Optional[str], bool]:
        """
        Synchronous validation function that can be run in a thread pool
        
        Args:
            proxy_dict: Dictionary with proxy information
            
        Returns:
            Tuple containing validation results
        """
        test_url = "https://httpbin.org/ip"
        
        ip = proxy_dict["ip"]
        port = proxy_dict["port"]
        protocol = proxy_dict["protocol"].lower()
        
        # Asegurar que el protocolo no tenga prefijos extraños
        if "." in protocol:
            protocol = protocol.split(".")[-1]
        
        proxies = {
            "http": f"{protocol}://{ip}:{port}",
            "https": f"{protocol}://{ip}:{port}"
        }
        
        try:
            start_time = datetime.utcnow()
            
            # Usar requests en lugar de httpx
            response = requests.get(test_url, proxies=proxies, timeout=15, verify=False)
            
            # Calcular latencia
            latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Verificar si la respuesta es válida
            if response.status_code == 200:
                try:
                    # Verificar si la respuesta es un JSON válido con una IP
                    json_data = response.json()
                    if 'origin' in json_data:
                        logger.debug(f"Proxy {ip}:{port} is working (latency: {latency_ms}ms)")
                        return True, latency_ms, None, False
                    else:
                        logger.debug(f"Proxy {ip}:{port} returned invalid response format")
                        return False, latency_ms, "Invalid response format", False
                except Exception as e:
                    logger.debug(f"Proxy {ip}:{port} returned invalid JSON: {e}")
                    return False, latency_ms, "Response is not valid JSON", False
            else:
                logger.debug(f"Proxy {ip}:{port} returned status code {response.status_code}")
                return False, latency_ms, f"Invalid status code: {response.status_code}", False
                
        except requests.exceptions.Timeout:
            logger.debug(f"Proxy {ip}:{port} timed out")
            return False, None, "Timeout", False
        except requests.exceptions.ProxyError as e:
            logger.debug(f"Proxy error for {ip}:{port}: {e}")
            return False, None, f"Proxy error: {str(e)}", False
        except Exception as e:
            logger.debug(f"Error validating proxy {ip}:{port}: {e}")
            return False, None, f"Error: {str(e)}", False
    
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
            - bool: Whether the proxy is blocked or not
        """
        # Convertir el proxy a un diccionario para pasarlo al executor
        proxy_dict = {
            "ip": proxy.ip,
            "port": proxy.port,
            "protocol": str(proxy.protocol)
        }
        
        # Ejecutar la validación en un thread pool para no bloquear asyncio
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor, 
                ProxyValidator._validate_proxy_sync, 
                proxy_dict
            )
            
        return result
    
    @classmethod
    async def validate_and_update(cls, proxy: Proxy) -> bool:
        """
        Validate a proxy and update its status in the database
        
        Args:
            proxy: Proxy to validate
            
        Returns:
            bool: True if validation was successful, False otherwise
        """
        success, latency_ms, error, blocked = await cls.validate_proxy(proxy)
        
        # Update proxy in database
        result = await ProxyService.report_proxy_result(
            ip=proxy.ip,
            port=proxy.port,
            success=success,
            latency_ms=latency_ms,
            error=error,
            blocked_by_google=blocked
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
        # Primero contamos el total de proxies
        total_count = await proxy_collection.count_documents({})
        
        logger.info(f"Found {total_count} proxies in database. Starting validation...")
        
        # Inicializar contadores
        results = {
            "total": total_count,
            "success": 0,
            "fail": 0,
            "blocked": 0,
            "deleted": 0
        }
        
        # Procesar todos los proxies en lotes
        batch_number = 0
        processed = 0
        
        # Usar cursor para evitar cargar todos los proxies en memoria
        cursor = proxy_collection.find({})
        
        # Procesamos en lotes para manejar grandes cantidades
        while True:
            batch = await cursor.to_list(length=batch_size)
            if not batch:
                break
                
            # Convertir documentos a objetos Proxy
            proxies = [Proxy(**proxy) for proxy in batch]
            
            # Validar lote concurrentemente
            tasks = [cls.validate_and_update(proxy) for proxy in proxies]
            await asyncio.gather(*tasks)
            
            # Actualizar contador
            processed += len(batch)
            batch_number += 1
            
            # Registrar progreso cada 10 lotes o en el último lote
            if batch_number % 10 == 0 or len(batch) < batch_size:
                logger.info(f"Validated {processed}/{total_count} proxies")
        
        # Eliminar proxies que han fallado múltiples veces y no han funcionado
        # en los últimos 3 días
        three_days_ago = datetime.utcnow() - timedelta(days=3)
        
        delete_result = await proxy_collection.delete_many({
            "status": "inactive",
            "fail_count": {"$gt": 3},
            "last_checked": {"$lt": three_days_ago}
        })
        
        results["deleted"] = delete_result.deleted_count
        logger.info(f"Deleted {results['deleted']} inactive proxies that failed multiple times")
        
        # Obtener estadísticas actualizadas
        active_count = await proxy_collection.count_documents({"status": "active"})
        inactive_count = await proxy_collection.count_documents({"status": "inactive"})
        blocked_count = await proxy_collection.count_documents({"status": "blocked"})
        
        results["success"] = active_count
        results["fail"] = inactive_count
        results["blocked"] = blocked_count
        
        logger.info(f"Validation completed: {results['success']} working, {results['fail']} failed, {results['blocked']} blocked, {results['deleted']} deleted")
        
        return results
    
    @classmethod
    async def cleanup_invalid_proxies(cls) -> int:
        """
        Remove proxies that consistently fail validation
        
        Returns:
            int: Number of proxies removed
        """
        # Eliminar proxies que han fallado más de 5 veces y tienen puntuación baja
        result = await proxy_collection.delete_many({
            "status": "inactive",
            "fail_count": {"$gt": 5},
            "score": {"$lt": 20}
        })
        
        logger.info(f"Cleanup removed {result.deleted_count} consistently failing proxies")
        return result.deleted_count