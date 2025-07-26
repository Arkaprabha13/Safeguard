#!/usr/bin/env python3
"""
MongoDB Connection Test Script
Tests various connection methods to help debug Atlas connectivity issues
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

try:
    from dotenv import load_dotenv
    from motor.motor_asyncio import AsyncIOMotorClient
    from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
    import certifi
    import ssl
except ImportError as e:
    print(f"❌ Missing required package: {e}")
    print("📦 Install with: pip install motor python-dotenv certifi")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MongoConnectionTester:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.mongodb_url = os.getenv("MONGODB_URL")
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} - {test_name}"
        if details:
            result += f" - {details}"
        
        print(result)
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now()
        })

    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        print("\n🔍 CHECKING PREREQUISITES")
        print("=" * 50)
        
        # Check .env file
        env_file = Path('.env')
        if env_file.exists():
            self.log_result("Environment file exists", True, str(env_file.absolute()))
        else:
            self.log_result("Environment file exists", False, "No .env file found")
            return False
        
        # Check MongoDB URL
        if self.mongodb_url:
            # Mask sensitive info
            masked_url = self.mongodb_url[:20] + "..." + self.mongodb_url[-15:] if len(self.mongodb_url) > 35 else self.mongodb_url
            self.log_result("MongoDB URL loaded", True, masked_url)
        else:
            self.log_result("MongoDB URL loaded", False, "MONGODB_URL not found in .env")
            return False
        
        # Check URL format
        if self.mongodb_url.startswith(("mongodb://", "mongodb+srv://")):
            self.log_result("URL format valid", True, "Correct MongoDB URI format")
        else:
            self.log_result("URL format valid", False, "Invalid MongoDB URI format")
            return False
        
        # Check if Atlas connection
        is_atlas = "mongodb+srv://" in self.mongodb_url or "mongodb.net" in self.mongodb_url
        self.log_result("Atlas connection detected", is_atlas, "MongoDB Atlas" if is_atlas else "Local MongoDB")
        
        # Check Python SSL support
        try:
            ssl_version = ssl.OPENSSL_VERSION
            self.log_result("SSL support", True, ssl_version)
        except Exception as e:
            self.log_result("SSL support", False, str(e))
        
        # Check certifi
        try:
            ca_file = certifi.where()
            self.log_result("CA certificates", True, f"Found at {ca_file}")
        except Exception as e:
            self.log_result("CA certificates", False, str(e))
        
        return True

    async def test_basic_connection(self):
        """Test basic MongoDB connection"""
        print("\n🔗 TESTING BASIC CONNECTION")
        print("=" * 50)
        
        try:
            client = AsyncIOMotorClient(
                self.mongodb_url,
                serverSelectionTimeoutMS=5000
            )
            
            # Test ping
            await client.admin.command("ping")
            
            # Get server info
            server_info = await client.admin.command("serverStatus")
            version = server_info.get("version", "unknown")
            
            self.log_result("Basic connection", True, f"MongoDB v{version}")
            
            client.close()
            return True
            
        except ServerSelectionTimeoutError as e:
            self.log_result("Basic connection", False, f"Timeout: {str(e)[:100]}...")
            return False
        except Exception as e:
            self.log_result("Basic connection", False, f"Error: {str(e)[:100]}...")
            return False

    async def test_ssl_connection(self):
        """Test SSL/TLS connection specifically"""
        print("\n🔒 TESTING SSL/TLS CONNECTION")
        print("=" * 50)
        
        # Test 1: With TLS and CA file
        try:
            client = AsyncIOMotorClient(
                self.mongodb_url,
                tls=True,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=5000
            )
            
            await client.admin.command("ping")
            self.log_result("TLS with CA file", True, "SSL connection successful")
            client.close()
            
        except Exception as e:
            self.log_result("TLS with CA file", False, str(e)[:100])
        
        # Test 2: TLS without CA file validation
        try:
            client = AsyncIOMotorClient(
                self.mongodb_url,
                tls=True,
                tlsAllowInvalidCertificates=True,
                serverSelectionTimeoutMS=5000
            )
            
            await client.admin.command("ping")
            self.log_result("TLS (skip cert validation)", True, "Connection successful")
            client.close()
            
        except Exception as e:
            self.log_result("TLS (skip cert validation)", False, str(e)[:100])
        
        # Test 3: No explicit TLS (let driver decide)
        try:
            client = AsyncIOMotorClient(
                self.mongodb_url,
                serverSelectionTimeoutMS=5000
            )
            
            await client.admin.command("ping")
            self.log_result("Auto TLS detection", True, "Driver handled TLS automatically")
            client.close()
            
        except Exception as e:
            self.log_result("Auto TLS detection", False, str(e)[:100])

    async def test_database_operations(self):
        """Test basic database operations"""
        print("\n🗄️ TESTING DATABASE OPERATIONS")
        print("=" * 50)
        
        try:
            # Use the connection method that works
            client = AsyncIOMotorClient(
                self.mongodb_url,
                tls=True,
                tlsAllowInvalidCertificates=True,  # For testing
                serverSelectionTimeoutMS=10000
            )
            
            # Test database access
            db = client.safeguard
            
            # Test collection access
            test_collection = db.connection_test
            
            # Test insert
            test_doc = {
                "test": True,
                "timestamp": datetime.now(),
                "message": "Connection test successful"
            }
            
            result = await test_collection.insert_one(test_doc)
            self.log_result("Document insert", True, f"ID: {result.inserted_id}")
            
            # Test find
            found_doc = await test_collection.find_one({"_id": result.inserted_id})
            self.log_result("Document find", found_doc is not None, "Document retrieved")
            
            # Test update
            update_result = await test_collection.update_one(
                {"_id": result.inserted_id},
                {"$set": {"updated": True}}
            )
            self.log_result("Document update", update_result.modified_count > 0, "Document updated")
            
            # Test delete (cleanup)
            delete_result = await test_collection.delete_one({"_id": result.inserted_id})
            self.log_result("Document delete", delete_result.deleted_count > 0, "Document deleted")
            
            # Test collections list
            collections = await db.list_collection_names()
            self.log_result("List collections", True, f"Found {len(collections)} collections")
            
            client.close()
            return True
            
        except Exception as e:
            self.log_result("Database operations", False, str(e))
            return False

    async def test_network_connectivity(self):
        """Test network connectivity to MongoDB Atlas"""
        print("\n🌐 TESTING NETWORK CONNECTIVITY")
        print("=" * 50)
        
        import socket
        
        # Extract host from URL
        if "mongodb+srv://" in self.mongodb_url:
            # For SRV records, we'll test the main cluster URL
            try:
                # Extract cluster host
                url_parts = self.mongodb_url.split("@")[1].split("/")[0].split("?")[0]
                host = url_parts
                port = 27017
                
                # Test socket connection
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    self.log_result("Network connectivity", True, f"Can reach {host}:{port}")
                else:
                    self.log_result("Network connectivity", False, f"Cannot reach {host}:{port}")
                    
            except Exception as e:
                self.log_result("Network connectivity", False, str(e))

    def print_summary(self):
        """Print test summary"""
        print("\n📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Tests passed: {passed}/{total}")
        print(f"Success rate: {(passed/total*100):.1f}%")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Your MongoDB connection is working.")
        else:
            print("\n⚠️ SOME TESTS FAILED. Check the issues above.")
            
            # Provide recommendations
            print("\n💡 RECOMMENDATIONS:")
            
            # Check for common issues
            failed_tests = [r for r in self.test_results if not r['success']]
            
            for test in failed_tests:
                if "SSL" in test['details'] or "TLS" in test['details']:
                    print("- SSL/TLS issue: Check MongoDB Atlas Network Access settings")
                    print("- Try adding your IP to Atlas whitelist: 0.0.0.0/0 for testing")
                    print("- Check if corporate firewall blocks port 27017")
                
                if "timeout" in test['details'].lower():
                    print("- Network timeout: Check internet connection")
                    print("- Increase timeout values in connection string")
                
                if "authentication" in test['details'].lower():
                    print("- Auth issue: Verify username/password in connection string")
                    print("- Check MongoDB Atlas database user permissions")

    async def run_all_tests(self):
        """Run all connection tests"""
        print("🚀 MONGODB CONNECTION TEST SUITE")
        print("=" * 50)
        print(f"Started at: {datetime.now()}")
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("\n❌ Prerequisites failed. Please fix issues above.")
            return
        
        # Run connection tests
        await self.test_network_connectivity()
        await self.test_basic_connection()
        await self.test_ssl_connection()
        
        # Only test database operations if basic connection works
        basic_connection_works = any(
            r['success'] for r in self.test_results 
            if 'connection' in r['test'].lower()
        )
        
        if basic_connection_works:
            await self.test_database_operations()
        else:
            print("\n⚠️ Skipping database operations - no working connection found")
        
        # Print summary
        self.print_summary()

async def main():
    """Main test function"""
    tester = MongoConnectionTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
