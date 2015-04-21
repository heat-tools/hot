import unittest
from hot.utils import test


class TestUtilTest(unittest.TestCase):

    def setUp(self):
        pass

    def test_local_http_check_google(self):
        url = "http://www.google.com"
        string = "Google"
        self.assertTrue(test.local_http_check(url, string))


if __name__ == "__main__":
    unittest.main()
