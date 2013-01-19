'''
Created on 16/01/2013

@author: fernando
'''
from utils.BasicClass import interface
class BaseDispatcher(interface):
    '''Dispatches a request to a respective callback'''    
    def __init__(self, sock):
        '''Initializes the dispatcher'''
        pass
    def run(self, msg):
        '''It's not a thread, it's just a method to run the dispatcher at read event'''
        pass
    def getSupportedPoints(self):
        '''Return a number of points indicating the support of this dispatcher to the specified socket'''
        pass
    def getSocket(self):
        '''Return the socket used by this dispatcher'''
        pass
    
