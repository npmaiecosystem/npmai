import fs from 'fs';
import { Blob } from 'buffer';

const CONFIG_URL = 'https://raw.githubusercontent.com/npmaiecosystem/npmai/main/npmai_js/config.json';

const FALLBACK_API = 'https://npmaiecosystem-load_balancer.hf.space/load_balancer';
const FALLBACK_FALLBACK_API = 'https://npmaiecosystem-loadbalancerfallback.hf.space/load_balancer';

let _cachedConfig = null;

async function _loadConfig() {
  if (_cachedConfig) return _cachedConfig;
  try {
    const res = await fetch(CONFIG_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    _cachedConfig = await res.json();
    if (!_cachedConfig.api || !_cachedConfig.fallback_api) throw new Error('Missing keys in config');
    return _cachedConfig;
  } catch {
    _cachedConfig = { api: FALLBACK_API, fallback_api: FALLBACK_FALLBACK_API };
    return _cachedConfig;
  }
}

export class Ollama {
  constructor({
    model = 'llama3.2',
    temperature = 0.3,
    change = true,
    Models = null,
    api = null,
    fallback_api = null
  } = {}) {
    this.model = model;
    this.temperature = temperature;
    this.change = change;
    this.Models = Models;
    this._api = api;
    this._fallback_api = fallback_api;
  }

  get _llm_type() {
    return 'npmai';
  }

  async _resolveUrls() {
    if (this._api && this._fallback_api) return;
    const config = await _loadConfig();
    if (!this._api) this._api = config.api;
    if (!this._fallback_api) this._fallback_api = config.fallback_api;
  }

  async _call(prompt, stop = null) {
    await this._resolveUrls();

    const payload = {
      prompt,
      model: this.model,
      temperature: this.temperature,
      change: this.change,
      Models: this.Models
    };

    const fallback_payload = {
      prompt,
      temperature: this.temperature,
      change: this.change,
      model: this.model,
      Models: this.Models
    };

    let response;
    try {
      response = await fetch(this._api, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
    } catch {
      response = await fetch(this._fallback_api, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(fallback_payload)
      });
      if (!response.ok) throw new Error(`Fallback HTTP ${response.status}`);
    }

    const data = await response.json();
    if (data && data.response !== undefined) {
      return data.response;
    }
    return JSON.stringify(data);
  }

  async invoke(prompt) {
    if (Array.isArray(prompt)) {
      prompt = prompt.map(String).join('\n');
    } else if (typeof prompt === 'object' && prompt !== null) {
      prompt = JSON.stringify(prompt);
    }
    return this._call(prompt);
  }
}

export class Memory {
  constructor(user_custom_file) {
    this.filename = `memory_${user_custom_file}.json`;
  }

  save_context(user_input, ai_output) {
    const line = JSON.stringify({ Human: user_input, AI: ai_output }) + '\n';
    fs.appendFileSync(this.filename, line, 'utf-8');
  }

  load_memory_variables() {
    let string_history = '';
    if (fs.existsSync(this.filename) && fs.statSync(this.filename).size > 0) {
      const content = fs.readFileSync(this.filename, 'utf-8');
      for (const line of content.split('\n')) {
        if (!line.trim()) continue;
        try {
          const ldata = JSON.parse(line);
          string_history += `Human: ${ldata.Human}\nAI: ${ldata.AI}\n`;
        } catch {
          continue;
        }
      }
    }
    return string_history;
  }

  clear_memory() {
    if (fs.existsSync(this.filename)) {
      fs.unlinkSync(this.filename);
    } else {
      return 'Sorry either your memory file had been deleted or not created';
    }
  }
}

export class Rag {
  constructor({
    files = null,
    query = null,
    secret_key = null,
    public: isPublic = null,
    Upload = null,
    output_path = null,
    DB_PATH = null,
    link = null,
    temperature = null,
    model = null
  } = {}) {
    this.files = files;
    this.query = query;
    this.db_path = DB_PATH;
    this.link = link;
    this.output_path = output_path;
    this.temperature = temperature;
    this.model = model;
    this.secret_key = secret_key;
    this.public = isPublic;
    this.Upload = Upload;
  }

  async send() {
    const HF_API = 'https://sonuramashish22028704-npmeduai.hf.space/ingestion';

    const data = new URLSearchParams();
    data.append('query', this.query ?? '');
    data.append('DB_PATH', this.db_path ?? '');
    data.append('link', this.link ?? '');
    data.append('temperature', this.temperature ?? '');
    data.append('model', this.model ?? '');
    data.append('output_path', this.output_path ?? '');
    data.append('public', this.public ?? '');
    data.append('secret_key', this.secret_key ?? '');
    data.append('Upload', this.Upload ?? '');

    let body;
    const headers = {};
    if (this.files) {
      const formData = new FormData();
      for (const [key, value] of data) {
        formData.append(key, value);
      }
      for (const filepath of this.files) {
        const buffer = fs.readFileSync(filepath);
        const blob = new Blob([buffer]);
        const name = filepath.split(/[/\\]/).pop();
        formData.append('file', blob, name);
      }
      body = formData;
    } else {
      headers['Content-Type'] = 'application/x-www-form-urlencoded';
      body = data;
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 900000);

    let res;
    try {
      res = await fetch(HF_API, {
        method: 'POST',
        headers,
        body,
        signal: controller.signal
      });
    } finally {
      clearTimeout(timeout);
    }

    try {
      const json = await res.json();
      return { response: json.response };
    } catch {
      return res;
    }
  }

  async vector_db_use() {
    const HF_API_VECTORDB_USE = 'https://sonuramashish22028704-npmeduai.hf.space/get_direct_retrieval';

    const data = new URLSearchParams();
    data.append('DB_PATH', this.db_path ?? '');
    data.append('query', this.query ?? '');
    data.append('secret_key', this.secret_key ?? '');
    data.append('public', this.public ?? '');

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 900000);

    let respons;
    try {
      respons = await fetch(HF_API_VECTORDB_USE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: data,
        signal: controller.signal
      });
    } finally {
      clearTimeout(timeout);
    }

    try {
      const json = await respons.json();
      return { response: json.response };
    } catch {
      return respons;
    }
  }
}
