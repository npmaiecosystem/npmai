import os
import json
import unittest
from unittest.mock import patch, MagicMock
from npmai import Ollama, Memory, Rag

class TestOllama(unittest.TestCase):
    def test_init_defaults(self):
        llm = Ollama()
        self.assertEqual(llm.model, "llama3.2")
        self.assertEqual(llm.temperature, 0.3)
        self.assertTrue(llm.change)
        self.assertIsNone(llm.Models)

    def test_llm_type(self):
        llm = Ollama()
        self.assertEqual(llm._llm_type, "npmai")

    @patch("requests.post")
    def test_call_primary_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "Hello world"}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        llm = Ollama()
        res = llm.invoke("Hi")
        self.assertEqual(res, "Hello world")
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_call_fallback_success(self, mock_post):
        primary_fail = MagicMock()
        primary_fail.raise_for_status.side_effect = Exception("Primary failed")

        fallback_ok = MagicMock()
        fallback_ok.json.return_value = {"response": "Fallback answer"}
        fallback_ok.raise_for_status.return_value = None

        mock_post.side_effect = [primary_fail, fallback_ok]

        llm = Ollama()
        res = llm.invoke(["Prompt 1", "Prompt 2"])
        self.assertEqual(res, "Fallback answer")
        self.assertEqual(mock_post.call_count, 2)

    @patch("requests.post")
    def test_invoke_dict_prompt(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "Processed dict"}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        llm = Ollama()
        res = llm.invoke({"key": "value"})
        self.assertEqual(res, "Processed dict")


class TestMemory(unittest.TestCase):
    def setUp(self):
        self.user_file = "test_session_123"
        self.memory = Memory(self.user_file)
        if os.path.exists(self.memory.filename):
            os.remove(self.memory.filename)

    def tearDown(self):
        if os.path.exists(self.memory.filename):
            os.remove(self.memory.filename)

    def test_save_and_load_memory(self):
        self.memory.save_context("What is Python?", "Python is a programming language.")
        history = self.memory.load_memory_variables()
        self.assertIn("Human: What is Python?", history)
        self.assertIn("AI: Python is a programming language.", history)

    def test_clear_memory(self):
        self.memory.save_context("Hello", "Hi")
        self.assertTrue(os.path.exists(self.memory.filename))
        self.memory.clear_memory()
        self.assertFalse(os.path.exists(self.memory.filename))

    def test_load_nonexistent_memory(self):
        history = self.memory.load_memory_variables()
        self.assertEqual(history, "")


class TestRag(unittest.TestCase):
    def test_rag_init_defaults(self):
        rag = Rag()
        self.assertIsNone(rag.files)
        self.assertIsNone(rag.query)

    @patch("requests.post")
    def test_send_without_files(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "Extraction result"}
        mock_post.return_value = mock_resp

        rag = Rag(link="https://example.com", query="Summarize")
        res = rag.send()
        self.assertEqual(res, {"response": "Extraction result"})
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        self.assertIsNone(kwargs["files"])

    @patch("requests.post")
    def test_send_with_files(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "File processed"}
        mock_post.return_value = mock_resp

        test_file = "temp_test_doc.txt"
        with open(test_file, "w") as f:
            f.write("Test document content")

        try:
            rag = Rag(files=[test_file], query="What is in doc?")
            res = rag.send()
            self.assertEqual(res, {"response": "File processed"})
            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            self.assertIsNotNone(kwargs["files"])
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    @patch("requests.post")
    def test_vector_db_use(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "Direct retrieval answer"}
        mock_post.return_value = mock_resp

        rag = Rag(DB_PATH="my_vector_db", query="test query")
        res = rag.vector_db_use()
        self.assertEqual(res, {"response": "Direct retrieval answer"})


if __name__ == "__main__":
    unittest.main()
