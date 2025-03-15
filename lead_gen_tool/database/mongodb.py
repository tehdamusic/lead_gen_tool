from pymongo import MongoClient, errors
import os
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class MongoDB:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
            cls._instance._client = None
            cls._instance._db = None
        return cls._instance

    def connect(self):
        """Initialize MongoDB connection with error handling and connection pooling."""
        try:
            self._client = MongoClient(
                os.getenv("MONGO_URI", "mongodb://localhost:27017/"),
                maxPoolSize=50,  # Connection Pooling
                minPoolSize=10,
                serverSelectionTimeoutMS=5000  # Timeout to prevent long waits
            )
            self._db = self._client["lead_generator"]
            logging.info("✅ Connected to MongoDB successfully.")
            
            # Ensure indexes for faster queries
            self._db["leads"].create_index("url", unique=True)  # Prevent duplicate leads
            self._db["leads"].create_index("platform")  # Optimized search by platform
            self._db["blacklist"].create_index("url", unique=True)  # Prevent duplicate blacklisting

        except errors.ServerSelectionTimeoutError:
            logging.error("❌ MongoDB connection failed! Check your MONGO_URI.")
            raise

    def get_db(self):
        """Return the database instance."""
        if self._db is None:
            self.connect()
        return self._db

    def close_connection(self):
        """Gracefully close the MongoDB connection."""
        if self._client:
            self._client.close()
            logging.info("✅ MongoDB connection closed.")

# Initialize MongoDB singleton instance
mongodb = MongoDB()
mongodb.connect()

def get_db():
    return mongodb.get_db()
