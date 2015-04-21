import unittest
import os
from hot.utils import files


class TestUtilFiles(unittest.TestCase):

    def setUp(self):
        self.wf = "writefile.temp"
        self.string = "test value"
        self.boolean = True
        self.lst = ["deletefile.temp"]
        self.dictionary = {}

    def test_write_file(self):
        self.assertIsNone(files.write_file(self.wf, self.string))
        os.remove(self.wf)

    def test_write_file_invalid(self):
        self.assertRaises(TypeError, files.write_file, self.wf, self.boolean)
        os.remove(self.wf)

    def test_delete_file(self):
        for f in self.lst:
            open(f, 'a').close()
        self.assertIsNone(files.delete_file(self.lst))

    def test_delete_file_invalid(self):
        self.assertRaises(TypeError, files.delete_file, self.dictionary)

if __name__ == "__main__":
    unittest.main(buffer=False)
