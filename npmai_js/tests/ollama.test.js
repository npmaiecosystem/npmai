import { describe, it, before, after } from 'node:test';
import assert from 'node:assert/strict';

const FAKE_API = 'https://fake.example/api';
const FAKE_FALLBACK = 'https://fake.example/fallback';
const HARDCODED_API = 'https://npmaiecosystem-load_balancer.hf.space/load_balancer';
const HARDCODED_FALLBACK = 'https://npmaiecosystem-loadbalancerfallback.hf.space/load_balancer';

describe('Ollama', () => {
  let originalFetch;

  before(() => {
    originalFetch = globalThis.fetch;
  });

  after(() => {
    globalThis.fetch = originalFetch;
  });

  describe('constructor', () => {
    it('uses defaults when no args', async () => {
      const { Ollama } = await import('../npmai.js?c=1');
      const o = new Ollama();
      assert.equal(o.model, 'llama3.2');
      assert.equal(o.temperature, 0.3);
      assert.equal(o.change, true);
      assert.equal(o.Models, null);
      assert.equal(o._api, null);
      assert.equal(o._fallback_api, null);
    });

    it('accepts custom options', async () => {
      const { Ollama } = await import('../npmai.js?c=2');
      const o = new Ollama({
        model: 'mixtral',
        temperature: 0.8,
        change: false,
        Models: ['llama3.2', 'mixtral'],
        api: FAKE_API,
        fallback_api: FAKE_FALLBACK,
      });
      assert.equal(o.model, 'mixtral');
      assert.equal(o.temperature, 0.8);
      assert.equal(o.change, false);
      assert.deepEqual(o.Models, ['llama3.2', 'mixtral']);
      assert.equal(o._api, FAKE_API);
      assert.equal(o._fallback_api, FAKE_FALLBACK);
    });
  });

  describe('_llm_type', () => {
    it('returns npmai', async () => {
      const { Ollama } = await import('../npmai.js?c=3');
      const o = new Ollama();
      assert.equal(o._llm_type, 'npmai');
    });
  });

  describe('invoke', () => {
    it('passes string prompt to _call', async () => {
      const { Ollama } = await import('../npmai.js?c=4');
      const o = new Ollama({ api: FAKE_API, fallback_api: FAKE_FALLBACK });
      const originalCall = o._call;
      let calledPrompt;
      o._call = (prompt) => {
        calledPrompt = prompt;
        return 'response text';
      };
      const result = await o.invoke('hello');
      assert.equal(calledPrompt, 'hello');
      assert.equal(result, 'response text');
      o._call = originalCall;
    });

    it('joins array prompts with newline', async () => {
      const { Ollama } = await import('../npmai.js?c=5');
      const o = new Ollama({ api: FAKE_API, fallback_api: FAKE_FALLBACK });
      const originalCall = o._call;
      let calledPrompt;
      o._call = (prompt) => {
        calledPrompt = prompt;
        return 'response text';
      };
      await o.invoke(['hello', 'world']);
      assert.equal(calledPrompt, 'hello\nworld');
      o._call = originalCall;
    });

    it('JSON-stringifies object prompts', async () => {
      const { Ollama } = await import('../npmai.js?c=6');
      const o = new Ollama({ api: FAKE_API, fallback_api: FAKE_FALLBACK });
      const originalCall = o._call;
      let calledPrompt;
      o._call = (prompt) => {
        calledPrompt = prompt;
        return 'response text';
      };
      await o.invoke({ key: 'value' });
      assert.equal(calledPrompt, '{"key":"value"}');
      o._call = originalCall;
    });

    it('converts array items to strings', async () => {
      const { Ollama } = await import('../npmai.js?c=7');
      const o = new Ollama({ api: FAKE_API, fallback_api: FAKE_FALLBACK });
      const originalCall = o._call;
      let calledPrompt;
      o._call = (prompt) => {
        calledPrompt = prompt;
        return 'response text';
      };
      await o.invoke([123, true]);
      assert.equal(calledPrompt, '123\ntrue');
      o._call = originalCall;
    });
  });

  describe('_call', () => {
    it('uses primary API on success', async () => {
      const { Ollama } = await import('../npmai.js?c=8');
      const o = new Ollama({ api: FAKE_API, fallback_api: FAKE_FALLBACK });
      let calledUrl;
      globalThis.fetch = async (url) => {
        calledUrl = url;
        return { ok: true, status: 200, json: async () => ({ response: 'hello there' }) };
      };
      const result = await o._call('hi');
      assert.equal(result, 'hello there');
      assert(calledUrl.includes('fake.example/api'));
    });

    it('falls back to fallback API on primary failure', async () => {
      const { Ollama } = await import('../npmai.js?c=9');
      const o = new Ollama({ api: FAKE_API, fallback_api: FAKE_FALLBACK });
      let callCount = 0;
      let secondUrl;
      globalThis.fetch = async (url) => {
        callCount++;
        if (callCount === 1) return { ok: false, status: 500 };
        secondUrl = url;
        return { ok: true, status: 200, json: async () => ({ response: 'fallback response' }) };
      };
      const result = await o._call('hi');
      assert.equal(result, 'fallback response');
      assert.equal(callCount, 2);
      assert(secondUrl.includes('fake.example/fallback'));
    });

    it('throws on fallback failure', async () => {
      const { Ollama } = await import('../npmai.js?c=10');
      const o = new Ollama({ api: FAKE_API, fallback_api: FAKE_FALLBACK });
      globalThis.fetch = async () => ({ ok: false, status: 500 });
      await assert.rejects(
        () => o._call('hi'),
        /Fallback HTTP 500/
      );
    });

    it('returns data.response when present', async () => {
      const { Ollama } = await import('../npmai.js?c=11');
      const o = new Ollama({ api: FAKE_API, fallback_api: FAKE_FALLBACK });
      globalThis.fetch = async () => ({ ok: true, status: 200, json: async () => ({ response: 'some answer' }) });
      const result = await o._call('q');
      assert.equal(result, 'some answer');
    });

    it('returns JSON stringified when no response field', async () => {
      const { Ollama } = await import('../npmai.js?c=12');
      const o = new Ollama({ api: FAKE_API, fallback_api: FAKE_FALLBACK });
      globalThis.fetch = async () => ({ ok: true, status: 200, json: async () => ({ foo: 'bar' }) });
      const result = await o._call('q');
      assert.equal(result, JSON.stringify({ foo: 'bar' }));
    });

    it('passes payload fields in primary call', async () => {
      const { Ollama } = await import('../npmai.js?c=13');
      const o = new Ollama({
        api: FAKE_API,
        fallback_api: FAKE_FALLBACK,
        model: 'mixtral',
        temperature: 0.7,
        change: false,
        Models: ['a', 'b'],
      });
      let sentBody;
      globalThis.fetch = async (url, opts) => {
        sentBody = JSON.parse(opts.body);
        return { ok: true, status: 200, json: async () => ({ response: 'ok' }) };
      };
      await o._call('hello');
      assert.equal(sentBody.prompt, 'hello');
      assert.equal(sentBody.model, 'mixtral');
      assert.equal(sentBody.temperature, 0.7);
      assert.equal(sentBody.change, false);
      assert.deepEqual(sentBody.Models, ['a', 'b']);
    });

    it('passes payload fields in fallback call', async () => {
      const { Ollama } = await import('../npmai.js?c=14');
      const o = new Ollama({
        api: FAKE_API,
        fallback_api: FAKE_FALLBACK,
        model: 'mixtral',
        temperature: 0.7,
        change: false,
        Models: ['a', 'b'],
      });
      let callCount = 0;
      let fallbackBody;
      globalThis.fetch = async (url, opts) => {
        callCount++;
        if (callCount === 1) return { ok: false, status: 500 };
        fallbackBody = JSON.parse(opts.body);
        return { ok: true, status: 200, json: async () => ({ response: 'ok' }) };
      };
      await o._call('hello');
      assert.equal(fallbackBody.prompt, 'hello');
      assert.equal(fallbackBody.model, 'mixtral');
      assert.equal(fallbackBody.temperature, 0.7);
      assert.equal(fallbackBody.change, false);
      assert.deepEqual(fallbackBody.Models, ['a', 'b']);
    });
  });

  describe('config caching via _resolveUrls', () => {
    it('loads from remote config on first call', async () => {
      const { Ollama } = await import('../npmai.js?c=15');
      const o = new Ollama();
      globalThis.fetch = async () => ({
        ok: true,
        status: 200,
        json: async () => ({ api: FAKE_API, fallback_api: FAKE_FALLBACK }),
      });
      await o._resolveUrls();
      assert.equal(o._api, FAKE_API);
      assert.equal(o._fallback_api, FAKE_FALLBACK);
    });

    it('caches config so second call uses cached value', async () => {
      const { Ollama } = await import('../npmai.js?c=16');
      const o1 = new Ollama();
      const o2 = new Ollama();
      let fetchCount = 0;
      globalThis.fetch = async () => {
        fetchCount++;
        return { ok: true, status: 200, json: async () => ({ api: FAKE_API, fallback_api: FAKE_FALLBACK }) };
      };
      await o1._resolveUrls();
      await o2._resolveUrls();
      assert.equal(fetchCount, 1, 'config should be cached, not fetched twice');
    });

    it('skips network if both URLs already set', async () => {
      const { Ollama } = await import('../npmai.js?c=17');
      const o = new Ollama({ api: FAKE_API, fallback_api: FAKE_FALLBACK });
      globalThis.fetch = () => { throw new Error('should not fetch'); };
      await o._resolveUrls();
      assert.equal(o._api, FAKE_API);
      assert.equal(o._fallback_api, FAKE_FALLBACK);
    });

    it('uses hardcoded fallback URLs when remote fetch fails', async () => {
      const { Ollama } = await import('../npmai.js?c=18');
      const o = new Ollama();
      globalThis.fetch = async () => ({ ok: false, status: 404 });
      await o._resolveUrls();
      assert.equal(o._api, HARDCODED_API);
      assert.equal(o._fallback_api, HARDCODED_FALLBACK);
    });

    it('uses hardcoded URLs when config lacks required keys', async () => {
      const { Ollama } = await import('../npmai.js?c=19');
      const o = new Ollama();
      globalThis.fetch = async () => ({
        ok: true,
        status: 200,
        json: async () => ({ not_api: 'x' }),
      });
      await o._resolveUrls();
      assert.equal(o._api, HARDCODED_API);
    });
  });
});
