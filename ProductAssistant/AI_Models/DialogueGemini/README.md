# Dialogue Agent

This is the Dialogue Agent of our multi-agent AI system. It:
- Classifies user needs
- Asks follow-up questions
- Knows about other agents like the Recommendation Agent
- Returns the specific needs


## Requirements:
- Python 3.10+


## Run Locally in virtual environment
```bash
source venv/bin/activate
pip install -r requirements.txt
python3 grod_chatbot.py 
#or 
streamlit run groq_chatbot.py #for running the agent locally 