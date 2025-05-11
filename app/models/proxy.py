from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator

class ProxyProtocol(str, Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"

class ProxyStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"

class ProxyValidationResult(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool
    latency_ms: Optional[int] = None
    error: Optional[str] = None
    blocked_by_google: bool = False

class Proxy(BaseModel):
    ip: str
    port: int
    protocol: ProxyProtocol = ProxyProtocol.HTTP
    country: Optional[str] = None
    city: Optional[str] = None
    anonymity: Optional[str] = None
    status: ProxyStatus = ProxyStatus.UNKNOWN
    score: int = 0  # 0-100
    last_checked: Optional[datetime] = None
    last_used: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    success_count: int = 0
    fail_count: int = 0
    validation_history: List[ProxyValidationResult] = []
    source: str = "manual"
    metadata: Dict = {}
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "ip": "192.168.1.1",
                "port": 8080,
                "protocol": "http",
                "country": "Spain",
                "anonymity": "high",
                "status": "active",
                "score": 85
            }
        }
    }
    
    @property
    def url(self) -> str:
        """Get proxy URL in format protocol://ip:port"""
        return f"{self.protocol}://{self.ip}:{self.port}"
    
    @validator('score')
    def score_range(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Score must be between 0 and 100')
        return v