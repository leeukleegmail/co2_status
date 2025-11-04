import atexit
import logging
import os
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, redirect, url_for, render_template_string, render_template, flash
from phue import Bridge

logging.basicConfig(level=logging.INFO)

co2 = os.getenv('CO2_SOCKET', '19')
bridge_ip = os.getenv('BRIDGE_IP', "192.168.178.158")
server_port= os.getenv('SERVER_PORT', "5002")
on_time = os.getenv('ON_TIME', '10:00')
off_time = os.getenv('ON_TIME', '20:00')

logging.info(f"CO2 socket       : {co2}")
logging.info(f"Bridge IP        : {bridge_ip}")
logging.info(f"Server port      : {server_port}")
logging.info(f"Switch On Time   : {on_time}")
logging.info(f"Switch Off Time  : {off_time}")

b = Bridge(bridge_ip)
b.connect()

scheduler = BackgroundScheduler()
scheduler.start()

app = Flask(__name__, static_folder='templates/assets', static_url_path='/assets')
app.secret_key = "4567889900"

# In-memory store of schedule
co2_schedule = {'on_time': on_time, 'off_time': off_time}

on_time_options = ["9:00", "10:00", "11:00", "12:00"]
off_time_options = ["18:00", "19:00", "20:00", "21:00"]


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
    return render_template('index.html',
                                  on_time_options=on_time_options,
                                  off_time_options=off_time_options,
                                  co2_status=co2_status,
                                  on_time=co2_schedule['on_time'],
                                  off_time=co2_schedule['off_time'],
                                  socket_number=co2,
                                  bridge_ip=bridge_ip,
                                  server_port=server_port)


@app.route('/set_schedule', methods=['POST'])
def set_schedule():
    new_on_time = request.form.get('on_time')
    new_off_time = request.form.get('off_time')
    co2_schedule["on_time"] = new_on_time
    co2_schedule["off_time"] = new_off_time

    update_schedule(new_on_time, new_off_time)
    flash("Updated Successfully!!!")

    return redirect(url_for('index'))

device_state = {'status': 'OFF'}


@app.route('/turn_on', methods=['POST'])
def turn_on():
    device_state['status'] = 'ON'
    co2_on()
    return redirect(url_for('index'))


@app.route('/turn_off', methods=['POST'])
def turn_off():
    device_state['status'] = 'OFF'
    co2_off()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0',port=int(server_port))