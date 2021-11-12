import os
from flask import Flask, render_template, request, url_for, redirect,send_from_directory,jsonify, abort
import requests
from sqlalchemy.sql.sqltypes import Float
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
import itertools
import random
import string
import time
import json

import datetime

from os import path


#SLQ access layer initialization
DATABASE_FILE = "userdata.sqlite"
db_exists = False
if path.exists(DATABASE_FILE):
    db_exists = True
    print("\t database already exists")

engine = create_engine('sqlite:///%s'%(DATABASE_FILE), echo=False) #echo = True shows all SQL calls

Base = declarative_base()

    
class UserData(Base):
    __tablename__= 'userdata'
    user = Column(String, primary_key=True)
    token = Column(String)
    code = Column(String)
    time_created = Column(Float)
    def __repr__(self):
        return "<UserData(user = %s token = %s code = %s time_created = %f)>" % (
                        self.user, self.token, self.code, self.time_created)
    
    
class UserHistory(Base):
    __tablename__ = 'userhistory'
    index = Column(Integer, primary_key=True)
    gate_id = Column(Integer)
    time_opened = Column(Float)

    user_id = Column(String, ForeignKey('userdata.user')) 

    user = relationship("UserData", back_populates="userhistory")

    def __repr__(self):
        return "<UserHistory(index ='%d', gate_id = %d, time_opened = %f, user_id = %s)>" % (
            self.index, self.gate_id, self.time_opened, self.user_id)
    
    
UserData.userhistory = relationship("UserHistory", order_by=UserHistory.index, 
                                    back_populates='user')



Base.metadata.create_all(engine) #Create tables for the data models

Session = sessionmaker(bind=engine)
session = Session()

def NewEntry(gate_id, user_id):
    time_opened = time.time()
    rows = session.query(UserHistory).count()
    
    hist = UserHistory(index = rows+1, gate_id = gate_id, time_opened = time_opened, 
                       user_id = user_id)
    try:
        session.add(hist)
        session.commit()
        return 1
    except:
        return 0
    

def GetEntries(user_id):
    entries = []
    
    user = session.query(UserData).filter(UserData.user==user_id).first()
    
    for line in user.userhistory:
        a = [line.user_id, line.gate_id, line.time_opened]
        entries.append(a)
    
    return entries




app = Flask(__name__)

@app.route("/newEntry", methods = ['POST'])
def newEntryEndpoint():
    request_json = request.get_json()
    try:
        user_id = request_json['ist_id']
        gate_id = request_json['gate_id']
    except:
        abort(400)
    status = NewEntry(gate_id, user_id)
    if status == 1:
        return "", 200
    else:
        abort(500)


@app.route("/getEntries")
def getEntriesEndpoint():
    request_json = request.get_json()
    try:
        user_id = request_json['ist_id']
    except:
        abort(400)
    try:
        entries = GetEntries(user_id)
    except:
        abort(500)
    entries_json = json.dumps(entries)
    return entries_json


if __name__ == "__main__":
    app.run(port=8500, debug=True)