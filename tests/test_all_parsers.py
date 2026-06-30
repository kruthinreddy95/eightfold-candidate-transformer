import unittest
import os
from src.parsers.csv_parser import parse_csv
from src.parsers.recruiter_notes_parser import parse_notes
from src.parsers.github_parser import parse_github
from src.parsers.linkedin_parser import parse_linkedin


class TestAllParsers(unittest.TestCase):

    def test_csv_parser(self):
        csv_path = "data/recruiter_export.csv"
        if not os.path.exists(csv_path):
            self.skipTest("Sample CSV not found")
        profile = parse_csv(csv_path)
        self.assertIsNotNone(profile)
        self.assertEqual(profile["full_name"]["value"], "Pillikandla Kruthin Reddy")
        self.assertIn("kruthinreddy95@gmail.com", profile["emails"]["value"])

    def test_notes_parser(self):
        notes_path = "data/recruiter_notes.txt"
        if not os.path.exists(notes_path):
            self.skipTest("Sample recruiter notes not found")
        profile = parse_notes(notes_path)
        self.assertIsNotNone(profile)
        self.assertEqual(profile["full_name"]["value"], "Pillikandla Kruthin Reddy")
        self.assertEqual(profile["headline"]["value"], "Software Developer Intern")
        self.assertEqual(profile["years_experience"]["value"], 3.0)

    def test_github_parser(self):
        profile = parse_github("https://github.com/kruthinreddy95")
        self.assertIsNotNone(profile)
        self.assertIn("github.com/kruthinreddy95", profile["links"]["value"]["github"])

    def test_linkedin_parser(self):
        profile = parse_linkedin("https://linkedin.com/in/pillikandla-kruthin-reddy-b97245289")
        self.assertIsNotNone(profile)
        self.assertEqual(profile["full_name"]["value"], "Pillikandla Kruthin Reddy")


if __name__ == "__main__":
    unittest.main()
