from utils.BasicClass import interface
class BaseSocket(interface):
    '''Base Class to all sockets from the Thupy Server'''
    def __init__(self, sock=None):
        '''Initialize the socket'''
    def write(self, msg):
        '''Write a message to the socket and return the bytes sended'''
        pass
    def read(self, buf= -1):
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
