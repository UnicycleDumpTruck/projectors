import threading
import time
import serial
import requests
import os
import sys
from loguru import logger
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
from rich.traceback import install

install(show_locals=True)

DEBUG = True

bucket = os.environ.get("INFLUXDB_BUCKET")
org = os.environ.get("INFLUXDB_ORG")
token = os.environ.get("INFLUXDB_TOKEN")
url = os.environ.get("INFLUXDB_URL")

if not all((bucket, org, token, url)):
    logger.warning("Failed to read InfluxDB environment variables.")
    raise AssertionError("Failed to read InfluxDB environment variables.")

client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)

write_api = client.write_api(write_options=SYNCHRONOUS)

p = (
    influxdb_client.Point("exhibit_boot")
    .tag("location", "Animate")
    .field("exhibit_name", "olaf")
)
try:
    write_api.write(bucket=bucket, org=org, record=p)
except Exception as e:
    logger.warning(f"Error sending boot point to InfluxDB: {e}")
    if DEBUG:
        raise


def send_error(proj: int, err: str) -> None:
    p = (
        influxdb_client.Point("projector_status")
        .tag("location", "Animate")
        .tag("projector", proj)
        .field("error", err)
    )
    print(p)    
    send_point_in_thread(p)


def send_power_status(proj: int, status: bool) -> None:
    p = (
        influxdb_client.Point("projector_status")
        .tag("location", "Animate")
        .tag("projector", proj)
        .field("power_status", status)
    )
    print(p)    
    send_point_in_thread(p)
    

def send_temps(temperatures: list) -> None:
    p = (
        influxdb_client.Point("projector_status")
        .tag("location", "Animate")
        .tag("projector", temperatures[0])
        .field("temp_1", temperatures[1])
        .field("temp_2", temperatures[2])
        .field("temp_3", temperatures[3])
        .field("temp_4", temperatures[4])
        .field("temp_5", temperatures[5])
        .field("temp_6", temperatures[6])
        .field("temp_7", temperatures[7])
        .field("temp_8", temperatures[8])
    )
    send_point_in_thread(p)


def send_point_in_thread(p):
    logging_thread = threading.Thread(target=send_point, args=((p,)))
    logging_thread.start()


def send_point(p):
    try:
        write_api.write(bucket=bucket, org=org, record=p)
    except Exception as e:
        logger.warning(f"Error sending point to InfluxDB: {e}")
        if DEBUG:
            raise


ser0 = serial.Serial(
    port="/dev/ttyUSB0",
    baudrate=19200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_TWO,
    bytesize=serial.EIGHTBITS,
)

ser1 = serial.Serial(
    port="/dev/ttyUSB1",
    baudrate=19200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_TWO,
    bytesize=serial.EIGHTBITS,
)

serials = (ser0, ser1)

if ser0.isOpen():
    ser0.close()
ser0.open()

if ser1.isOpen():
    ser1.close()
ser1.open()

print(ser0.portstr, " , ", ser1.portstr)


def get_error(proj: int) -> str:
    try:
        print(f"Requesting error status from projector: {proj}.")
        serials[proj].write(("\r" + "get=err" + "\r").encode())
        out = ""
        time.sleep(1)
        while serials[proj].inWaiting() > 0:
            out += str(serials[proj].read(1))[2:3]
        if out != "":
            print(out)
            # Ideally returns no error:
            # i:OK\g:ERR=NO_ERROR\
            err = out [11:-1]
            print(err)
            err = None if err == "NO_ERROR" else err
            print(f"Projector {proj} err status read as: ", err)
        return err
    except Exception as e:
        print(f"Exception getting error status from projector {proj}: {e}")
        if DEBUG:
            raise

def get_power(proj: int) -> bool:
    try:
        print(f"Requesting power status from projector: {proj}.")
        serials[proj].write(("\r" + "get=power" + "\r").encode())
        out = ""
        time.sleep(1)
        while serials[proj].inWaiting() > 0:
            out += str(serials[proj].read(1))[2:3]
        if out != "":
            print(out)
            power_on = out[13:15]
            power_on = True if power_on == "ON" else None
            print(f"Sending projector {proj} power_on: ", power_on)
        return power_on
    except Exception as e:
        print(f"Exception getting power status from projector {proj}: {e}")
        if DEBUG:
            raise

def get_temps(proj: int) -> list:
    try:
        print(f"Requesting temperatures from projector: {proj}.")
        serials[proj].write(("\r" + "get=temp" + "\r").encode())
        out = ""
        time.sleep(1)
        while serials[proj].inWaiting() > 0:
            out += str(serials[proj].read(1))[2:3]
        # i:OK\g:TEMP=8,64.1,43.8,56.5,47.1,21.7,44.3,70.1,77.2\
        if out != "":
            print(out)
            temps = out[14:-1].split(",")
            temps = [float(temp) for temp in temps]
            temps.insert(0, proj)
            return temps
    except Exception as e:
        print(f"Exception getting temperature from projector {proj}: {e}")
        if DEBUG:
            raise

while True:
    try:
        for projector in (0,1):
            err = get_error(projector)
            if err is not None:
                send_error(projector, err)
            time.sleep(1)
            pwr = get_power(projector)
            if pwr is not None:
                send_power_status(projector, pwr)
            time.sleep(1)
            temps = get_temps(projector)
            print(f"Sending projector {projector} temps: ", temps)
            send_temps(temps)
            time.sleep(1)
        time.sleep(600)

    except Exception as e:
        print(f"Exception getting power or temperature: {e}")
        if DEBUG:
            raise
