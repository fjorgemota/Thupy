'''
Created on 24/12/2012

@author: fernando
'''
from utils.BasicClass import abstract, abstractFn, enum
class BaseSocket(abstract):
    '''Base Class to all sockets from the Thupy Server'''
    @abstractFn
    def write(self, msg):
        '''Write a message to the socket and return the bytes sended'''
        pass
    @abstractFn
    def read(self, buf=-1):
        '''Read a determinated message with a determinated length from the socket'''
        pass
    @abstractFn
    def setConfig(self, name, value):
        '''Set a configuration using the key name'''
        pass
    @abstractFn
    def getConfig(self, name):
        '''Return a configuration by the key name'''
        pass
    @abstractFn
    def accept(self):
        '''Accepts and return a connnection using the same base class to implement the socket'''
        pass
    @abstractFn
    def fileno(self):
        '''Returns the file number of the socket to use with listeners'''
    def isAsync(self):
        '''Return if it's async or not'''
        return False
def BaseAsyncSocket(BaseSocket, abstract):
    @abstractFn
    def canRead(self):
        '''Return if the socket is readable'''
        pass
    @abstractFn
    def canWrite(self):
        '''Return if the socket is writable'''
        pass
    @abstractFn
    def handle_write(self):
        '''Handles a write event emited by the listener'''
    @abstractFn
    def handle_read(self):
        '''Handles a write event emited by the listener'''   
    @abstractFn
    def handle_accept(self):
        '''Handles a write event emited by the listener'''   
    @abstractFn
    def handle_connect(self):
        '''Handles a write event emited by the listener'''   
    def isAsync(self):
        '''Return if it's async or not'''
        return True
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
    