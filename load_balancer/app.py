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


""" Endpoint stats:-
1.Public endpoints:- 55 Endpoints are public,
These endpoints (2,3,4) is handled by people who handle endpoints by themselves and load_balancer at Alibaba Cloud automatically
handle these as PUBLIC CANNOT USE THESE (2,3,4) ENDPOINTS DIRECTLY.
2.Private endpoints:- 47 Endpoints are those endpoints which is contributed by some teams or oganisation who do not want to 
allow 
the use of their compute to everyone they allow to some specific clients but maintained and powered by 
NPMAI ECOSYSTEM(NPMAI LLM)
3.Emergency Priority Fallback endpoints:- 26 Endpoints fall in this category where if all 22 and 4th category endpoints are 
busy then our
load_balancer stop serving new users and start prioritizing those requests from organisations who had contributed in NPMAI ECOSYSTEM or helped
NPMAI ECOSYSTEM.
4.Emergency General Endpoints:- 6 Endpoints are those endpoints where main models like llama3.2,qwen2.5-coder:7b,vicuna:7b,
for emergency we keep a loaded copy wheneever Public Endpoints fail by an error in server,code, or any other condition except
all 55 Endpoints are busy in such condition we open 6 Endpoints which is higly capable to handle around 4000 requests per 60 Minute
this is hosted by Vicent our npmai Backend Head who works in alibaba, he hosted these models on his Alibaba Cloud accounts these are
for public but not public endpoints these are private by Vincent but whenever a emergency occurs we open these endpoints.
"""

""" IF Anyone Wants to contribute their compute:-
1.Please first contact us on sonuramashishnpm@gmail.com before raising any PR or Issue related to Compute Contribution.
2.What to write in email :-
  a) Write in which category you want to contribute Public,Private,Priority Emergency, Public Emergency (this is in same order as in Endpoint stats)
  b) If you had developed your own code and hosted models as per your choice so send the code either by github or generally we prefer
      Private Huggingface Accounts.
  c) If you just want to contribute compute and want that we(NPMAI ECOSYSTEM should use as we want then just send you account data
     like Usage, current_plan, current_status, and other things as per asked by our team after you drop your first mail, after we review
     and understand and if we accept your contribution then give us a access token (if You are contributing Huggingface Accounts) otherwise
     whatever platform compute you are offering send us the access key or token as per platform so that we can manage the compute.
  d) Ensure you give us at least Hugginface Account links so that we can connect with you easily.
  e) Ensure you do not publicly release any contribution update before we deploy and test the idea or product.
3.Do not share account if you think you can cancel the link very quickly becuase every endpoint is important for us as we are handling
  massive userbase.
4.After having a deal if we deploy something you do not have to change without asking NPMAI ECOSYSTEM core team and remember do not
  log anything in any way.
"""
Model_links = {
    "llama3.2": "https://galactromedaNPMAIECOSYSTEM-model23.hf.space/llama3.2", #https://sonuramashishnpm-npmai.hf.space/llama
    "qwen2.5-coder:7b":"https://galactromedaNPMAIECOSYSTEM-model24.hf.space/qwen2.5-coder:7b", #https://sonuramashishnpm-npmai.hf.space/qwen
    "vicuna:7b":"https://galactromedaNPMAIECOSYSTEM-model25.hf.space/vicuna:7b", #https://sonuramashish22028704-vicuna7b.hf.space/vicuna
    "internlm2:7b":"https://sonuramashish22028704-internlm27b.hf.space/internlm",
    "falcon:7b-instruct":"https://sonuramashish22028704-falcon7binstruct.hf.space/falcon",
    "codellama:7b-instruct":"https://sonuramashish22028704-falcon7binstruct.hf.space/codellama",
    "mistral:7b":"https://sonuramashish22028704-mistral7b.hf.space/mistral",
    "phi3:medium":"https://sonuramashish22028704-phi3medium.hf.space/phi3medium",
    "qwen3.5:9b":"https://sonuramashish22028704-vicuna7b.hf.space/qwen359gb",
    "gemma2:9b":"https://sonuramashish22028704-internlm27b.hf.space/gemma29b",
    "llama3.2:3b":"https://npmaiecosystem-model5.hf.space/llama3.2:3b",
    "llama3.1:8b":"https://npmaiecosystem-model5.hf.space/llama3.1:8b",
    "qwen2.5:7b":"https://npmaiecosystem-model6.hf.space/qwen2.5:7b",
    "llama3.2:1b":"https://npmaiecosystem-model6.hf.space/llama3.2:1b",
    "qwen2-math:7b":"https://npmaiecosystem-model7.hf.space/qwen2-math:7b",
    "qwen2.5vl":"https://npmaiecosystem-model7.hf.space/qwen2.5vl",
    "phi3:3.8b":"https://sonuramashishnpmai-model8.hf.space/phi3:3.8b",
    "llava-phi3":"https://sonuramashishnpmai-model8.hf.space/llava-phi3",
    "gemma2:2b":"https://sonuramashishnpmai-model9.hf.space/gemma2:2b",
    "openhermes":"https://sonuramashishnpmai-model9.hf.space/openhermes",
    "deepseek-coder:6.7b":"https://sonuramashishnpmai-model10.hf.space/deepseek-coder:6.7b",
    "yi":"https://sonuramashishnpmai-model10.hf.space/yi",
    "granite3.3:2b":"https://sonuramashishnpmai-model12.hf.space/granite3.3:2b",
    "smollm:1.7b":"https://sonuramashishnpmai-model12.hf.space/smollm:1.7b",
    "stablelm2":"https://sonuramashishnpmai-model13.hf.space/stablelm2",
    "cniongolo_biomistral":"https://sonuramashishnpm-model13.hf.space/cniongolo_biomistral",
    "meditron":"https://KarachiUniNPMAIECOSYSTEM-model14.hf.space/meditron",
    "granite4.1:3b":"https://karachiuninpmaiecosystem-model14.hf.space/granite4.1:3b",
    "wizard-math":"https://karachiuninpmaiecosystem-model15.hf.space/wizard-math",
    "llava":"https://karachiuninpmaiecosystem-model15.hf.space/llava",
    "moondream":"https://karachiuninpmaiecosystem-model16.hf.space/moondream",
    "openchat":"https://karachiuninpmaiecosystem-model16.hf.space/openchat",
    "deepseek-r1:7b":"https://karachiuninpmaiecosystem-model17.hf.space/deepseek-r1:7b",
    "openbmb_minicpm-v2.6":"https://karachiuninpmaiecosystem-model17.hf.space/openbmb_minicpm-v2.6",
    "llama3:8b":"https://karachiuninpmaiecosystem-model18.hf.space/llama3:8b",
    "gemma3:4b":"https://karachiuninpmaiecosystem-model18.hf.space/gemma3:4b",
    "olmo2":"https://karachiuninpmaiecosystem-model19.hf.space/olmo2",
    "nemotron-mini":"https://karachiuninpmaiecosystem-model19.hf.space/nemotron-mini",
    "stable-code":"https://galactromedanpmaiecosystem-model20.hf.space/stable-code",
    "codellama:7b":"https://galactromedanpmaiecosystem-model20.hf.space/codellama:7b",
    "aya:8b":"https://galactromedanpmaiecosystem-model21.hf.space/aya:8b",
    "phi4:14b":"https://galactromedanpmaiecosystem-model20.hf.space/phi4:14b",
    "gemma4:e2b":"https://galactromedanpmaiecosystem-model22.hf.space/gemma4:e2b",
    "qwen3.5:2b":"https://galactromedanpmaiecosystem-model22.hf.space/qwen3.5:2b",
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
    "gemma2:9b_fall":"https://sonuramashishnpm-model3.hf.space/llm_fall_gemma29b",
    "gemma3:12b":"https://npmaiecosystem-gemma312b.hf.space/gemma312b"
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
        raise HTTPException(status_code=404, detail="Model not found.")

    model_link = Model_links[inputs.model]
    fall_links = []

    fall_models = inputs.Models
    if inputs.change and fall_models:
        for m in fall_models:
            model_name_fall = f"{m}_fall"
            if model_name_fall in Model_links:
                fall_links.append(Model_links[model_name_fall])
            elif m in Model_links:
                fall_links.append(Model_links[m])
            else:
                raise HTTPException(status_code=400, detail=f"Fallback model '{m}' not found in Models Dictionary.")

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
