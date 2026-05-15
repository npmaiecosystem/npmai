"""This space is of NPM-Journalist space there this model is deployed because NPM-Journalist work is not so heavy or time taking
that can affect llm so we deployed a LLM also there here code will only of LLM but on hf space full code is available"""
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from supabase import create_client, Client
from supabase.client import ClientOptions
from pydantic import BaseModel 
from tavily import TavilyClient 
from datetime import date 
from langchain_ollama.llms import OllamaLLM 
import requests
import json
import uuid
import math
import os

#FastAPI Initialistaion


app = FastAPI()

class PromptRequest(BaseModel): 
    prompt: str 
    temperature: float = 0.5 
    

today_date = date.today() 

def search_tool(query:str): 
    api_key= os.environ.get("TAVILY_API_KEY") 
    client = TavilyClient(api_key) 
    response = client.search( query=query, include_answer="advanced", search_depth="advanced" ) 
    return response 
    
@app.post("/llm_fall_llama") 
async def qwen_generate_response(request:PromptRequest): 
    llm = OllamaLLM( 
        model="llama3.2", 
        temperature=request.temperature, 
        base_url="http://localhost:11434" 
    ) 
    tool_prompt = f""" System Role: You are an autonomous AI Agent with real-time internet access. Current Date: {today_date} TOOL_DEFINITION: - Name: Search_tool - Activation Command: Search [Your Query Here] - Use Case: Use ONLY when you lack specific facts, need the latest 2026 data, or your training data is outdated. STRICT OUTPUT RULES: 1. To use the tool: Your entire response must start with the word "Search" followed by your query. Example: Search Who is the current Prime Minister of India? 2. To answer normally: If you already have the information, provide a direct answer. 3. DO NOT use the word "Search" at the beginning of your response unless you are calling the tool. 4. DO NOT use brackets or quotes in the tool call. """ 
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
