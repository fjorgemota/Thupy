'''
Created on 11/01/2013

@author: fernando
'''
from NormalSocket import NormalSocket
import Queue
from sockets.bases import BaseAsyncSocket, SocketConfig, SocketType, AsyncCallbackMode
class AsyncSocket(BaseAsyncSocket, NormalSocket):
    '''Implements a AsyncSocket using handlers defined by the AsyncSocket class'''
    def __init__(self, *args, **kwargs):
        '''Implements constructor to construct queues'''
        super(AsyncSocket, self).__init__(*args, **kwargs)  # Call super class to initialize other variables
        self.__write_messages__ = []  # List with characters to be writed to the socket
        self.__read_messages__ = Queue.Queue()  # Queue with readed messages
        self.__read_buffer__ = []  # Save ALL chars from the socket
        self.__accepted_sockets__ = Queue.Queue()  # Queue with accepted sockets
        self.__callbacks__ = dict.fromkeys(AsyncCallbackMode, [])  # Create a dictionary to save the events
    def canRead(self):
        '''It's always readable'''
        return True  # It can read in any time..
    def canWrite(self):
        '''If has messages to be sended, return True, otherwise False'''
        return bool(self.__write_messages__)  # It have new characters?
    def write(self, msg):
        '''Put each character in the queue'''
        self.__write_messages__.extend(msg)
    def getReadedBuffer(self, buf= -1):
        '''Just return the history'''
        if buf < 0:
                buf = len(self.__read_buffer__)
        buf *= -1  # Inverse
        result = self.__read_buffer__[buf:]
        return "".join(result)
    def read(self, buf= -1, history=False):
        '''Read a determinated number of characters from the buffer. If the socket is blocking, await to get the determinated number of characters with the receive by the thread listener'''
        result = []
        blocking = self.getConfig(SocketConfig.BLOCKING) 
        if buf < 0:
            buf = self.__read_messages__.qsize()
        for _ in xrange(0, buf):
            try:
                result.append(self.__read_messages__.get(blocking))  # Await a new character
            except Queue.Empty: 
                break
            self.__read_messages__.task_done()
            
        return "".join(result)
    def handle_read(self):
        if self.getConfig(SocketConfig.MODE) == SocketType.SERVER:  # It can't read from a socket that is a...server
            return  # Just return
        msg = super(AsyncSocket, self).read()  # Read the message from the socket
        self.__read_buffer__.extend(msg)
        map(self.__read_messages.put_nowait, msg)
        for callback in self.__callbacks__[AsyncCallbackMode.READ]:
            callback(self, msg)
        for callback in self.__callbacks__[AsyncCallbackMode.ALL]:
            callback(AsyncCallbackMode.READ, self, msg)
    def handle_write(self):
        '''Send messages from the buffer..'''
        if not self.__write_messages or self.getConfig(SocketConfig.MODE) == SocketType.SERVER:  # It can't write if not have messages or the socket is a...server
            return
        sended = self.__sock.send("".join(self.__write_messages))
        msg = self.__write_messages__[:sended]
        self.__write_messages__ = self.__write_messages__[sended:]
        for callback in self.__callbacks__[AsyncCallbackMode.WRITE]:
            callback(self, msg, "".join(self.__write_messages__))
        for callback in self.__callbacks__[AsyncCallbackMode.ALL]:
            callback(AsyncCallbackMode.WRITE, self, msg, "".join(self.__write_messages__))
    def handle_accept(self):
        '''Accepts...But not in this socket (?)'''
        if self.getConfig(SocketConfig.MODE) == SocketType.CLIENT:  # It can't accept of a client
            return  # Just return
        sock = AsyncSocket(self.__sock.accept())
        self.__accepted_sockets.put_nowait(sock)  # Accept and put on queue..
        for callback in self.__callbacks__[AsyncCallbackMode.ACCEPT]:
            callback(self, sock)
        for callback in self.__callbacks__[AsyncCallbackMode.ALL]:
            callback(AsyncCallbackMode.ACCEPT, self, sock)
    def handle_close(self): 
        '''Just close the socket, just this'''
        self.close()
    def applyConfig(self):
        # Override to allow fast calls to handle_read and handle_accept
        super(AsyncSocket, self).applyConfig()
        if self.getConfig(SocketConfig.MODE) == SocketType.CLIENT:
            self.handle_read_event = self.handle_read  # If a client
        else:
            self.handle_read_event = self.handle_accept  # If a server
    def addCallback(self, callback, mode=AsyncCallbackMode.ALL):
        assert mode in AsyncCallbackMode, "Mode invalid"
        self.__callbacks__[mode].append(callback)
    def removeCallback(self, callback, mode=AsyncCallbackMode.ALL):
        assert mode in AsyncCallbackMode, "Mode invalid"
        self.__callbacks__[mode].remove(callback)    
    
