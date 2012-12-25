'''
Created on 24/12/2012

@author: fernando
'''
from utils.BasicClass2 import interface
class BaseSocket(interface):
    def write(self, msg):
        pass
    def read(self):
        pass
    def canRead(self):
        pass
    def canWrite(self):
        pass