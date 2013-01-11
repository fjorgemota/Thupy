'''
Created on 28/12/2012

@author: Fernando
'''
import sys, logging, unittest, os
logging.basicConfig(level=logging.INFO)
sys.path.insert(0, os.path.realpath(os.path.join(os.getcwd(), "..","..")))
from utils.PackageManager import *
class TestDjango(unittest.TestCase):
    def test_installLastestVersion(self):
        self.assertTrue(PackageManager.installPackage("django"))
    def test_installEspecificVersion(self):
        self.assertTrue(PackageManager.installPackage("django", version="1.3.5"))
    def test_upgrade(self):
        self.assertTrue(PackageManager.upgradePackage("django"))
    def test_uninstall(self):
        self.assertTrue(PackageManager.uninstallPackage("django"))
class TestTornado(unittest.TestCase):
    def test_installLastestVersion(self):
        self.assertTrue(PackageManager.installPackage("tornado"))
    def test_installEspecificVersion(self):
        self.assertTrue(PackageManager.installPackage("tornado", version="1.0"))
    def test_upgrade(self):
        self.assertTrue(PackageManager.upgradePackage("tornado"))
    def test_uninstall(self):
        self.assertTrue(PackageManager.uninstallPackage("tornado"))
if __name__ == "__main__":
    unittest.main()
