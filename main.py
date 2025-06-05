import os
import logging
import time
import requests
import subprocess
import sys
import threading
from pathlib import Path
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

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
backend_ready = False
AGENT_PORTS = {
    "orchestrator": 8000,
    "classifier": 8001,
    "shopping": 8002
}

def wait_for_agent(port: int, max_retries: int = 30, retry_delay: int = 1) -> bool:
    """Wait until specific agent is ready"""
    for i in range(max_retries):
        try:
            response = requests.get(f"http://localhost:{port}/docs")
            if response.status_code == 200:
                logger.info(f"✅ Agent on port {port} is ready!")
                return True
        except requests.exceptions.ConnectionError:
            logger.info(f"⌛ Waiting for agent on port {port}... (attempt {i+1}/{max_retries})")
            time.sleep(retry_delay)
    
    logger.error(f"❌ Agent on port {port} failed to start in expected time")
    return False

def run_agent(agent_name: str, port: int) -> subprocess.Popen:
    """Run specific agent in a separate process"""
    try:
        # Path to agent's server.py
        server_path = Path(__file__).parent / "agents" / agent_name / "server.py"
        
        # Run agent with output redirection
        agent_process = subprocess.Popen(
            [sys.executable, str(server_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Print agent output
        def print_output(pipe, prefix):
            for line in pipe:
                logger.info(f"{prefix}: {line.strip()}")
        
        # Start threads for logging
        stdout_thread = threading.Thread(target=print_output, args=(agent_process.stdout, f"{agent_name.upper()}"))
        stderr_thread = threading.Thread(target=print_output, args=(agent_process.stderr, f"{agent_name.upper()}-ERROR"))
        stdout_thread.daemon = True
        stderr_thread.daemon = True
        stdout_thread.start()
        stderr_thread.start()
        
        logger.info(f"🚀 {agent_name.capitalize()} agent started")
        return agent_process
    except Exception as e:
        logger.error(f"❌ Error starting {agent_name} agent: {str(e)}")
        return None

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

@app.on_event("startup")
async def startup_event():
    """Initialize the API on startup"""
    global backend_ready
    logger.info("🚀 Starting Shopping Assistant API")
    
    # Load environment variables
    if not os.path.exists(".env"):
        raise ValueError("❌ .env file not found")
    
    logger.info("✅ Environment configuration loaded successfully")
    backend_ready = True

@app.post("/chat")
async def chat(message: Message):
    """Handle chat messages by forwarding to orchestrator"""
    try:
        logger.info(f"📥 Received message: {message.content}")
        
        # Forward message to orchestrator
        response = requests.post(
            f"http://localhost:{AGENT_PORTS['orchestrator']}/chat",
            json={"content": message.content},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail="Error from orchestrator")
            
    except Exception as e:
        logger.error(f"❌ Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Start all agents
    agent_processes = {}
    for agent_name, port in AGENT_PORTS.items():
        agent_process = run_agent(agent_name, port)
        if agent_process:
            agent_processes[agent_name] = agent_process
        else:
            logger.error(f"❌ Failed to start {agent_name} agent")
            sys.exit(1)
    
    # Wait for all agents to be ready
    all_ready = True
    for port in AGENT_PORTS.values():
        if not wait_for_agent(port):
            all_ready = False
            break
        
    if all_ready:
        # Run frontend
        streamlit_process = run_streamlit()
        if streamlit_process:
            try:
                # Wait for Streamlit process to finish
                streamlit_process.wait()
            except KeyboardInterrupt:
                logger.info("👋 Shutting down application...")
                # Terminate all processes
                streamlit_process.terminate()
                for process in agent_processes.values():
                    process.terminate()
        else:
            logger.error("❌ Failed to start all agents")
            # Terminate any started processes
            for process in agent_processes.values():
                process.terminate()
            sys.exit(1) 