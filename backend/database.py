import os
import logging
import certifi
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure, ConfigurationError
from dotenv import load_dotenv
load_dotenv("D:/Pradip_collab/safeguard-app/backend/.env")

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables


class DatabaseConfig:
    """Database configuration and validation"""
    
    def __init__(self):
        self.mongodb_url = self._get_mongodb_url()
        self.database_name = os.getenv("MONGODB_DATABASE", "safeguard")
        self.connection_timeout = int(os.getenv("MONGODB_TIMEOUT", "10000"))
        self.max_pool_size = int(os.getenv("MONGODB_POOL_SIZE", "10"))
        
    def _get_mongodb_url(self) -> str:
        """Get and validate MongoDB URL from environment"""
        mongodb_url = os.getenv("MONGODB_URL")
        
        if not mongodb_url:
            logger.error("❌ MONGODB_URL not found in environment variables")
            logger.info("💡 Please check your .env file contains: MONGODB_URL=your_connection_string")
            raise ValueError("MONGODB_URL environment variable is required")
        
        logger.info("✅ MongoDB URL loaded from environment")
        logger.debug(f"🔍 MongoDB URL: {mongodb_url[:20]}...{mongodb_url[-10:] if len(mongodb_url) > 30 else mongodb_url}")
        return mongodb_url
    
    def validate_url_format(self) -> bool:
        """Validate MongoDB URL format"""
        if not self.mongodb_url.startswith(("mongodb://", "mongodb+srv://")):
            logger.error("❌ Invalid MongoDB URL format. Must start with 'mongodb://' or 'mongodb+srv://'")
            return False
        
        logger.info("✅ MongoDB URL format is valid")
        return True

class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        self.config = DatabaseConfig()
        self.is_connected = False
        
    async def connect(self) -> bool:
        """
        Establish connection to MongoDB with comprehensive error handling
        Returns: True if successful, False otherwise
        """
        try:
            logger.info("🔄 Initializing MongoDB connection...")
            
            # Validate URL format first
            if not self.config.validate_url_format():
                return False
            
            # Determine if this is Atlas or local MongoDB
            is_atlas = "mongodb+srv://" in self.config.mongodb_url or "mongodb.net" in self.config.mongodb_url
            
            # Configure client based on connection type
            client_options = {
                "serverSelectionTimeoutMS": self.config.connection_timeout,
                "connectTimeoutMS": self.config.connection_timeout,
                "socketTimeoutMS": 20000,
                "maxPoolSize": self.config.max_pool_size,
                "retryWrites": True,
            }
            
            if is_atlas:
                logger.info("🌐 Detected MongoDB Atlas connection")
                client_options.update({
                    "tls": True,
                    "tlsCAFile": certifi.where(),
                    "tlsAllowInvalidCertificates": False,
                    "tlsAllowInvalidHostnames": False,
                })
            else:
                logger.info("🏠 Detected local MongoDB connection")
            
            logger.debug(f"🔧 Connection options: {client_options}")
            
            # Create client
            self.client = AsyncIOMotorClient(self.config.mongodb_url, **client_options)
            self.database = self.client[self.config.database_name]
            
            # Test connection with ping
            logger.info("🏓 Testing connection with ping...")
            await self.client.admin.command("ping")
            
            # Verify database access
            logger.info("🔍 Verifying database access...")
            collections = await self.database.list_collection_names()
            logger.debug(f"📁 Available collections: {collections}")
            
            self.is_connected = True
            logger.info(f"✅ Successfully connected to MongoDB database: '{self.config.database_name}'")
            
            return True
            
        except ServerSelectionTimeoutError as e:
            logger.error(f"❌ Connection timeout - Could not reach MongoDB server")
            logger.error(f"🔍 Details: {str(e)}")
            logger.info("💡 Check your internet connection and MongoDB Atlas network access settings")
            return False
            
        except ConnectionFailure as e:
            logger.error(f"❌ Connection failed - Authentication or network issue")
            logger.error(f"🔍 Details: {str(e)}")
            logger.info("💡 Check your MongoDB credentials and cluster status")
            return False
            
        except ConfigurationError as e:
            logger.error(f"❌ Configuration error in connection string")
            logger.error(f"🔍 Details: {str(e)}")
            logger.info("💡 Check your MongoDB URL format and parameters")
            return False
            
        except Exception as e:
            logger.error(f"❌ Unexpected error during connection: {str(e)}")
            logger.debug(f"🔍 Error type: {type(e).__name__}")
            return False
    
    async def disconnect(self) -> None:
        """Close database connection"""
        if self.client:
            self.client.close()
            self.is_connected = False
            logger.info("🔌 MongoDB connection closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        if not self.is_connected:
            return {"status": "disconnected", "healthy": False}
        
        try:
            # Ping test
            start_time = os.times().elapsed
            await self.client.admin.command("ping")
            ping_time = (os.times().elapsed - start_time) * 1000
            
            # Get server info
            server_info = await self.client.admin.command("serverStatus")
            
            # Get database stats
            db_stats = await self.database.command("dbStats")
            
            health_info = {
                "status": "connected",
                "healthy": True,
                "ping_ms": round(ping_time, 2),
                "database": self.config.database_name,
                "collections_count": len(await self.database.list_collection_names()),
                "server_version": server_info.get("version", "unknown"),
                "storage_size_mb": round(db_stats.get("storageSize", 0) / (1024 * 1024), 2),
            }
            
            logger.debug(f"💓 Health check passed: {health_info}")
            return health_info
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")
            return {"status": "error", "healthy": False, "error": str(e)}
    
    def get_collection(self, collection_name: str):
        """Get collection with connection validation"""
        if not self.is_connected:
            raise ConnectionError("Database not connected. Call connect() first.")
        return self.database[collection_name]

# Global database instance
db_manager = Database()

# Connection management functions
async def connect_to_mongo() -> None:
    """Initialize database connection"""
    logger.info("🚀 Starting MongoDB connection process...")
    
    success = await db_manager.connect()
    if not success:
        logger.error("💥 Failed to establish MongoDB connection")
        raise ConnectionError("Could not connect to MongoDB")
    
    # Create indexes after successful connection
    await create_indexes()
    logger.info("🎉 Database initialization completed successfully")

async def close_mongo_connection() -> None:
    """Close database connection"""
    await db_manager.disconnect()

async def get_database_health() -> Dict[str, Any]:
    """Get database health status"""
    return await db_manager.health_check()

# Collection accessors with validation
def get_users_collection():
    """Get users collection"""
    try:
        return db_manager.get_collection("users")
    except ConnectionError as e:
        logger.error(f"❌ Cannot access users collection: {e}")
        raise

def get_contacts_collection():
    """Get contacts collection"""
    try:
        return db_manager.get_collection("contacts")
    except ConnectionError as e:
        logger.error(f"❌ Cannot access contacts collection: {e}")
        raise

def get_activities_collection():
    """Get activities collection"""
    try:
        return db_manager.get_collection("activities")
    except ConnectionError as e:
        logger.error(f"❌ Cannot access activities collection: {e}")
        raise

# CRUD Operations with comprehensive logging
async def create_indexes() -> None:
    """Create database indexes for optimal performance"""
    try:
        logger.info("📊 Creating database indexes...")
        
        users_collection = get_users_collection()
        contacts_collection = get_contacts_collection()
        activities_collection = get_activities_collection()
        
        # Users indexes
        logger.debug("🔍 Creating users collection indexes...")
        await users_collection.create_index("email", unique=True)
        await users_collection.create_index("createdAt")
        await users_collection.create_index([("firstName", 1), ("lastName", 1)])
        logger.debug("✅ Users indexes created")
        
        # Contacts indexes
        logger.debug("🔍 Creating contacts collection indexes...")
        await contacts_collection.create_index("userId")
        await contacts_collection.create_index("email")
        await contacts_collection.create_index("priority")
        await contacts_collection.create_index([("userId", 1), ("priority", -1)])
        logger.debug("✅ Contacts indexes created")
        
        # Activities indexes
        logger.debug("🔍 Creating activities collection indexes...")
        await activities_collection.create_index("userId")
        await activities_collection.create_index("timestamp")
        await activities_collection.create_index("type")
        await activities_collection.create_index([("userId", 1), ("timestamp", -1)])
        logger.debug("✅ Activities indexes created")
        
        logger.info("🎯 All database indexes created successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to create indexes: {str(e)}")
        raise

# Enhanced CRUD operations with debugging
class CRUDOperations:
    """CRUD operations with comprehensive logging and error handling"""
    
    @staticmethod
    async def create_document(collection_name: str, document: Dict[str, Any]) -> str:
        """Create a new document"""
        try:
            collection = db_manager.get_collection(collection_name)
            logger.debug(f"📝 Creating document in {collection_name}: {document.get('email', 'N/A')}")
            
            result = await collection.insert_one(document)
            logger.info(f"✅ Document created in {collection_name} with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"❌ Failed to create document in {collection_name}: {str(e)}")
            raise
    
    @staticmethod
    async def find_document(collection_name: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document"""
        try:
            collection = db_manager.get_collection(collection_name)
            logger.debug(f"🔍 Finding document in {collection_name} with filter: {filter_dict}")
            
            document = await collection.find_one(filter_dict)
            if document:
                logger.debug(f"✅ Document found in {collection_name}")
            else:
                logger.debug(f"📭 No document found in {collection_name}")
            
            return document
            
        except Exception as e:
            logger.error(f"❌ Failed to find document in {collection_name}: {str(e)}")
            raise
    
    @staticmethod
    async def update_document(collection_name: str, filter_dict: Dict[str, Any], 
                            update_dict: Dict[str, Any]) -> bool:
        """Update a document"""
        try:
            collection = db_manager.get_collection(collection_name)
            logger.debug(f"📝 Updating document in {collection_name}")
            
            result = await collection.update_one(filter_dict, {"$set": update_dict})
            
            if result.modified_count > 0:
                logger.info(f"✅ Document updated in {collection_name}")
                return True
            else:
                logger.warning(f"⚠️ No document updated in {collection_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to update document in {collection_name}: {str(e)}")
            raise
    
    @staticmethod
    async def delete_document(collection_name: str, filter_dict: Dict[str, Any]) -> bool:
        """Delete a document"""
        try:
            collection = db_manager.get_collection(collection_name)
            logger.debug(f"🗑️ Deleting document from {collection_name}")
            
            result = await collection.delete_one(filter_dict)
            
            if result.deleted_count > 0:
                logger.info(f"✅ Document deleted from {collection_name}")
                return True
            else:
                logger.warning(f"⚠️ No document deleted from {collection_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to delete document from {collection_name}: {str(e)}")
            raise

# Initialize CRUD operations
crud = CRUDOperations()

# Connection status checker
def is_database_connected() -> bool:
    """Check if database is connected"""
    return db_manager.is_connected

# Debug function to test all operations
async def test_database_operations():
    """Test all database operations - useful for debugging"""
    logger.info("🧪 Starting database operations test...")
    
    try:
        # Test connection
        health = await get_database_health()
        logger.info(f"💓 Database health: {health}")
        
        # Test collections access
        users = get_users_collection()
        contacts = get_contacts_collection()
        activities = get_activities_collection()
        
        logger.info("✅ All database operations test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database operations test failed: {str(e)}")
        return False
