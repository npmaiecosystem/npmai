# npmai JavaScript SDK Documentation

npmai is a lightweight JavaScript package that gives you access to 45+ open source LLMs without any setup. No API keys, no login, no local models, no installations. Just import and use.

This package works in Node.js (version 18 or higher). It is an ESM module.

---

## Installation

### Install from npm registry (recommended)

Install it locally in your project:

```
npm install npmai
```

Or if you want to install it globally on your system:

```
npm install -g npmai
```

Or if you prefer yarn:

```
yarn add npmai
```

After installing, you can import the classes like this:

```js
import { Ollama, Memory, Rag } from 'npmai';
```

### Install from local folder

If you are not using a package manager or want to use the source directly, navigate into the npmai_js folder and install it locally from there:

```
npm install /path/to/npmai_js
```

Or you can copy the files from the npmai_js folder directly into your project and import from the local path:

```js
import { Ollama, Memory, Rag } from './npmai.js';
```

---

## Ollama Class

The Ollama class is the main way to talk to language models. You send a prompt, it sends it to our load balancer which finds a free model endpoint and returns the response. If the primary server is busy, it automatically falls back to a secondary server.

### How to create an instance

```js
const llm = new Ollama();
```

This uses all the defaults (model is llama3.2, temperature is 0.3).

You can also pass options:

```js
const llm = new Ollama({
  model: 'qwen2.5-coder:7b',
  temperature: 0.5,
  change: true,
  Models: ['llama3.2', 'gemma2']
});
```

### Options explained

**model** (string, default: 'llama3.2')
The name of the model you want to use. You can use any model from our supported list. Some common ones are llama3.2, qwen2.5-coder:7b, vicuna:7b, gemma2:9b, mistral:7b, and many more.

**temperature** (number, default: 0.3)
Controls how creative the model is. Lower values like 0.1 give more focused and deterministic answers. Higher values like 0.8 give more varied and creative responses.

**change** (boolean, default: true)
If set to true, when the requested model is busy, the system will automatically try other models to make sure your request goes through. If set to false, it will only use the exact model you asked for.

**Models** (array of strings, default: null)
If you set change to true, you can optionally provide a list of model names to use as fallbacks. For example, if you ask for vicuna:7b and it is busy, it will try llama3.2, then gemma2. If you do not provide this list, it will search through all 45+ models to find one that is free.

**api** (string, default: loaded from config)
The primary load balancer URL. You usually do not need to change this.

**fallback_api** (string, default: loaded from config)
The fallback load balancer URL. Used when the primary one fails.

### How to send a prompt

The simplest way:

```js
const llm = new Ollama();
const response = await llm.invoke('What is the capital of France?');
console.log(response);
```

With a specific model and settings:

```js
const llm = new Ollama({ model: 'mistral:7b', temperature: 0.7 });
const response = await llm.invoke('Explain quantum computing in simple terms.');
console.log(response);
```

The invoke method can accept different types of input:

**A plain string:**

```js
const response = await llm.invoke('Hello, who are you?');
```

**An array of strings (they get joined with newlines):**

```js
const response = await llm.invoke([
  'System: You are a helpful assistant.',
  'User: What is the weather like today?'
]);
```

**A JavaScript object (gets converted to JSON string):**

```js
const response = await llm.invoke({
  role: 'user',
  content: 'Write a poem about AI.'
});
```

### How the failover works

When you call invoke, the package first tries the primary load balancer URL. If that request fails for any reason (network error, server busy, timeout), it automatically tries the fallback URL. You do not need to write any error handling code for this. It just works.

---

## Memory Class

The Memory class helps your AI agents remember past conversations. It stores the history in a JSON file on your local machine.

### How to create an instance

```js
const memory = new Memory('my_chat_session');
```

This creates a file called memory_my_chat_session.json in your current working directory.

### Methods

**save_context(user_input, ai_output)**

Saves one exchange between a human and the AI.

```js
memory.save_context('What is the capital of India?', 'The capital of India is New Delhi.');
memory.save_context('What is its population?', 'The population of New Delhi is about 32 million.');
```

Each call appends a line to the file. The file format is one JSON object per line.

**load_memory_variables()**

Returns the entire conversation history as a formatted string. You can inject this directly into your LLM prompts to give the model context.

```js
const history = memory.load_memory_variables();
const llm = new Ollama();
const response = await llm.invoke(
  'Based on our conversation so far, what have we talked about?\n\n' + history
);
console.log(response);
```

The returned string looks like this:

```
Human: What is the capital of India?
AI: The capital of India is New Delhi.
Human: What is its population?
AI: The population of New Delhi is about 32 million.
```

If the file does not exist or is empty, it returns an empty string.

**clear_memory()**

Deletes the memory file. If the file does not exist, it returns a message saying so.

```js
memory.clear_memory();
```

### A complete example with Memory

```js
import { Ollama, Memory } from 'npmai';

const memory = new Memory('chat_with_llama');
const llm = new Ollama({ model: 'llama3.2' });

// First exchange
const answer1 = await llm.invoke('My name is Sonu. Nice to meet you!');
memory.save_context('My name is Sonu. Nice to meet you!', answer1);
console.log('AI:', answer1);

// Second exchange - model remembers the name from context
const history = memory.load_memory_variables();
const answer2 = await llm.invoke(
  history + '\nUser: What is my name?'
);
memory.save_context('What is my name?', answer2);
console.log('AI:', answer2);
```

---

## Rag Class

The Rag class is for Retrieval Augmented Generation. It lets you upload files (PDFs, images, videos, text files) and ask questions about them. Everything is processed on the cloud, so you do not need to install any models or tools locally.

### How to create an instance

```js
const rag = new Rag({
  files: ['document.pdf', 'image.png'],
  query: 'What does this document say about AI?',
  model: 'llama3.2',
  temperature: 0.5
});
```

### Options explained

**files** (array of file paths)
The files you want to process. Supported types are PDF, PNG, JPG, TXT, and MP4.

**query** (string)
Your question about the files. If you provide both files and a query, it will extract the text and then answer your question using RAG.

**DB_PATH** (string)
The name for your vector database. If you provide this along with a query, the system will store the extracted text as a vector database and then retrieve relevant chunks before answering.

**link** (string)
A YouTube video link. The system will download the video, extract audio, transcribe it, and then process it.

**model** (string)
The model to use for answering. Defaults to llama3.2 when not specified.

**temperature** (number)
The temperature for the model. Defaults to 0.5 when not specified.

**output_path** (string)
Where to save any downloaded or processed files.

**public** (boolean)
If set to true, the vector database will be stored publicly on Supabase.

**secret_key** (string)
If provided, the vector database will be stored privately on Supabase under this key.

**Upload** (boolean)
If set to true, the vector database will be uploaded to Supabase for persistent storage.

### The send method

The send method uploads your files and gets back a response.

```js
const rag = new Rag({
  files: ['report.pdf'],
  query: 'Summarize this report in 3 bullet points.',
  model: 'llama3.2'
});

const result = await rag.send();
console.log(result.response);
```

What happens behind the scenes:
1. Your files are uploaded to the NPMAI ingestion server
2. The server extracts text (PDF text, OCR for images, Whisper for videos)
3. If a DB_PATH and query are provided, it creates a vector database using FAISS with BGE embeddings
4. It retrieves relevant chunks using dynamic K (70% of total chunks)
5. It refines the answer using a sliding window batch approach (processes 3 chunks at a time)
6. The final answer is returned

If you only want to extract text without asking a question, just omit the query:

```js
const rag = new Rag({
  files: ['scanned_document.pdf']
});

const result = await rag.send();
console.log(result.response); // Just the extracted text
```

### The vector_db_use method

If you have already uploaded files and created a vector database (using the Upload option or through the web app), you can query it later without reuploading the files.

```js
const rag = new Rag({
  DB_PATH: 'my_knowledge_base',
  query: 'What did we discuss about machine learning?',
  secret_key: 'your_private_key'  // or public: true
});

const result = await rag.vector_db_use();
console.log(result.response);
```

This will:
1. Look for the vector database files locally first
2. If not found locally, try to download from Supabase (public or private based on your settings)
3. Load the FAISS index and retrieve relevant chunks
4. Answer your question using the model

### Using private storage

If you want your data to be private, provide a secret_key during upload and reuse it when querying:

```js
// Upload with private storage
const ragUpload = new Rag({
  files: ['confidential.pdf'],
  DB_PATH: 'my_private_data',
  secret_key: 'my_secret_abc123',
  Upload: true
});
await ragUpload.send();

// Query later
const ragQuery = new Rag({
  DB_PATH: 'my_private_data',
  query: 'What are the key points?',
  secret_key: 'my_secret_abc123'
});
const result = await ragQuery.vector_db_use();
console.log(result.response);
```

### Using public storage

If your data can be public, set public to true:

```js
const rag = new Rag({
  files: ['public_article.pdf'],
  DB_PATH: 'public_articles',
  public: true,
  Upload: true
});
await rag.send();
```

Anyone who knows the DB_PATH can query it later by setting public to true.

---

## Working with the load balancer directly

If you want to use the API directly without the npmai package, you can make HTTP requests to the load balancer:

```
POST https://npmaiecosystem-load_balancer.hf.space/load_balancer
```

With a JSON body:

```json
{
  "model": "llama3.2",
  "prompt": "Hello! Who are you?",
  "temperature": 0.4,
  "change": true,
  "Models": null
}
```

The response will be:

```json
{
  "response": "Hello! I am Llama 3.2, an AI assistant..."
}
```

Fallback endpoint:

```
POST https://npmaiecosystem-loadbalancerfallback.hf.space/load_balancer
```

---

## Complete examples

### Example 1: Simple Q&A

```js
import { Ollama } from 'npmai';

const llm = new Ollama({
  model: 'qwen2.5-coder:7b',
  temperature: 0.3
});

const answer = await llm.invoke('Write a JavaScript function to check if a number is prime.');
console.log(answer);
```

### Example 2: Multi turn conversation with memory

```js
import { Ollama, Memory } from 'npmai';

const memory = new Memory('coding_help');
const llm = new Ollama({ model: 'codellama:7b' });

async function chat(userMessage) {
  const history = memory.load_memory_variables();
  const prompt = history + 'User: ' + userMessage + '\nAI:';
  const response = await llm.invoke(prompt);
  memory.save_context(userMessage, response);
  return response;
}

const r1 = await chat('How do I read a file in Node.js?');
console.log('AI:', r1);

const r2 = await chat('Can you show me an example with error handling?');
console.log('AI:', r2);
```

### Example 3: Ask questions about a PDF

```js
import { Rag } from 'npmai';

const rag = new Rag({
  files: ['research_paper.pdf'],
  query: 'What is the main contribution of this paper?',
  model: 'llama3.2',
  temperature: 0.3
});

const result = await rag.send();
console.log('Answer:', result.response);
```

### Example 4: Create a persistent knowledge base

```js
import { Rag } from 'npmai';

// First, upload and index
const uploadRag = new Rag({
  files: ['company_policy.pdf', 'employee_handbook.pdf'],
  DB_PATH: 'company_docs',
  secret_key: 'company_secret_456',
  Upload: true
});
await uploadRag.send();
console.log('Documents indexed successfully.');

// Later, query
const queryRag = new Rag({
  DB_PATH: 'company_docs',
  query: 'What is the leave policy?',
  secret_key: 'company_secret_456'
});
const answer = await queryRag.vector_db_use();
console.log('Answer:', answer.response);
```

---

## Supported models

Here are some of the models you can use. You can pass any of these as the model parameter.

| Model name | Description |
| :--- | :--- |
| llama3.2 | Meta's latest small but powerful model |
| llama3.2:3b | Balanced for low RAM footprint |
| llama3.2:1b | Ultra lightweight, fast responses |
| llama3.1:8b | General purpose, multilingual |
| qwen2.5-coder:7b | Great for coding tasks |
| qwen2.5:7b | General purpose from Alibaba |
| qwen3.5:9b | Latest Qwen model, 2026 knowledge cutoff |
| gemma2:9b | Google DeepMind model |
| gemma3:12b | Latest Google model, 2026 cutoff |
| gemma3:4b | Compact but capable |
| mistral:7b | Fast and efficient |
| vicuna:7b | Good general reasoning |
| phi3:medium | Microsoft's reasoning model |
| phi4:14b | Advanced math and logic |
| deepseek-coder:6.7b | Code specialized |
| deepseek-r1:7b | Reasoning focused |
| falcon:7b-instruct | From TII, UAE |
| codellama:7b | Code synthesis |
| llama3:8b | Meta's older but reliable model |
| command-r | Enterprise agent tool calling |
| llava | Multimodal vision model |
| moondream | Tiny vision model for edge |
| aya:8b | Multilingual from Cohere |
| olmo2 | Fully open training architecture |
| nemotron-mini | NVIDIA's fast text model |

---

## Important notes

The npmai JavaScript package uses Node.js built in modules like fs and buffer. It does not have any external dependencies. All the heavy lifting happens on our servers.

There is no need to install Ollama locally or sign up for any API service. Everything is free and works out of the box.

If you are behind a firewall or proxy, make sure your environment can reach the following URLs:

- https://npmaiecosystem-load_balancer.hf.space
- https://npmaiecosystem-loadbalancerfallback.hf.space
- https://sonuramashish22028704-npmeduai.hf.space

The package uses ES modules (type: module in package.json). If you are using CommonJS, you might need to use dynamic import:

```js
const { Ollama, Memory, Rag } = await import('npmai');
```

---

## Need help?

If you run into any issues, have questions, or want to contribute, you can reach out at sonuramashishnpm@gmail.com.

The source code is available on GitHub at https://github.com/npmaiecosystem/npmai

Documentation and demo at https://npmai.netlify.app

---

Copyright (c) 2026 Sonu Kumar. MIT License.
