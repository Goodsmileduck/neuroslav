import unittest

# Import modules from parent dir
import sys
sys.path.append('..')
import models

class TestModels(unittest.TestCase):
    # Init
    def setUp(self):
        pass
    # Clean up
    def tearDown(self):
        pass
    # Each test method starts with the keyword test_
    def test_questions_exists(self):
        self.assertGreater(models.Question.objects.all().count(), 0)
    def test_phrases_exists(self):
        self.assertGreater(models.Phrase.objects.all().count(), 0)


if __name__ == "__main__":
    unittest.main()