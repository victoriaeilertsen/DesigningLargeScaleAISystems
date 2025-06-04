import os
from dotenv import load_dotenv
import logging
from langchain_community.chat_models import ChatPerplexity
from langchain.schema import HumanMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
import traceback
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShoppingAgent:
    def __init__(self):
        load_dotenv()
        self._load_prompt()
        self._initialize_chain()
    
    def _load_prompt(self):
        """Load the system prompt from prompt.txt"""
        try:
            with open("agents/shopping/prompt.txt", "r", encoding="utf-8") as f:
                self.system_prompt = f.read()
            logger.info("Successfully loaded prompt.txt")
        except Exception as e:
            logger.error(f"Failed to load prompt.txt: {str(e)}")
            raise
    
    def _initialize_chain(self):
        """Initialize LangChain components"""
        try:
            # Initialize Perplexity chat model
            perplexity_api_key = os.getenv("PPLX_API_KEY")
            if not perplexity_api_key:
                raise ValueError("PPLX_API_KEY not found in .env file")
            
            self.chat_model = ChatPerplexity(
                model="sonar",
                temperature=0.7,
                pplx_api_key=perplexity_api_key
            )
            
            # Initialize memory
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            
            # Create prompt template
            self.prompt = PromptTemplate(
                input_variables=["chat_history", "human_input"],
                template=f"""
                {self.system_prompt}
                
                Previous conversation:
                {{chat_history}}
                
                Human: {{human_input}}
                Assistant:"""
            )
            
            # Initialize conversation chain
            self.conversation = ConversationChain(
                llm=self.chat_model,
                memory=self.memory,
                prompt=self.prompt,
                input_key="human_input",
                verbose=True
            )
            
            logger.info("Successfully initialized LangChain components")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangChain: {str(e)}")
            raise
    
    def _extract_requirements(self, message: str) -> dict:
        """Extract key requirements from the message"""
        requirements = {
            "product_type": None,
            "budget": None,
            "usage": None,
            "specific_requirements": []
        }
        
        # Extract budget
        budget_match = re.search(r"max\s*(\d+)\s*(?:euro|€|EUR)", message.lower())
        if budget_match:
            requirements["budget"] = int(budget_match.group(1))
        
        # Extract product type
        product_types = ["bike", "bicycle", "tablegame", "book", "laptop"]
        for product_type in product_types:
            if product_type in message.lower():
                requirements["product_type"] = product_type
                break
        
        # Extract usage
        usage_patterns = {
            "city": ["city", "urban", "commuting"],
            "mountain": ["mountain", "off-road", "trail"],
            "road": ["road", "racing", "speed"]
        }
        
        for usage, patterns in usage_patterns.items():
            if any(pattern in message.lower() for pattern in patterns):
                requirements["usage"] = usage
                break
        
        return requirements
    
    def process_message(self, message: str) -> str:
        """
        Process the user message and return a response
        
        Args:
            message (str): The user's message
            
        Returns:
            str: The agent's response
        """
        try:
            logger.info(f"Processing message: {message}")
            
            # Extract requirements
            requirements = self._extract_requirements(message)
            logger.info(f"Extracted requirements: {requirements}")
            
            # Add requirements to the message if they're not already present
            if "Summary of requirements:" not in message:
                message = f"Summary of requirements:\n" + \
                         f"* Product type: {requirements['product_type'] or 'Unspecified'}\n" + \
                         f"* Budget: €{requirements['budget'] or 'Unspecified'}\n" + \
                         f"* Usage: {requirements['usage'] or 'Unspecified'}\n" + \
                         f"* Specific requirements: {'None specified' if not requirements['specific_requirements'] else ', '.join(requirements['specific_requirements'])}\n\n" + \
                         f"---SUMMARY---\n\n" + message
            
            # Process message through LangChain
            response = self.conversation.predict(human_input=message)
            logger.info(f"Received response from Perplexity API: {response}")
            return response
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            logger.error("Full traceback:")
            logger.error(traceback.format_exc())
            raise 