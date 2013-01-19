'''
Created on 13/01/2013

@author: fernando
'''
from BaseListener import BaseListener, ListenerMode
from utils.BasicClass import enum
import select, threading, Queue, time
from sockets.bases import isAsync, SocketConfig, SocketType
def getFileNO(s):
    '''Just get File Number to use with Sockets =P'''
    return s.fileno()
def getSockets(sockets):
    '''Return a dict with file numbers as keys and sockets objects as values'''
    return dict(zip(map(getFileNO, sockets), sockets)) 
class SelectActions(enum):
    ADD = None
    REMOVE = None
class SelectListener(BaseListener):
    '''Listener that use Select functions to detect events'''
    def __init__(self):
        '''Constructs the listener, initializing variables such as readed sockets, writed sockets and etc...'''
        super(SelectListener, self).__init__()
        self.__read_sockets__ = []
        self.__write_sockets__ = []
        self.__read_events__ = []
        self.__write_events__ = []
        self.__timeout__ = None
        self.__modes__ = {ListenerMode.READ:self.__read_sockets__, ListenerMode.WRITE:self.__write_sockets__}
        self.__new_sockets__ = []
        self.__new_modify_sockets__ = threading.Lock()
        self.__actions__ = Queue.Queue() 
        self.__empty__ = threading.Event()
    def poll(self, blocking=False):
        '''Returns a list with sockets that have events to read and write'''
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
        return self.__read_events__ + self.__write_events__
    def add(self, sock, mode):
        '''Add the socket to the listener'''
        assert mode in ListenerMode, "Mode invalid"
        self.__actions__.put_nowait([SelectActions.ADD, sock, mode])  # Add to the queue
    def remove(self, sock):
        '''Remove the socket from the listener'''
        for mode in self.__modes__.keys():
            self.__actions__.put_nowait([SelectActions.REMOVE, sock, mode])  # Add to the queue
    def modify(self, sock, mode):
        '''Modify the listener mode of the socket'''
        assert mode in ListenerMode, "Mode invalid"
        self.remove(sock)  # Remove the other event (?)
        self.add(sock, mode)
    def getToRead(self, blocking=False):
        '''Return a list with sockets that can be readed'''
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
        return self.__read_events__
    def getToWrite(self, blocking=False):
        '''Return a list with sockets that can be readed'''
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
        return self.__write_events__
    def getTimeout(self):
        return self.__timeout__
    def setTimeout(self, timeout= -1):
        self.__timeout__ = [timeout, None][timeout < 0]
    def run(self):
        '''Run the thread listener in a separate thread, and send the data to other channels (if not sync)'''
        while True:
            # Runs infinitely
            while True:
                try:
                    action, sock, mode = self.__actions__.get_nowait()  # Get a item on the queue
                except Queue.Empty:
                    break  # Or break if empty =P
                if action == SelectActions.ADD:
                    self.__modes__[mode].append(sock)
                elif action == SelectActions.REMOVE and sock in self.__modes__[mode]:
                    self.__modes__[mode].remove(sock)
            if not self.__read_sockets__ and not self.__write_sockets__:
                time.sleep([self.__timeout__, 1][self.__timeout__ == None])  # Sleep the thread
                continue  # Continue and repeat
            read_sockets = getSockets(self.__read_sockets__)  # Organize it..xD
            write_sockets = getSockets(self.__write_sockets__)  # Organize it..xD
            to_read, to_write, to_except = select.select(read_sockets.keys(), write_sockets.keys(), read_sockets.keys() + write_sockets.keys(), self.__timeout__)
            read_events = []
            write_events = []
            for sockno in to_read:
                # If socket is async...we have to see if it's a client, if it is, we call handle_read, if it's a server, we call handle_accept, otherwise, we publish it in a list
                sock = read_sockets[sockno]
                if isAsync(sock):  # If async, call the methods..
                    sock.handle_read_event()
                else:
                    read_events.append(sock)
            for sockno in to_write:
                # If socket is async..we call the handler to write to the socket..If not, we publish it in a list..=P
                sock = write_sockets[sockno]
                if isAsync(sock):
                    sock.handle_write()
                else:
                    write_events.append(sock)
            for sockno in to_except:
                # Closes all sockets that emit a exceptional condition
                sock = read_sockets.get(sockno, write_sockets.get(sockno))
                sock.close()  # If not exist, we have a big error in question of:::: Logic =P
            self.__read_events__ = read_events  # Just replace the list of sockets that can be readed (PS: It's thread-safe)
            self.__write_events__ = write_events  # Just replace the list of sockets that can be writed (PS: It's thread-safe)
    @staticmethod
    def getSupportedPoints():
        return [-1, 10][hasattr(select, "select")]  # In some implementations of Python that can be not exist =P
            
