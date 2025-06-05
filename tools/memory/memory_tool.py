from typing import List
import json
import google.generativeai as genai
import os
from datetime import datetime
import logging
from dotenv import load_dotenv
load_dotenv()


# Konfigurer logging (f.eks. til konsoll)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemorySummarizer:
    def __init__(self, save_path: str = "conversation_memory.json", prompt_path: str = None):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.save_path = save_path

        # Sett riktig prompt-sti basert på hvor denne filen ligger
        if prompt_path is None:
            self.prompt_path = os.path.join(os.path.dirname(__file__), "prompt.txt")
        else:
            self.prompt_path = prompt_path
            
    def summarize_conversation(self, conversation: List[dict]) -> str:
        formatted = "\n".join(
            [f"{turn['role'].capitalize()}: {turn['content']}" for turn in conversation]
        )

        try:
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
            logger.info(f"Successfully loaded prompt from {self.prompt_path}")
        except Exception as e:
            logger.error(f"Failed to load prompt from {self.prompt_path}: {e}")
            raise RuntimeError(f"Could not load prompt file: {e}")

        prompt = system_prompt.replace("{{conversation}}", formatted)

        try:
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            logger.info("Successfully generated memory summary")
            return result
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise RuntimeError(f"LLM generation failed: {e}")

    def save_memory(self, memory_summary: str):
        memory_record = {
            "summary": memory_summary,
            "timestamp": datetime.now().isoformat()
        }

        try:
            with open(self.save_path, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        data.append(memory_record)

        try:
            with open(self.save_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved memory to {self.save_path}")
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
            raise RuntimeError(f"Could not write to memory file: {e}")

    def process_and_save(self, conversation: List[dict]):
        summary = self.summarize_conversation(conversation)
        self.save_memory(summary)
        return summary

    def load_latest_memory(self) -> str:
        """
        Loads the most recent memory summary from the save file.
        Returns an empty string if no memory is found.
        """
        try:
            with open(self.save_path, "r") as f:
                data = json.load(f)
                if data:
                    latest = data[-1]
                    logger.info("Loaded latest memory summary")
                    return latest["summary"]
                else:
                    logger.info("Memory file is empty")
                    return ""
        except FileNotFoundError:
            logger.warning(f"No memory file found at {self.save_path}")
            return ""
        except Exception as e:
            logger.error(f"Failed to load memory file: {e}")
            raise RuntimeError(f"Could not read memory file: {e}")
