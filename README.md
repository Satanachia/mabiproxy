# mabiproxy
bad implementation of a packet proxy for mabinogi

run tcpproxy before connecting to a game channel (specified in the tcpproxy script)

you will need to make a dummy network adapter configured with the ip address of the game channel you will connect to when the proxy is running (line129)
also the script will need the local ip of your computer main network adapter to bind to (line45)
there are better ways to do it but I can 't be bothered to fix it right now

parser.py is what does the parsing of the packets

based on liveoverflows version of this same thing for pwnie island
