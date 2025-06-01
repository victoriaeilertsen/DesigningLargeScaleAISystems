import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging
import time
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import subprocess
import sys
import threading
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Shopping Assistant API")

# Pydantic model for messages
class Message(BaseModel):
    content: str

# Global variables
model = None
backend_ready = False

def wait_for_backend():
    """Wait until backend is ready"""
    max_retries = 30
    retry_delay = 1
    
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:8000/docs")
            if response.status_code == 200:
                logger.info("✅ Backend is ready!")
                return True
        except requests.exceptions.ConnectionError:
            logger.info(f"⌛ Waiting for backend... (attempt {i+1}/{max_retries})")
            time.sleep(retry_delay)
    
    logger.error("❌ Backend failed to start in expected time")
    return False

def run_streamlit():
    """Run Streamlit application in a separate process"""
    try:
        # Path to app.py
        app_path = Path(__file__).parent / "app.py"
        
        # Run Streamlit with output redirection
        streamlit_process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", str(app_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Print Streamlit output
        def print_output(pipe, prefix):
            for line in pipe:
                logger.info(f"{prefix}: {line.strip()}")
        
        # Start threads for logging
        stdout_thread = threading.Thread(target=print_output, args=(streamlit_process.stdout, "STREAMLIT"))
        stderr_thread = threading.Thread(target=print_output, args=(streamlit_process.stderr, "STREAMLIT-ERROR"))
        stdout_thread.daemon = True
        stderr_thread.daemon = True
        stdout_thread.start()
        stderr_thread.start()
        
        logger.info("🚀 Frontend Streamlit started")
        return streamlit_process
    except Exception as e:
        logger.error(f"❌ Error starting Streamlit: {str(e)}")
        return None

def analyze_message(message):
    """Analyze if the message is about needs or shopping"""
    global model
    logger.info(f"🔍 Analyzing message type: {message}")
    
    prompt = """
    Analyze if this message is about:
    1. Understanding needs/requirements (respond with 'needs')
    2. Finding products/shopping (respond with 'shopping')
    
    Message: {message}
    
    Respond with only one word: 'needs' or 'shopping'
    """
    
    try:
        start_time = time.time()
        response = model.generate_content(prompt.format(message=message))
        elapsed_time = time.time() - start_time
        
        result = response.text.strip().lower()
        logger.info(f"⏱️ Analysis took {elapsed_time:.2f} seconds")
        logger.info(f"📊 Message classified as: {result}")
        
        return result
    except Exception as e:
        logger.error(f"❌ Error analyzing message: {str(e)}")
        return "needs"  # Default to needs analyzer

def get_needs_analyzer_response(message):
    """Get response from needs analyzer"""
    global model
    logger.info(f"🤔 Getting Needs Analyzer response for: {message}")
    
    prompt = """
    You are a Needs Analyzer. Your task is to quickly identify user needs.
    Be direct and efficient. Ask only essential questions.
    Make quick assessments and provide clear summaries.
    
    User message: {message}
    
    Respond in a helpful and efficient way.
    """
    
    try:
        start_time = time.time()
        response = model.generate_content(prompt.format(message=message))
        elapsed_time = time.time() - start_time
        
        logger.info(f"⏱️ Needs Analyzer response took {elapsed_time:.2f} seconds")
        return response.text
    except Exception as e:
        logger.error(f"❌ Error getting needs analyzer response: {str(e)}")
        return "I'm having trouble analyzing your needs. Please try again."

def get_shopping_assistant_response(message):
    """Get response from shopping assistant using Perplexity API"""
    logger.info(f"🛍️ Getting Shopping Assistant response for: {message}")
    
    perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
    if not perplexity_api_key:
        logger.error("❌ PERPLEXITY_API_KEY not found in .env file")
        return "I'm having trouble searching for products. Please check the API configuration."
    
    headers = {
        "Authorization": f"Bearer {perplexity_api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    You are a Shopping Assistant. Search the internet for the best products based on these requirements:
    {message}
    
    Please provide:
    1. Specific product recommendations with prices
    2. FULL, CLICKABLE links to where to buy them (use markdown format: [Product Name](full_url))
    3. Brief comparison of options
    4. Current availability information
    
    IMPORTANT:
    - ALWAYS include FULL URLs in markdown format for each product
    - Make sure all links are complete and clickable
    - Include direct links to specific product pages, not just store homepages
    - Format prices in the local currency
    - Focus on finding the best value for money
    - Include recent prices and availability
    - If possible, include links to multiple stores for price comparison
    """
    
    try:
        start_time = time.time()
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json={
                "model": "sonar",
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        response.raise_for_status()
        result = response.json()["choices"][0]["message"]["content"]
        elapsed_time = time.time() - start_time
        
        logger.info(f"⏱️ Shopping Assistant response took {elapsed_time:.2f} seconds")
        return result
    except Exception as e:
        logger.error(f"❌ Error getting shopping assistant response: {str(e)}")
        return "I'm having trouble searching for products. Please try again."

@app.on_event("startup")
async def startup_event():
    """Initialize the API on startup"""
    global model, backend_ready
    logger.info("🚀 Starting Shopping Assistant API")
    
    # Load API keys
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
    
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file")
    if not perplexity_api_key:
        raise ValueError("PERPLEXITY_API_KEY not found in .env file")
    
    logger.info("✅ API configuration loaded successfully")
    
    # Initialize Gemini
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("✅ AI model initialized successfully")
        backend_ready = True
    except Exception as e:
        logger.error(f"❌ Error initializing AI model: {str(e)}")
        raise

@app.post("/chat")
async def chat(message: Message):
    """Handle chat messages"""
    try:
        logger.info(f"📥 Received message: {message.content}")
        
        # Analyze message type
        message_type = analyze_message(message.content)
        
        # Get appropriate response
        if message_type == 'needs':
            logger.info("🎯 Routing to Needs Analyzer")
            response = get_needs_analyzer_response(message.content)
        else:
            logger.info("🎯 Routing to Shopping Assistant")
            response = get_shopping_assistant_response(message.content)
        
        return {"response": response}
    except Exception as e:
        logger.error(f"❌ Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Run backend in a separate thread
    backend_thread = threading.Thread(
        target=lambda: uvicorn.run(app, host="0.0.0.0", port=8000),
        daemon=True
    )
    backend_thread.start()
    
    # Wait for backend to be ready
    if wait_for_backend():
        # Run frontend
        streamlit_process = run_streamlit()
        if streamlit_process:
            try:
                # Wait for Streamlit process to finish
                streamlit_process.wait()
            except KeyboardInterrupt:
                logger.info("👋 Shutting down application...")
                streamlit_process.terminate()
    else:
        logger.error("❌ Failed to start application")
        sys.exit(1) 