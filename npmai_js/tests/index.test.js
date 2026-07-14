import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { Ollama, Memory, Rag } from '../index.js';

describe('index.js exports', () => {
  it('exports Ollama class', () => {
    assert.equal(typeof Ollama, 'function');
    assert.equal(Ollama.name, 'Ollama');
  });

  it('exports Memory class', () => {
    assert.equal(typeof Memory, 'function');
    assert.equal(Memory.name, 'Memory');
  });

  it('exports Rag class', () => {
    assert.equal(typeof Rag, 'function');
    assert.equal(Rag.name, 'Rag');
  });
});
