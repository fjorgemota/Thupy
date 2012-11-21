#from ..utils.BasicClass import *
import sys, unittest
sys.path.insert(0, "../")
from utils.BasicClass2 import *
class ConstructorEmpty(abstract):
    @abstractFn
    def abstract1(self, name="Teste"):
        pass
    @abstractFn
    def __init__(self, name="Fernando"):
        pass
class ConstructorDefined(abstract):
    @abstractFn
    def abstract1(self, name="Teste"):
        pass
    def getName(self):
        return self.name
    def __init__(self, name="Fernando"):
        self.name = name
class ConstructorAbstract(abstract):
    @abstractFn
    def abstract1(self, name="Teste"):
        pass
    @abstractFn
    def __init__(self, name):
        pass
class ClassDefined(ConstructorDefined):
    def abstract1(self, name="Teste"):
        pass

class TestAbstractClasses(unittest.TestCase):
    def setUp(self):
        pass
    @unittest.expectedFailure
    def test_constructEmpty(self):
        test = ConstructorEmpty()
    @unittest.expectedFailure
    def test_constructDefined(self):
        test = ConstructorDefined()
    @unittest.expectedFailure
    def test_constructAbstract(self):
        test = ConstructorAbstract()
    def test_defined(self):
        test = ClassDefined("Teste")
        self.assertEqual(test.getName(), "Teste")
        test = ClassDefined()
        self.assertEqual(test.getName(), "Fernando")
if __name__ == "__main__":
    unittest.main()
