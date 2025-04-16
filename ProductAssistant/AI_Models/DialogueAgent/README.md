# Dialogue Agent

This is the Dialogue Agent of our multi-agent AI system. It:
- Classifies user needs
- Asks follow-up questions
- Knows about other agents like the Recommendation Agent
- Returns the specific needs


## Requirements:
- Python 3.10+
- [Ollama](https://ollama.com) installed and running locally

## Run Locally in virtual environment
```bash
source venv/bin/activate
pip install -r requirements.txt
python3 app.py