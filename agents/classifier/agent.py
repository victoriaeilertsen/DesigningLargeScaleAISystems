import os
from dotenv import load_dotenv
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClassifierAgent:
    def __init__(self):
        load_dotenv()
        self._load_prompt()
        self._initialize_chain()
    
    def _load_prompt(self):
        """Load the system prompt from prompt.txt"""
        try:
            with open("agents/classifier/prompt.txt", "r", encoding="utf-8") as f:
                self.system_prompt = f.read()
            logger.info("Successfully loaded prompt.txt")
        except Exception as e:
            logger.error(f"Failed to load prompt.txt: {str(e)}")
            raise
    
    def _initialize_chain(self):
        """Initialize LangChain components"""
        try:
            # Initialize Google Generative AI
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in .env file")
            
            self.chat_model = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=0.7,
                google_api_key=api_key
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
    
    def process_message(self, message: str) -> str:
        """
        Process the user message and return a response
        
        Args:
            message (str): The user's message
            
        Returns:
            str: The agent's response
        """
        try:
            # Process message through LangChain
            response = self.conversation.predict(human_input=message)
            return response
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise 