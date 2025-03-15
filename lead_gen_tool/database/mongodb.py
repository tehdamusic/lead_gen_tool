from pymongo import MongoClient, errors
import os
import logging
from ai.lead_scoring import score_lead

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class MongoDB:
    _instance = None
    MIN_SCORE_THRESHOLD = 4  # Minimum score threshold for keeping leads

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
            self._db["leads"].create_index("score")  # Index for score-based queries

        except errors.ServerSelectionTimeoutError:
            logging.error("❌ MongoDB connection failed! Check your MONGO_URI.")
            raise

    def get_db(self):
        """Return the database instance."""
        if self._db is None:
            self.connect()
        return self._db
    
    def add_lead(self, lead_data):
        """
        Add a new lead to the database after scoring.
        Only adds leads that meet or exceed the minimum score threshold.
        
        Args:
            lead_data (dict): Lead information including name, platform, and content
            
        Returns:
            bool: True if lead was added, False otherwise
        """
        if self._db is None:
            self.connect()
        
        # Extract relevant information for scoring
        name = lead_data.get("name", lead_data.get("username", "Unknown"))
        platform = lead_data.get("platform", "unknown")
        
        # Gather all available text content
        title = lead_data.get("job_title", "")
        description = lead_data.get("description", "")
        comment = lead_data.get("comment", "")
        post_text = lead_data.get("post_text", "")
        content = lead_data.get("content", "")
        
        # Combine all text content for scoring
        combined_content = f"{title} {description} {comment} {post_text} {content}".strip()
        
        # Score the lead
        score = score_lead(name, title, combined_content)
        lead_data["score"] = score
        
        # Only add leads that meet minimum score threshold
        if score >= self.MIN_SCORE_THRESHOLD:
            try:
                # Check if the lead already exists
                existing_lead = self._db["leads"].find_one({"url": lead_data["url"]})
                if existing_lead:
                    # Update existing lead's score
                    self._db["leads"].update_one(
                        {"_id": existing_lead["_id"]},
                        {"$set": {"score": score}}
                    )
                    logging.info(f"📊 Updated lead score: {name} - Score: {score}")
                    return True
                else:
                    # Insert new lead
                    self._db["leads"].insert_one(lead_data)
                    logging.info(f"✅ Added lead: {name} from {platform} - Score: {score}")
                    return True
            except Exception as e:
                logging.error(f"❌ Error adding lead: {e}")
                return False
        else:
            logging.info(f"⏩ Skipping low-scoring lead: {name} - Score: {score}")
            return False
    
    def get_leads_by_score(self, min_score=None, max_score=None):
        """
        Retrieve leads within a specified score range.
        
        Args:
            min_score (int, optional): Minimum score threshold
            max_score (int, optional): Maximum score threshold
            
        Returns:
            list: Leads matching the score criteria
        """
        if self._db is None:
            self.connect()
            
        query = {}
        if min_score is not None:
            query["score"] = {"$gte": min_score}
        if max_score is not None:
            if "score" in query:
                query["score"]["$lte"] = max_score
            else:
                query["score"] = {"$lte": max_score}
                
        leads = list(self._db["leads"].find(query))
        return leads
    
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

def add_lead(lead_data):
    """Wrapper function for MongoDB.add_lead"""
    return mongodb.add_lead(lead_data)

def get_leads_by_score(min_score=None, max_score=None):
    """Wrapper function for MongoDB.get_leads_by_score"""
    return mongodb.get_leads_by_score(min_score, max_score)