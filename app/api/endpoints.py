from fastapi import APIRouter, Depends, HTTPException, Header, Query
from typing import Dict, List, Optional
from ..models.proxy import Proxy, ProxyStatus
from ..services.proxy_service import ProxyService
from ..services.scraper_service import ScraperService
from ..validators.proxy_validator import ProxyValidator
from ..core.config import settings

router = APIRouter()

def verify_api_key(x_api_key: str = Header(...)):
    """Verify the API key from header"""
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

@router.get("/proxy", response_model=Proxy)
async def get_proxy(
    status: Optional[ProxyStatus] = Query(ProxyStatus.ACTIVE),
    min_score: int = Query(50, ge=0, le=100),
    api_key: str = Depends(verify_api_key)
):
    """Get a single valid proxy"""
    proxies = await ProxyService.get_proxies(status=status, min_score=min_score, limit=1)
    if not proxies:
        raise HTTPException(status_code=404, detail="No valid proxies found")
    return proxies[0]

@router.get("/proxies", response_model=List[Proxy])
async def get_proxies(
    status: Optional[ProxyStatus] = Query(ProxyStatus.ACTIVE),
    min_score: int = Query(50, ge=0, le=100),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(verify_api_key)
):
    """Get multiple proxies filtered by status and score"""
    proxies = await ProxyService.get_proxies(status=status, min_score=min_score, limit=limit)
    return proxies

@router.post("/proxy", response_model=bool)
async def add_proxy(
    proxy: Proxy,
    api_key: str = Depends(verify_api_key)
):
    """Add a new proxy to the database"""
    success = await ProxyService.add_proxy(proxy)
    return success

@router.post("/proxy/report", response_model=bool)
async def report_proxy_result(
    ip: str,
    port: int,
    success: bool,
    latency_ms: Optional[int] = None,
    error: Optional[str] = None,
    blocked_by_google: bool = False,
    api_key: str = Depends(verify_api_key)
):
    """Report the result of using a proxy"""
    success = await ProxyService.report_proxy_result(
        ip=ip,
        port=port,
        success=success,
        latency_ms=latency_ms,
        error=error,
        blocked_by_google=blocked_by_google
    )
    return success

# Scraping endpoints
@router.post("/scrape/all", response_model=int)
async def scrape_all_sources(api_key: str = Depends(verify_api_key)):
    """Scrape proxies from all registered sources"""
    total_added = await ScraperService.scrape_all()
    return total_added

@router.post("/scrape/{source_name}", response_model=int)
async def scrape_source(
    source_name: str,
    api_key: str = Depends(verify_api_key)
):
    """Scrape proxies from a specific source"""
    try:
        added = await ScraperService.scrape_source(source_name)
        return added
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Validation endpoints
@router.post("/validate/all", response_model=Dict[str, int])
async def validate_all_proxies(
    batch_size: int = Query(10, ge=1, le=50),
    api_key: str = Depends(verify_api_key)
):
    """Validate all proxies in the database"""
    results = await ProxyValidator.validate_all(batch_size=batch_size)
    return results

@router.post("/validate/{ip}/{port}", response_model=bool)
async def validate_proxy(
    ip: str,
    port: int,
    api_key: str = Depends(verify_api_key)
):
    """Validate a specific proxy"""
    # First get the proxy from the database
    proxies = await ProxyService.get_proxies(status=None, min_score=0, limit=1000)
    
    # Find the proxy with matching IP and port
    proxy = next((p for p in proxies if p.ip == ip and p.port == port), None)
    
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    
    # Validate the proxy
    result = await ProxyValidator.validate_and_update(proxy)
    return result