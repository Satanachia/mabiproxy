import socket
import sys

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
server_address = ('52.41.162.90', 11022)
print ('connecting to %s port %s' % server_address)
sock.connect(server_address)

