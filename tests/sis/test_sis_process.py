import os
import unittest
from multiprocessing import Pipe, freeze_support
from hyo2.abc.lib.testing import Testing
from hyo2.kng.sis.lib.sis_process import SisProcess


class TestSisProcess(unittest.TestCase):

    def setUp(self):
        data_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
        testing = Testing(root_folder=data_folder)
        self.test_files = testing.download_test_files(ext=".all")

    def test_simple_sis4(self):
        freeze_support()

        parent_conn, child_conn = Pipe()
        p = SisProcess(conn=child_conn, use_sis5=False)

        p.start()
        self.assertTrue(p.is_alive())

        p.stop()
        while True:
            if not p.is_alive():
                break
        self.assertFalse(p.is_alive())

    def test_simple_sis5(self):
        freeze_support()

        parent_conn, child_conn = Pipe()
        p = SisProcess(conn=child_conn, use_sis5=True)

        p.start()
        self.assertTrue(p.is_alive())

        p.stop()
        while True:
            if not p.is_alive():
                break
        self.assertFalse(p.is_alive())

    def test_sis4_with_files(self):
        freeze_support()

        parent_conn, child_conn = Pipe()
        p = SisProcess(conn=child_conn, use_sis5=False)

        p.set_files(self.test_files)

        p.start()
        self.assertTrue(p.is_alive())

        p.stop()
        while True:
            if not p.is_alive():
                break
        self.assertFalse(p.is_alive())

    def test_sis5_with_files(self):
        freeze_support()

        parent_conn, child_conn = Pipe()
        p = SisProcess(conn=child_conn, use_sis5=True)

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
    s.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSisProcess))
    return s
