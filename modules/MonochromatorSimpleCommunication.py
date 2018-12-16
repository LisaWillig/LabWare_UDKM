# -*- coding: utf-8 -*-
"""
Created on Tue Aug 22 14:26:51 2017

@author: lwillig
"""
import serial


ser = serial.Serial()
ser.port = 'COM1'
ser.baudrate=9600
ser.bytesize = serial.EIGHTBITS
ser.parity = serial.PARITY_NONE
ser.stopbits = serial.STOPBITS_ONE 
ser.timeout=0.1
ser.close() 
ser.open()

#befehl="GOWAVE 638\r\n"
befehl="?GRATINGS\r"

befehlb= befehl.encode()
ser.flushInput()
ser.flushOutput()
ser.write(befehlb)
resunicode=ser.readline()
resunicode2=ser.readline()
resunicode2=ser.readline()
resunicode2=ser.readline()
resunicode3=ser.readline()
resunicode4=ser.readline()
resunicode5=ser.readline()
res=resunicode.decode()
res2=resunicode2#.decode()
res3=resunicode3#.decode()
res4=resunicode4#.decode()
res5=resunicode5#.decode()
res=res.rstrip('\r')
#res2=res2.rstrip('\r')
print(res)
print(res2)
print(res3)
print(res4)
print(res5)
ser.close() 
       
    
 
