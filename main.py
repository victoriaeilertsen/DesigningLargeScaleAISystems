import subprocess
import sys
import os
import time
import logging
import requests
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_server(url: str, max_attempts: int = 3, delay: int = 2) -> bool:
    """Wait for server to be ready."""
    for attempt in range(max_attempts):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                logger.info(f"Server at {url} is ready")
                return True
        except requests.exceptions.ConnectionError:
            pass
        logger.info(f"Waiting for server at {url}... (attempt {attempt + 1}/{max_attempts})")
        time.sleep(delay)
    return False

def run_agent_server(path, name, port):
    try:
        logger.info(f"Starting {name} server...")
        subprocess.Popen([sys.executable, os.path.abspath(path)], cwd=os.path.abspath("."))
        return wait_for_server(f"http://localhost:{port}")
    except Exception as e:
        logger.error(f"Failed to start {name} server: {e}")
        return False

def run_frontend():
    try:
        print("=== [DEBUG] run_frontend STARTED ===", flush=True)
        logger.info("Starting frontend...")
        os.chdir("frontend")
        print("=== [DEBUG] Changed directory to frontend ===", flush=True)
        subprocess.run(["streamlit", "run", "src/App.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Frontend failed to start: {e}")
        sys.exit(1)

def main():
    print("=== [DEBUG] main STARTED ===", flush=True)
    
    # Start all agent servers in parallel
    servers = [
        ("agents/orchestrator/server.py", "Orchestrator", 8000),
        ("agents/shopping/server.py", "Shopping", 8002),
        ("agents/classifier/server.py", "Classifier", 8001)
    ]
    
    # Start all servers
    server_processes = []
    for path, name, port in servers:
        logger.info(f"Starting {name} server...")
        process = subprocess.Popen([sys.executable, os.path.abspath(path)], cwd=os.path.abspath("."))
        server_processes.append((process, name, port))
    
    # Wait for all servers to be ready
    all_ready = True
    for process, name, port in server_processes:
        if not wait_for_server(f"http://localhost:{port}"):
            logger.error(f"{name} server failed to start")
            all_ready = False
            break
    
    if not all_ready:
        logger.error("Some servers failed to start. Exiting...")
        sys.exit(1)
    
    # Start frontend
    run_frontend()

if __name__ == "__main__":
    main()
