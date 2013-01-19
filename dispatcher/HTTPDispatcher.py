'''
Created on 17/01/2013

@author: fernando
'''
from dispatcher.BaseDispatcher import BaseDispatcher
from sockets.bases.BaseAsyncSock import isAsync
class HTTPDispatcher(BaseDispatcher):
    def __init__(self, sock):
        self.__sock__ = sock
        self.__request__ = []
        if isAsync(sock):
            sock.addCallback(self.processAsync)
    def processAsync(self, sock, msg):
        self
