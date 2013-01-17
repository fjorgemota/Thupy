'''
Created on 16/01/2013

@author: fernando
'''
from utils.BasicClass import enum
class AsyncCallbackMode(enum):
    WRITE = None
    READ = None
    CLOSE = None
    ACCEPT = None    
    ALL = None