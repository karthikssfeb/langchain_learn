from typing import Optional, List, Dict
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date
import json, os
import uvicorn
from langchain_community.llms import Ollama

app = FastAPI()

folder_path = "db"

cached_llm = Ollama(model="llama2")

class Query(BaseModel):
    text: str

@app.post("/ai")
def ai_post(query: Query):

    print("query is ", query)
    response = cached_llm.invoke(query.text)
    print (response)
    return {"llm_response": response}

def serve_chain_api():
    uvicorn.run(app, host='0.0.0.0', port=5000 )

if __name__ == "__main__":
    # Serve the app with uvicorn
    serve_chain_api()