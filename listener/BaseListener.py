'''
Created on 05/01/2013

@author: fernando
'''
from utils.BasicClass import interface
class BaseListener(interface):
    def __init__(self):
        pass
    def poll(self):
        pass
    def add(self, sock, mode):
        pass
    