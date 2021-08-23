#!/usr/bin/env python
''' chuRRuscat@Morrastronix V1.0  2021
************************************************************************************
Read an UDP stream and print received msgs

'''
import socket
import sys
import json
portUDP=4000



if __name__ == '__main__':

    # Create  socket AF_INET:ipv4, SOCK_DGAM:UDP
    clienteSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clienteSock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)       
    # La direccion en blanco equivale a 0.0.0.0 que equivale a INADDR_ANY
    clienteSock.bind(('' , portUDP))

    while True:
        try:
            sentence, origen = clienteSock.recvfrom(1024)
            sentence=sentence.decode("utf-8")
            print(sentence.strip('\r\n'))

        except KeyboardInterrupt:
            break
