import { describe, it, before, after, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'fs';
import os from 'os';
import path from 'path';
import { Memory } from '../npmai.js';

let tmpDir;
let originalCwd;

before(() => {
  originalCwd = process.cwd();
  tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'npmai-memory-test-'));
  process.chdir(tmpDir);
});

after(() => {
  process.chdir(originalCwd);
  fs.rmSync(tmpDir, { recursive: true, force: true });
});

describe('Memory', () => {
  afterEach(() => {
    const files = fs.readdirSync('.');
    for (const f of files) {
      if (f.startsWith('memory_') && f.endsWith('.json')) {
        fs.rmSync(f);
      }
    }
  });

  describe('constructor', () => {
    it('creates filename from user_custom_file', () => {
      const m = new Memory('test_user');
      assert.equal(m.filename, 'memory_test_user.json');
    });

    it('handles custom string', () => {
      const m = new Memory('session_1');
      assert.equal(m.filename, 'memory_session_1.json');
    });
  });

  describe('save_context', () => {
    it('appends a JSON line to the file', () => {
      const m = new Memory('save_test');
      m.save_context('hello', 'world');
      const content = fs.readFileSync(m.filename, 'utf-8');
      const parsed = JSON.parse(content.trim());
      assert.equal(parsed.Human, 'hello');
      assert.equal(parsed.AI, 'world');
    });

    it('appends multiple entries in JSONL format', () => {
      const m = new Memory('multi_test');
      m.save_context('q1', 'a1');
      m.save_context('q2', 'a2');
      const content = fs.readFileSync(m.filename, 'utf-8');
      const lines = content.trim().split('\n');
      assert.equal(lines.length, 2);
      assert.equal(JSON.parse(lines[0]).Human, 'q1');
      assert.equal(JSON.parse(lines[1]).Human, 'q2');
    });

    it('uses utf-8 encoding', () => {
      const m = new Memory('utf8_test');
      m.save_context('hello', 'unicode: ñáéíóú');
      const content = fs.readFileSync(m.filename, 'utf-8');
      const parsed = JSON.parse(content.trim());
      assert.equal(parsed.AI, 'unicode: ñáéíóú');
    });
  });

  describe('load_memory_variables', () => {
    it('returns formatted history from saved context', () => {
      const m = new Memory('load_test');
      m.save_context('Hi', 'Hello!');
      const history = m.load_memory_variables();
      assert(history.includes('Human: Hi'));
      assert(history.includes('AI: Hello!'));
    });

    it('returns empty string when file does not exist', () => {
      const m = new Memory('nonexistent');
      const result = m.load_memory_variables();
      assert.equal(result, '');
    });

    it('returns empty string when file is empty', () => {
      const m = new Memory('empty_file');
      fs.writeFileSync(m.filename, '');
      const result = m.load_memory_variables();
      assert.equal(result, '');
    });

    it('skips malformed JSON lines gracefully', () => {
      const m = new Memory('malformed');
      m.save_context('good', 'entry');
      fs.appendFileSync(m.filename, 'not valid json\n', 'utf-8');
      m.save_context('another', 'entry');
      const history = m.load_memory_variables();
      assert(history.includes('Human: good'));
      assert(history.includes('Human: another'));
      assert(!history.includes('not valid json'));
    });

    it('preserves order of entries', () => {
      const m = new Memory('order_test');
      m.save_context('first', 'alpha');
      m.save_context('second', 'beta');
      m.save_context('third', 'gamma');
      const history = m.load_memory_variables();
      const humanMatches = history.match(/Human: /g);
      assert.equal(humanMatches.length, 3);
      assert(history.indexOf('first') < history.indexOf('second'));
      assert(history.indexOf('second') < history.indexOf('third'));
    });
  });

  describe('clear_memory', () => {
    it('deletes the file when it exists', () => {
      const m = new Memory('delete_test');
      m.save_context('x', 'y');
      assert(fs.existsSync(m.filename));
      m.clear_memory();
      assert(!fs.existsSync(m.filename));
    });

    it('returns message when file does not exist', () => {
      const m = new Memory('no_file');
      const result = m.clear_memory();
      assert.match(result, /either your memory file had been deleted or not created/i);
    });

    it('returns undefined on successful deletion', () => {
      const m = new Memory('success_delete');
      m.save_context('x', 'y');
      const result = m.clear_memory();
      assert.equal(result, undefined);
    });
  });
});
