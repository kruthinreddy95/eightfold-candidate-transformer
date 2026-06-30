import unittest
from src.projector import project


class TestProjector(unittest.TestCase):

    def test_project_basic(self):
        profile = {
            "full_name": "Kruthin Reddy",
            "emails": ["kruthinreddy95@gmail.com", "second@gmail.com"],
            "phones": ["+919502235163"],
            "skills": [
                {"name": "Python", "confidence": 0.9},
                {"name": "SQL", "confidence": 0.8}
            ],
            "overall_confidence": 0.85,
            "provenance": []
        }

        config = {
            "fields": [
                {"path": "name", "from": "full_name", "type": "string", "required": True},
                {"path": "primary_email", "from": "emails[0]", "type": "string"},
                {"path": "skills", "from": "skills[].name", "type": "string[]"}
            ],
            "include_confidence": True,
            "on_missing": "null"
        }

        projected = project(profile, config)

        self.assertEqual(projected["name"], "Kruthin Reddy")
        self.assertEqual(projected["primary_email"], "kruthinreddy95@gmail.com")
        self.assertEqual(projected["skills"], ["Python", "SQL"])
        self.assertEqual(projected["overall_confidence"], 0.85)

    def test_project_missing_strict(self):
        profile = {
            "full_name": "Kruthin Reddy",
            "emails": []
        }
        
        config = {
            "fields": [
                {"path": "name", "from": "full_name"},
                {"path": "primary_email", "from": "emails[0]", "required": True}
            ],
            "on_missing": "error"
        }
        
        with self.assertRaises(ValueError):
            project(profile, config)


if __name__ == "__main__":
    unittest.main()
