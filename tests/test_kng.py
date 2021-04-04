import datetime
import unittest

from hyo2.kng import name, __version__, __author__, __license__, __copyright__


class TestKng(unittest.TestCase):

    def test_name(self):
        self.assertGreater(len(name), 0)

    def test_version(self):
        self.assertGreaterEqual(int(__version__.split(".")[0]), 0)

    def test_author(self):
        self.assertTrue("masetti" in __author__.lower())

    def test_license(self):
        self.assertTrue("lgpl" in __license__.lower())

    def test_copyright(self):
        self.assertTrue(str(datetime.datetime.now().year) in __copyright__)


def suite():
    s = unittest.TestSuite()
    s.addTests(unittest.TestLoader().loadTestsFromTestCase(TestKng))
    return s
