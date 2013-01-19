'''
Created on 14/01/2013

@author: fernando
'''
import sys, logging, os
logging.basicConfig(level=logging.DEBUG)
sys.path.insert(0, os.path.realpath(os.path.join(os.getcwd(), "..", "..")))
from utils.BasicClass import interface
class a(interface):
    def a(self):
        pass
    @staticmethod
    def b():
        pass
class b(a):
    def a(self):
        pass
    @staticmethod
    def b():
        pass
    @staticmethod 
    def c():
        print "Teste"
print a.__subclasses__()
print a
print b
