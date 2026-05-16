from typing import Optional, List, Union, Iterator, Dict, Any
import requests
import json
import os

PromptType = Union[str, List[str], dict]

class Ollama():
    """
A resilient LLM provider for NPMAI providing access to 45+ Open Source models.

This class features a dual-gateway architecture:
1. Primary API: Attempts to process requests via https://npmai-api.onrender.com.
2. Failover System: Automonously switches to a fallback load balancer if the primary gateway fails.

Key Capabilities:
- High Availability: Automatic retry logic ensures minimal downtime.
- Model Variety: Supports Llama 3.2, Qwen 2.5, Vicuna, Gemma 2, InternLM2, Mistral, and more.
- Versatile Input: The 'invoke' method handles strings, lists, or dictionary prompts.

Parameters:
-----------
model : str, default="llama3.2"
    The specific identifier for your target model. For a complete list of valid model names
    and precise syntax, visit the official documentation at https://npmai.netlify.app.
temperature : float, default=0.3
    Controls the randomness and creativity of the generated response.
change : bool, default=True
    Enables automatic model fallback. If the requested model is busy or unresponsive, 
    the system automatically routes the request to an available model to prevent request failures.
Models : List[str], optional
    A custom list of backup model names used if `change=True`. If `change=True` and this list 
    is omitted, the system will dynamically loop through all 45+ available models to find an active server.

How to Use:
-----------
1. Basic String Query:
    >>> llm = Ollama(model="llama3.2", temperature=0.5)
    >>> response = llm.invoke("What is open source?")

2. With Failover Customization:
    >>> # If vicuna:7b is busy, it falls back to llama3.2 or gemma2
    >>> llm = Ollama(
    ...     model="vicuna:7b", 
    ...     change=True, 
    ...     Models=["llama3.2", "gemma2"]
    ... )
    >>> response = llm.invoke("Summarize quantum computing.")
"""

    def __init__(
        self, 
        model: str = "llama3.2", 
        temperature: float = 0.3, 
        change:bool = True, 
        Models:Optional[list]=None, 
        api: str = "https://npmaiecosystem-load_balancer.hf.space/load_balancer", 
        fallback_api: str = "https://npmaiecosystem-loadbalancerfallback.hf.space/load_balancer"
        ):
      self.model = model
      self.temperature = temperature
      self.change = change
      self.Models = Models
      self.api = api
      self.fallback_api = fallback_api


    @property
    def _llm_type(self) -> str:
        return "npmai"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        payload = {
            "prompt": prompt,
            "model": self.model,
            "temperature": self.temperature,
            "change":self.change,
            "Models":self.Models
        }

        fallback_payload ={
            "prompt":prompt,
            "temperature":self.temperature,
            "change":self.change,
            "model":self.model,
            "Models":self.Models
        }
        try:
            response = requests.post(self.api, json=payload)
            response.raise_for_status()
        except:
            response = requests.post(self.fallback_api, json=fallback_payload)
            response.raise_for_status()

        data=response.json()
        if "response" in data:
            return data["response"]
        return json.dumps(data)



    def invoke(self, prompt: PromptType):
        if isinstance(prompt, list):
            prompt = "\n".join(map(str, prompt))
        elif isinstance(prompt, dict):
            prompt = json.dumps(prompt)

        return self._call(prompt)

class Memory:
    """
    A lightweight persistent memory system for AI Agents to maintain conversation context.

    This class enables agents to remember past interactions by storing them in a local
    JSON-based file system. It is designed to be easily integrated into any workflow
    where long-term or session-based memory is required.

    Key Features:
    - Custom Persistence: Creates a unique .json file based on the provided user_custom_file name.
    - Context Management: save_context() appends new Human-AI interactions to the history.
    - History Retrieval: load_memory_variables() parses the stored data into a formatted
      string for easy injection into LLM prompts.
    - Fault Tolerance: Safely handles empty files and skips corrupted JSON lines during loading.
    - Clear Memory easily.
    """
    def __init__(self, user_custom_file):
        self.filename = f"memory_{user_custom_file}.json"

    def save_context(self, user_input, ai_output):
        with open(self.filename, "a") as data:
            json.dump({"Human": user_input, "AI": ai_output}, data)
            data.write("\n")

    def load_memory_variables(self):
        string_history = ""
        if os.path.exists(self.filename) and os.path.getsize(self.filename) > 0:
            with open(self.filename, "r") as data:
                for line in data:
                    try:
                        ldata = json.loads(line)
                        string_history += f"Human: {ldata['Human']}\nAI: {ldata['AI']}\n"
                    except json.JSONDecodeError:
                        continue
        return string_history

    def clear_memory(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)
        else:
            return "Sorry either your memory file had been deleted or not created"

class Rag:
    """
    An all-in-one Retrieval-Augmented Generation (RAG) and File-to-Text conversion engine.

    This class serves two primary purposes:
    1. Unified File Conversion: Converts PDFs, images, local videos, and YouTube videos into text.
    2. Automated RAG Pipeline: When a query and DB_PATH are provided, it automatically handles
       text extraction, vector database ingestion, and LLM reasoning without requiring
       manual LLM integration, persistent storage of your Documents through 'vector_db_use' method you can easily store your documents on Supabase securely and for public also.
    3.Every thing is on cloud without any local installation or load in FREE OF COST UNLIMITED.

    Key Logic:
    - Smart Defaults: If DB_PATH and query are provided, the system defaults to 'llama3.2'
      and a temperature of 0.5 unless otherwise specified.
    - Context-Aware Mode: If DB_PATH and query are omitted, the class functions as a pure
      extraction tool, returning only the text content of the files.
    - Multi-Source Support: Accepts local file paths and external links (e.g., YouTube)
      via a single interface.
    - Persistent Storage: You can save your Documents on supabase with npmai with just 5 lines of code.
    """
    def __init__(self, files=None, query=None, secret_key=None, public: bool =None, Upload: bool = None, output_path=None, DB_PATH=None, link=None, temperature=None, model=None):
        self.files=files
        self.files_to_send=[]
        self.query=query
        self.db_path=DB_PATH
        self.link=link
        self.output_path=output_path
        self.temperature=temperature
        self.model=model
        self.secret_key=secret_key
        self.public=public
        self.Upload=Upload

    def send(self):
        files=self.files
        files_to_send=self.files_to_send
        DB_PATH=self.db_path
        link=self.link
        query=self.query
        model=self.model
        temperature=self.temperature
        public=self.public
        Upload=self.Upload
        secret_key=self.secret_key
        output_path=self.output_path

        data={
            "query":query,
            "DB_PATH":DB_PATH,
            "link":link,
            "temperature":temperature,
            "model":model,
            "output_path":output_path,
            "public":public,
            "secret_key":secret_key,
            "Upload":Upload
        }
        for path in files:
          files_to_send.append(('file', open(path, 'rb')))

        HF_API="https://sonuramashish22028704-npmeduai.hf.space/ingestion"

        res=requests.post(HF_API,data=data,files=files_to_send,timeout=900)
        response=str(res)
        try:
          return {"response":res.json().get("response")}
        except:
          return res

    def vector_db_use(self):
      DB_PATH=self.db_path
      secret_key=self.secret_key
      query=self.query
      public=self.public

      data={
          "DB_PATH":DB_PATH,
          "query":query,
          "secret_key":secret_key,
          "public":public
          }

      HF_API_VECTORDB_USE="https://sonuramashish22028704-npmeduai.hf.space/get_direct_retrieval"

      respons= requests.post(HF_API_VECTORDB_USE,data=data,timeout=900)
      try:
        return {"response":respons.json().get("response")}
      except:
        return respons
