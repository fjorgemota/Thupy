'''
Created on 11/01/2013

@author: fernando
'''
from NormalSocket import NormalSocket
from BaseSocket import BaseAsyncSocket
from Queue import Queue
from BaseSocket import SocketConfig
from sockets.BaseSocket import SocketType
class AsyncSocket(NormalSocket, BaseAsyncSocket):
    '''Implements a AsyncSocket using handlers defined by the AsyncSocket class'''
    def __init__(self):
        '''Implements constructor to construct queues'''
        super(AsyncSocket, self).__init__()
        self.__write_messages = []
        self.__read_messages = Queue()
    def canRead(self):
        '''It's always readable'''
        return True
    def canWrite(self):
        '''If has messages to be sended, return True, otherwise False'''
        return bool(self.__write_messages)
    def write(self, msg):
        '''Put each character in the queue'''
        self.__write_messages.extend(msg)
    def read(self, buf=-1):
        '''Read a determinated number of characters from the buffer. If the socket is blocking, await to get the determinated number of characters with the receive by the thread listener'''
        result = []
        blocking = self.getConfig(SocketConfig.BLOCKING) 
        if buf < 0:
            buf = self.__read_messages.qsize()
        for _ in xrange(0, buf):
            result.append(self.__read_messages.get(blocking))
            self.__read_messages.task_done()
        return "".join(result)
    def handle_read(self):
        map(self.__read_messages.put_nowait, super(AsyncSocket, self).read())
    def handle_write(self):
        '''Send messages from the buffer..'''
        if not self.__write_messages or not self.:
            return
        self.__write_messages = self.__write_messages[self.__sock.send("".join(self.__write_messages)):]
    def handle_accept(self):
        '''Accepts...But not in this socket (?)'''
        
    
        
    
