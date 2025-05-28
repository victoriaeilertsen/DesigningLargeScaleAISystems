import subprocess
import sys
import os
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_agent_server(path, name):
    try:
        logger.info(f"Starting {name} server...")
        subprocess.Popen([sys.executable, os.path.abspath(path)], cwd=os.path.abspath("."))
    except Exception as e:
        logger.error(f"Failed to start {name} server: {e}")

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
    # Start all agent servers
    run_agent_server("agents/orchestrator/server.py", "Orchestrator")
    run_agent_server("agents/shopping/server.py", "Shopping")
    run_agent_server("agents/classifier/server.py", "Classifier")

    # Wait for servers to start
    logger.info("Waiting for agent servers to initialize...")
    time.sleep(3)

    # Start frontend
    run_frontend()

if __name__ == "__main__":
    main()
