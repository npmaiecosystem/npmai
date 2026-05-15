from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Annotated, Any, Optional
import asyncio
from redis.asyncio import Redis
import httpx
import os

app = FastAPI()

@app.post("/")
def health_check():
    return "Healthy"

password = os.environ.get("PASSWORD")
r = Redis(
    host='redis-15562.c1.us-west-2-2.ec2.cloud.redislabs.com',
    port=15562,
    decode_responses=True,
    username="default",
    password=password,
)



Model_links = {
    "llama3.2": "https://sonuramashishnpm-npmai.hf.space/llama",
    "qwen2.5-coder:7b":"https://sonuramashishnpm-npmai.hf.space/qwen",
    "vicuna:7b":"https://sonuramashish22028704-vicuna7b.hf.space/vicuna",
    "gemma3:12b":"https://npmaiecosystem-gemma312b.hf.space/gemma312b",
    "internlm2:7b":"https://sonuramashish22028704-internlm27b.hf.space/internlm",
    "falcon:7b-instruct":"https://sonuramashish22028704-falcon7binstruct.hf.space/falcon",
    "codellama:7b-instruct":"https://sonuramashish22028704-falcon7binstruct.hf.space/codellama",
    "mistral:7b":"https://sonuramashish22028704-mistral7b.hf.space/mistral",
    "phi3:medium":"https://sonuramashish22028704-phi3medium.hf.space/phi3medium",
    "qwen3.5:9b":"https://sonuramashish22028704-vicuna7b.hf.space/qwen359gb",
    "gemma2:9b":"https://sonuramashish22028704-internlm27b.hf.space/gemma29b",
    "llama3.2_fall":"https://sonuramashishnpm-npm-journalist.hf.space/llm_fall_llama",
    "qwen2.5-coder:7b_fall":"https://sonuramashish22028704-mistral7b.hf.space/llm_fall_qwen2",
    "vicuna:7b_fall":"https://sonuramashishnpm-model4.hf.space/llm_fall_vicuna",
    "gemma3:12b_fall":"https://npmaiecosystem-gemma312b_fall.hf.space/llm_fall_gemma312b",
    "internlm2:7b_fall":"https://sonuramashishnpm-model2.hf.space/llm_fall_interlm",
    "falcon:7b-instruct_fall":"https://sonuramashishnpm-model1.hf.space/llm_fall_falcon",
    "codellama:7b-instruct_fall":"https://sonuramashishnpm-model3.hf.space/llm_fall_codellama",
    "mistral:7b_fall":"https://sonuramashishnpm-model2.hf.space/fall_llm_mistral",
    "phi3:medium_fall":"https://sonuramashishnpm-model1.hf.space/llama_fall_phi",
    "qwen3.5:9b_fall":"https://sonuramashishnpm-model4.hf.space/llm_fall_qwen359gb",
    "gemma2:9b_fall":"https://sonuramashishnpm-model3.hf.space/llm_fall_gemma29b"
}

# Updated Lua Script
LUA_CHECK_AND_INC = """
local key = KEYS[1]
local status = tonumber(redis.call('HGET', key, 'status') or '0')
if status < 1 then
    redis.call('HSET', key, 'status', status + 1)
    return status
end
return -1
"""

LUA_REMOVAL_STATUS = """
local key = KEYS[1]
local status = tonumber(redis.call('HGET', key, 'status') or '0')
if status > 0 then
    redis.call('HSET', key, 'status', status -1)
    return status -1
end
return 0
"""

async def check_cond(model_link: str, fall_model: Optional[list] = None):
    status = await r.eval(LUA_CHECK_AND_INC, 1, model_link)
    if status != -1:
        return {"link": model_link, "statusno": status}

    if fall_model:
        for model in fall_model:
            status = await r.eval(LUA_CHECK_AND_INC, 1, model)
            if status != -1:
                return {"link": model, "statusno": status}
                
    else:
        for model in Model_links.values():
            status = await r.eval(LUA_CHECK_AND_INC, 1, model)
            if status != -1:
                return {"link": model, "statusno": status}

    return None


class Input(BaseModel):
    model: str
    temperature: float = 0.5
    prompt: str
    change: bool = True
    Models: Optional[list] = None

@app.post("/load_balancer")
async def llm_router(inputs: Input):
    if not inputs.model or not inputs.prompt:
        raise HTTPException(status_code=400, detail="Model name and Prompt are required.")

    if inputs.model not in Model_links:
        raise HTTPException(status_code=444, detail="Model not found.")

    model_link = Model_links[inputs.model]
    fall_links = []

    fall_models = inputs.Models
    if inputs.change and fall_models:
        for m in fall_models:
            model_name = f"{m}_fall"
            if model_name in Model_links.keys():
                link = Model_links[model_name]
                fall_links.append(link)
            else:
                raise HTTPException(status_code=402, detail="Fallback models are not found in Models Dictionary")

    model_cond = await check_cond(model_link=model_link, fall_model=fall_links)
    
    if model_cond and model_cond.get("link") and model_cond.get("statusno") is not None:
        return await router(
            model_url=model_cond["link"],
            prompt=inputs.prompt,
            temp=inputs.temperature
        )
    else:
        raise HTTPException(status_code=503, detail="All model endpoints and fallbacks are busy.")

async def router(model_url, prompt, temp):
    error_log = ""
    process= ""
    payload = {"prompt": prompt, "temperature": temp}
    timeout = httpx.Timeout(connect=30.0, read=360.0, write=30.0, pool=120.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(model_url, json=payload)
            response.raise_for_status()
            f_response = response.json()["response"]
            if f_response is not None and str(f_response).strip() != "":
                process += f_response

            else:
                raise ValueError("Empty string or None returned in response from LLM")
    except Exception as e:
        error_log += f"LLM backend error: {str(e)}"

    finally:
        await r.eval(LUA_REMOVAL_STATUS, 1, model_url)

    if error_log:
        raise HTTPException(status_code=502, detail=error_log)
    else:
        return {"response": process}
