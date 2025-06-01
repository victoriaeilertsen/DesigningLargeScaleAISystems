import os
import requests
from dotenv import load_dotenv
import logging
import time
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrchestratorAgent:
    def __init__(self):
        load_dotenv()
        self._load_prompt()
        self._initialize_chain()
        
        # Agent configuration
        self.agents = {
            "classifier": {"port": 8001, "name": "Needs Analyzer"},
            "shopping": {"port": 8002, "name": "Shopping Assistant"}
        }
        
        # Timeout settings
        self.request_timeout = 10  # seconds
        self.max_retries = 2
    
    def _load_prompt(self):
        """Load the system prompt from prompt.txt"""
        try:
            with open("agents/orchestrator/prompt.txt", "r", encoding="utf-8") as f:
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
            
            # Create prompt template for agent selection
            self.agent_selection_prompt = PromptTemplate(
                input_variables=["chat_history", "human_input"],
                template=f"""
                {self.system_prompt}
                
                Previous conversation:
                {{chat_history}}
                
                Human: {{human_input}}
                
                Based on the conversation, determine which agent should handle this request.
                Respond with ONLY one word: 'classifier' or 'shopping'
                Assistant:"""
            )
            
            # Initialize agent selection chain
            self.agent_selection_chain = ConversationChain(
                llm=self.chat_model,
                memory=self.memory,
                prompt=self.agent_selection_prompt,
                input_key="human_input",
                verbose=True
            )
            
            logger.info("Successfully initialized LangChain components")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangChain: {str(e)}")
            raise
    
    def _get_agent_response(self, port: int, message: str) -> str:
        """
        Get response from a specific agent
        
        Args:
            port (int): The port number of the agent
            message (str): The message to send
            
        Returns:
            str: The agent's response
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Sending message to agent on port {port} (attempt {attempt + 1}/{self.max_retries})")
                start_time = time.time()
                
                response = requests.post(
                    f"http://localhost:{port}/chat",
                    json={"content": message},
                    timeout=self.request_timeout
                )
                
                elapsed_time = time.time() - start_time
                logger.info(f"Response received in {elapsed_time:.2f} seconds")
                
                if response.status_code == 200:
                    logger.info(f"Received response from agent on port {port}")
                    return response.json()["response"]
                else:
                    error_msg = f"Agent communication error: {response.status_code}"
                    logger.error(error_msg)
                    if attempt < self.max_retries - 1:
                        time.sleep(1)
                        continue
                    return error_msg
                    
            except requests.Timeout:
                logger.error(f"Timeout while waiting for agent on port {port}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue
                return "Agent response timeout. Please try again."
                
            except Exception as e:
                error_msg = f"Agent connection error: {str(e)}"
                logger.error(error_msg)
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue
                return error_msg
        
        return "Failed to get response from agent after multiple attempts."
    
    def process_message(self, message: str) -> Dict[str, Any]:
        """
        Process the user message and route it to appropriate agent
        
        Args:
            message (str): The user's message
            
        Returns:
            Dict[str, Any]: Response containing the selected agent and its response
        """
        try:
            # For initial testing, return a simple response
            if message.lower() in ["hello", "hi", "hey"]:
                return {
                    "agent": "orchestrator",
                    "response": "Hello! I'm your shopping assistant. How can I help you today?"
                }
            
            # Use LangChain to determine which agent should handle the message
            agent_choice = self.agent_selection_chain.predict(human_input=message).strip().lower()
            logger.info(f"Selected agent: {agent_choice}")
            
            if agent_choice == "classifier":
                logger.info("Routing to Needs Analyzer")
                agent_response = self._get_agent_response(
                    self.agents["classifier"]["port"], 
                    message
                )
                return {
                    "agent": self.agents["classifier"]["name"],
                    "response": agent_response
                }
            elif agent_choice == "shopping":
                logger.info("Routing to Shopping Assistant")
                agent_response = self._get_agent_response(
                    self.agents["shopping"]["port"], 
                    message
                )
                return {
                    "agent": self.agents["shopping"]["name"],
                    "response": agent_response
                }
            else:
                logger.warning("Could not determine appropriate agent")
                return {
                    "agent": "orchestrator",
                    "response": "I cannot determine which agent should handle this request. Please try rephrasing."
                }
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise 