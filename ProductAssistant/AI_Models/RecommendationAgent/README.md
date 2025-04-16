# Recommender Agent

This is the Recommender Agent of our multi-agent AI system. It:

- Gives a reccomendation on where to buy/rent a product. 
- Provides **pros and cons** comparisons for product or experience options.
- **Forecasts trends** and evaluates future suitability of recommendations.
- Tailors responses using:
  - Previous user interactions
  - Personal traits
  - Re-ranking of options

## Requirements:
- Python 3.10+
- [Ollama](https://ollama.com) installed and running locally

## Run Locally in virtual environment
```bash
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
