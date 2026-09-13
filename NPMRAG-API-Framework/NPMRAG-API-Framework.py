""" IMPORTANT UPDATE"""

""" 🚀 NPMAI Update: Advanced RAG Architecture
We have officially moved beyond basic RAG to a more intelligent and cost-efficient pipeline. 
These updates focus on maximizing context relevance while minimizing LLM latency. 

1. Dynamic K-Context Retrieval (70% Coverage)
The Problem: Fixed k values (e.g., k=4) are inefficient. They often provide too little context for large documents or too much "noise" for very short snippets.
The Solution: I have implemented a Proportional Scaling logic that calculates the optimal number of chunks to retrieve based on the actual size of your vectorized database.
Logic: dynamic_k = max(1, int(total_chunks * 0.70))
How it works:
Short Text: If your document has only 1 chunk, the system retrieves only that 1 relevant chunk.
Large PDF: If your PDF has 100 chunks, the system automatically scales up to retrieve 70 relevant chunks (

), ensuring the AI sees the "full picture" without missing critical details.
Benefit: Provides Smart Scaling that adapts to any document size automatically.

2. Sliding Window Batch-Refinement (3-Chunk Window)
The Problem: Standard "Refine" strategies process one chunk at a time, making 
 separate API calls. For a 20-chunk document, this is incredibly slow and expensive.
The Solution: I have engineered a Batch-Refine system that processes chunks in a sliding window of 3 instead of 1.
Logic: for i in range(0, total_chunks, 3):
How it works:
Instead of sending 1 chunk per loop, the system sends a group of 3 related chunks (


 characters) to the LLM in a single pass.
It uses a "Refine" prompt to merge the new 3-chunk information with the existing answer.
Benefit: 
3x Faster Execution: Reduces total LLM API calls by 66%.
Improved Coherence: The AI can see relationships across a broader context ( chars vs chars), leading to much smarter and more accurate answers.

3. Infrastructure: Persistent Supabase Integration (v0.1.8)
We have successfully integrated Supabase Object Storage for long-term, persistent storage of vectorized files.
Vector Persistence: Your documents are no longer temporary; they are stored in a vectorized form on a secure cloud database for unlimited time.
Universal Access: This allows your NPM-Rag-AI and NPM-AutoCode-AI to access the same knowledge base from anywhere.
Summary of Impact:
These updates make the NPMAI SDK significantly more Production-Ready. We are now processing data faster, retrieving it smarter, and storing it 
more securely than standard open-source RAG implementations.
"""


from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_ollama.llms import OllamaLLM
from fastapi import FastAPI, UploadFile, File, Form 
from fastapi.responses import JSONResponse
from moviepy.editor import VideoFileClip
from pdf2image import convert_from_path
from supabase import create_client
from pydantic import BaseModel
from fastapi import FastAPI
from npmai import Ollama
from PIL import Image
import numpy as np
import pytesseract
import threading
import whisper
#import yt_dlp
import fitz
import time
import cv2
import os
import re

SAFE_BASE = os.path.abspath("uploads")

def safe_filename(filename: str) -> str:
    name = os.path.basename(filename)
    if not name or name in ('.', '..'):
        return "unnamed"
    name = re.sub(r'[^\w.\-]', '_', name)
    return name

def safe_db_path(db_path: str) -> str:
    safe = os.path.basename(os.path.normpath(db_path))
    if not safe:
        raise ValueError("Invalid DB_PATH")
    safe = re.sub(r'[^\w\-]', '_', safe)
    result = os.path.abspath(os.path.join(SAFE_BASE, safe))
    if not result.startswith(SAFE_BASE):
        raise ValueError("DB_PATH escaped safe directory")
    return result

def safe_resolve_path(user_path: str) -> str:
    full = os.path.abspath(os.path.normpath(user_path))
    if full.startswith(os.path.abspath(SAFE_BASE)):
        return full
    full = os.path.abspath(os.path.normpath(os.path.join(SAFE_BASE, user_path)))
    if not full.startswith(os.path.abspath(SAFE_BASE)):
        raise ValueError("path escapes safe directory")
    return full

app=FastAPI()


SUPABASE_URL= os.environ["SUPABASE_URL"]
SUPABASE_KEY= os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

os.environ["CUDA_VISIBLE_DEVICES"] = ""


_whisper_model = None
_whisper_lock = threading.Lock()

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        with _whisper_lock:
            if _whisper_model is None:
                _whisper_model = whisper.load_model("base")
    return _whisper_model


#FUNCTIONS

def pdf_has_text(path):
    print("has_text")
    doc=fitz.open(path)
    for i in range(len(doc)):
        page=doc[i]
        text=page.get_text().strip()
        if text:
            print("texttrue")
            return True
    return False

@app.post("/pdfetext")
def extractable_text(path):
    path = safe_resolve_path(path)
    print("Extracting")
    doc=fitz.open(path)
    full=[]
    for page in doc:
        full.append(page.get_text())
    text="\n".join(full)
    return text

def preprocess_for_ocr(path):
    img=cv2.imread(path,cv2.IMREAD_COLOR)
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    h,w=gray.shape
    if w < 1000:
        gray=cv2.resize(gray,(int(w*2),int(h*2)),interpolation=cv2.INTER_CUBIC)
    gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th

@app.post("/pdfstext")
def pdf_scanned_to_text(pdf_path,dpi=300, tesseract_lang='eng'):
    pdf_path = safe_resolve_path(pdf_path)
    print("scanning")
    pages = convert_from_path(pdf_path, dpi=dpi)
    print("pages")
    full = []
    for img in pages:
        print("img")
        full.append(pytesseract.image_to_string(img, lang=tesseract_lang, config='--psm 6'))
    text="\n\n".join(full)
    print(text)
    return text

@app.post("/ocr")
def ocr(path,lang="eng"):
    path = safe_resolve_path(path)
    proc = preprocess_for_ocr(path)
    pil = Image.fromarray(proc)
    full = pytesseract.image_to_string(pil, lang=lang, config='--psm 6')
    return full

"""
@app.post("/ytvideo)
def get_transcript(link,output_path):
    url = link
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'noplaylist': True,
        'ignoreerrors': 'only_sample',
        'extractor_args': {'youtube': {'player_client': 'default'}}, 
        'age_limit': 99,
        }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            print("\nDownload finished successfully!")
    except Exception as e:
        print(f"\nAn error occurred during download: {e}")
    print("If the error is 'Sign In', you need to provide cookies as mentioned previously.")

    clip=VideoFileClip(output_path)

    audio=clip.audio
    audio.write_audiofile("temp.wav")

    model= get_whisper_model()
    result=model.transcribe("temp.wav")
    text=result["text"]
    return text
    """

@app.post("/video")
def local_video_processing(video_path):
    video_path = safe_resolve_path(video_path)
    clip=VideoFileClip(video_path)

    audio=clip.audio
    audio.write_audiofile("temp.wav")

    model= get_whisper_model()
    result=model.transcribe("temp.wav")
    text=result["text"]
    return text

@app.post("/text")
def text_processes(path):
    path = safe_resolve_path(path)
    with open(path,"r") as f:
        text=f.read()
        return text
    

#ROUTING POINT
@app.get("/")
def health():
    return {"ok":True}
    

@app.post("/ingestion")
async def ingest_file(
    query: str = Form(""),
    DB_PATH: str = Form(None),
    file: list[UploadFile] = File(None),
    link: str = Form(None),
    output_path: str = Form(None),
    temperature: float = Form(None),
    model: str = Form(None),
    public: bool = Form(None),
    Upload: bool = Form(None),
    secret_key: str = Form(None)
):
    os.makedirs("uploads", exist_ok=True)
    result = None
    extracted_texts=[]

    # Sanitize DB_PATH at entry
    safe_db = None
    if DB_PATH:
        try:
            safe_db = safe_db_path(DB_PATH)
        except ValueError:
            return JSONResponse({"response": "Invalid DB_PATH"})

    # ---------- FILE MODE ----------
    if file:
        length=len(file)
        for i in range(length):
            contents = await file[i].read()
            raw_name = file[i].filename or f"file_{i}"
            safe_name = safe_filename(raw_name)
            file_path = os.path.join(SAFE_BASE, safe_name)
            print("file_path", file_path)
            
            with open(file_path, "wb") as f:
                f.write(contents)
                
            ext = safe_name.lower().split(".")[-1] if "." in safe_name else ""
            
            if ext == "pdf":
                print("pdf")
                if pdf_has_text(file_path):
                    result = extractable_text(path=file_path)
                    extracted_texts.append(f"PDF: {result}")
                    print("yes")
                else:
                    result = pdf_scanned_to_text(pdf_path=file_path)
                    extracted_texts.append(f"PDF: {result}")
                    print('yes2')
                
            elif ext in ("png", "jpg", "jpeg"):
                result = ocr(path=file_path)
                extracted_texts.append(f"Image: {result}")
            
            elif ext == "txt":
                result = text_processes(path=file_path)
                extracted_texts.append(f"Text: {result}")
            
            elif ext == "mp4":
                result = local_video_processing(video_path=file_path)
                extracted_texts.append(f"Video: {result}")
            else:
                return JSONResponse({"response": "Unsupported file type"})

    else:
        return JSONResponse({"response": "No input provided"})

    results= extractable_router(extracted_texts=extracted_texts, DB_PATH=safe_db, query=query, temperature=temperature, model=model, secret_key=secret_key, Upload=Upload, public=public)
    
    return JSONResponse({"response": results})
        
    """# ---------- LINK MODE ----------
    elif link:
        result = get_transcript(link, DB_PATH, query, output_path)"""




def extractable_router(extracted_texts, DB_PATH=None, query=None, temperature=None, model=None, secret_key=None, Upload=None, public=None):
    if query is not "" and DB_PATH is not None:
        stringed_extracted_texts= "\n\n----------\n\n".join(extracted_texts)
        return retrieval(DB_PATH=DB_PATH,query=query,texts=stringed_extracted_texts,temperature=temperature,model=model)
    elif Upload:
        stringed_extracted_texts2= "\n\n----------\n\n".join(extracted_texts)
        return retrieval(DB_PATH=DB_PATH,query=query,texts=stringed_extracted_texts2,temperature=temperature,model=model,secret_key=secret_key, Upload=Upload, public=public)
    else:
        return "\n\n----------\n\n".join(extracted_texts)


@app.post("/get_direct_retrieval")
async def get_retrieval(
    DB_PATH: str = Form(...),
    query: str = Form(""),
    secret_key: str = Form(None),
    public: bool = Form(None),
):
    if DB_PATH is None and query is "":
        return JSONResponse({"response":"Sorry but please pass DB_PATH name and Query name in string data type."})

    try:
        safe_db = safe_db_path(DB_PATH)
    except ValueError:
        return JSONResponse({"response": "Invalid DB_PATH"})
        
    if os.path.exists(safe_db):
        normal_retriever= retrieval(temperature=0.5,model="llama3.2",DB_PATH=safe_db,query=query)
        return JSONResponse({"response":normal_retriever})
        
    else:
        safe_key = re.sub(r'[^\w\-]', '_', secret_key) if secret_key else None
        safe_db_name = os.path.basename(safe_db)

        if not safe_db_name:
            safe_db_name = "unnamed"

        if public:
            download_index_faiss = (
                supabase.storage
                .from_("NPMRagWebVectorDB")
                .download(f"public/{safe_db_name}/index.faiss")
            )
            
            download_index_pkl = (
                supabase.storage
                .from_("NPMRagWebVectorDB")
                .download(f"public/{safe_db_name}/index.pkl")
            )

            os.makedirs(safe_db, exist_ok=True)

            full_path_faiss = os.path.join(safe_db, "index.faiss")
            full_path_pkl = os.path.join(safe_db, "index.pkl")

            with open(full_path_faiss,"wb+") as faiss_save:
                faiss_save.write(download_index_faiss)

            with open(full_path_pkl,"wb+") as pkl_save:
                pkl_save.write(download_index_pkl)

            result= retrieval(DB_PATH=safe_db,query=query,temperature=0.5,model="llama3.2")
            return JSONResponse({"response":result})

        elif secret_key and safe_key:
            download_index_faiss = (
                supabase.storage
                .from_("NPMRagWebVectorDB")
                .download(f"{safe_key}/{safe_db_name}/index.faiss")
            )
            
            download_index_pkl = (
                supabase.storage
                .from_("NPMRagWebVectorDB")
                .download(f"{safe_key}/{safe_db_name}/index.pkl")
            )

            os.makedirs(safe_db, exist_ok=True)

            full_path_faiss = os.path.join(safe_db, "index.faiss")
            full_path_pkl = os.path.join(safe_db, "index.pkl")

            with open(full_path_faiss,"wb+") as faiss_save:
                faiss_save.write(download_index_faiss)

            with open(full_path_pkl,"wb+") as pkl_save:
                pkl_save.write(download_index_pkl)

            result_sec= retrieval(DB_PATH=safe_db,query=query,temperature=0.5,model="llama3.2")
            return JSONResponse({"response":result_sec})

        else:
            return JSONResponse({"response":"Sorry please provide secret_key that you entered during uploading Documents for processing or do public parameter True."})
    
    
    

#RETRIEVAL
def retrieval(DB_PATH,emb=HuggingFaceBgeEmbeddings(model_name="BAAI/bge-small-en-v1.5",model_kwargs={"device":"cpu"},encode_kwargs = {"normalize_embeddings": True},query_instruction="Represent this sentence for searching relevant passages: "), texts=None, query=None, temperature=None, model=None, secret_key=None, Upload=None, public=None):
    if DB_PATH:
      db_short_name = os.path.basename(DB_PATH)
      if os.path.exists(DB_PATH):
          vector_db=FAISS.load_local(
              DB_PATH,
              emb,
              allow_dangerous_deserialization=True
          )
          print("2")
          no_of_chunks= vector_db.index.ntotal
          dynamic_k= max(1,int(no_of_chunks*0.70))
          retriever=vector_db.similarity_search(query,k=dynamic_k)
          return preref(text=retriever,question=query,temperature=temperature,model=model)
      
      else:
          text_splitter=RecursiveCharacterTextSplitter(
              chunk_size=1000,
              chunk_overlap=200
          )
          chunks=text_splitter.split_text(texts)
          
          vector_db=FAISS.from_texts(chunks,emb)
          vector_db.save_local(DB_PATH)

          if Upload:
              index_file_faiss_var= open(os.path.join(DB_PATH, "index.faiss"), "rb")
              index_file_pkl_var= open(os.path.join(DB_PATH, "index.pkl"), "rb")
              
              if secret_key:
                  try:
                      index1faiss = (
                          supabase.storage
                          .from_("NPMRagWebVectorDB")
                          .upload(
                              file=index_file_faiss_var,
                              path=f"{secret_key}/{db_short_name}/index.faiss",
                              file_options={"upsert": "false"}
                          )
                      )
                      print(index1faiss)
                  except:
                      return "Sorry Some problems in uploading your Documents in Database, reupload the documents"
                  
                  try:
                      index2pkl= (
                          supabase.storage
                          .from_("NPMRagWebVectorDB")
                          .upload(
                              file=index_file_pkl_var,
                              path=f"{secret_key}/{db_short_name}/index.pkl",
                              file_options={"upsert": "false"}
                          )
                      )
                      print(index2pkl)
                  except:
                      file_first_faiss_removal = (
                          supabase.storage
                          .from_("NPMRagWebVectorDB")
                          .remove([f"{secret_key}/{db_short_name}/index.faiss"])
                      )
                      print(file_first_faiss_removal)
                      
                      return "Sory some problem in uploading your Documents in Database, reupload the documents"
                      
              elif public:
                  try:
                      index_public_faiss=(
                          supabase.storage
                          .from_("NPMRagWebVectorDB")
                          .upload(
                              file=index_file_faiss_var,
                              path=f"public/{db_short_name}/index.faiss",
                              file_options={"upsert": "false"}
                          )
                      )
                      print(index_public_faiss)
                  except:
                      return "Sory some problem in uploading your Documents in Database, reupload the documents"

                  try:
                      index_public_pkl=(
                          supabase.storage
                          .from_("NPMRagWebVectorDB")
                          .upload(
                              file=index_file_pkl_var,
                              path=f"public/{db_short_name}/index.pkl",
                              file_options={"upsert": "false"}
                          )
                      )
                      print(index_public_pkl)
                  except:
                      file_first_faiss_removal = (
                          supabase.storage
                          .from_("NPMRagWebVectorDB")
                          .remove([f"public/{db_short_name}/index.faiss"])
                      )
                      print(file_first_faiss_removal)
                      return "Sory some problem in uploading your Documents in Database, reupload the documents"
                      
              else:
                  return "Sorry please pass at least Secret_key or Public param in order to save your document in Database for persistent memory."
                  
          else:
              no_of_chunks_d= vector_db.index.ntotal
              dynamic_k_d= max(1,(no_of_chunks_d*0.70))
              retriever=vector_db.similarity_search(query,k=dynamic_k_d)
              return preref(text=retriever,question=query,temperature=temperature,model=model)
    else:
      return "Sorry but you have to provide query and DB_PATH also in order to retrieve from Vectorised DataBase"

  
#REFINE INITIALISATION
def preref(text,question, temperature, model, **kwargs):
  ref=refine(
      text=text,
      question=question,
      temperature=temperature,
      model=model
  )
  result=ref.refinef()
  return result


#REFINE
class refine:
  def __init__(self,text,question, temperature, model):
    self.text=text
    self.question=question
    self.temperature=temperature
    self.model=model

  def refinef(self):
    texts=self.text
    question=self.question
    temperature=self.temperature
    model=self.model
    answers=[]
    no=len(texts)
    no_of_loop=0
    if no > 2:
        chunks_send=no/3
        for i in range(chunks_send):
            context=texts[i*3:(i+1)*3]
            final_context="\n---\n".join([doc.page_content for doc in context])
            prompt=f"""Use the following information to answer the question: 
            Text: {final_context}
            Existing Answer: {answers}
            Question: {question}
            """
            
            llm=Ollama(
                model=model,
                temperature=temperature
            )
            response=llm.invoke(prompt)
            
            if answers:
                answers.remove(answers[0])
                answers.append(response)
            else:
                answers.append(response)
            
            if not no_of_loop==chunks_send:
                no_of_loop+=1
            else:
                pass
        return response
    elif no == 2 or no < 2:
      context_texts=texts[0:2]
      final_context_e="\n---\n".join([doc.page_content for doc in context_texts])
      prompt=f"""Use the following information to answer the question: 
      Text: {final_context_e}
      Existing Answer: {answers}
      Question: {question}
      """

      llm=Ollama(
          model=model,
          temperature=temperature
      )
      response_e=llm.invoke(prompt)
      return response
