#!/usr/bin/env python
''' chuRRuscat@Morrastronix V1.0  2021
************************************************************************************
Read an udp stream coming from OpenCPN and :
   - summarizes it and sends it to an mqtt queue
   - if engine is stopped, stores all the fdta in a file
Configuration data in: /etc/log-nmea/log-nmea.conf
# loglevel: specify log detail. valid values are:
# none,debug, info, warning, error ,critical
#[loglevel]
#   loglevel=warning
#[udp]
#   port=4000 
#[rawfile]
#    filename=/var/log/log-nmea   # program will add yymmdd.log to name

'''
import socket
import sys
import logging, json
from configparser import ConfigParser
import paho.mqtt.client as paho
from datetime import datetime
#import datetime
from time import time
#import pynmea2

configFile='/etc/log-nmea/log-nmea.conf'
tipoLogging=['none','debug', 'info', 'warning', 'error' ,'critical']
tags={'deviceId':'Raymarine','location':'Barco'}
measurement='NMEA'
configData={
    "device_id":"NMEA",
    "location":"Boat",
    "influxdb":"127.0.0.1",
    "username":"",
    "password":"",
    "destination_mqtt":"destination.host.com",
    "publish_topic":"datosVela",
    "log_topic":"NMEA",
    "port":"1883",
    "portudp":"4000",
    "loglevel":"info",
    "rawfile":"",
    "num_records":100
    }

def recibeudp(datos,estado):
    #datos=sentence.split(',')
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
    logging.debug(estado["RPM"]) 
    if int(datos[2])>0:
        estado["RPM"]=1
        estado["ENG"]=True
    else:
        estado["RPM"]=0
        estado["ENG"]=False
    logging.debug("RPM="+str(estado["RPM"]))   

def escribe(linea):
    if len(clientes["sender"]["broker"])>2:
        try:   
            result, mid = clientes["sender"]["cliente"].publish(clientes["sender"]["publish_topic"], json.dumps(dato), qos=2, retain=True )
            logging.info("data sent to %s, rc=%d",clientes["sender"]["broker"],result)
            if result!=0:
                logging.warning("publish rc!=0 : rc= %d ",result)
        except Exception as exErr:
            if hasattr(exErr, 'message'):
                logging.warning("Connection error type 1 = "+ exErr.message)
            else:
                logging.warning("Connection error type 2 = "+ exErr)                   
            sleep(30)
            logging.warning("Connection lost with Sender destination. Retrying")
            arrancaCliente(clientes["sender"],True)

def leeParser(configFile,configData):
    parser = ConfigParser()
    parser.read(configFile)
    if parser.has_section("loglevel"):
        if parser.has_option("loglevel","loglevel"):  
            configData["loglevel"]=parser.get("loglevel","loglevel")
    logging.basicConfig(stream=sys.stderr, format = '%(asctime)-15s  %(message)s', level=configData["loglevel"].upper()) 
    if parser.has_section("udp"):
        if parser.has_option("udp","port"):
            configData["portudp"]=int(parser.get("udp","port"))
    if parser.has_section("settings"):
        if parser.has_option("settings","device_id"):   
            configData["device_id"]=parser.get("settings","device_id")      
        if parser.has_option("settings","location"):    
            configData["location"]=parser.get("settings","location")
        if parser.has_option("settings","influxdb"):    
            configData["influxdb"]=parser.get("settings","influxdb")
        if parser.has_option("settings","destination_mqtt"):    
            configData["destination_mqtt"]=parser.get("settings","destination_mqtt")          
        if parser.has_option("settings","user_name"):   
            configData["username"]=parser.get("settings","user_name")
        if parser.has_option("settings","password"):    
            configData["password"]=parser.get("settings","password")
        if parser.has_option("settings","publish_topic"):   
            configData["publish_topic"]=parser.get("settings","publish_topic")
        if parser.has_option("settings","log_topic"):   
            configData["log_topic"]=parser.get("settings","log_topic")                
        if parser.has_option("settings","port"):   
            configData["port"]=int(parser.get("settings","port"))
        if parser.has_option("settings","num_records"):   
            configData[
            "num_records"]=int(parser.get("settings","num_records"))            

    filename=""
    if parser.has_section("rawfile"):
        if parser.has_option("rawfile","filename"):    
            configData["rawfile"]=parser.get("rawfile","rawfile")
    else:
        configData["rawfile"]=''
    return

if __name__ == '__main__':
    leeParser(configFile,configData)
    tags["deviceId"]=configData["device_id"]
    tags["location"]=configData["location"]
    logging.info(configData)
    # Create  socket AF_INET:ipv4, SOCK_DGAM:udp
    clienteSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clienteSock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)       
    # La direccion en blanco equivale a 0.0.0.0 que equivale a INADDR_ANY
    clienteSock.bind(('' , int(configData["portudp"])))
    logging.info("Socket="+str(clienteSock))
    logging.info("Waiting for message")
    estado={}
    estado["RPM"]=0
    if configData["rawfile"]=='':
        estado["FILE"]=False
    else:
        estado["FILE"]=True
        ahora = datetime.now()
        configData["rawfile"]=configData["rawfile"]+'-'+str(ahora.strftime("%Y%m%d"))
        logging.debug("log filename="+configData["rawfile"])
        fileNMEA=open(configData["rawfile"],"a")         
    estado["ENG"]=False
    estado["RPM"]=0
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
    estado["Mag_dev"] =""
    logging.debug("end of inicialization")
    i=0
    try:  
        logging.debug("define mqtt client")
        logging.debug(configData["device_id"])
        #mqttc = paho.Client(configData["device_id"], clean_session=True)
        mqttc = paho.Client(clean_session=True)
        logging.debug("mqtt client defined")
        logging.debug("mqtt client connected")
        mqttc.reconnect_delay_set(60, 600) 
        #mqttc.username_pw_set(configData["username"] , password=configData["password"])
        mqttc.loop_start()  
        conectado=True
    except:
        logging.error("could not connect to remote mqtt")
        conectado=False
    while True:
        try:
            sentence, origen = clienteSock.recvfrom(1024)
            sentence=sentence.decode("utf-8")
            if ((not estado["ENG"]) and estado["FILE"]):   #engine stopped and there is logfile 
                 fileNMEA.write(sentence)
            else:
                pass
            datos=sentence.split(',')            
            recibeudp(datos,estado)
            if (i>configData["num_records"]):
                cadena="'RPK'"+':'+str(estado["RPM"])+','
                cadena=cadena+"'AWA':"+estado["AWA"]+',' if estado["AWA"]!='' else cadena
                cadena=cadena+"'AWS':"+estado["AWS"]+',' if estado["AWS"]!='' else cadena
                cadena=cadena+"'TWA':"+estado["TWA"]+',' if estado["TWA"]!='' else cadena   
                cadena=cadena+"'TWS':"+estado["TWS"]+',' if estado["TWS"]!='' else cadena
                cadena=cadena+"'lat':"+str(round(estado["lat"],7))+',' if estado["lat"]!='' else cadena
                cadena=cadena+"'lon':"+str(round(estado["lon"],7))+',' if estado["lon"]!='' else cadena
                cadena=cadena+"'Water_T':"+estado["Water_T"]+',' if estado["Water_T"]!='' else cadena
                cadena=cadena+"'Rudder_A':"+estado["Rudder_A"]+',' if estado["Rudder_A"]!='' else cadena
                cadena=cadena+"'SOW':"+estado["SOW"]+',' if estado["SOW"]!='' else cadena
                cadena=cadena+"'SOG':"+estado["SOG"]+',' if estado["SOG"]!='' else cadena
                cadena=cadena+"'Head_T':"+estado["Head_T"]+',' if estado["Head_T"]!='' else cadena
                cadena=cadena+"'Head_M':"+estado["Head_M"]+',' if estado["Head_M"]!='' else cadena
                #cadena=cadena+"'Mag_dev':"+estado["Mag_dev"] if estado["Mag_dev"]!='' else cadena
                cadena=cadena.strip(',')
                cadena='{'+cadena +'}'
                lostags="{'deviceId':\""+tags["deviceId"]+"\",'location'"+":\""+tags["location"]+"\"}"
                logging.debug(cadena)
                logging.debug(lostags)
                try:
                    #datosJSON=json.dumps('{"measurement":"'+measurement+'","time":'+str(estado["hora"])+',"fields":'+cadena+',"tags":'+tags+'}')
                    datosJSON1=  "{'measurement':\""+measurement+"\",'time':"+str(estado["hora"])+",'fields':"+cadena+",'tags':"+lostags+"}"
                    #datosJSON1=["'measurement':'"+measurement+"','time':"+str(estado["hora"])+",'fields':"+cadena+ ",'tags':"+json.dumps(tags)]
                    datosJSON=json.loads(datosJSON1)
                    logging.info(datosJSON)
                    result, mid = mqttc.publish(configData["publish_topic"], datosJSON, 1, True )
                except:
                    logging.warning("could not JSONize "+datosJSON1)
                i=0
                estado["ENG"]=False
                if (estado["FILE"]):
                    fileNMEA.flush()
            if datos[0]!="$ERRPM":  # only increments counter if data is different of $ERRPM
                i+=1
            if conectado==False:
                try:  
                    logging.debug("define mqtt client",configData["device_id"])
                    #mqttc = paho.Client(configData["device_id"], clean_session=True)
                    mqttc = paho.Client(clean_session=True)
                    logging.debug("mqtt client defined")
                    mqttc.connect(configData["destination_mqtt"], configData["port"], 60)
                    logging.debug("mqtt client connected")
                    mqttc.reconnect_delay_set(60, 600) 
                    #mqttc.username_pw_set(configData["username"] , password=configData["password"])
                    conectado=True
                except:
                    logging.error("could not connect to remote mqtt")
                    conectado=False
        except KeyboardInterrupt:
            if (estado["FILE"]):
                fileNMEA.close()
            break
        except:
            if (estado["FILE"]):
                fileNMEA.close()
            logging.error("Abnormal end of program")
    exit()

