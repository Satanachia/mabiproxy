import socket
import os
import importlib
from threading import Thread
import parser as parser
import struct

def recv_msg(sock):
    # Read message length and unpack it into an integer
    header = sock.recv(6)
    #print(f"recv header {header}")
    if not header:
        return None
    if len(header) < 6:
        return header
    msglen = struct.unpack_from('<I', header, 1)[0]

   # print(f"message len is: {msglen}")
    # Read the message data
    return recvall(sock, msglen, header)

def recvall(sock, n, header):
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
   # print("extending header")
    data.extend(header)
  #  print("reading bytes")
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
      #  print("extending packet")
        data.extend(packet)
    return data
#RECV
class Proxy2Server(Thread):

    def __init__(self, host, port):
        super(Proxy2Server, self).__init__()
        self.game = None # game client socket not known yet
        self.port = port
        self.host = host
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #Bind your local IP address onnetwork adapter as workaround for using loopback
        self.server.bind(('192.168.1.35',0)) #change ip to local ip of main network adapter
        self.server.connect((host, port))

    # run in thread
    def run(self):
        while True:
            #ECV
            #data = self.server.recv(4096)
            data = recv_msg(self.server)
            if data:
                #print "[{}] <- {}".format(self.port, data[:100].encode('hex'))
                try:
                    importlib.reload(parser)                        
                    parser.parse(data, self.port, 'recv')
                except Exception as e:
                    print('recv[{}]'.format(self.port), e)
                # forward to client
                if len(data) > 11:
                    if data[6:10].hex() == '0000520c':
                         if data[63:67].hex() == '0000c351':
                                print(f"typeof data: {type(data)}")
                                data[63:67] =  bytearray.fromhex('00000c1e')
                                self.game.sendall(data)
                    else:
                         self.game.sendall(data)
                else:
                    self.game.sendall(data)
                #self.game.sendall(data)
#SEND
class Game2Proxy(Thread):

    def __init__(self, host, port):
        super(Game2Proxy, self).__init__()
        self.server = None # real server socket not known yet
        self.port = port
        self.host = host
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(1)
        # waiting for a connection
        self.game, addr = sock.accept()
    #SEND
    def run(self):
        while True:
            #data = self.game.recv(4096)
            data = recv_msg(self.game)
            if data:
                #print "[{}] -> {}".format(self.port, data[:100].encode('hex'))
                try:
                    importlib.reload(parser)        
                    parser.parse(data, self.port, 'send')
                except Exception as e:
                    print('send[{}]'.format(self.port), e)
                # forward to server
                self.server.sendall(data)

class Proxy(Thread):

    def __init__(self, from_host, to_host, port):
        super(Proxy, self).__init__()
        self.from_host = from_host
        self.to_host = to_host
        self.port = port

    def run(self):
        while True:
            print("[proxy({})] setting up".format(self.port))
            self.g2p = Game2Proxy(self.from_host, self.port) # waiting for a client
            print("[proxy({})] setting up game2proxydone".format(self.port))
            self.p2s = Proxy2Server(self.to_host, self.port)
            print("[proxy({})] connection established".format(self.port))
            self.g2p.server = self.p2s.server
            self.p2s.game = self.g2p.game

            self.g2p.start()
            self.p2s.start()

'''
master_server = Proxy('0.0.0.0', '1.2.3.4', 11022) 
master_server.start()'''

game_servers = []
for port in range(11020, 11024):
    _game_server = Proxy('0.0.0.0', '52.11.161.60', port) #mabi channel ip + port
    _game_server.start()
    game_servers.append(_game_server)


while True:
    try:
        cmd = input('$ ')
        if cmd[:4] == 'quit':
            os._exit(0)
    except Exception as e:
        print(e)