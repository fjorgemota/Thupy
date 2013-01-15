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
    def __init__(self, *args, **kwargs):
        '''Implements constructor to construct queues'''
        super(AsyncSocket, self).__init__(*args, **kwargs) #Call super class to initialize other variables
        self.__write_messages = [] #List with characters to be writed to the socket
        self.__read_messages = Queue() #Queue with readed messages
        self.__accepted_sockets = Queue() #Queue with accepted sockets
    def canRead(self):
        '''It's always readable'''
        return True #It can read in any time..
    def canWrite(self):
        '''If has messages to be sended, return True, otherwise False'''
        return bool(self.__write_messages) #It have new characters?
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
            result.append(self.__read_messages.get(blocking)) #Await a new character
            self.__read_messages.task_done()
        return "".join(result)
    def handle_read(self):
        if self.getConfig(SocketConfig.MODE) == SocketType.SERVER: #It can't read from a socket that is a...server
            return #Just return
        map(self.__read_messages.put_nowait, super(AsyncSocket, self).read())
    def handle_write(self):
        '''Send messages from the buffer..'''
        if not self.__write_messages or self.getConfig(SocketConfig.MODE) == SocketType.SERVER:#It can't write if not have messages or the socket is a...server
            return
        self.__write_messages = self.__write_messages[self.__sock.send("".join(self.__write_messages)):]
    def handle_accept(self):
        '''Accepts...But not in this socket (?)'''
        if self.getConfig(SocketConfig.MODE) == SocketType.CLIENT:#It can't accept of a client
            return #Just return
        self.__accepted_sockets.put_nowait(AsyncSocket(self.__sock.accept())) #Accept and put on queue..
    def handle_close(self): 
        '''Just close the socket, just this'''
        self.close()
    def applyConfig(self):
        #Override to allow fast calls to handle_read and handle_accept
        super(AsyncSocket, self).applyConfig()
        if self.getConfig(SocketConfig.MODE) == SocketType.CLIENT:
            self.handle_read_event = self.handle_read #If a client
        else:
            self.handle_read_event = self.handle_accept #If a server
    
        
    
