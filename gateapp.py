import requests
import sys
import time
from flask import Flask, render_template, request, url_for, redirect,send_from_directory,jsonify, abort, session
from flask.templating import render_template
from werkzeug.wrappers import response
import requests


try:
    gate_id = sys.argv[1]
    secret = sys.argv[2]
except:
    print("Information missing. Please provide the Gate ID and Secret")
    print("Exiting...")
    exit(0)


print("Contacting Server...")
try:
    response = requests.get('http://localhost:7000/gate/gateCheck', json={ 'gate_id' : gate_id, 'secret' : secret })
except requests.exceptions.ConnectionError:
        print("Couldn't reach server")
        exit(0)
if response.status_code == 400:
    print('Information formated incorrectly, exiting...')
    exit(0)
if response.status_code == 503:
    print("Couldn't reach server")
    exit(0)
response_Json = response.json()
status, message = response_Json['status'], response_Json['message']
if status != 1:
    print(message)
    print("Exiting...")
    exit(0)



app = Flask(__name__)

@app.route("/")
def index():
    return render_template("camera.html")

@app.route("/codeCheck/<code>")
def codeCheck(code):
    try:
        response = requests.get('http://localhost:7000/gate/codeCheck', json = {'code': code, 'gate_id': gate_id})
    except:
        return render_template("ServerOffline.html")
    if response.status_code == 200:
        return jsonify({'access': 1})
    else:
        return jsonify({'access': 0})
    

if __name__ == "__main__":
    app.run(port=2500, debug=True)