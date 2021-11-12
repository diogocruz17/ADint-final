import os
from flask import Flask, render_template, request, url_for, redirect,send_from_directory,jsonify, abort, session
import requests
from sqlalchemy.sql.expression import true
from sqlalchemy.sql.sqltypes import Float
from werkzeug.utils import secure_filename
import random
import string
import time
import json


from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
import datetime
from sqlalchemy.orm import sessionmaker
from os import path

from requests_oauthlib import OAuth2Session


client_id = "851490151334144"
client_secret = "75qyTg+A8i/UnmzYkD7fo4xKB9rQGymUZcB9HA+c2QmhxMyFyPTp3kuNoJecAxqcrD7SZ9BlHpAIBPFOBmzQaw=="
authorization_base_url = 'https://fenix.tecnico.ulisboa.pt/oauth/userdialog'
token_url = 'https://fenix.tecnico.ulisboa.pt/oauth/access_token'


#SLQ access layer initialization
DATABASE_FILE = "usercodes.sqlite"
db_exists = False
if path.exists(DATABASE_FILE):
    db_exists = True
    print("\t database already exists")

engine = create_engine('sqlite:///%s'%(DATABASE_FILE), echo=False) #echo = True shows all SQL calls

Base = declarative_base()

class UserCode(Base):
    __tablename__= 'UserCode'
    user = Column(String, primary_key=True)
    code = Column(String)
    time_created = Column(Float)
    def __repr__(self):
        return "<UserCode(user = %s code = %s time_created = %f)>" % (
                        self.user, self.code, self.time_created)

Base.metadata.create_all(engine) #Create tables for the data models


Session = sessionmaker(bind=engine)
session = Session()

def newCode(user, token, code):
    response = requests.post('http://localhost:9000/newCode', json={'user': user, 'token': token, 'code': code})
    status = response.status_code
    if status == 200:
        return 1
    else:
        return 0
    
def checkCodeData(code):
    response = requests.get('http://localhost:9000/codeCheck', json={'code': code})
    status = response.status_code
    if status == 200:
        return 1
    else:
        return 0


def Authenticate(token):
    try:
        github = OAuth2Session(client_id, token = token)
        info = github.get('https://fenix.tecnico.ulisboa.pt/api/fenix/v1/person').json()
        ist_id = info['username']
        user_token = token['access_token']
        return ist_id, user_token
    except:
        return None, None



app = Flask(__name__)


def generateCode(user, token):
    size = 12
    code = ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k = size))    
    return str(user+token+code)




@app.route("/")
def index():
    return render_template("index.html", message="Dynamic content!")


@app.route("/admin/createGate", methods = ['POST', 'GET'])
def createGate():
    return render_template("newGate.html")

@app.route("/admin/newGate", methods = ['POST', 'GET'])
def newGate():
    gate_id = int(request.form['gateID'])
    location = request.form['location']
    try:
        response = requests.post('http://localhost:8000/newGate', json={'gateID': gate_id, 'location': location})
    except requests.exceptions.ConnectionError:
        return("Could't connect to Gate Data. Exiting ...")
    status = response.status_code
    if(status == 201):
        response_Json = response.json()
        return render_template("GateCreated.html", secret = response_Json['secret'])
    if(status == 200):
        response_Json = response.json()
        return render_template("GateNotCreated.html", message = response_Json['response'])
    if(status == 500):
        return "There was a problem with the server. Gate not created"
    if(status == 400):
        return "There was a problem with the json formating"

@app.route("/admin/gateList", methods = ['GET'])
def listGate():
    try:
        response = requests.get('http://localhost:8000/gateList')
    except requests.exceptions.ConnectionError:
        return("Could't connect to Gate Data. Exiting ...")
    response_Json = response.json()
    gate_info = [[]] * 4
    try:
        gate_info[0] = response_Json['gate_id']
        gate_info[1] = response_Json['secret']
        gate_info[2] = response_Json['location']
        gate_info[3] = response_Json['gate_opens']
    except:
        return 'Gate list with wrong format'
    size = len(gate_info[0])
    return render_template("listGates.html", size = size,  gate_info = gate_info)




@app.route("/user/newCode", methods =['GET'])
def getCode():
    request_json = request.get_json()
    token = json.loads(request_json)
   
    ist_id, user_token = Authenticate(token)
    if ist_id == None:
        abort(403)

    code = generateCode(ist_id, user_token)
    print(code)
    status = newCode(ist_id, user_token, code)
    print(status)
    if status == 1:
        return jsonify({'code' : code})
    else:
        return "", 301

@app.route("/user/newUser", methods =['POST'])
def newUserEndpoint():
    request_json = request.get_json()
    token = json.loads(request_json)
   
    ist_id, user_token = Authenticate(token)
    if ist_id == None:
        abort(403)
    try:
         response = requests.post('http://localhost:9000/newUser', json = {'ist_id': ist_id, 'user_token': user_token})
    except requests.exceptions.ConnectionError:
        print("Could't connect to UserData. Exiting ...")
        exit(0)

    if response.status_code == 200:
        return "", 200
    else:
        return "", 500
    





@app.route("/gate/gateCheck", methods = ['GET'])
def checkGate():
    request_json = request.get_json()
    try:
        gate_id=request_json['gate_id']
        secret=request_json['secret']
    except:
        abort(400)
    try:
        response = requests.get('http://localhost:8000/gateCheck', json = request_json)
    except requests.exceptions.ConnectionError:
        abort(503)
    if response.status_code == 400:
        print('Wrong formating on info received')
        abort(400)
    response_Json = response.json()
    try:
        status=response_Json['status']
        message=response_Json['message']
    except:
        abort(400)
    return response_Json


@app.route("/gate/codeCheck", methods = ['POST', 'GET'])
def checkCode():
    request_json = request.get_json()
    try:
        code = request_json['code']
        print(code)
    except:
        abort(400)
    
    auth = checkCodeData(code)
    if auth == 1:
        """"
        try:
            response = requests.post('http://localhost:8000/%s/open' % gate_id)
        except requests.exceptions.ConnectionError:
            abort(503)
        """
        return '', 200
    else:
        abort(401)


if __name__ == "__main__":
    app.run(port=7000, debug=True)