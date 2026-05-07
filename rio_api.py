from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import bcrypt
import os
import logging

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection (sync)
MONGO_URI = os.environ.get("MONGO_URI", "")
MONGO_DB = os.environ.get("MONGO_DB", "RioPrintMedia_Test")
HTML_FILE = os.environ.get("HTML_FILE", "Rio_Sales_Tracker_ONLINE.html")

# Global DB client
mongo_client = None
db = None

@app.on_event("startup")
async def startup_event():
    global mongo_client, db
    try:
        logger.info(f"Connecting to MongoDB...")
        logger.info(f"Using database: {MONGO_DB}")
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        mongo_client.admin.command('ping')
        db = mongo_client[MONGO_DB]
        logger.info("MongoDB connected successfully")
    except ConnectionFailure as e:
        logger.warning(f"MongoDB connection failed: {e}")
        logger.warning("App will run without database (login disabled)")
    except Exception as e:
        logger.error(f"Startup error: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    global mongo_client
    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB connection closed")

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

# Serve HTML
@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    logger.info(f"GET / — serving {HTML_FILE}")
    if not os.path.exists(HTML_FILE):
        logger.error(f"HTML file not found: {HTML_FILE}")
        return HTMLResponse(f"<h2>File not found: {HTML_FILE}</h2>", 404)
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(html)

# Login endpoint
@app.post("/api/login")
def login(request: LoginRequest):
    try:
        if db is None:
            raise HTTPException(status_code=503, detail="Database not available")
            
        logger.info(f"Login attempt: {request.username}")
        
        # Debug: Check database and collection
        logger.info(f"Database: {db.name}")
        logger.info(f"Collections: {db.list_collection_names()}")
        
        # Count users
        user_count = db.rio_users.count_documents({})
        logger.info(f"Total users in collection: {user_count}")
        
        # Find user in database
        user = db.rio_users.find_one({"username": request.username})
        
        if not user:
            logger.warning(f"User not found: {request.username}")
            # Debug: List all usernames
            all_users = list(db.rio_users.find({}, {"username": 1, "_id": 0}))
            logger.info(f"Available usernames: {all_users}")
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Check bcrypt hashed password
        stored_password = user.get("password", "")
        if stored_password.startswith("$2b$") or stored_password.startswith("$2a$"):
            # Bcrypt hashed password
            if not bcrypt.checkpw(request.password.encode('utf-8'), stored_password.encode('utf-8')):
                logger.warning(f"Invalid password for: {request.username}")
                raise HTTPException(status_code=401, detail="Invalid username or password")
        else:
            # Plain text password (fallback for testing)
            if stored_password != request.password:
                logger.warning(f"Invalid password for: {request.username}")
                raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Return user data (exclude password)
        user_data = {
            "username": user["username"],
            "role": user.get("role", "user"),
            "name": user.get("name", user["username"])
        }
        
        logger.info(f"Login successful: {request.username}")
        return {
            "success": True,
            "message": "Login successful",
            "user": user_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Health check
@app.get("/api/health")
def health():
    db_status = "connected" if db is not None else "disconnected"
    return {"status": "ok", "database": db_status}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
