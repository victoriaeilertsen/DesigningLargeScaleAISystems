import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging
import time
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
model = None

def print_separator():
    print("\n" + "=" * 50)

def print_status(message):
    print(f"\n🔄 {message}")

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

def main():
    global model
    print_separator()
    print("🚀 Starting Shopping Assistant System")
    print_separator()
    
    # Load API keys
    print_status("Loading API configuration...")
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
    
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file")
    if not perplexity_api_key:
        raise ValueError("PERPLEXITY_API_KEY not found in .env file")
    
    print("✅ API configuration loaded successfully")
    
    # Initialize Gemini
    print_status("Initializing AI model...")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ AI model initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing AI model: {str(e)}")
        return
    
    print_separator()
    print("✨ System is ready!")
    print("\nYou can now chat with me about:")
    print("  • Your needs and requirements")
    print("  • Product recommendations (with real-time internet search)")
    print("\nType 'exit' to quit")
    print_separator()
    
    while True:
        message = input("\nYou: ")
        if message.lower() == 'exit':
            print("\n👋 Goodbye!")
            break
        
        logger.info(f"📥 Received message: {message}")
        
        # Analyze message type
        message_type = analyze_message(message)
        
        # Get appropriate response
        if message_type == 'needs':
            logger.info("🎯 Routing to Needs Analyzer")
            response = get_needs_analyzer_response(message)
            print(f"\nNeeds Analyzer:", response)
        else:
            logger.info("🎯 Routing to Shopping Assistant")
            response = get_shopping_assistant_response(message)
            print(f"\nShopping Assistant:", response)
        
        print("-" * 50)

if __name__ == "__main__":
    main() 