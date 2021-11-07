import os
from flask import Flask, render_template, request, url_for, redirect,send_from_directory,jsonify, abort
import requests
from sqlalchemy.sql.expression import true
from sqlalchemy.sql.sqltypes import Float
from werkzeug.utils import secure_filename
import random
import string
import time


from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
import datetime
from sqlalchemy.orm import sessionmaker
from os import path


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
    response = requests.post('http://localhost:9000/newcode', json={'user': user, 'token': token, 'code': code})
    status = response.status_code
    if status == 200:
        return 1
    else:
        return 0
    
def checkCodeData(user, code):
    try:
        user_q = session.query(UserCode).filter(UserCode.user == user).first()
        code_database = user_q.code
        time_created = user_q.time_created
        time_check = time.time()
        if code == code_database and (time_check-time_created)<60 :
            return 1
        else:
            return 0
    except:
        return 0



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

@app.route("/user/newCode", methods =['POST'])
def getCode():
    request_json = request.get_json()
    try:
        user = request_json['user']
        token = request_json['token']
    except:
        return 0
    code = generateCode()
    status = newCode(user, code)
    if status == 1:
        return jsonify({'code' : code}), 201
    else:
        return "", 301

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
    print(request_json)
    user = 'default'
    try:
        user_code = request_json['code']
        gate_id = request_json['gate_id']
    except:
        abort(400)
    auth = checkCodeData(user, user_code)
    if auth == 1:
        try:
            response = requests.get('http://localhost:8000/%s/open' % gate_id)
        except requests.exceptions.ConnectionError:
            abort(503)
        return '', 202
    else:
        abort(401)


if __name__ == "__main__":
    app.run(port=7000, debug=True)