from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import os
import requests
from dotenv import load_dotenv
import traceback
import logging
from datetime import datetime
import time

# Logging configuration
class CustomFormatter(logging.Formatter):
    """Custom formatter with emojis for different log levels"""
    
    def format(self, record):
        # Add emojis based on log level
        if record.levelno == logging.INFO:
            record.msg = f"ℹ️ {record.msg}"
        elif record.levelno == logging.WARNING:
            record.msg = f"⚠️ {record.msg}"
        elif record.levelno == logging.ERROR:
            record.msg = f"❌ {record.msg}"
        elif record.levelno == logging.DEBUG:
            record.msg = f"🔍 {record.msg}"
        return super().format(record)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log'),
        logging.StreamHandler()
    ]
)

# Apply custom formatter
for handler in logging.getLogger().handlers:
    handler.setFormatter(CustomFormatter())

logger = logging.getLogger(__name__)

load_dotenv()

# Gemini configuration
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

try:
    logger.info("Initializing Gemini...")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Test Gemini connection
    logger.info("Testing Gemini connection...")
    test_response = model.generate_content("Hello")
    logger.info(f"Gemini test response: {test_response.text}")
    logger.info("Gemini initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gemini: {str(e)}")
    raise

app = FastAPI(title="Orchestrator Agent")

class Message(BaseModel):
    content: str

AGENTS = {
    "classifier": {"port": 8001, "name": "Needs Analyzer"},
    "shopping": {"port": 8002, "name": "Shopping Assistant"}
}

# Timeout settings
REQUEST_TIMEOUT = 10  # seconds
MAX_RETRIES = 2

def get_agent_response(port, message):
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Sending message to agent on port {port} (attempt {attempt + 1}/{MAX_RETRIES})")
            start_time = time.time()
            
            response = requests.post(
                f"http://localhost:{port}/chat",
                json={"content": message},
                timeout=REQUEST_TIMEOUT
            )
            
            elapsed_time = time.time() - start_time
            logger.info(f"Response received in {elapsed_time:.2f} seconds")
            
            if response.status_code == 200:
                logger.info(f"Received response from agent on port {port}")
                return response.json()["response"]
            else:
                error_msg = f"Agent communication error: {response.status_code}"
                logger.error(error_msg)
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1)  # Wait before retry
                    continue
                return error_msg
                
        except requests.Timeout:
            logger.error(f"Timeout while waiting for agent on port {port}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
                continue
            return "Agent response timeout. Please try again."
            
        except Exception as e:
            error_msg = f"Agent connection error: {str(e)}"
            logger.error(error_msg)
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
                continue
            return error_msg
    
    return "Failed to get response from agent after multiple attempts."

@app.post("/chat")
async def chat(message: Message):
    try:
        logger.info(f"Received new message: {message.content}")
        
        # For initial testing, return a simple response
        if message.content.lower() in ["hello", "hi", "hey"]:
            return {"response": "Hello! I'm your shopping assistant. How can I help you today?"}
        
        try:
            with open("prompt.txt", "r", encoding="utf-8") as f:
                system_prompt = f.read()
            logger.info("Successfully loaded prompt.txt")
        except Exception as e:
            logger.error(f"Failed to load prompt.txt: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to load system prompt")
        
        # Prepare Gemini context with timeout
        logger.info("Starting Gemini analysis...")
        start_time = time.time()
        
        try:
            logger.info("Creating new chat session...")
            chat = model.start_chat(history=[])
            
            logger.info("Sending message to Gemini...")
            response = chat.send_message(
                f"{system_prompt}\n\nUser message: {message.content}",
                timeout=REQUEST_TIMEOUT
            )
            
            elapsed_time = time.time() - start_time
            logger.info(f"Gemini analysis completed in {elapsed_time:.2f} seconds")
            logger.info(f"Gemini response: {response.text}")
            
        except Exception as e:
            logger.error(f"Gemini analysis failed: {str(e)}")
            logger.error("Full traceback:")
            logger.error(traceback.format_exc())
            return {"response": "I'm having trouble analyzing your message. Please try again."}
        
        # Analyze response and choose appropriate agent
        agent_choice = response.text.lower()
        logger.info(f"Gemini agent choice: {agent_choice}")
        
        if "classifier" in agent_choice or "analyzer" in agent_choice:
            logger.info("Selected Needs Analyzer")
            agent_response = get_agent_response(AGENTS["classifier"]["port"], message.content)
            return {"response": f"Selected {AGENTS['classifier']['name']}:\n{agent_response}"}
        elif "shopping" in agent_choice or "shop" in agent_choice:
            logger.info("Selected Shopping Assistant")
            agent_response = get_agent_response(AGENTS["shopping"]["port"], message.content)
            return {"response": f"Selected {AGENTS['shopping']['name']}:\n{agent_response}"}
        else:
            logger.warning("Could not determine appropriate agent")
            return {"response": "I cannot determine which agent should handle this request. Please try rephrasing."}
            
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info("Starting Orchestrator server...")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 