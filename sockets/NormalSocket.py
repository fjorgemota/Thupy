'''
Created on 23/12/2012

@author: fernando
'''
import socket
from sockets.BaseSocket import BaseSocket, SocketType, SocketConfig
from config import Configuration

class NormalSocket(BaseSocket):
    '''Just a implementation to a normal socket. Used as base for the all others sockets'''
    def __init__(self,sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)):
        self.__sock = sock
        self.__config = {
                         SocketConfig.BLOCKING:False,
                         SocketConfig.IP:None,
                         SocketConfig.PORT:None,
                         SocketConfig.TCP_DELAY:True,
                         SocketConfig.REUSE_ADDR:False,
                         SocketConfig.MODE:SocketType.CLIENT,
                         SocketConfig.RECEIVE_BUFFER_LENGTH:4096,
                         SocketConfig.NUM_CLIENTS:0 #If it's client..
                          }
        self.__initialized = False
    def write(self, msg):
        assert self.__mode == SocketType.CLIENT, "Can't write on server socket"
        return self.__sock.send(msg)
    def read(self, buf = -1):
        if buf < 0:
            buf = self.__config[SocketConfig.RECEIVE_BUFFER_LENGTH]
        assert self.__mode == SocketType.CLIENT, "Can't read on server socket"
        return self.__read.recv(buf)
    def accept(self):
        assert self.__mode == SocketType.SERVER, "Can't accept on clients sockets"
        return NormalSocket(self.__sock.accept())
    def getConfig(self, key):
        assert key in SocketConfig, "Not valid"
        return self.__config[key]
    def setConfig(self, key, val):
        assert key in SocketConfig, "Not valid"
        self._config[key] = val
        return True
    def applyConfig(self):
        cfg = self.__config
        if not self.__initialized:
            self.__sock.setblocking([0,1][cfg[SocketConfig.BLOCKING]])
            if cfg[SocketConfig.MODE] == SocketType.SERVER:
                self.__sock.bind((cfg[SocketConfig.IP], SocketConfig.PORT))
                self.__sock.listen(cfg[SocketConfig.NUM_CLIENTS])
            elif SocketConfig.IP and SocketConfig.PORT:
                self.__sock.connect((cfg[SocketConfig.IP], SocketConfig.PORT))
            self.__initialized = True #It's just updated now!
        self.__sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, [0,1][cfg[SocketConfig.TCP_DELAY]])
        self.__sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, [0,1][cfg[SocketConfig.REUSE_ADDR]])
                                                                             
        
        