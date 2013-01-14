import unittest
from utils.BasicClass import *
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
class EnumDefined(enum):
    lol = None
    risos = None
class EnumDefined2(enum):
    lol = None
    risos = None
class EnumDefined3(EnumDefined):
    aheuahue = None
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
class TestEnummClasses(unittest.TestCase):
    def setUp(self):
        pass
    @unittest.expectedFailure
    def test_construct(self):
        test = EnumDefined()
    def test_dif(self):
        self.assertNotEqual(EnumDefined.lol, None)
        self.assertNotEqual(EnumDefined.risos, None)
        self.assertNotEqual(EnumDefined.lol, 1)
        self.assertNotEqual(EnumDefined.risos, 2)
        self.assertNotEqual(EnumDefined.lol, 2)
        self.assertNotEqual(EnumDefined.risos, 1)
        self.assertNotEqual(EnumDefined.lol, EnumDefined2.lol)
        self.assertNotEqual(EnumDefined.risos, EnumDefined2.risos)
    def testEqual(self):
        self.assertEqual(EnumDefined.lol, EnumDefined.lol)
    def testInherit(self):
        self.assertEqual(EnumDefined.lol, EnumDefined3.lol)
    @unittest.expectedFailure
    def test_modify(self):
        EnumDefined.lol = EnumDefined.risos
    @unittest.expectedFailure
    def test_modifyDict(self):
        EnumDefined["lol"] = EnumDefined.risos
    @unittest.expectedFailure
    def test_delete(self):
        del EnumDefined.lol
    @unittest.expectedFailure
    def test_deleteDict(self):
        del EnumDefined["lol"]
    def test_contains(self):
        self.assertTrue(EnumDefined.lol in EnumDefined)
    def test_nocontains(self):
        self.assertTrue(EnumDefined3.lol in EnumDefined)
if __name__ == "__main__":
    unittest.main()
