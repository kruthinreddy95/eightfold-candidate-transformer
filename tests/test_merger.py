import unittest
from src.merger import merge


class TestMerger(unittest.TestCase):

    def test_merge_profiles(self):
        profile1 = {
            "full_name": {"value": "Kruthin", "confidence": 0.80, "source": "resume_docx"},
            "emails": {"value": ["kruthin@gmail.com"], "confidence": 0.80, "source": "resume_docx"},
            "skills": [
                {"name": "Python", "confidence": 0.80, "source": "resume_docx"},
                {"name": "Git", "confidence": 0.80, "source": "resume_docx"}
            ]
        }

        profile2 = {
            "full_name": {"value": "Kruthin Reddy", "confidence": 0.90, "source": "ats_json"},
            "emails": {"value": ["kruthinreddy95@gmail.com"], "confidence": 0.90, "source": "ats_json"},
            "skills": [
                {"name": "Python", "confidence": 0.90, "source": "ats_json"},
                {"name": "SQL", "confidence": 0.90, "source": "ats_json"}
            ]
        }

        result = merge([profile1, profile2])

        self.assertIsNotNone(result)
        # Winner for full_name should be Kruthin Reddy (confidence 0.90)
        self.assertEqual(result["full_name"], "Kruthin Reddy")
        # Emails should keep highest-confidence primary
        self.assertEqual(result["emails"], ["kruthinreddy95@gmail.com"])
        # Skills should be combined, and Python should be boosted since it appears in both
        skills_map = {s["name"]: s for s in result["skills"]}
        self.assertIn("Python", skills_map)
        self.assertIn("Git", skills_map)
        self.assertIn("SQL", skills_map)
        # Python should have confidence 0.90 + 0.10 = 1.0
        self.assertEqual(skills_map["Python"]["confidence"], 1.0)


if __name__ == "__main__":
    unittest.main()