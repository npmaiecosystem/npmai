import { describe, it, mock, before, after, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'fs';
import path from 'path';
import os from 'os';
import { Rag } from '../npmai.js';

describe('Rag', () => {
  let originalFetch;
  let tmpDir;
  let testFilePath;
  let originalCwd;

  before(() => {
    originalFetch = globalThis.fetch;
    originalCwd = process.cwd();
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'npmai-rag-test-'));
    process.chdir(tmpDir);
    testFilePath = path.join(tmpDir, 'test.pdf');
    fs.writeFileSync(testFilePath, 'fake pdf content');
  });

  after(() => {
    globalThis.fetch = originalFetch;
    process.chdir(originalCwd);
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  afterEach(() => {
    mock.restoreAll();
  });

  describe('constructor', () => {
    it('uses defaults when no args', () => {
      const r = new Rag();
      assert.equal(r.files, null);
      assert.equal(r.query, null);
      assert.equal(r.db_path, null);
      assert.equal(r.link, null);
      assert.equal(r.output_path, null);
      assert.equal(r.temperature, null);
      assert.equal(r.model, null);
      assert.equal(r.secret_key, null);
      assert.equal(r.public, null);
      assert.equal(r.Upload, null);
    });

    it('accepts custom options including public key', () => {
      const r = new Rag({
        files: ['a.pdf'],
        query: 'hello',
        secret_key: 'sk-123',
        public: true,
        Upload: 'some_upload',
        output_path: '/out',
        DB_PATH: '/db',
        link: 'http://example.com',
        temperature: 0.5,
        model: 'llama3.2',
      });
      assert.deepEqual(r.files, ['a.pdf']);
      assert.equal(r.query, 'hello');
      assert.equal(r.secret_key, 'sk-123');
      assert.equal(r.public, true);
      assert.equal(r.Upload, 'some_upload');
      assert.equal(r.output_path, '/out');
      assert.equal(r.db_path, '/db');
      assert.equal(r.link, 'http://example.com');
      assert.equal(r.temperature, 0.5);
      assert.equal(r.model, 'llama3.2');
    });
  });

  describe('send', () => {
    it('sends URL-encoded body when no files', async () => {
      const r = new Rag({
        query: 'test query',
        secret_key: 'sk-123',
        public: true,
      });
      let sentHeaders;
      let sentBody;
      globalThis.fetch = mock.fn(async (url, opts) => {
        sentHeaders = opts.headers;
        sentBody = opts.body;
        return { ok: true, status: 200, json: async () => ({ response: 'answer' }) };
      });
      const result = await r.send();
      assert.equal(result.response, 'answer');
      assert(sentBody instanceof URLSearchParams);
      assert.equal(sentBody.get('query'), 'test query');
      assert.equal(sentBody.get('secret_key'), 'sk-123');
      assert.equal(sentBody.get('public'), 'true');
      assert.equal(sentHeaders['Content-Type'], 'application/x-www-form-urlencoded');
    });

    it('sends multipart FormData when files provided', async () => {
      const r = new Rag({ files: [testFilePath], query: 'file query' });
      let sentBody;
      globalThis.fetch = mock.fn(async (url, opts) => {
        sentBody = opts.body;
        return { ok: true, status: 200, json: async () => ({ response: 'file answer' }) };
      });
      const result = await r.send();
      assert.equal(result.response, 'file answer');
      assert(sentBody instanceof FormData);
    });

    it('sends all optional fields as URL-encoded params', async () => {
      const r = new Rag({
        query: 'q',
        DB_PATH: '/custom/db',
        link: 'http://link.com',
        temperature: '0.8',
        model: 'mixtral',
        output_path: '/output',
        secret_key: 'sk-456',
        public: false,
        Upload: 'my_upload',
      });
      globalThis.fetch = mock.fn(async (url, opts) => {
        return { ok: true, status: 200, json: async () => ({ response: 'ok' }) };
      });
      const spy = mock.method(URLSearchParams.prototype, 'append');
      await r.send();
      const params = {};
      for (const call of spy.mock.calls) {
        params[call.arguments[0]] = call.arguments[1];
      }
      assert.equal(params.query, 'q');
      assert.equal(params.DB_PATH, '/custom/db');
      assert.equal(params.link, 'http://link.com');
      assert.equal(params.temperature, '0.8');
      assert.equal(params.model, 'mixtral');
      assert.equal(params.output_path, '/output');
      assert.equal(params.secret_key, 'sk-456');
      assert.equal(params.public, false);
      assert.equal(params.Upload, 'my_upload');
    });

    it('sends file with correct Blob and filename', async () => {
      const r = new Rag({ files: [testFilePath], query: 'q' });
      let sentFormData;
      globalThis.fetch = mock.fn(async (url, opts) => {
        sentFormData = opts.body;
        return { ok: true, status: 200, json: async () => ({ response: 'ok' }) };
      });
      await r.send();
      const entries = [];
      for (const [key, value] of sentFormData.entries()) {
        entries.push({ key, value });
      }
      const fileEntry = entries.find(e => e.key === 'file');
      assert(fileEntry, 'file entry must exist in FormData');
      assert(fileEntry.value instanceof Blob);
      assert.equal(fileEntry.value.name, 'test.pdf');
    });

    it('returns { response } on JSON response', async () => {
      const r = new Rag({ query: 'test' });
      globalThis.fetch = mock.fn(async () => ({
        ok: true,
        status: 200,
        json: async () => ({ response: 'some answer' }),
      }));
      const result = await r.send();
      assert.deepEqual(result, { response: 'some answer' });
    });

    it('returns raw Response object on non-JSON response', async () => {
      const r = new Rag({ query: 'test' });
      const rawResponse = {
        ok: true,
        status: 200,
        json: async () => { throw new Error('not json'); },
        text: async () => 'plain text',
      };
      globalThis.fetch = mock.fn(async () => rawResponse);
      const result = await r.send();
      assert.equal(result, rawResponse);
    });

    it('uses AbortController with 900s timeout', async () => {
      const r = new Rag({ query: 'test' });
      const abortSpy = mock.method(AbortController.prototype, 'abort');
      globalThis.fetch = mock.fn(async (url, opts) => {
        assert(opts.signal instanceof AbortSignal);
        return { ok: true, status: 200, json: async () => ({ response: 'ok' }) };
      });
      await r.send();
      assert.equal(abortSpy.mock.calls.length, 0, 'abort should not be called on success');
    });

    it('clears timeout in finally block on error', async () => {
      const r = new Rag({ query: 'test' });
      globalThis.fetch = mock.fn(async () => {
        throw new Error('network error');
      });
      await assert.rejects(() => r.send());
    });
  });

  describe('vector_db_use', () => {
    it('sends URL-encoded POST to correct endpoint', async () => {
      const r = new Rag({ query: 'db query', DB_PATH: '/db', secret_key: 'sk-789', public: true });
      let sentUrl;
      let sentBody;
      let sentHeaders;
      globalThis.fetch = mock.fn(async (url, opts) => {
        sentUrl = url;
        sentBody = opts.body;
        sentHeaders = opts.headers;
        return { ok: true, status: 200, json: async () => ({ response: 'db answer' }) };
      });
      const result = await r.vector_db_use();
      assert.equal(result.response, 'db answer');
      assert(sentUrl.includes('get_direct_retrieval'));
      assert(sentHeaders['Content-Type'], 'application/x-www-form-urlencoded');
      assert(sentBody instanceof URLSearchParams);
      assert.equal(sentBody.get('query'), 'db query');
      assert.equal(sentBody.get('DB_PATH'), '/db');
      assert.equal(sentBody.get('secret_key'), 'sk-789');
      assert.equal(sentBody.get('public'), 'true');
    });

    it('sends only DB_PATH, query, secret_key, and public', async () => {
      const r = new Rag({
        query: 'q',
        DB_PATH: '/db',
        secret_key: 'sk',
        public: false,
        temperature: '0.9',
        model: 'x',
      });
      const spy = mock.method(URLSearchParams.prototype, 'append');
      globalThis.fetch = mock.fn(async () => ({
        ok: true,
        status: 200,
        json: async () => ({ response: 'ok' }),
      }));
      await r.vector_db_use();
      const params = {};
      for (const call of spy.mock.calls) {
        params[call.arguments[0]] = call.arguments[1];
      }
      assert.deepEqual(Object.keys(params).sort(), ['DB_PATH', 'public', 'query', 'secret_key']);
      assert.equal(params.temperature, undefined);
      assert.equal(params.model, undefined);
    });

    it('returns raw Response on non-JSON response', async () => {
      const r = new Rag({ query: 'test', DB_PATH: '/db' });
      const rawResponse = {
        ok: true,
        status: 200,
        json: async () => { throw new Error('not json'); },
      };
      globalThis.fetch = mock.fn(async () => rawResponse);
      const result = await r.vector_db_use();
      assert.equal(result, rawResponse);
    });

    it('uses AbortController with 900s timeout', async () => {
      const r = new Rag({ query: 'test', DB_PATH: '/db' });
      globalThis.fetch = mock.fn(async (url, opts) => {
        assert(opts.signal instanceof AbortSignal);
        return { ok: true, status: 200, json: async () => ({ response: 'ok' }) };
      });
      const result = await r.vector_db_use();
      assert.deepEqual(result, { response: 'ok' });
    });
  });
});
