import httpx
import asyncio
from fastapi import FastAPI, Response
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows your Netlify URL to connect
    allow_credentials=False,
    allow_methods=["*"],  # Resolves the 405 OPTIONS error
    allow_headers=["*"],
)

@app.post("/")
def health_responder():
    return {"response":"Healthy"}

class Input(BaseModel):
    model: str
    temperature: float = 0.5
    prompt: str
    change: bool = True
    Models: Optional[list] = None


@app.post("/connector")
async def connector_load_balancer(inputs:Input):
    load_balancer_uri = "https://npmaiecosystem-loadbalancer.hf.space/load_balancer"
    load_balancer_fall_uri = "https://npmaiecosystem-loadbalancerfallback.hf.space/load_balancer"

    payload = {
        "model":inputs.model,
        "temperature":inputs.temperature,
        "prompt":inputs.prompt,
        "change":True,
        "Models":inputs.Models
    }

    timeout = httpx.Timeout(connect=100.0, read=560.0, write=300.0, pool=320.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(load_balancer_uri, json=payload)
            response.raise_for_status()
            f_response = response.json()["response"]
            return {"response":f_response}
            
    except Exception as e:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(load_balancer_fall_uri, json=payload)
            response.raise_for_status()
            f_response_f = response.json()["response"]
            return {"response":f_response_f}
