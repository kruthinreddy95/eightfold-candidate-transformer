import unittest
import os
from src.parsers.resume_parser import parse_resume


class TestResumeParser(unittest.TestCase):

    def test_parse_sample_resume(self):
        resume_path = "data/resume.docx"
        if not os.path.exists(resume_path):
            self.skipTest(f"Sample resume file {resume_path} not found")

        profile = parse_resume(resume_path)

        self.assertIsNotNone(profile)
        # Check Name
        self.assertIn("full_name", profile)
        self.assertEqual(profile["full_name"]["value"], "PILLIKANDLA KRUTHIN REDDY")

        # Check Email
        self.assertIn("emails", profile)
        self.assertIn("kruthinreddy95@gmail.com", profile["emails"]["value"])

        # Check Phone
        self.assertIn("phones", profile)
        self.assertIn("+919502235163", profile["phones"]["value"])

        # Check Location
        self.assertIn("location", profile)
        self.assertEqual(profile["location"]["value"]["city"], "Chennai")
        self.assertEqual(profile["location"]["value"]["country"], "India")

        # Check Links
        self.assertIn("links", profile)
        links = profile["links"]["value"]
        self.assertEqual(links["github"], "github.com/kruthinreddy95")
        self.assertEqual(links["linkedin"], "linkedin.com/in/pillikandla-kruthin-reddy-b97245289")

        # Check Skills
        self.assertIn("skills", profile)
        skills = [s["name"] for s in profile["skills"]]
        self.assertIn("Python", skills)
        self.assertIn("Java", skills)
        self.assertIn("MySQL", skills)

        # Check Experience
        self.assertIn("experience", profile)
        exp = profile["experience"]
        self.assertTrue(len(exp) >= 4)
        companies = [e["company"] for e in exp]
        self.assertIn("SmartED Innovations", companies)
        self.assertIn("YBI Foundation", companies)

        # Check Education
        self.assertIn("education", profile)
        edu = profile["education"]
        self.assertTrue(len(edu) >= 3)
        institutions = [e["institution"] for e in edu]
        self.assertIn("Hindustan Institute of Technology and Science (HITS), Chennai", institutions)


if __name__ == "__main__":
    unittest.main()
