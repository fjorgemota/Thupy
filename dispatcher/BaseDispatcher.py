'''
Created on 16/01/2013

@author: fernando
'''
from utils.BasicClass import interface
from threading import Thread
class BaseDispatcher(interface, Thread):
    '''Dispatches any request of the Thupy server to respective callbacks'''    
    def __init__(self):
        super(BaseDispatcher, self).__init__() #Initialize a thread