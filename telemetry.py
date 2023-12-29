"""Send log messages to remote log aggregation servers."""
import threading
import requests
import os
import sys
from loguru import logger
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

bucket = os.environ.get("INFLUXDB_BUCKET")
org = os.environ.get("INFLUXDB_ORG")
token = os.environ.get("INFLUXDB_TOKEN")
url = os.environ.get("INFLUXDB_URL")

if not all((bucket, org, token, url)):
    logger.warning("Failed to read InfluxDB environment variables.")

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


def send_point_in_thread(temperatures):
    logging_thread = threading.Thread(
        target=send_point, args=(temperatures)
    )
    logging_thread.start()


def send_point(temperatures):
    try:
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
        write_api.write(bucket=bucket, org=org, record=p)
    except Exception as e:
        logger.warning(f"Error sending point to InfluxDB: {e}")


if __name__ == "__main__":
    pass
    # send_log_message(sys.argv[1])
