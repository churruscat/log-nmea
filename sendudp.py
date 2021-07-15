import socket
import sys
import argparse
import time


parser = argparse.ArgumentParser(description='lee fichero y envia datagramas')
parser.add_argument('-i', '--ipaddress', nargs='?', default='255.255.255.255',
                    help='IP destination address, default=broadcast')
parser.add_argument('-p', '--port', nargs='?', default='4000',
                        help='IP destination port')
parser.add_argument('-f', '--file', nargs='?', default=None,
                        help='filename')

args = parser.parse_args()
ip=args.ipaddress
port=int(args.port)
filename=args.file

print("broadcast addr",str(socket.SO_BROADCAST))
# Create socket for server
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
print("Do Ctrl+c to exit the program !!")
fileH=open(filename,"r")
# Let's send data through UDP protocol
send_data=fileH.readline()
while send_data!='':
    try:
        send_data=fileH.readline()
        s.sendto(send_data.encode('utf-8'), (ip, port))
        print(" Client Sent : ", send_data, "")
        #time.sleep(0.1)
        send_data=fileH.readline()
    except:
        print("could not send")
        exit()
# close the socket
s.close()
fileH.close()