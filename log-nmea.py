#!/usr/bin/env python
''' chuRRuscat@Morrastronix V1.0  2021
************************************************************************************
Read an udp stream coming from OpenCPN and :
   - summarizes it and sends it to an mqtt queue
   - if engine is stopped, stores all data in a file
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
import paho.mqtt.client as mqtt
from datetime import datetime
#import datetime
from time import time
#import pynmea2

configFile='/etc/log-nmea/log-nmea.conf'
tipoLogging=['none','debug', 'info', 'warning', 'error' ,'critical']
measurement='NMEA'
configData={
    "device_id":"NMEA",
    "location":"Boat",
    "influxdb":"127.0.0.1",
    "username":"",
    "password":"",
    "destination_mqtt":"destination.host.com",
    "publish_topic":"cooked",
    "log_topic":"NMEA",
    "port":"1883",
    "portudp":"4000",
    "loglevel":"info",
    "rawfile":"",
    "num_records":100
    }
mqttCliente={"name":"log_nmea","broker":"","port":1883,
              "cliente":None,"userid":"","password":"",
              "publish_topic":"cooked"}
estado={
    "ENG":True, 
    "RPM":1,
    "epoch":0, 
    "FILE":False
    }

datosJSON={    
    "measurement":"medidas",
    "time":0,
    "fields": {
        "RPM":0,
        "AWA":0,
        "AWS":0,
        "TWA":0,
        "TWS":0,
        "lat":0,
        "lon":0,
        "Water_T":0,
        "Rudder_A":0,
        "SOW":0,
        "SOG":0,
        "Head_T":0,
        "Head_M":0,
        },
    "tags":{
        "deviceId":"Raymarine",
        "location":"Barco"
        }
    }

def recibeudp(datos,dJSON):
    #datos=sentence.split(',')
    if datos[0]=="$IIHDM":     #Heading
        pass    #NMEA_IIHDM(datos,dJSON)
    elif datos[0]=="$IIMTW":
        NMEA_IIMTW(datos,dJSON)
    elif datos[0]=="$IIRSA":
        NMEA_IIRSA(datos,dJSON)
    elif datos[0]=="$IIMWV":
        NMEA_IIMWV(datos,dJSON)
    elif datos[0]=="$IIDBT":    #depth below transducer
        pass #NMEA_IIDBT(datos)
    elif datos[0]=="$IIMTW":
        NMEA_IIMTW(datos,dJSON)
    elif datos[0]=="$IIVHW":
        NMEA_IIVHW(datos,dJSON)
    elif datos[0]=="$IIVLW":             #distance traveled. 1: Tota, 2: Distance since reset
        pass #NMEA_IIVLW(datos,dJSON)      
    elif datos[0]=="$GPGSV":
        NMEA_GPGSV(datos)
    elif datos[0]=="$GPGLL":
        pass         #NMEA_GPGLL(datos,dJSON)
    elif datos[0]=="$GPRMC":
        NMEA_GPRMC(datos, dJSON)
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
        NMEA_ERRPM(datos, dJSON)
    else:
        logging.warning("unknown directive : "+sentence)
    return

def NMEA_IIDBT(datos): #Depth below transducer
    pass

def NMEA_IIMWV(datos,dJSON):
    if datos[2]=="R":
        dJSON["AWA"]=float(datos[1])
        dJSON["AWS"]=float(datos[3])
    elif datos[2]=="T":
        dJSON["TWA"]=float(datos[1])
        dJSON["TWS"]=float(datos[3])
    return; 

def NMEA_IIMTW(datos,dJSON):
    dJSON["Water_T"]=float(datos[1])
    return;

def NMEA_IIVHW(datos,dJSON):
    if datos[2]=='T':
        dJSON["Head_T"]=float(datos[1])
    if datos[4]=='M':
        dJSON["Head_M"]=float(datos[3]) 
    dJSON["SOW"]=float(datos[5])
    return

def NMEA_IIRSA(datos,dJSON):
    if datos[2]=='A':
        dJSON["Rudder_A"]=float(datos[1]) 

def NMEA_GPGLL(datos,dJSON):
    pass
    if datos[5]=="A" :
        dJSON["lat"]=float(datos[1])/100 
        if datos[2]=="S":
            dJSON["lat"]*=-1
        dJSON["lon"]=float(datos[3])/100 
        if datos[4]=="O" :
            dJSON["lon"]*=-1
    return

def NMEA_GPGSV(datos):
    pass

def NMEA_GPRMC(datos,dJSON):
     if datos[2]=='A':
        dJSON["lat"]=float(datos[3])/100 
        if datos[4]=="S":
            dJSON["lat"]*=-1
        dJSON["lon"]=float(datos[5])/100
        if datos[6]=="O":
            dJSON["lon"]*=-1
        dJSON["SOG"]=float(datos[7])
        dJSON["Head_T"]=float(datos[8])
        if datos[11]!='':
            dJSON["Mag_dev"]=float(datos[10])
            if datos[11]=="O":
                estado["Mag_dev"]=-float(datos[10])
        secs,usecs=divmod(time(),1)   # si a time() le restara altzone tendria la hora local
        datosJSON["time"]=int(int(secs*1000000000)+int(usecs*1000000000))

def NMEA_GPVTG(datos):
    pass

def NMEA_ERRPM(datos,dJSON): 
    global estado 
    #$ERRPM,E|S,Speed,%,A*CRC
    logging.debug(dJSON["RPM"]) 
    if int(datos[2])>0:
        dJSON["RPM"]=1
        estado["ENG"]=True
    else:
        dJSON["RPM"]=0
        estado["ENG"]=False
    logging.debug("RPM="+str(dJSON["RPM"]))   
#*******************************************************************
#****************************** MQTT *******************************
# Funciones de Callback
def on_connect(mqttCliente, userdata, flags, rc):
    logging.debug("Connected to broker")
    pass
 
def on_subscribe(mqttCliente, userdata, mid, granted_qos):
    logging.info("Subscribed OK; message "+str(mid)+"   qos= "+ str(granted_qos))
    sleep(1)

def on_disconnect(mqttCliente, userdata, rc):
    logging.info("Disconnected, rc= "+str(rc))    
    reconectate(mqttCliente)   

def on_publish(mqttCliente, userdata, mid):
    logging.debug("message published "+ str(mid))   

def on_message(mqttCliente, userdata, mid):
    logging.debug("Not subscribed, this is imposible "+ str(mid))   


#Initializes an mqtt Client
def arrancaCliente(mqttCliente, cleanSess):
    if (cleanSess==False):
        mqttCliente["cliente"]= mqtt.Client(mqttCliente["name"],clean_session=cleanSess)           
    else:
        mqttCliente["cliente"]  = mqtt.Client(clean_session=cleanSess) 
    mqttCliente["cliente"].on_connect = on_connect
    mqttCliente["cliente"].on_message = on_message    
    mqttCliente["cliente"].on_connect = on_connect
    mqttCliente["cliente"].on_publish = on_publish
    mqttCliente["cliente"].on_subscribe = on_subscribe
    logging.info("call back registered for "+mqttCliente["name"])
    if (mqttCliente["userid"]!=''):
        mqttCliente["cliente"].username_pw_set(mqttCliente["userid"] , password=mqttCliente["password"])
    mqttCliente["cliente"].connect(mqttCliente["broker"],mqttCliente ["port"])
    return mqttCliente["cliente"]
    
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
            configData["rawfile"]=parser.get("rawfile","filename")
    else:
        configData["rawfile"]=''
    return

if __name__ == '__main__':
    leeParser(configFile,configData)
    mqttCliente["name"]=configData["device_id"]+"_"+configData["location"]
    mqttCliente["userid"]=configData["username"]
    mqttCliente["password"]=configData["password"]
    mqttCliente["broker"]=configData["destination_mqtt"]
    mqttCliente["port"]=configData["port"]
    mqttCliente["publish_topic"]=configData["publish_topic"]
    logging.info(mqttCliente)
    datosJSON["tags"]["deviceId"]=configData["device_id"]
    datosJSON["tags"]["location"]=configData["location"]
    logging.info(mqttCliente)
    # Create  socket AF_INET:ipv4, SOCK_DGAM:udp
    clienteSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clienteSock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)       
    # La direccion en blanco equivale a 0.0.0.0 que equivale a INADDR_ANY
    clienteSock.bind(('' , int(configData["portudp"])))
    logging.info("Socket="+str(clienteSock))
    estado["RPM"]=1
    estado["ENG"]=True
    if configData["rawfile"]=='':
        estado["FILE"]=False
    else:
        estado["FILE"]=True
        ahora = datetime.now()
        configData["rawfile"]=configData["rawfile"]+'-'+str(ahora.strftime("%Y%m%d"))+".log"
        logging.debug("log filename="+configData["rawfile"])
        fileNMEA=open(configData["rawfile"],"a")         
  
    logging.debug("end of inicialization")
    i=0
    try:  
        logging.debug("define mqtt client")
        logging.debug(configData["device_id"])
        mqttc=arrancaCliente(mqttCliente , False)
        mqttc.loop_start()  
        conectado=True
    except:
        logging.error("could not connect to remote mqtt")
        conectado=False
    logging.info("Waiting for message")
    while True:
        try:
            sentence, origen = clienteSock.recvfrom(1024)
            sentence=sentence.decode("utf-8")
            if ((not estado["ENG"]) and estado["FILE"]):   #engine stopped and there is logfile 
                 fileNMEA.write(sentence)
            else:
                pass
            datos=sentence.split(',')            
            recibeudp(datos,datosJSON["fields"])
            if (i>configData["num_records"]):
                try:
                    logging.info(datosJSON)
                    result, mid = mqttc.publish(configData["publish_topic"], json.dumps(datosJSON), 1, True )
                except:
                    logging.warning("Error sending topic")
                    logging.wrning(datosJSON)
                i=0
                estado["ENG"]=True
                if (estado["FILE"]):
                    fileNMEA.flush()
            if datos[0]!="$ERRPM":  # only increments counter if data is different of $ERRPM
                i+=1
            if conectado==False:
                try:  
                    logging.debug("define mqtt client")
                    logging.debug(configData["device_id"])
                    mqttc=arrancaCliente(mqttCliente , False)
                    mqttc.loop_start()  
                    conectado=True
                except:
                    logging.error("could not connect to remote mqtt")
                    conectado=False
        except KeyboardInterrupt:
            if (estado["FILE"]):
                fileNMEA.close()
            mqttCliente["cliente"].loop_stop() 
            logging.error("Abnormal end of program")
            exit()
    exit()

