import serial
import time

data = serial.Serial(
                  'COM3',
                  baudrate = 9600,
                  parity=serial.PARITY_NONE,
                  stopbits=serial.STOPBITS_ONE,
                  bytesize=serial.EIGHTBITS,                  
                  timeout=1
                  )

def Tracking():
    while True:
        d = data.read(12)
        d = d.decode('utf-8', 'ignore')
        d = d.strip()
        if len(d) == 12:
            print(d)
            break
    time.sleep(1)
    return d
    
