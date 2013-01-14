'''
Created on 13/01/2013

@author: fernando
'''
from BaseListener import BaseListener, ListenerMode
from utils.itertools import itertools
import select, threading
from sockets.BaseSocket import isAsync, SocketConfig, SocketType
def getFileNO(s):
    '''Just get File Number to use with Sockets =P'''
    return s.fileno()
def getSockets(sockets):
    '''Return a dict with file numbers as keys and sockets objects as values'''
    return dict(zip(map(getFileNO, sockets), sockets)) 
class SelectListener(BaseListener):
    '''Listener that use Select functions to detect events'''
    def __init__(self):
        '''Constructs the listener, initializing variables such as readed sockets, writed sockets and etc...'''
        self.__read_sockets__ = []
        self.__write_sockets__ = []
        self.__modify_sockets__ = threading.Lock()
        self.__result_events__ = threading.Lock()
        self.__read_events__ = []
        self.__write_events__ = []
    def poll(self):
        '''Returns a list with sockets that have events to read and write'''
        return self.__read_events__+self.__write_events__
    def add(self, sock, mode):
        '''Add the socket to the listener'''
        assert mode in ListenerMode, "Mode invalid"
        add = [self.__read_sockets__.append, self.__write_sockets__.append][mode==ListenerMode.WRITE]
        self.__modify_sockets__.acquire()
        add(sock)
        self.__modify_sockets__.release()
    def remove(self, sock, mode):
        '''Remove the socket from the listener'''
        assert mode in ListenerMode, "Mode invalid"
        remove = [self.__read_sockets__.remove, self.__write_sockets__.remove][mode==ListenerMode.WRITE]
        self.__modify_sockets__.acquire()
        remove(sock) #Remove, or raises a error if not exists
        self.__modify_sockets__.release()
    def modify(self, sock, mode):
        '''Modify the listener mode of the socket'''
        assert mode in ListenerMode, "Mode invalid"
        self.remove(sock, [ListenerMode.READ, ListenerMode.WRITE][mode == ListenerMode.READ])
        self.add(sock, mode)
    def getToRead(self):
        '''Return a list with sockets that can be readed'''
        r = self.__read_events__[:]
        return r
    def getToWrite(self):
        '''Return a list with sockets that can be readed''',
        r = self.__write_events__[:]
        return r
    def run(self):
        '''Run the thread listener in a separate thread, and send the data to other channels (if not sync)'''
        while True:
            #Runs infinitely
            self.__modify_sockets__.acquire()
            read_sockets = getSockets(self.__read_sockets__)#Organize it..xD
            write_sockets = getSockets(self.__write_sockets__) #Organize it..xD
            self.__modify_sockets__.release()
            to_read, to_write, to_except = select.select(read_sockets.keys(), write_sockets.keys(), read_sockets.keys()+write_sockets.keys())
            read_events = []
            write_events = []
            for sockno in to_read:
                sock = read_sockets[sockno]
                if isAsync(sock):
                    if sock.getConfig(SocketConfig.MODE) == SocketType.CLIENT:
                        sock.handle_read()
                    else:
                        sock.handle_accept()
                else:
                    read_events.append(sock)
            for sockno in to_write:
                sock = write_sockets[sockno]
                if isAsync(sock):
                    sock.handle_write()
                else:
                    write_events.append(sock)
            map()