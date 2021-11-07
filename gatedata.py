import os
from flask import Flask, render_template, request, url_for, redirect,send_from_directory,jsonify, abort
import requests
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
import itertools
import random
import string

import datetime
from sqlalchemy.orm import sessionmaker
from os import path

#SLQ access layer initialization
DATABASE_FILE = "gatedata.sqlite"
db_exists = False
if path.exists(DATABASE_FILE):
    db_exists = True
    print("\t database already exists")

engine = create_engine('sqlite:///%s'%(DATABASE_FILE), echo=False) #echo = True shows all SQL calls

Base = declarative_base()

class GateData(Base):
    __tablename__= 'GateData'
    gate_id = Column(Integer, primary_key=True)
    secret = Column(String)
    location = Column(String)
    gate_opens = Column(Integer)

    def __repr__(self):
        return "<GateData(gate_id = %d secret = %d location = '%s' gate_opens = %d)>" % (
                        self.gate_id, self.secret, self.location, self.gate_opens)

def generateSecret():
    size = 5
    code = ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k = size))    
    return str(code)


def newGate(gate_id, location):
    secret = generateSecret()
    gate_opens = 0
    new_gate = GateData(gate_id = gate_id, secret = secret, location = location, gate_opens = gate_opens)
    try:
        session.add(new_gate)
        session.commit()
        return secret
    except:
        session.rollback()
        return None

def openGate(gate_id):
    opens_q = session.query(GateData).filter(GateData.gate_id == gate_id).first()
    if opens_q == None:
        return 0
    else:
        gate_opens = opens_q.gate_opens+1
        opens_q.gate_opens =  gate_opens
        session.commit()
        return 1


def listGates():
    gate_info = [[]] * 4
    query_aux = session.query(GateData.gate_id).all()
    gate_info[0] = list(itertools.chain(*query_aux))

    query_aux = session.query(GateData.secret).all()
    gate_info[1] = list(itertools.chain(*query_aux))

    query_aux = session.query(GateData.location).all()
    gate_info[2] = list(itertools.chain(*query_aux))

    query_aux = session.query(GateData.gate_opens).all()
    gate_info[3] = list(itertools.chain(*query_aux))

    return gate_info

# def listGateId():
#     gatesId_list = session.query(GateData.gate_id).all()
#     out = list(itertools.chain(*gatesId_list))
#     return out


def checkGate(id, secret):
    gate_q = session.query(GateData).filter(GateData.gate_id == id).first()
    if gate_q == None:
        return 0
    if gate_q.secret == secret:
        return 2
    else:
        return 1



Base.metadata.create_all(engine) #Create tables for the data models

Session = sessionmaker(bind=engine)
session = Session()


app = Flask(__name__)
     
@app.route("/")
def index():
    return render_template("index.html", message="Dynamic content!")   

@app.route("/newGate" , methods= ['POST'])
def newGateEndpoint():
    request_json = request.get_json()
    try:
        gate_id = request_json['gateID']
        location = request_json['location']
    except:
        abort(400)
    print(gate_id, location)
    try:
        secret = newGate(gate_id,location)
    except:
        abort(500)
    if secret == None:
        return jsonify({'response' : 'Gate ID already exists', 'secret' : ''}), 200
    else:
        return jsonify({'response' : 'gate created', 'secret' : secret}), 201
    

@app.route("/gateList" , methods = ['GET'])
def listGateEndpoint():
    gate_info = listGates()
    return jsonify({'gate_id' : gate_info[0], 'secret' : gate_info[1], 'location' : gate_info[2], 'gate_opens' : gate_info[3]})



@app.route("/gateCheck")
def checkGateEndpoint():
    request_json = request.get_json()
    try:
        gate_id=request_json['gate_id']
        secret=request_json['secret']
    except:
        abort(400)
    gate_check = checkGate(gate_id, secret)
    status = 0
    message = ""
    if(gate_check == 0):
        status = 0
        message = "Wrong Gate ID"
    if(gate_check == 1):
        status = 0
        message = "Wrong Secret"
    if(gate_check == 2):
        status = 1
        message = ""
    return jsonify({'status' : status, 'message' : message})

@app.route("/<gate>/open")
def openGateEndpoint(gate):
    gate_id = gate
    success = openGate(gate_id)
    if success == 1:
        return '', 200
    else:
        abort(404)


if __name__ == "__main__":
    app.run(port=8000, debug=True)