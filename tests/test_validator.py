import unittest
from src.validator import validate, validate_projected


class TestValidator(unittest.TestCase):

    def test_valid_profile(self):
        profile = {
            "candidate_id": "mock_id",
            "full_name": "Kruthin Reddy",
            "emails": ["test@test.com"],
            "phones": ["+919876543210"],
            "skills": [{"name": "Python", "confidence": 0.8, "sources": ["ats_json"]}],
            "overall_confidence": 0.8
        }

        self.assertEqual(validate(profile), [])

    def test_missing_name(self):
        profile = {
            "candidate_id": "mock_id",
            "emails": ["test@test.com"],
            "phones": ["+919876543210"],
            "skills": [{"name": "Python", "confidence": 0.8, "sources": ["ats_json"]}],
            "overall_confidence": 0.8
        }

        self.assertIn("Missing full_name", validate(profile))

    def test_projected_validation(self):
        config = {
            "fields": [
                {"path": "name", "type": "string", "required": True},
                {"path": "email", "type": "string", "required": True},
                {"path": "skills", "type": "string[]"}
            ]
        }
        
        valid_projected = {
            "name": "Kruthin",
            "email": "kruthin@gmail.com",
            "skills": ["Python", "SQL"]
        }
        self.assertEqual(validate_projected(valid_projected, config), [])
        
        invalid_projected = {
            "name": 123,  # should be string
            "skills": "Python"  # should be string[]
        }
        errors = validate_projected(invalid_projected, config)
        self.assertTrue(len(errors) > 0)
        self.assertIn("Projected field 'email' is required but missing or empty.", errors)
        self.assertIn("Projected field 'name' should be string, got int.", errors)


if __name__ == "__main__":
    unittest.main()