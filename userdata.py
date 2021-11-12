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
import itertools
import random
import string
import time
import json

import datetime
from sqlalchemy.orm import sessionmaker
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
    __tablename__= 'UserData'
    user = Column(String, primary_key=True)
    token = Column(String)
    code = Column(String)
    time_created = Column(Float)

    def __repr__(self):
        return "<UserData(user = %s token = %s code = %s time_created = %f)>" % (
                        self.user, self.token, self.code, self.time_created)



def newUser(user, token):
    time_created = time.time()
    code = None
    user_q = session.query(UserData).filter(UserData.user == user).first()
    if user_q == None:
        new_user = UserData(user = user, token = token, code = code, time_created = time_created)
        session.add(new_user)
        session.commit()
        return 
    else:
        user_q.token = token
        user_q = code
        session.commit()
        return

def newCode(user, token, code):
    time_created = time.time()
    user_q = session.query(UserData).filter(UserData.user == user).first()
    if user_q == None:
        return 0
    if user_q.token == token:
        user_q.code = code
        user_q.time_created = time_created
        session.commit()
        return 1

def checkCode(code):
    user_q = session.query(UserData).filter(UserData.code == code).first()
    #user_q = session.query(UserData).filter(UserData.user == user).first()
    #print(user_q.code)
    #if( code == user_q.code):
     #   print("igual")
    if user_q == None:
        return 0, ""
    else:
        time_created = user_q.time_created
        time_check = time.time()
        if (time_check-time_created)<60 :
            return 2, str(user_q.user)
        else:
            return 1, ""



Base.metadata.create_all(engine) #Create tables for the data models

Session = sessionmaker(bind=engine)
session = Session()


app = Flask(__name__)
     

@app.route("/newUser", methods = ['POST'])
def newUserEndpoint():
    request_json = request.get_json()
    try:
        user = request_json['ist_id']
        token = request_json['user_token']
    except:
        abort(400)
    try:
        newUser(user, token)
    except:
        abort(500)
    return "", 200

@app.route("/newCode" , methods = ['POST'])
def newCodeEndpoint():
    request_json = request.get_json()
    try:
        user = request_json['user']
        token = request_json['token']
        code = request_json['code']
    except:
        abort(400)
    ret = newCode(user, token, code)
    if ret == 1:
        return "", 200
    else:
        return "", 401



@app.route("/codeCheck")
def checkCodeEndpoint():
    request_json = request.get_json()
    try:
        code = request_json['code']
    except:
        abort(400)
    code_check, user_id = checkCode(code)
    if(code_check == 0 or code_check == 1):
        abort(400)
    if(code_check == 2):
        return jsonify({'user_id': user_id}), 200
    


if __name__ == "__main__":
    app.run(port=9000, debug=True)