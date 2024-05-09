import logging
import os
from datetime import datetime

from phue import Bridge

from flask import Flask
from flask_cors import CORS


app = Flask(__name__)
CORS(app)


logging.basicConfig(level=logging.INFO)

co2 = os.getenv('CO2_SOCKET')
bridge_ip = os.getenv('BRIDGE_IP')


logging.info(f"CO2 socket       : {co2}")
logging.info(f"Bridge IP        : {bridge_ip}")
logging.info(f"Server port      : {os.getenv('SERVER_PORT')}")
os.getenv('SERVER_PORT')

b = Bridge(bridge_ip)
b.connect()


@app.route('/', methods=['get'])
def get_status_and_respond():
    co2_status = b.get_light(int(19))["state"]["on"]

    current_time = datetime.now().strftime("%Y/%m/%d - %H:%M:%S")

    if co2_status:
        co2_status = "On"
    else:
        co2_status = "Off"

    return f"{current_time}, CO2 is {co2_status}"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv('SERVER_PORT'), debug=True)