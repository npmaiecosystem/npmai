from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date
from fastapi.responses import StreamingResponse
from langchain_ollama.llms import OllamaLLM
from tavily import TavilyClient
import os

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str
    temperature: float = 0.7

@app.get("/")
def health():
    return {"ok": True}

today_date = date.today()

def search_tool(query:str):
    api_key= os.environ.get("TAVILY_API_KEY")
    client = TavilyClient(api_key)
    response = client.search(
        query=query,
        include_answer="advanced",
        search_depth="advanced"
    )
    return response

@app.post("/llm_fall_codellama")
async def generate_response(request: PromptRequest):
    llm = OllamaLLM(
        model="codellama:7b-instruct",
        temperature=request.temperature,
        base_url="http://localhost:11435"
    )

    tool_prompt = f"""
    System Role: You are an autonomous AI Agent with real-time internet access.
    Current Date: {today_date}
    
    TOOL_DEFINITION:
    - Name: Search_tool
    - Activation Command: Search [Your Query Here]
    - Use Case: Use ONLY when you lack specific facts, need the latest 2026 data, or your training data is outdated.
    
    STRICT OUTPUT RULES:
    1. To use the tool: Your entire response must start with the word "Search" followed by your query. 
    Example: Search Who is the current Prime Minister of India?
    2. To answer normally: If you already have the information, provide a direct answer. 
    3. DO NOT use the word "Search" at the beginning of your response unless you are calling the tool.
    4. DO NOT use brackets or quotes in the tool call.
    """
    response = llm.invoke(f'{tool_prompt}, User-Query:-{request.prompt}')
    print("RESPONSE")
    print(response)
    if "Search " in response:
        new_query = response.removeprefix("Search ")
        print("NEW_QUERY")
        print(new_query)
        search_response = search_tool(query=new_query)
        print("SEARCH_RESPONSE")
        print(search_response)
        new_response = llm.invoke(f"Extra_information:- {search_response} User-Query:- {request.prompt}")
        return {"response": new_response}
    else:
        return {"response": response}

@app.post("/llm_fall_gemma29b")
async def generate_response(request: PromptRequest):
    llm = OllamaLLM(
        model="gemma2:9b",
        temperature=request.temperature,
        base_url="http://localhost:11436"
    )

    tool_prompt = f"""
    System Role: You are an autonomous AI Agent with real-time internet access.
    Current Date: {today_date}
    
    TOOL_DEFINITION:
    - Name: Search_tool
    - Activation Command: Search [Your Query Here]
    - Use Case: Use ONLY when you lack specific facts, need the latest 2026 data, or your training data is outdated.
    
    STRICT OUTPUT RULES:
    1. To use the tool: Your entire response must start with the word "Search" followed by your query. 
    Example: Search Who is the current Prime Minister of India?
    2. To answer normally: If you already have the information, provide a direct answer. 
    3. DO NOT use the word "Search" at the beginning of your response unless you are calling the tool.
    4. DO NOT use brackets or quotes in the tool call.
    """
    response = llm.invoke(f'{tool_prompt}, User-Query:-{request.prompt}')
    print("RESPONSE")
    print(response)
    if "Search " in response:
        new_query = response.removeprefix("Search ")
        print("NEW_QUERY")
        print(new_query)
        search_response = search_tool(query=new_query)
        print("SEARCH_RESPONSE")
        print(search_response)
        new_response = llm.invoke(f"Extra_information:- {search_response} User-Query:- {request.prompt}")
        return {"response": new_response}
    else:
        return {"response": response}
      
