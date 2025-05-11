# Proxy Service

<div align="center">

![Proxy Service Logo](https://via.placeholder.com/150?text=Proxy+Service)

**Sistema de gestión de proxies para scraping web a gran escala**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.88.0+-green.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-4.0+-green.svg)](https://www.mongodb.com/)

</div>

## 📋 Resumen

Proxy Service es un sistema avanzado que automatiza la obtención, validación y gestión de proxies para operaciones de scraping web a gran escala. Diseñado como un servicio independiente con una API REST, proporciona proxies de alta calidad y mantiene estadísticas detalladas de rendimiento.

## ✨ Características Principales

- 🔍 **Scraping Automático**: Obtiene proxies de múltiples fuentes públicas
- 🧪 **Validación Inteligente**: Verifica el funcionamiento de los proxies contra Google
- 🏆 **Sistema de Puntuación**: Califica los proxies según velocidad, estabilidad y funcionalidad
- 🔄 **Rotación Dinámica**: Proporciona proxies frescos para evitar bloqueos
- 📊 **Monitoreo de Rendimiento**: Mantiene estadísticas detalladas de cada proxy
- ⏱️ **Actualización Periódica**: Refresca automáticamente la base de datos de proxies
- 🔌 **API REST Completa**: Fácil integración con sistemas de scraping

## 🚀 Inicio Rápido

### Requisitos

- Python 3.10+
- MongoDB 4.0+
- Docker (opcional, para MongoDB)

### Instalación

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

```bash
# Opción con Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

5. **Configurar variables de entorno**

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```
# API Settings
API_KEY=your_secret_api_key_here

# MongoDB Settings
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=proxy_service
```

### Ejecución

```bash
uvicorn app.main:app --reload
```

El servicio estará disponible en: http://127.0.0.1:8000

Documentación Swagger UI: http://127.0.0.1:8000/docs

## 🔌 Uso de la API

### Autenticación

Todos los endpoints requieren autenticación mediante la cabecera `x-api-key`.

```bash
curl -X GET "http://localhost:8000/api/proxies" -H "x-api-key: your_secret_api_key_here"
```

### Endpoints Principales

#### Gestión de Proxies

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/proxy` | Obtener un único proxy válido |
| GET | `/api/proxies` | Obtener múltiples proxies filtrados |
| POST | `/api/proxy` | Añadir un nuevo proxy manualmente |
| POST | `/api/proxy/report` | Reportar el resultado de usar un proxy |

#### Scraping de Proxies

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/scrape/all` | Obtener proxies de todas las fuentes registradas |
| POST | `/api/scrape/{source_name}` | Obtener proxies de una fuente específica |

#### Validación de Proxies

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/validate/all` | Validar todos los proxies en la base de datos |
| POST | `/api/validate/{ip}/{port}` | Validar un proxy específico |

### Ejemplos de Uso

#### Obtener un Proxy Válido

```bash
curl -X GET "http://localhost:8000/api/proxy" \
     -H "x-api-key: your_secret_api_key_here" \
     -H "accept: application/json"
```

Respuesta:

```json
{
  "ip": "203.0.113.1",
  "port": 8080,
  "protocol": "http",
  "country": "United States",
  "anonymity": "high",
  "status": "active",
  "score": 92,
  "last_checked": "2025-05-11T10:23:45.123456",
  "source": "free_proxy_list"
}
```

#### Iniciar Scraping de Proxies

```bash
curl -X POST "http://localhost:8000/api/scrape/all" \
     -H "x-api-key: your_secret_api_key_here" \
     -H "accept: application/json"
```

Respuesta:

```json
42
```

(Número de proxies añadidos a la base de datos)

## 🏗️ Arquitectura

### Estructura del Proyecto

```
proxy-service/
├── app/
│   ├── api/            # Endpoints y routers de la API
│   ├── core/           # Configuración y componentes centrales
│   ├── db/             # Conexión y operaciones con la base de datos
│   ├── models/         # Modelos de datos y esquemas
│   ├── scrapers/       # Módulos para scraping de diferentes fuentes
│   ├── services/       # Lógica de negocio
│   ├── validators/     # Validación de proxies
│   └── main.py         # Punto de entrada de la aplicación
├── logs/               # Logs del servicio
├── .env                # Variables de entorno
├── requirements.txt    # Dependencias
└── README.md           # Este archivo
```

### Componentes Principales

- **API Layer**: Gestiona las solicitudes HTTP y devuelve respuestas
- **Services Layer**: Implementa la lógica de negocio
- **Data Layer**: Gestiona el almacenamiento y recuperación de datos
- **Scrapers**: Obtienen proxies de diferentes fuentes
- **Validators**: Verifican el funcionamiento de los proxies
- **Scheduler**: Ejecuta tareas periódicas de scraping y validación

### Flujo de Datos

1. El scheduler activa periódicamente el scraping de proxies
2. Los scrapers obtienen proxies de diferentes fuentes
3. Los proxies son almacenados en la base de datos
4. El scheduler activa la validación periódica
5. El validator verifica cada proxy y actualiza su estado
6. La API proporciona acceso a los proxies validados
7. Los clientes reportan el rendimiento de los proxies utilizados

## 🧩 Extensibilidad

### Añadir un Nuevo Scraper

1. Crear un nuevo archivo en `app/scrapers/`, por ejemplo `my_source_scraper.py`

```python
from typing import List
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
from ..models.proxy import Proxy, ProxyProtocol, ProxyStatus

class MySourceScraper(BaseScraper):
    """Scraper for my-source.com"""
    
    name = "my_source"
    url = "https://my-source.com/proxies"
    
    async def scrape(self) -> List[Proxy]:
        # Implementación específica
        proxies = []
        
        # Añadir lógica de scraping aquí
        
        return proxies
```

2. Registrar el scraper en `app/services/scraper_service.py`

```python
# Importar el nuevo scraper
from ..scrapers.my_source_scraper import MySourceScraper

class ScraperService:
    _scrapers: Dict[str, Type[BaseScraper]] = {
        "free_proxy_list": FreeProxyListScraper,
        "my_source": MySourceScraper  # Añadir aquí
    }
    # ...
```

## 📈 Rendimiento y Escalabilidad

- **Procesamiento Asíncrono**: Utiliza asyncio para operaciones concurrentes
- **Procesamiento por Lotes**: Valida proxies en lotes para optimizar recursos
- **Índices Optimizados**: Estructura de MongoDB optimizada para consultas frecuentes
- **Caché Inteligente**: Minimiza consultas a la base de datos
- **Operación Distribuida**: Puede ejecutarse en múltiples instancias

## 🔧 Configuración Avanzada

### Variables de Entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `API_KEY` | Clave de autenticación para la API | `your_secret_api_key_here` |
| `MONGODB_URL` | URL de conexión a MongoDB | `mongodb://localhost:27017` |
| `MONGODB_DB` | Nombre de la base de datos | `proxy_service` |
| `PROXY_VALIDATION_INTERVAL` | Intervalo de validación (segundos) | `3600` |
| `PROXY_MIN_SCORE` | Puntuación mínima para considerar un proxy válido | `50` |
| `SCRAPING_INTERVAL` | Intervalo de scraping (segundos) | `21600` |

### Configuración de Logging

El servicio utiliza Loguru para logging. Los logs se guardan en `logs/proxy_service.log` y rotan automáticamente cuando alcanzan 10 MB.

## 🤝 Integración con Otros Sistemas

Este servicio está diseñado para integrarse con sistemas de scraping web. El cliente puede solicitar proxies a través de la API, utilizarlos para sus operaciones de scraping, y luego reportar su rendimiento.

### Ejemplo de Integración con Python

```python
import httpx

class ProxyClient:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key
        self.headers = {"x-api-key": api_key}
    
    async def get_proxy(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/api/proxy",
                headers=self.headers
            )
            return response.json()
    
    async def report_result(self, ip, port, success, latency_ms=None, error=None):
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.api_url}/api/proxy/report",
                headers=self.headers,
                params={
                    "ip": ip,
                    "port": port,
                    "success": success,
                    "latency_ms": latency_ms,
                    "error": error
                }
            )
```

## 📋 Licencia

Este proyecto está licenciado bajo los términos de la licencia MIT.

---

<div align="center">
Desarrollado con ❤️ por [Tu Nombre/Organización]
</div>