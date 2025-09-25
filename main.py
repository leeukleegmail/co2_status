import atexit
import logging
import os
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, redirect, url_for, render_template_string
from phue import Bridge

logging.basicConfig(level=logging.INFO)

co2 = os.getenv('CO2_SOCKET', '19')
bridge_ip = os.getenv('BRIDGE_IP', "192.168.178.158")
server_port= os.getenv('SERVER_PORT', "5002")
on_time = os.getenv('ON_TIME', '11:00')
off_time = os.getenv('ON_TIME', '18:00')

logging.info(f"CO2 socket       : {co2}")
logging.info(f"Bridge IP        : {bridge_ip}")
logging.info(f"Server port      : {server_port}")
logging.info(f"Switch On Time   : {on_time}")
logging.info(f"Switch Off Time  : {off_time}")

b = Bridge(bridge_ip)
b.connect()

scheduler = BackgroundScheduler()
scheduler.start()

app = Flask(__name__)

# In-memory store of task statuses
co2_config = {'on_time': on_time, 'off_time': off_time}

on_time_options = ["9:00", "10:00", "11:00", "12:00"]
off_time_options = ["18:00", "19:00", "20:00", "21:00"]

# HTML Template
HTML_TEMPLATE = """
<!doctype html>
<html>
   <head>
      <title>C02 Schedule</title>
      <style>
        .button-container {
            display: flex;
            gap: 10px; /* space between buttons */
        }

        button {
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
        }

        h1 {
            font-family: Arial, sans-serif;
        }
    </style>
   </head>
   <body>
      <h2>Status</h2>
      <table border="1" cellpadding="5">
         <tr>
            <th>C02 Status</th>
         </tr>
         <tr>
            <td align ="center">{{ co2_status }}</td>
         </tr>
      </table>
      <h2>Schedule</h2>
      <p></p>
      <table border="1" cellpadding="5">
         <tr>
            <th>On Time</th>
            <th>Off Time</th>
         </tr>
         <tr>
            <td align ="center">{{ on_time }}</td>
            <td align ="center">{{ off_time }}</td>
         </tr>
      </table>
      <h2></h2>
      <form method="POST" action="{{ url_for('set_status') }}">
         <label for="on_time">Choose On Time:</label>
         <select name="on_time" id="on_time">
         {% for on_time_option in on_time_options %}
         <option value="{{ on_time_option }}" {% if on_time_option == on_time %}selected{% endif %}>
         {{ on_time_option }}
         </on_time_option>
         {% endfor %}
         </select>
         <p></p>
         <label for="off_time">Choose Off Time:</label>
         <select name="off_time" id="off_time">
         {% for off_time_option in off_time_options %}
         <option value="{{ off_time_option }}" {% if off_time_option == off_time %}selected{% endif %}>
         {{ off_time_option }}
         </off_time_option>
         {% endfor %}
         </select>
         <p></p>
         <button type="submit">Update Time</button>
      </form>
      <p></p>
      <h2>Manual Override</h2>
     <div class="button-container">

      <form action="/turn_on" method="post">
        <button type="submit">Turn On</button>
      </form>
      <form action="/turn_off" method="post">
        <button type="submit">Turn Off</button>
      </form>
      </div>
      <h2>Configuration</h2>
      <table border="1" cellpadding="5">
         <tr>
            <th>Bridge IP</th>
            <th>Switch Number</th>
            <th>Server Port</th>
         </tr>
         <tr>
            <td>{{ bridge_ip }}</td>
            <td align ="center">{{ socket_number }}</td>
            <td align ="center">{{ server_port }}</td>
         </tr>
      </table>
   </body>
</html>
"""


def get_co2_status():
    if b.get_light(int(19))["state"]["on"]:
        return "On"
    else:
        return "Off"


def switch_co2(action, message):
    print(action)
    current_time = datetime.now().strftime("%Y/%m/%d - %H:%M:%S")
    b.set_light(light_id=int(co2), parameter='on', value=action)
    logging.info(f"{current_time}, Switching {message} CO2 {co2}")


def co2_on():
    switch_co2(True, 'On')


def co2_off():
    switch_co2(False, 'Off')


def update_schedule(schedule_on_time, schedule_off_time):
    scheduler.add_job(func=co2_on,
                      trigger='cron',
                      hour=int(schedule_on_time.split(':')[0]),
                      id='co2_on',
                      name=f'turning on C02 at {schedule_on_time}',
                      replace_existing=True)
    scheduler.add_job(func=co2_off,
                      trigger='cron',
                      hour=int(schedule_off_time.split(':')[0]),
                      id='co2_off',
                      name=f'turning off C02 at {schedule_off_time}',
                      replace_existing=True)

    atexit.register(lambda: scheduler.shutdown())


@app.route('/', methods=['GET'])
def index():
    co2_status = get_co2_status()
    return render_template_string(HTML_TEMPLATE,
                                  on_time_options=on_time_options,
                                  off_time_options=off_time_options,
                                  co2_status=co2_status,
                                  on_time=co2_config['on_time'],
                                  off_time=co2_config['off_time'],
                                  socket_number=co2,
                                  bridge_ip=bridge_ip,
                                  server_port=server_port)


@app.route('/set_status', methods=['POST'])
def set_status():
    new_on_time = request.form.get('on_time')
    new_off_time = request.form.get('off_time')
    co2_config["on_time"] = new_on_time
    co2_config["off_time"] = new_off_time

    update_schedule(new_on_time, new_off_time)
    return redirect(url_for('index'))

device_state = {'status': 'OFF'}


@app.route('/turn_on', methods=['POST'])
def turn_on():
    device_state['status'] = 'ON'
    print("on")
    return redirect(url_for('index'))


@app.route('/turn_off', methods=['POST'])
def turn_off():
    device_state['status'] = 'OFF'
    print("off")
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0',port=int(server_port))