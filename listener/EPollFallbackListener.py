'''
Created on 15/01/2013

@author: fernando
'''
'''
Created on 14/01/2013

@author: fernando
'''
from BaseListener import BaseListener, ListenerMode
import select, threading, Queue
from sockets.BaseSocket import isAsync
from utils.BasicClass import enum
from utils.PackageManager import PackageManager
try:
    PackageManager.importPackage("epoll", "python-epoll")  # Tries to import a fallback to epoll that is available in Pypi
except ImportError:
    epoll = None  # Set to None
class EPollActions(enum):
    ADD = None
    MODIFY = None
    REMOVE = None
class EPollListener(BaseListener):
    def __init__(self):
        super(EPollListener, self).__init__()
        self.__manager__ = epoll.epoll()
        self.__timeout__ = -1
        self.__readed_sockets__ = []
        self.__writed_sockets__ = []
        self.__registered_sockets__ = {}
        self.__modes__ = {ListenerMode.READ:epoll.POLLIN, ListenerMode.WRITE: epoll.POLLOUT}
        self.__queue_sockets__ = Queue.Queue()
        self.__new_sockets__ = []
        self.__new_modify_sockets__ = threading.Lock() 
    def getTimeout(self):
        return self.__timeout__
    def setTimeout(self, timeout= -1):
        self.__timeout__ = timeout
    def getToRead(self, blocking=False):
        if blocking:
            event = threading.Event()
            self.__new_modify_sockets__.acquire()
            self.__new_sockets__.append(event)
            self.__new_modify_sockets__.release()
            event.wait()  # Block..
            event.clear()
            self.__new_modify_sockets__.acquire()
            self.__new_sockets__.remove(event)
            self.__new_modify_sockets__.release()
        return self.__readed_sockets__
    def getToWrite(self, blocking=False):
        if blocking:
            event = threading.Event()
            self.__new_modify_sockets__.acquire()
            self.__new_sockets__.append(event)
            self.__new_modify_sockets__.release()
            event.wait()  # Block..
            event.clear()
            self.__new_modify_sockets__.acquire()
            self.__new_sockets__.remove(event)
            self.__new_modify_sockets__.release()
        return self.__writed_sockets__
    def poll(self, blocking=False):
        if blocking:
            event = threading.Event()
            self.__new_modify_sockets__.acquire()
            self.__new_sockets__.append(event)  # Add to list!
            self.__new_modify_sockets__.release()
            event.wait()  # Block..
            event.clear()  # Clear (?)
            self.__new_modify_sockets__.acquire()
            self.__new_sockets__.remove(event)  # Remove from the list..
            self.__new_modify_sockets__.release()
        return self.__readed_sockets__ + self.__writed_sockets__
    def add(self, sock, mode):
        assert mode in ListenerMode, "Mode invalid"
        self.__queue_sockets__.put_nowait([EPollActions.ADD, sock, self.__modes__[mode]])
    def modify(self, sock, mode):
        assert mode in ListenerMode, "Mode invalid"
        self.__queue_sockets__.put_nowait([EPollActions.MODIFY, sock, self.__modes__[mode]])
    def remove(self, sock):
        self.__queue_sockets__.put_nowait([EPollActions.REMOVE, sock, None])
    def run(self):
        while True:
            # Process the queue to be thread-safe =P
            while True:
                try:
                    mode, sock, sock_mode = self.__queue_sockets__.get_nowait()
                except Queue.Empty:
                    break
                if mode == EPollActions.ADD:
                    self.__manager__.register(sock.fileno(), sock_mode)
                    self.__registered_sockets__[sock.fileno()] = sock 
                elif mode == EPollActions.MODIFY:
                    self.__manager__.modify(sock.fileno(), sock_mode)
                elif mode == EPollActions.REMOVE:
                    self.__manager__.unregister(sock.fileno())
                    self.__registered_sockets__.pop(sock.fileno(), None)
            socks = self.__registered_sockets__.copy()
            self.__modify_socket__.release()
            write_sockets = []
            read_sockets = []
            for sockno, event in self.__manager__.poll(self.__timeout__):
                sock = socks[sockno]  # If it raises a error, it's a error in the logic..
                if event & select.EPOLLIN:
                    if isAsync(sock):
                        try:
                            sock.handle_read_event()  # If server it call handle_accept, if client it call handle_read..
                        except:
                            pass  # Just catch the error
                    else:
                        read_sockets.append(sock)
                elif event & select.EPOLLOUT:
                    if isAsync(sock):
                        try:
                            sock.handle_write()
                        except:
                            pass  # Just catch the error
                    else:
                        write_sockets.append(sock)
                elif event & select.EPOLLHUP:
                    if isAsync(sock):
                        try:
                            sock.handle_close()
                        except:
                            pass  # Just catch the error
                    else:
                        sock.close()
                    self.remove(sock)
            self.__new_modify_sockets__.acquire()  # Block until all events is set
            map(threading.Event.set, self.__new_sockets__)  # Set all flags that are waiting to True..
            self.__new_modify_sockets__.release()  # Release..
    @staticmethod
    @staticmethod
    def getSupportedPoints():
        return [-1, 25][epoll != None]  # If it can be installed..
                    
