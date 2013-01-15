'''
Created on 05/01/2013

@author: fernando
'''
from utils.BasicClass import interface, enum
from threading import Thread
class BaseListener(interface, Thread): 
    '''Thread that dispatches socket events sync and asyncronously in real time'''
    def __init__(self):
        '''Constructs the listener, initializing variables such as readed sockets, writed sockets and etc...'''
        pass
    def poll(self):
        '''Returns a iterable with sockets that have events to read and write'''
        pass
    def add(self, sock, mode):
        '''Add the socket to the listener'''
        pass
    def remove(self, sock):
        '''Remove the socket from the listener'''
        pass    
    def modify(self, sock, mode):
        '''Modify the listener mode of the socket'''
        pass
    def getToRead(self):
        '''Return a iterator with sockets that can be readed'''
        pass
    def getToWrite(self):
        '''Return a iterator with sockets that can be readed'''
        pass
    def getTimeout(self):
        '''Return the timeout between loops of this listener'''
    def setTimeout(self, timeout=-1):
        '''Set the timeout between loops of this listener'''    
    def run(self):
        '''Run the thread listener in a separate thread, and send the data to other channels (if not sync)'''
        pass
    @staticmethod
    def getSupportedPoints():
        '''Return a integer indicating if the listener is supported in the actual runtime and the relative performance of it. A value < 0 indicate that the listener is not supported, and the listener with the biggest value is used in the system'''
        return 0
class ListenerMode(enum):
    WRITE = None
    READ = None
