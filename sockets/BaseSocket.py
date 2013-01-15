'''
Created on 24/12/2012

@author: fernando
'''
import sys, logging
sys.path.insert(0, "../")
from utils.BasicClass import interface, enum
class BaseSocket(interface):
    '''Base Class to all sockets from the Thupy Server'''
    def write(self, msg):
        '''Write a message to the socket and return the bytes sended'''
        pass
    def read(self, buf=-1):
        '''Read a determinated message with a determinated length from the socket'''
        pass
    def close(self):
        '''Just close the socket'''
    def setConfig(self, name, value):
        '''Set a configuration using the key name'''
        pass
    def getConfig(self, name):
        '''Return a configuration by the key name'''
        pass
    def accept(self):
        '''Accepts and return a connnection using the same base class to implement the socket'''
        pass
    def fileno(self):
        '''Returns the file number of the socket to use with listeners'''
        pass
def BaseAsyncSocket(BaseSocket, interface):
    def canRead(self):
        '''Return if the socket is readable'''
        pass
    def canWrite(self):
        '''Return if the socket is writable'''
        pass
    def handle_write(self):
        '''Handles a write event emited by the listener'''
    def handle_read(self):
        '''Handles a read event emited by the listener'''   
    def handle_accept(self):
        '''Handles a accept event emited by the listener'''   
    def handle_close(self):
        '''Handles a close event emited by the listener'''
class SocketType(enum):
    SERVER = None
    CLIENT = None
class SocketConfig(enum):
    MODE = None
    RECEIVE_BUFFER_LENGTH = None
    REUSE_ADDR = None
    TCP_DELAY = None
    BLOCKING = None
    NUM_CLIENTS = None
    IP = None
    PORT = None
def isAsync(sock):
    return isinstance(sock, BaseAsyncSocket)