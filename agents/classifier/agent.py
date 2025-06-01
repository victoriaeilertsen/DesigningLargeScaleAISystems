from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import os
from dotenv import load_dotenv
import traceback

load_dotenv()

# Gemini configuration
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

app = FastAPI(title="Formal Professional Agent")

class Message(BaseModel):
    content: str

@app.post("/chat")
async def chat(message: Message):
    try:
        with open("prompt.txt", "r", encoding="utf-8") as f:
            system_prompt = f.read()
        
        # Preparing Gemini context
        chat = model.start_chat(history=[])
        response = chat.send_message(f"{system_prompt}\n\nUser message: {message.content}")
        
        return {"response": response.text}
    except Exception as e:
        print(f"Error details: {str(e)}")
        print("Full traceback:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 