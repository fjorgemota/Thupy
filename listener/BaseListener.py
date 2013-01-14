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
    def remove(self, sock, mode):
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
    def run(self):
        '''Run the thread listener in a separate thread, and send the data to other channels (if not sync)'''
        pass
class ListenerMode(enum):
    WRITE = None
    READ = None
