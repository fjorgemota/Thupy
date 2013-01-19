'''
Created on 16/01/2013

@author: fernando
'''
from utils.BasicClass import interface 
from BaseSocket import BaseSocket
from sockets.bases.AsyncCallbackMode import AsyncCallbackMode
class BaseAsyncSocket(BaseSocket, interface):
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
    def addCallback(self, callback, mode=AsyncCallbackMode.ALL):
        '''Register a callback to manage a event in the async socket'''
    def removeCallback(self, callback, mode=AsyncCallbackMode.ALL):
        '''Remove a registered callback'''
def isAsync(sock):
    return isinstance(sock, BaseAsyncSocket)
