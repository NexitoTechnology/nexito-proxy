# Manual de Usuario: Proxy Service API

## 1. Introducción

El Proxy Service es una API completa para la gestión automatizada de proxies en operaciones de web scraping a gran escala. Este manual explica cada funcionalidad del sistema y proporciona instrucciones paso a paso para su utilización.

## 2. Requisitos de Instalación

### 2.1. Requisitos Previos

Para instalar y ejecutar el Proxy Service se necesita:

- Python 3.10 o superior
- MongoDB 4.0 o superior
- Entorno virtual de Python (recomendado)
- Docker (opcional, para MongoDB)

### 2.2. Proceso de Instalación

1. **Clonar el repositorio**

```bash
git clone https://github.com/tu-usuario/proxy-service.git
cd proxy-service
```

2. **Configurar entorno virtual**

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate
```

3. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

4. **Configurar MongoDB**

Si no tienes MongoDB instalado, puedes usar Docker:

```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

5. **Configurar variables de entorno**

Crea un archivo `.env` en la raíz del proyecto con:

```
# API Settings
API_KEY=tu_clave_secreta_aqui

# MongoDB Settings
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=proxy_service

# Scheduler Settings (en segundos)
SCRAPING_INTERVAL=21600  # 6 horas
PROXY_VALIDATION_INTERVAL=3600  # 1 hora
```

6. **Iniciar el servicio**

```bash
uvicorn app.main:app --reload
```

El servicio estará disponible en: http://127.0.0.1:8000
Documentación Swagger UI: http://127.0.0.1:8000/docs

## 3. Descubrimiento Automático de Proxies

### 3.1. ¿Qué hace?

Esta funcionalidad rastrea automáticamente fuentes públicas para encontrar nuevos proxies, los normaliza y almacena en la base de datos.

### 3.2. Cómo utilizarla

#### 3.2.1. Iniciar scraping de todas las fuentes

**Opción 1: Mediante API**

```bash
curl -X POST "http://localhost:8000/api/scrape/all" \
     -H "x-api-key: tu_clave_secreta_aqui" \
     -H "accept: application/json"
```

**Opción 2: Automáticamente**

El scraping se ejecuta automáticamente según el intervalo definido en `SCRAPING_INTERVAL`.

#### 3.2.2. Iniciar scraping de una fuente específica

```bash
curl -X POST "http://localhost:8000/api/scrape/geonode" \
     -H "x-api-key: tu_clave_secreta_aqui" \
     -H "accept: application/json"
```

#### 3.2.3. Añadir una nueva fuente de proxies

1. Crea un nuevo archivo en `app/scrapers/`, por ejemplo `mi_fuente_scraper.py`
2. Implementa una clase que herede de `BaseScraper`
3. Implementa el método `scrape()` para obtener proxies de la fuente
4. Registra el nuevo scraper en `app/services/scraper_service.py`

Ejemplo de implementación:

```python
# 1. Crea el archivo app/scrapers/mi_fuente_scraper.py
from typing import List
from .base_scraper import BaseScraper
from ..models.proxy import Proxy, ProxyProtocol, ProxyStatus

class MiFuenteScraper(BaseScraper):
    """Scraper para mi-fuente.com"""
    
    name = "mi_fuente"
    url = "https://mi-fuente.com/proxies"
    
    async def scrape(self) -> List[Proxy]:
        # Implementa la lógica específica para extraer proxies
        # ...
        return proxies

# 2. Registra el scraper en app/services/scraper_service.py
from ..scrapers.mi_fuente_scraper import MiFuenteScraper

class ScraperService:
    _scrapers: Dict[str, Type[BaseScraper]] = {
        "free_proxy_list": FreeProxyListScraper,
        "geonode": GeonodeScraper,
        "mi_fuente": MiFuenteScraper  # Añade aquí tu nuevo scraper
    }
```

## 4. Sistema de Validación Inteligente

### 4.1. ¿Qué hace?

Verifica el funcionamiento real de cada proxy mediante pruebas contra Google, detecta bloqueos y mide la latencia para garantizar calidad.

### 4.2. Cómo utilizarla

#### 4.2.1. Validar todos los proxies

**Opción 1: Mediante API**

```bash
curl -X POST "http://localhost:8000/api/validate/all?batch_size=20" \
     -H "x-api-key: tu_clave_secreta_aqui" \
     -H "accept: application/json"
```

El parámetro `batch_size` determina cuántos proxies se validarán concurrentemente.

**Opción 2: Automáticamente**

La validación se ejecuta automáticamente según el intervalo definido en `PROXY_VALIDATION_INTERVAL`.

#### 4.2.2. Validar un proxy específico

```bash
curl -X POST "http://localhost:8000/api/validate/192.168.1.1/8080" \
     -H "x-api-key: tu_clave_secreta_aqui" \
     -H "accept: application/json"
```

#### 4.2.3. Personalizar criterios de validación

Para modificar el comportamiento del validador, edita el archivo `app/validators/proxy_validator.py`:

1. Ajusta el timeout para pruebas modificando `timeout = httpx.Timeout(5.0)`
2. Cambia la URL de prueba modificando `test_url = "https://www.google.com"`
3. Personaliza las condiciones de detección de bloqueo en la sección:

```python
# Verificación de bloqueo por Google
if "Our systems have detected unusual traffic" in response.text or \
   "unusual traffic from your computer network" in response.text or \
   "captcha" in response.text.lower():
    # Añade tus propias condiciones aquí
```

## 5. Sistema de Puntuación Sofisticado

### 5.1. ¿Qué hace?

Asigna una puntuación de 0-100 a cada proxy basándose en su rendimiento, tasa de éxito y latencia.

### 5.2. Cómo utilizarla y personalizarla

#### 5.2.1. Cómo se calcula la puntuación

La puntuación se calcula automáticamente en el método `report_proxy_result()` del `ProxyService`.

La fórmula actual es:
1. Puntuación base = (éxitos / (éxitos + fallos)) * 100
2. Ajuste por latencia = Si hay latencia, la puntuación se ajusta con: 
   `puntuación final = puntuación base * 0.7 + factor de latencia * 0.3`

#### 5.2.2. Personalizar el algoritmo de puntuación

Para modificar cómo se calculan las puntuaciones, edita la sección correspondiente en `app/services/proxy_service.py`:

```python
# Encuentra esta sección en report_proxy_result()
if total > 0:
    # Puntuación basada en ratio de éxito
    success_ratio = success_count / total
    new_score = int(success_ratio * 100)
    
    # Ajustar por latencia si está disponible
    if latency_ms is not None and success:
        # Modifica esta fórmula según tus necesidades
        latency_factor = max(0, min(1, (2000 - latency_ms) / 2000))
        new_score = int(new_score * 0.7 + latency_factor * 100 * 0.3)
```

#### 5.2.3. Filtrar proxies por puntuación mínima

Al solicitar proxies, puedes especificar una puntuación mínima:

```bash
curl -X GET "http://localhost:8000/api/proxies?min_score=75" \
     -H "x-api-key: tu_clave_secreta_aqui" \
     -H "accept: application/json"
```

## 6. API REST Completa

### 6.1. Obtener Proxies

#### 6.1.1. Obtener un único proxy

**Endpoint:** `GET /api/proxy`

```bash
curl -X GET "http://localhost:8000/api/proxy?status=active&min_score=70" \
     -H "x-api-key: tu_clave_secreta_aqui" \
     -H "accept: application/json"
```

**Parámetros:**
- `status`: Filtrar por estado (`active`, `inactive`, `blocked`, `unknown`)
- `min_score`: Puntuación mínima (0-100)

#### 6.1.2. Obtener múltiples proxies

**Endpoint:** `GET /api/proxies`

```bash
curl -X GET "http://localhost:8000/api/proxies?status=active&min_score=50&limit=20" \
     -H "x-api-key: tu_clave_secreta_aqui" \
     -H "accept: application/json"
```

**Parámetros:**
- `status`: Filtrar por estado
- `min_score`: Puntuación mínima
- `limit`: Número máximo de proxies a retornar (1-100)

### 6.2. Añadir y Reportar Proxies

#### 6.2.1. Añadir un proxy manualmente

**Endpoint:** `POST /api/proxy`

```bash
curl -X POST "http://localhost:8000/api/proxy" \
     -H "x-api-key: tu_clave_secreta_aqui" \
     -H "Content-Type: application/json" \
     -d '{
           "ip": "192.168.1.1",
           "port": 8080,
           "protocol": "http",
           "country": "Spain",
           "anonymity": "high"
         }'
```

#### 6.2.2. Reportar resultado de uso de un proxy

**Endpoint:** `POST /api/proxy/report`

```bash
curl -X POST "http://localhost:8000/api/proxy/report?ip=192.168.1.1&port=8080&success=true&latency_ms=350" \
     -H "x-api-key: tu_clave_secreta_aqui" \
     -H "accept: application/json"
```

**Parámetros:**
- `ip`: Dirección IP del proxy
- `port`: Puerto del proxy
- `success`: Si funcionó correctamente (true/false)
- `latency_ms`: Latencia en milisegundos (opcional)
- `error`: Mensaje de error (opcional)
- `blocked_by_google`: Si fue bloqueado por Google (true/false, opcional)

## 7. Programación Automática de Tareas

### 7.1. ¿Qué hace?

Ejecuta automáticamente tareas de scraping y validación en segundo plano según intervalos configurables.

### 7.2. Cómo configurar y personalizar

#### 7.2.1. Configurar intervalos de tareas

Modifica las variables en el archivo `.env`:

```
SCRAPING_INTERVAL=21600  # Intervalo de scraping en segundos (6 horas)
PROXY_VALIDATION_INTERVAL=3600  # Intervalo de validación en segundos (1 hora)
```

#### 7.2.2. Personalizar comportamiento del scheduler

Edita el archivo `app/core/scheduler.py` para modificar el comportamiento:

1. Añadir nuevas tareas programadas:

```python
@staticmethod
async def mi_nueva_tarea():
    """Nueva tarea programada"""
    logger.info("Iniciando mi nueva tarea programada")
    # Implementa tu lógica aquí
    
@classmethod
async def start(cls):
    """Iniciar el scheduler"""
    logger.info("Iniciando scheduler")
    
    while True:
        try:
            # Ejecutar tareas existentes
            await cls.scrape_job()
            await cls.validate_job()
            
            # Ejecutar nueva tarea
            await cls.mi_nueva_tarea()
            
            # Dormir hasta la próxima ejecución
            await asyncio.sleep(settings.SCRAPING_INTERVAL)
            
        except Exception as e:
            logger.error(f"Error en scheduler: {e}")
            await asyncio.sleep(60)
```

2. Modificar secuencia de ejecución:

Para ejecutar tareas en diferentes intervalos, puedes usar contadores:

```python
job_counter = 0

@classmethod
async def start(cls):
    """Iniciar el scheduler con diferentes intervalos"""
    logger.info("Iniciando scheduler")
    job_counter = 0
    
    while True:
        try:
            # Ejecutar scraping cada 6 ciclos (6 horas)
            if job_counter % 6 == 0:
                await cls.scrape_job()
            
            # Ejecutar validación en cada ciclo (1 hora)
            await cls.validate_job()
            
            # Incrementar contador
            job_counter += 1
            
            # Dormir 1 hora
            await asyncio.sleep(3600)
            
        except Exception as e:
            logger.error(f"Error en scheduler: {e}")
            await asyncio.sleep(60)
```

## 8. Sistema de Rotación de Proxies

### 8.1. ¿Qué hace?

Proporciona diferentes proxies en cada solicitud, priorizando aquellos con mejor puntuación para optimizar el rendimiento y evitar bloqueos.

### 8.2. Cómo utilizarlo efectivamente

#### 8.2.1. Implementar rotación básica desde el cliente

```python
import requests
import random

class ProxyRotator:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key
        self.proxies = []
        self.refresh_proxies()
    
    def refresh_proxies(self):
        """Obtener nuevos proxies de la API"""
        response = requests.get(
            f"{self.api_url}/api/proxies?min_score=70&limit=20",
            headers={"x-api-key": self.api_key}
        )
        self.proxies = response.json()
    
    def get_proxy(self):
        """Obtener un proxy aleatorio del pool"""
        if not self.proxies:
            self.refresh_proxies()
        if not self.proxies:
            return None
        
        proxy = random.choice(self.proxies)
        proxy_url = f"{proxy['protocol']}://{proxy['ip']}:{proxy['port']}"
        return {
            "http": proxy_url,
            "https": proxy_url,
            "proxy_info": proxy  # Para reportar resultados
        }
    
    def report_result(self, proxy_info, success, latency_ms=None, error=None):
        """Reportar resultado de uso"""
        if not proxy_info:
            return
        
        requests.post(
            f"{self.api_url}/api/proxy/report",
            params={
                "ip": proxy_info["ip"],
                "port": proxy_info["port"],
                "success": success,
                "latency_ms": latency_ms,
                "error": error
            },
            headers={"x-api-key": self.api_key}
        )

# Ejemplo de uso
rotator = ProxyRotator("http://localhost:8000", "tu_clave_secreta_aqui")

def hacer_peticion(url):
    max_intentos = 3
    for intento in range(max_intentos):
        proxy_data = rotator.get_proxy()
        if not proxy_data:
            print("No hay proxies disponibles")
            return None
        
        proxies = {
            "http": proxy_data["http"],
            "https": proxy_data["https"]
        }
        proxy_info = proxy_data["proxy_info"]
        
        try:
            inicio = time.time()
            response = requests.get(url, proxies=proxies, timeout=10)
            latencia = int((time.time() - inicio) * 1000)
            
            # Reportar éxito
            rotator.report_result(proxy_info, True, latencia)
            return response
            
        except Exception as e:
            # Reportar error
            rotator.report_result(proxy_info, False, error=str(e))
            print(f"Error con proxy {proxy_info['ip']}: {e}")
    
    return None
```

#### 8.2.2. Implementar estrategias avanzadas de rotación

Para casos de uso más complejos, puedes implementar diferentes estrategias:

1. **Rotación por país:**

```python
def get_proxy_by_country(self, country_code):
    """Obtener proxy de un país específico"""
    country_proxies = [p for p in self.proxies if p.get("country_code") == country_code]
    if not country_proxies:
        return self.get_proxy()  # Fallback a proxy aleatorio
    return random.choice(country_proxies)
```

2. **Rotación con blacklisting temporal:**

```python
def get_proxy_with_blacklist(self, blacklist_duration=30):
    """Evitar reutilizar proxies durante un tiempo"""
    now = time.time()
    available_proxies = [p for p in self.proxies if 
                        p.get("last_used", 0) + blacklist_duration < now]
    
    if not available_proxies:
        self.refresh_proxies()
        return self.get_proxy_with_blacklist(blacklist_duration)
    
    proxy = random.choice(available_proxies)
    proxy["last_used"] = now
    return proxy
```

## 9. Integración con Sistemas de Scraping

### 9.1. Integración con Requests

```python
import requests
import time

class ProxyScraperRequests:
    def __init__(self, proxy_api_url, proxy_api_key):
        self.proxy_api_url = proxy_api_url
        self.proxy_api_key = proxy_api_key
    
    def get_proxy(self):
        response = requests.get(
            f"{self.proxy_api_url}/api/proxy",
            headers={"x-api-key": self.proxy_api_key}
        )
        return response.json()
    
    def scrape(self, url):
        proxy = self.get_proxy()
        proxy_url = f"{proxy['protocol']}://{proxy['ip']}:{proxy['port']}"
        
        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
        
        start_time = time.time()
        success = False
        error = None
        
        try:
            response = requests.get(url, proxies=proxies, timeout=10)
            success = response.status_code == 200
            return response.text
        except Exception as e:
            error = str(e)
            raise
        finally:
            # Reportar resultado
            latency_ms = int((time.time() - start_time) * 1000) if success else None
            requests.post(
                f"{self.proxy_api_url}/api/proxy/report",
                params={
                    "ip": proxy["ip"],
                    "port": proxy["port"],
                    "success": success,
                    "latency_ms": latency_ms,
                    "error": error
                },
                headers={"x-api-key": self.proxy_api_key}
            )
```

### 9.2. Integración con Scrapy

```python
# middleware.py
import requests
import json
import logging
from scrapy.exceptions import NotConfigured

class ProxyServiceMiddleware:
    def __init__(self, proxy_api_url, proxy_api_key):
        self.proxy_api_url = proxy_api_url
        self.proxy_api_key = proxy_api_key
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.get('PROXY_SERVICE_ENABLED'):
            raise NotConfigured
        
        return cls(
            proxy_api_url=crawler.settings.get('PROXY_SERVICE_URL'),
            proxy_api_key=crawler.settings.get('PROXY_SERVICE_KEY')
        )
    
    def get_proxy(self):
        try:
            response = requests.get(
                f"{self.proxy_api_url}/api/proxy",
                headers={"x-api-key": self.proxy_api_key},
                timeout=5
            )
            return response.json()
        except Exception as e:
            self.logger.error(f"Error obteniendo proxy: {e}")
            return None
    
    def process_request(self, request, spider):
        proxy = self.get_proxy()
        if not proxy:
            return
        
        request.meta['proxy'] = f"{proxy['protocol']}://{proxy['ip']}:{proxy['port']}"
        request.meta['proxy_service_data'] = proxy
        self.logger.debug(f"Usando proxy: {request.meta['proxy']}")
    
    def process_response(self, request, response, spider):
        self._report_result(request, True, response.status)
        return response
    
    def process_exception(self, request, exception, spider):
        self._report_result(request, False, error=str(exception))
        return None
    
    def _report_result(self, request, success, status_code=None, error=None):
        proxy_data = request.meta.get('proxy_service_data')
        if not proxy_data:
            return
        
        try:
            requests.post(
                f"{self.proxy_api_url}/api/proxy/report",
                params={
                    "ip": proxy_data["ip"],
                    "port": proxy_data["port"],
                    "success": success,
                    "error": error
                },
                headers={"x-api-key": self.proxy_api_key},
                timeout=5
            )
        except Exception as e:
            self.logger.error(f"Error reportando resultado: {e}")

# En settings.py
PROXY_SERVICE_ENABLED = True
PROXY_SERVICE_URL = 'http://localhost:8000'
PROXY_SERVICE_KEY = 'tu_clave_secreta_aqui'

DOWNLOADER_MIDDLEWARES = {
   'myproject.middlewares.ProxyServiceMiddleware': 350,
}
```

### 9.3. Integración con Selenium

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import time

class SeleniumProxyManager:
    def __init__(self, proxy_api_url, proxy_api_key):
        self.proxy_api_url = proxy_api_url
        self.proxy_api_key = proxy_api_key
    
    def get_proxy(self):
        response = requests.get(
            f"{self.proxy_api_url}/api/proxy",
            headers={"x-api-key": self.proxy_api_key}
        )
        return response.json()
    
    def get_driver_with_proxy(self):
        proxy = self.get_proxy()
        
        chrome_options = Options()
        chrome_options.add_argument(f'--proxy-server={proxy["ip"]}:{proxy["port"]}')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.proxy_data = proxy  # Guardar para reportar después
        
        return driver
    
    def report_result(self, driver, success, error=None):
        proxy_data = getattr(driver, 'proxy_data', None)
        if not proxy_data:
            return
        
        requests.post(
            f"{self.proxy_api_url}/api/proxy/report",
            params={
                "ip": proxy_data["ip"],
                "port": proxy_data["port"],
                "success": success,
                "error": error
            },
            headers={"x-api-key": self.proxy_api_key}
        )

# Ejemplo de uso
proxy_manager = SeleniumProxyManager("http://localhost:8000", "tu_clave_secreta_aqui")

def scrape_with_selenium(url):
    driver = proxy_manager.get_driver_with_proxy()
    success = False
    
    try:
        driver.get(url)
        # Realizar operaciones de scraping...
        success = True
        return driver.page_source
    except Exception as e:
        proxy_manager.report_result(driver, False, str(e))
        raise
    finally:
        if success:
            proxy_manager.report_result(driver, True)
        driver.quit()
```

## 10. Monitoreo y Mantenimiento

### 10.1. Revisar Logs

Los logs del sistema se guardan en `logs/proxy_service.log` y contienen información detallada sobre operaciones y errores.

Para monitorear los logs en tiempo real:

```bash
tail -f logs/proxy_service.log
```

### 10.2. Estadísticas de Proxies

Para obtener estadísticas rápidas sobre el estado de los proxies, puedes crear un endpoint adicional:

```python
@router.get("/stats")
async def get_stats(api_key: str = Depends(verify_api_key)):
    """Obtener estadísticas de proxies"""
    total = await proxy_collection.count_documents({})
    active = await proxy_collection.count_documents({"status": "active"})
    inactive = await proxy_collection.count_documents({"status": "inactive"})
    blocked = await proxy_collection.count_documents({"status": "blocked"})
    unknown = await proxy_collection.count_documents({"status": "unknown"})
    
    high_quality = await proxy_collection.count_documents({"score": {"$gte": 80}})
    medium_quality = await proxy_collection.count_documents({"score": {"$gte": 50, "$lt": 80}})
    low_quality = await proxy_collection.count_documents({"score": {"$lt": 50}})
    
    return {
        "total": total,
        "by_status": {
            "active": active,
            "inactive": inactive,
            "blocked": blocked,
            "unknown": unknown
        },
        "by_quality": {
            "high": high_quality,
            "medium": medium_quality,
            "low": low_quality
        }
    }
```

### 10.3. Mantenimiento de la Base de Datos

Para limpiar proxies antiguos y no utilizados, puedes implementar una tarea de mantenimiento:

```python
@staticmethod
async def cleanup_job():
    """Tarea periódica para limpiar proxies antiguos"""
    logger.info("Iniciando limpieza de proxies antiguos")
    
    # Eliminar proxies inactivos que no se han utilizado en una semana
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    result = await proxy_collection.delete_many({
        "status": "inactive",
        "last_checked": {"$lt": one_week_ago}
    })
    
    logger.info(f"Eliminados {result.deleted_count} proxies inactivos antiguos")
    
    # Marcar como desconocidos los proxies activos que no se han validado en 2 días
    two_days_ago = datetime.utcnow() - timedelta(days=2)
    result = await proxy_collection.update_many(
        {
            "status": "active",
            "last_checked": {"$lt": two_days_ago}
        },
        {
            "$set": {"status": "unknown"}
        }
    )
    
    logger.info(f"Marcados {result.modified_count} proxies activos antiguos como desconocidos")
```

Agrega esta tarea al scheduler:

```python
@classmethod
async def start(cls):
    """Iniciar el scheduler"""
    logger.info("Iniciando scheduler")
    
    while True:
        try:
            # Ejecutar scraping
            await cls.scrape_job()
            
            # Ejecutar validación
            await cls.validate_job()
            
            # Ejecutar limpieza
            await cls.cleanup_job()
            
            # Dormir hasta la próxima ejecución
            await asyncio.sleep(settings.SCRAPING_INTERVAL)
            
        except Exception as e:
            logger.error(f"Error en scheduler: {e}")
            await asyncio.sleep(60)
```

## 11. Solución de Problemas Comunes

### 11.1. No se obtienen proxies de ciertas fuentes

**Problema**: El scraper no puede obtener proxies de una fuente específica.

**Solución**:
1. Revisa los logs para errores específicos
2. Verifica si la estructura de la página web ha cambiado
3. Actualiza el scraper para adaptarse a la nueva estructura
4. Comprueba si la fuente ha implementado protección anti-bot

### 11.2. Todos los proxies fallan la validación

**Problema**: Los proxies se obtienen correctamente pero fallan al validarse.

**Solución**:
1. Revisa los criterios de validación, podrían ser demasiado estrictos
2. Aumenta el timeout en las pruebas de validación
3. Cambia la URL de prueba por una menos restrictiva que Google
4. Verifica si tu IP o rango está siendo bloqueado por los servicios de prueba

### 11.3. La API es lenta o se queda sin responder

**Problema**: La API muestra tiempos de respuesta altos o no responde.

**Solución**:
1. Aumenta los recursos del servidor (CPU/RAM)
2. Reduce el batch_size en operaciones de validación
3. Optimiza las consultas a MongoDB añadiendo índices adicionales
4. Implementa un sistema de caché para respuestas frecuentes
5. Considera separar el scheduler en un proceso independiente

### 11.4. Error de conexión a MongoDB

**Problema**: La aplicación no puede conectarse a la base de datos.

**Solución**:
1. Verifica que MongoDB esté en ejecución
2. Comprueba la URL de conexión en el archivo .env
3. Asegúrate de que las credenciales sean correctas
4. Verifica la configuración de red y firewalls
5. Comprueba los logs de MongoDB

## 12. Expansión y Personalización

### 12.1. Añadir soporte para nuevos protocolos

Para añadir soporte para nuevos protocolos de proxy (como SOCKS4A, HTTP/2):

1. Actualiza el enum `ProxyProtocol` en `app/models/proxy.py`:

```python
class ProxyProtocol(str, Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"
    SOCKS4A = "socks4a"  # Nuevo protocolo
    HTTP2 = "http2"      # Nuevo protocolo
```

2. Actualiza el validador en `app/validators/proxy_validator.py` para manejar el nuevo protocolo.

### 12.2. Implementar un sistema de caché

Para mejorar el rendimiento, puedes implementar un sistema de caché:

```python
# app/services/cache_service.py
from datetime import datetime, timedelta

class CacheService:
    _cache = {}
    
    @classmethod
    async def get(cls, key, ttl_seconds=60):
        """Obtener valor de caché"""
        if key not in cls._cache:
            return None
        
        value, expiry = cls._cache[key]
        if datetime.utcnow() > expiry:
            del cls._cache[key]
            return None
        
        return value
    
    @classmethod
    async def set(cls, key, value, ttl_seconds=60):
        """Guardar valor en caché"""
        expiry = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        cls._cache[key] = (value, expiry)
    
    @classmethod
    async def clear(cls):
        """Limpiar caché"""
        cls._cache.clear()
    
    @classmethod
    async def cleanup(cls):
        """Eliminar entradas expiradas"""
        now = datetime.utcnow()
        expired_keys = [k for k, (_, exp) in cls._cache.items() if exp < now]
        for key in expired_keys:
            del cls._cache[key]
```

Y luego usarlo en los servicios:

```python
# En ProxyService.get_proxies
async def get_proxies(...):
    cache_key = f"proxies_{status}_{min_score}_{limit}"
    cached = await CacheService.get(cache_key)
    if cached:
        return cached
    
    # Lógica normal para obtener proxies
    # ...
    
    # Guardar en caché
    await CacheService.set(cache_key, proxies, ttl_seconds=300)
    return proxies
```

### 12.3. Implementar autenticación avanzada

Para mejora la seguridad, puedes implementar JWT en lugar de API key simple:

1. Instala las dependencias necesarias:

```bash
pip install python-jose python-multipart
```

2. Implementa el sistema de autenticación:

```python
# app/core/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = "tu_clave_secreta"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username
```

3. Actualiza los endpoints para usar el nuevo sistema:

```python
@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != "admin" or form_data.password != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/proxy")
async def get_proxy(
    current_user: str = Depends(get_current_user),
    # otros parámetros
):
    # Lógica normal del endpoint
```

## 13. Escalabilidad y Despliegue

### 13.1. Despliegue en Docker

1. Crea un `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. Crea un `docker-compose.yml`:

```yaml
version: '3'

services:
  proxy-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - API_KEY=tu_clave_secreta_aqui
      - MONGODB_URL=mongodb://mongodb:27017
      - MONGODB_DB=proxy_service
    depends_on:
      - mongodb
    volumes:
      - ./logs:/app/logs

  mongodb:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - mongo-data:/data/db

volumes:
  mongo-data:
```

3. Iniciar con Docker Compose:

```bash
docker-compose up -d
```

### 13.2. Escalado Horizontal

Para escalar horizontalmente el servicio:

1. Separa el scheduler en un servicio independiente:

```yaml
services:
  proxy-api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    # ...

  proxy-scheduler:
    build: .
    command: python -m app.scheduler
    # ...
```

2. Implementa un servicio dedicado para el scheduler:

```python
# app/scheduler.py
import asyncio
from loguru import logger
import os

from app.core.scheduler import Scheduler
from app.db.mongodb import connect_to_mongodb

# Configurar loguru
logger.add(
    "logs/scheduler.log",
    rotation="10 MB",
    retention="1 week",
    level="INFO"
)

# Crear directorio logs si no existe
os.makedirs("logs", exist_ok=True)

async def main():
    """Función principal del scheduler"""
    logger.info("Iniciando servicio de scheduler")
    
    # Conectar a MongoDB
    await connect_to_mongodb()
    
    # Iniciar scheduler
    await Scheduler.start()

if __name__ == "__main__":
    asyncio.run(main())
```

3. Escala el servicio API según sea necesario:

```bash
docker-compose up -d --scale proxy-api=3
```

## 14. Glosario de Términos

- **Proxy**: Servidor intermedio que actúa como puente entre un cliente y un servidor final.
- **Scraping**: Proceso de extracción automática de datos de sitios web.
- **API Key**: Clave secreta utilizada para autenticar solicitudes a la API.
- **Rate Limiting**: Limitación de la frecuencia de solicitudes a un servicio.
- **Latencia**: Tiempo que tarda un proxy en responder a una solicitud.
- **Puntuación**: Valor numérico (0-100) que indica la calidad de un proxy.
- **Rotación**: Cambio sistemático entre diferentes proxies para distribuir solicitudes.
- **Validación**: Proceso de verificar si un proxy funciona correctamente.
- **Scheduler**: Sistema que ejecuta tareas programadas automáticamente.
- **Batch Processing**: Procesamiento de datos en lotes para mayor eficiencia.