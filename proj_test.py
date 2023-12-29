import time
import serial

ser = serial.Serial(
    port='/dev/ttyUSB1',
    baudrate=19200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_TWO,
    bytesize=serial.EIGHTBITS
)

if ser.isOpen() : 
    ser.close()
ser.open()

print(ser.portstr)

print('Enter your commands below.\r\nInsert "exit" to leave the application.')

cmd_input=1
while 1 :
    # get keyboard input
    cmd_input = input(">> ")
    if cmd_input == 'exit':
        ser.close()
        exit()
    else:
        ser.write(('\r' + cmd_input + '\r').encode())
        out = ''
        time.sleep(1)
        while ser.inWaiting() > 0:
            out += str(ser.read(1))[2:3]

        if out != '':
            print(">>" + out)
