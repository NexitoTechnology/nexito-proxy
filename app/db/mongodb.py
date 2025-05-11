import motor.motor_asyncio
from loguru import logger
from ..core.config import settings

client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
db = client[settings.MONGODB_DB]

# Collections
proxy_collection = db.proxies

async def create_indexes():
    """Create indexes for better performance"""
    try:
        # Create unique index on ip:port
        await proxy_collection.create_index([("ip", 1), ("port", 1)], unique=True)
        
        # Create index on status for quick filtering
        await proxy_collection.create_index([("status", 1)])
        
        # Create index on score for sorting
        await proxy_collection.create_index([("score", -1)])
        
        # Create index on last_checked for maintenance
        await proxy_collection.create_index([("last_checked", 1)])
        
        logger.info("MongoDB indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating MongoDB indexes: {e}")
        raise

async def connect_to_mongodb():
    """Connect to MongoDB and create indexes"""
    try:
        # Check connection
        await client.admin.command('ping')
        logger.info("Connected to MongoDB!")
        
        # Create indexes
        await create_indexes()
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        raise