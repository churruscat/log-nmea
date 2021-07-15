#!/usr/bin/env python
''' chuRRuscat@Morrastronix V1.0  2021
************************************************************************************
Read an UDP stream coming from OpenCPN
Cofiguration data in: /etc/recibeUDP/recibeUDP.conf
# log_level: specify log detail. valid values are:
# none,debug, info, warning, error ,critical
#[log_level]
#   log_level=warning
#[UDP]
#   port=4000 
#[raw_file]
#    filename=/var/log/recibeUDP   # program will add yymmdd.log to name

'''
import socket
import sys
import logging, json
from configparser import ConfigParser
from datetime import datetime
from time import time
#import pynmea2

configFile='/etc/recibeudp/recibeudp.conf'
tipoLogging=['none','debug', 'info', 'warning', 'error' ,'critical']
portUDP=4000
tags='{"deviceId":"Raymarine","location":"Barco"}'
measurement='NMEA'

def recibeUDP(sentence,estado):
    ''' secs,usecs=divmod(time(),1)   # si a time() le restara altzone tendria la hora local
    if secs-estado["epoch"] < 1800 :
        estado["hora"]=str(int(estado["epoch"]))+str(int(usecs*1000000000))
    else:
        estado["hora"]=str(int(secs))+str(int(usecs*1000000000))
    ''' 
    datos=sentence.split(',')
    if datos[0]=="$IIHDM":     #Heading
        pass    #NMEA_IIHDM(datos,estado)
    elif datos[0]=="$IIMTW":
        NMEA_IIMTW(datos,estado)
    elif datos[0]=="$IIRSA":
        NMEA_IIRSA(datos,estado)
    elif datos[0]=="$IIMWV":
        NMEA_IIMWV(datos,estado)
    elif datos[0]=="$IIDBT":    #depth below transducer
        pass #NMEA_IIDBT(datos)
    elif datos[0]=="$IIMTW":
        NMEA_IIMTW(datos,estado)
    elif datos[0]=="$IIVHW":
        NMEA_IIVHW(datos,estado)
    elif datos[0]=="$IIVLW":             #distance traveled. 1: Tota, 2: Distance since reset
        pass #NMEA_IIVLW(datos,estado)      
    elif datos[0]=="$GPGSV":
        NMEA_GPGSV(datos)
    elif datos[0]=="$GPGLL":
        pass         #NMEA_GPGLL(datos,estado)
    elif datos[0]=="$GPRMC":
        NMEA_GPRMC(datos, estado)
    elif datos[0]=="$GPGGA":
        pass #NMEA_GPGGA(datos)
    elif datos[0]=="$GPVTG":  # i use RMC instead
        pass    #NMEA_GPVTG(datos)
    elif datos[0]=="$PNKEP":  # ?????
        pass  
    elif datos[0]=="!AIVDM":  # AIS data
        pass          
    elif datos[0]=="!AIVDO":  # AIS data
        pass
    elif datos[0]=="$ERRPM":  # Engine RPM
        NMEA_ERRPM(datos, estado)
    else:
        logging.warning("unknown directive : "+sentence)
    return

def NMEA_IIDBT(datos): #Depth below transducer
    pass

def NMEA_IIMWV(datos,estado):
    if datos[2]=="R":
        estado["AWA"]=datos[1]
        estado["AWS"]=datos[3]
    elif datos[2]=="T":
        estado["TWA"]=datos[1]
        estado["TWS"]=datos[3]
    return; 

def NMEA_IIMTW(datos,estado):
    estado["Water_T"]=datos[1]
    return;

def NMEA_IIVHW(datos,estado):
    if datos[2]=='T':
        estado["Head_T"]=datos[1] 
    if datos[4]=='M':
        estado["Head_M"]=datos[3] 
    estado["SOW"]=datos[5]
    return

def NMEA_IIRSA(datos,estado):
    if datos[2]=='A':
        estado["Rudder_A"]=datos[1] 

def NMEA_GPGLL(datos,estado):
    pass
    if datos[5]=="A" :
        estado["lat"]=float(datos[1])/100 
        if datos[2]=="S":
            estado["lat"]*=-1
        estado["lon"]=float(datos[3])/100 
        if datos[4]=="O" :
            estado["lon"]*=-1
    return

def NMEA_GPGSV(datos):
    pass

def NMEA_GPRMC(datos,estado):
    if datos[2]=='A':
        estado["lat"]=float(datos[3])/100 
        if datos[4]=="S":
            estado["lat"]*=-1
        estado["lon"]=float(datos[5])/100
        if datos[6]=="O":
            estado["lon"]*=-1
        estado["SOG"]=datos[7]
        estado["Head_T"]=datos[8]
        estado["Mag_dev"]=datos[10]
        if datos[11]=="O":
            estado["Mag_dev"]=-datos[10]
            
        currentTime=datetime(int(datos[9][4:6])+2000,int(datos[9][2:4]),int(datos[9][0:2]),
                      int(datos[1][0:2]),int(datos[1][2:4]),int(datos[1][4:6]) )    
        estado["epoch"]=currentTime.timestamp()
        secs,usecs=divmod(time(),1)   # si a time() le restara altzone tendria la hora local
        if secs-estado["epoch"] < 7500 :
            estado["hora"]=str(int(estado["epoch"]))+str(int(usecs*1000000000))
        else:
            estado["hora"]=str(int(secs))+str(int(usecs*1000000000))

def NMEA_GPVTG(datos):
    pass

def NMEA_ERRPM(datos,estado):  
    #$ERRPM,E|S,Speed,%,A*CRC
    if datos[4]=="A":
        if datos[2]>1:
            estado["RPM"]=datos[2]
        else:
            estado["RPM"]=1
        estado["ENG"]=1
    else:
        estado["RPM"]=0  
    logging.info("RPM="+str(estado["RPM"]))   

def leeParser():
    parser = ConfigParser()
    parser.read(configFile)
    log_level='info'
    if parser.has_section("log_level"):
        if parser.has_option("log_level","log_level"):  
            loglevel=parser.get("log_level","log_level")
            print("loglevel=",log_level)
    print("log_level="+str(log_level))
    logging.basicConfig(stream=sys.stderr, format = '%(asctime)-15s  %(message)s', level=log_level.upper()) 
    if parser.has_section("UDP"):
        if parser.has_option("UDP","port"):
            portUDP=parser.get("UDP","port")
        else:
            portUDP=4000
    if parser.has_section("settings"):
        print("settings")
        if parser.has_option("settings","device_id"):   
            DEVICE_ID=parser.get("settings","device_id")
            print(DEVICE_ID)
        else:
            DEVICE_ID='NMEA'
        if parser.has_option("settings","location"):    
            LOCATION=parser.get("settings","location")
        else:
            LOCATION='Nowhere'
        if parser.has_option("settings","destination_host"):    
            host=parser.get("settings","destination_host")
        else:
            host='127.0.0.1'
        if parser.has_option("settings","user_name"):   
            username=parser.get("settings","user_name")
        else:
            username=''
        if parser.has_option("settings","password"):    
            password=parser.get("settings","password")
        else:
            password=''        
        if parser.has_option("settings","publish_topic"):   
            publish_topic=parser.get("settings","publish_topic")
        else:
            publish_topic='NMEA'
        if parser.has_option("settings","port"):   
            port=parser.get("settings","port")
        else:
            publish_topic=1883
    #filename="/var/log/recibeUDP"
    print(DEVICE_ID)
    filename="recibeUDP"
    if parser.has_section("rawfile"):
        if parser.has_option("raw_file","filename"):    
            filename=parser.get("raw_file","filename")
    ahora = datetime.now()
    filename=filename+'-'+str(ahora.strftime("%Y%m%d"))+".log"
    fileRaw=open(filename,"a")
    return fileRaw

if __name__ == '__main__':
    #mqttc = paho.Client(clientId) 
    leeParser()
    clientId=DEVICE_ID
    mqttc = paho.Client(clientId, clean_session=True) 
    #mqttc.username_pw_set(username , password=token)
    mqttc.reconnect_delay_set(60, 600) 
    conectado=False
    fileRaw=leeParser()
    # Create  socket AF_INET:ipv4, SOCK_DGAM:UDP
    clienteSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clienteSock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)       
    # La direccion en blanco equivale a 0.0.0.0 que equivale a INADDR_ANY
    clienteSock.bind(('' , portUDP))
    logging.info("Socket="+str(clienteSock))
    logging.info("Waiting for message")
    estado={}
    estado["RPM"]=0
    estado["ENG"]=0
    estado["epoch"]=0
    estado["hora"]=0
    estado["AWA"]=""
    estado["AWS"]=""
    estado["TWA"]=""
    estado["TWS"]=""
    estado["lat"]=""
    estado["lon"]=""
    estado["Water_T"]=""
    estado["Rudder_A"]=""
    estado["SOW"]=""
    estado["SOG"]=""
    estado["Head_T"]=""
    estado["Head_M"]=""
    estado["Mag_dev"]  =""
    i=0
    while True:
        try:
            sentence, origen = clienteSock.recvfrom(1024)
            sentence=sentence.decode("utf-8")
            logging.debug(sentence.strip('\r\n'))
            if estado["ENG"]==0:
                fileRaw.write(sentence)
            else:
                pass            
            recibeUDP(sentence,estado)
            if i>100:
                #dato='{"measurement":"'+"NMEA"+'","time":'+estado["epoch"]+\
                #',"fields":'+json.dumps(payload[0])+',"tags":'+tags+'}'
                cadena='{"RPM":',str(estado["RPM"])+','
                cadena=cadena+'"AWA":'+estado["AWA"]+',' if estado["AWA"]!='' else cadena
                cadena=cadena+'"AWS":'+estado["AWS"]+',' if estado["AWS"]!='' else cadena
                cadena=cadena+'"TWA":'+estado["TWA"]+',' if estado["TWA"]!='' else cadena   
                cadena=cadena+'"TWS":'+estado["TWS"]+',' if estado["TWS"]!='' else cadena
                cadena=cadena+'"lat":'+str(round(estado["lat"],7))+',' if estado["lat"]!='' else cadena
                cadena=cadena+'"lon":'+str(round(estado["lon"],7))+',' if estado["lon"]!='' else cadena
                cadena=cadena+'"Water_T":'+estado["Water_T"]+',' if estado["Water_T"]!='' else cadena
                cadena=cadena+'"Rudder_A":'+estado["Rudder_A"]+',' if estado["Rudder_A"]!='' else cadena
                cadena=cadena+'"SOW":'+estado["SOW"]+',' if estado["SOW"]!='' else cadena
                cadena=cadena+'"SOG":'+estado["SOG"]+',' if estado["SOG"]!='' else cadena
                cadena=cadena+'"Head_T":'+estado["Head_T"]+',' if estado["Head_T"]!='' else cadena
                cadena=cadena+'"Head_M":'+estado["Head_M"]+',' if estado["Head_M"]!='' else cadena
                cadena=cadena+'"Mag_dev":'+estado["Mag_dev"] if estado["Mag_dev"]!='' else cadena
                cadena=cadena.strip(',')
                cadena=cadena +'}'
                logging.debug("Estado: Hora "+ " AWA:"+estado["AWA"]+" AWS:"+estado["AWS"]+
                    " TWA:"+estado["TWA"]+" TWS:"+estado["TWS"]+" lat:"+str(round(estado["lat"],7))+
                    " lon:"+str(round(estado["lon"],7))+" Water_T:"+estado["Water_T"]+" Rudder_A:"+estado["Rudder_A"]+
                    " SOW:"+estado["SOW"]+" SOG:"+estado["SOG"]+" Head_T:"+estado["Head_T"]
                    +" Head_M:"+estado["Head_M"]+" Mag_dev:"+str(estado["Mag_dev"])) 
                try:  
                    datoJSON=json.dumps('{"measurement":"'+measurement+'","time":'+str(estado["hora"])+',"fields":'+cadena+',"tags":'+tags+'}')
                    logging.info(datoJSON)
                    result, mid = mqttc.publish(publishTopic, datoJSON, 1, True )
                    #FALTA ENVIAR A MQTT
                except:
                    logging.warning("could not JSONize "+'{"measurement":"'+measurement+'","time":'+str(estado["hora"])+',"fields":'+cadena+',"tags":'+tags+'}')
                i=0
                estado["ENG"]=0
            i+=1
        except KeyboardInterrupt:
            break
