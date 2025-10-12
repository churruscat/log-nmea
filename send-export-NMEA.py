#!/usr/bin/env python
''' chuRRuscat@Morrastronix V1.0  2021
************************************************************************************
Read an udp stream coming from OpenCPN
Cofiguration data in: /etc/recibeudp/recibeudp.conf
# log_level: specify log detail. valid values are:
# none,debug, info, warning, error ,critical
#[log_level]
#   log_level=warning
#[udp]
#   port=4000 
#[raw_file]
#    filename=/var/log/recibeudp   # program will add yymmdd.log to name

'''
import socket
import sys
import logging, json
import paho.mqtt.client as paho
from datetime import datetime
#import datetime
from time import time
#import pynmea2

fichero_origen='NMEAtst2.csv'
log_level='info'
configFile='/etc/recibeudp/recibeudp.conf'
tipoLogging=['none','debug', 'info', 'warning', 'error' ,'critical']
tags={"deviceId":"Raymarine","location":"Barco"}
measurement='NMEA'
configData={
    "device_id":"NMEA",
    "location":"Barco",
    "influxdb":'127.0.0.1',
    "username":"",
    "password":"",
    "destination_host":'192.168.1.12',
    "publish_topic":"datosVela",
    "log_topic":"NMEA",
    "port":'1883',
    "portudp":"4000",
    "loglevel":"info",
    "fileraw":""
    }

def lee_fila(sentence,estado):
    datos=sentence.split(',')
    estado["AWA"]=datos[1]
    estado["AWS"]=datos[2]
    estado["Head_M"]=datos[3]
    estado["Head_T"]=datos[3]
    estado["RPM"]=datos[5]
    estado["Rudder_A"]=datos[6]
    estado["SOG"]=datos[7]
    estado["SOW"]=datos[8]
    estado["TWA"]=datos[9]
    estado["TWS"]=datos[10]
    estado["Water_T"]=datos[11]
    estado["deviceId"]=datos[12]
    estado["lat"]=datos[13]
    estado["location"]=datos[14]
    estado["lon"]= datos[15]
    fecha=datos[0]
    x = datetime.strptime( fecha[:-4], '%Y-%m-%dT%H:%M:%S.%f')
    estado["hora"]=int(x.timestamp()*1e9)

    
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

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr, format = '%(asctime)-15s  %(message)s', level=log_level.upper()) 
    tags["deviceId"]=configData["device_id"]
    tags["location"]=configData["location"]
    logging.info(configData)

    estado={}    
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
    file_in=open(fichero_origen)

    try:  
        print('define mqtt client',configData["device_id"])
        mqttc = paho.Client(configData["device_id"], clean_session=True)
        logging.info('mqtt client defined')
        mqttc.connect(configData["destination_host"], configData["port"], 60)
        logging.info("mqtt client connected")
        mqttc.reconnect_delay_set(60, 600) 
        #mqttc.username_pw_set(configData["username"] , password=configData["password"])
        conectado=True
    except:
        logging.error("could not connect to remote mqtt")
        conectado=False
    print(configData)
    while True:
        try:  
            linea=file_in.readline()    
            lee_fila(linea,estado)

            #dato='{"measurement":"'+"NMEA"+'","time":'+estado["epoch"]+\
             #',"fields":'+json.dumps(payload[0])+',"tags":'+tags+'}'
            cadena='"RPM"'+':'+str(estado["RPM"])+','
            cadena=cadena+'"AWA":'+estado["AWA"]+',' 
            cadena=cadena+'"AWS":'+estado["AWS"]+',' 
            cadena=cadena+'"TWA":'+estado["TWA"]+','   
            cadena=cadena+'"TWS":'+estado["TWS"]+',' 
            cadena=cadena+'"lat":'+ str( round(float(estado["lat"]),7)) +',' 
            cadena=cadena+'"lon":'+ str(round(float(estado["lon"]),7))+',' 
            cadena=cadena+'"Water_T":'+estado["Water_T"]+',' 
            cadena=cadena+'"Rudder_A":'+estado["Rudder_A"]+',' 
            cadena=cadena+'"SOW":'+estado["SOW"]+',' 
            cadena=cadena+'"SOG":'+estado["SOG"]+',' 
            cadena=cadena+'"Head_T":'+estado["Head_T"]+',' 
            cadena=cadena+'"Head_M":'+estado["Head_M"]+',' 
            cadena=cadena.strip(',')
            cadena='{'+cadena +'}'
            try:
                cadena='{"measurement":"'+measurement+'","time":'+str(estado["hora"])+',"fields":'+cadena+',"tags":'+json.dumps(tags)+'}'
                #datoJSON=json.loads('{"measurement":"'+measurement+'","time":'+str(estado["hora"])+',"fields":'+cadena+',"tags":'+json.dumps(tags)+'}')
                logging.debug(cadena)
                #datoJSON=json.loads(cadena)
                datoJSON=cadena
                logging.info(datoJSON)
                result, mid = mqttc.publish(configData["publish_topic"], datoJSON, 1, True )
            except:
                logging.warning("could not JSONize ",'{"measurement":"'+measurement+'","time":'+str(estado["hora"])+',"fields":'+cadena+',"tags":'+tags+'}')
        
            if conectado==False:
                try:  
                    logging.info("define mqtt client "+configData["device_id"])
                    mqttc = paho.Client(configData["device_id"], clean_session=True)
                    logging.info("mqtt client defined")
                    mqttc.connect(configData["destination_host"], configData["port"], 60)
                    logging.info("mqtt client connected")
                    mqttc.reconnect_delay_set(60, 600) 
                    #mqttc.username_pw_set(configData["username"] , password=configData["password"])
                    conectado=True
                except:
                    logging.error("could not connect to remote mqtt "+configData["destination_host"]+":"+ configData["port"])
                    conectado=False                       
        except KeyboardInterrupt:
            break;

    exit
