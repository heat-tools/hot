import unittest
from hot.utils import string


class TestUtilString(unittest.TestCase):

    def setUp(self):
        self.values = "this is a space separated string."
        self.list_of_str = ["testing", "lists", "to", "strings"]
        self.project_name = "test-project-name"

    def test_list_to_string(self):
        self.assertIsInstance(string.list_to_string(self.list_of_str), str)

    def test_string_to_list(self):
        self.assertIsInstance(string.string_to_list(self.values), list)

    def test_valid_project_name(self):
        self.assertTrue(string.valid_project_name(self.project_name))

    def test_invalid_project_name(self):
        self.assertFalse(string.valid_project_name("a" * 1000))

if __name__ == "__main__":
    unittest.main()
