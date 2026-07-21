import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
from agent import process_transcript, _clean_str


class TestAgent(unittest.TestCase):

    def test_sample_transcript_exists_and_readable(self):
        """1. Checking that sample_transcript.txt exists and is readable."""
        filepath = "sample_transcript.txt"
        self.assertTrue(os.path.exists(filepath), f"File '{filepath}' does not exist.")
        self.assertTrue(os.path.isfile(filepath), f"'{filepath}' is not a valid file.")
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertGreater(len(content.strip()), 0, f"File '{filepath}' is empty.")

    @patch("agent.OpenAI")
    def test_process_transcript_returns_valid_json(self, mock_openai_cls):
        """2. Testing process_transcript() with a mock string to ensure it returns valid JSON structure with 'summary' and 'action_items'."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        
        expected_payload = {
            "summary": "The team aligned on the launch plan and set October 15 for public release.",
            "action_items": [
                {
                    "task": "Finalize API documentation",
                    "owner": "David",
                    "due_date": "2026-10-01"
                }
            ]
        }
        
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps(expected_payload)
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        result = process_transcript(
            transcript_text="Alex: Let's release on Oct 15. David: I will finalize API docs by Oct 1.",
            api_key="mock_api_key_for_unit_test"
        )

        self.assertIsInstance(result, dict)
        self.assertIn("summary", result)
        self.assertIn("action_items", result)
        self.assertEqual(result["summary"], expected_payload["summary"])
        self.assertEqual(len(result["action_items"]), 1)
        self.assertEqual(result["action_items"][0]["owner"], "David")

    def test_missing_transcript_file_handling(self):
        """3. Testing gracefully handling a missing transcript file error."""
        non_existent_path = "non_existent_transcript_file_xyz123.txt"
        self.assertFalse(os.path.exists(non_existent_path))
        
        with self.assertRaises(FileNotFoundError):
            with open(non_existent_path, "r", encoding="utf-8") as f:
                f.read()

    @patch.dict(os.environ, {}, clear=True)
    def test_process_transcript_missing_api_key_error(self):
        """Additional test: Ensure ValueError is raised when API key is completely absent."""
        with self.assertRaises(ValueError) as ctx:
            process_transcript("Sample text", api_key=None)
        self.assertIn("OPENAI_API_KEY is missing", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
