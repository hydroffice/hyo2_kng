import os
import unittest
from multiprocessing import Pipe, freeze_support
from hyo2.abc.lib.testing import Testing
from hyo2.kng.emu.sis5.lib.sis5_process import Sis5Process


class TestSis5Process(unittest.TestCase):

    def setUp(self):
        self.ip_out = "localhost"
        self.port_out = 16103

        data_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
        testing = Testing(root_folder=data_folder)
        self.test_files = testing.download_test_files(ext=".kmall")

    def test_simple(self):
        freeze_support()

        parent_conn, child_conn = Pipe()
        p = Sis5Process(conn=child_conn, ip_out=self.ip_out, port_out=self.port_out)

        p.start()
        self.assertTrue(p.is_alive())

        p.stop()
        while True:
            if not p.is_alive():
                break
        self.assertFalse(p.is_alive())

    def test_with_files(self):
        freeze_support()

        parent_conn, child_conn = Pipe()
        p = Sis5Process(conn=child_conn, ip_out=self.ip_out, port_out=self.port_out)

        p.set_files(self.test_files)

        p.start()
        self.assertTrue(p.is_alive())

        p.stop()
        while True:
            if not p.is_alive():
                break
        self.assertFalse(p.is_alive())


def suite():
    s = unittest.TestSuite()
    s.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSis5Process))
    return s
