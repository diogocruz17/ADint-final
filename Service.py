import os
from flask import Flask, render_template, request, url_for, redirect,send_from_directory,jsonify, abort, session
import requests
from requests_oauthlib import OAuth2Session
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


client_id_user = "851490151334144"
client_id_admin = "851490151334153"
client_secret = "Uk0ueMf32FYpFJ0dvE71hYDVlUQMxSmAK6h5Xgpe3DLm0w+f77aFyyCu/1w6M0sOZbI/5Db3bFiWfOphnjBptw=="
authorization_base_url = 'https://fenix.tecnico.ulisboa.pt/oauth/userdialog'
token_url = 'https://fenix.tecnico.ulisboa.pt/oauth/access_token'

admin_id = ["ist193049"]


DATABASE_FILE = "gateaccess.sqlite"
db_exists = False
if path.exists(DATABASE_FILE):
    db_exists = True
    print("\t database already exists")

engine = create_engine('sqlite:///%s'%(DATABASE_FILE), echo=False)

Base = declarative_base()

Base.metadata.create_all(engine) #Create tables for the data models

Session = sessionmaker(bind=engine)
session_bd = Session()

class GateAccess(Base):
    __tablename__= 'GateAcess'
    index = Column(Integer, primary_key=True)
    gate_id = Column(Integer)
    access = Column(Integer)
    time_opened = Column(Float)

    def __repr__(self):
        return "<GateAccess(index = %d gate_id = %d access = %d time_opened = %f)>" % (
            self.index, self.gate_id, self.access, self.time_opened)


def newCode(user, token, code):
    try:
        response = requests.post('http://localhost:9000/newCode', json={'user': user, 'token': token, 'code': code})
    except:
        return 0
    status = response.status_code
    if status == 200:
        return 1
    else:
        return 0
    
def checkCodeData(code):
    try:
        response = requests.get('http://localhost:9000/codeCheck', json={'code': code})
    except:
        return 0, ""
    status = response.status_code
    response_json = response.json()
    if status == 200:
        return 1, response_json['user_id']
    else:
        return 0, ""


def Authenticate(token):
    try:
        github = OAuth2Session(client_id_user, token = token)
        info = github.get('https://fenix.tecnico.ulisboa.pt/api/fenix/v1/person').json()
        ist_id = info['username']
        user_token = token['access_token']
        return ist_id, user_token
    except:
        return None, None


def AddGate(gate_id, auth):
    time_opened = time.time()
    rows = session_bd.query(GateAccess).count()
    
    access = GateAccess(index = rows+1, gate_id = gate_id, access = auth, 
                        time_opened = time_opened)
    try:
        session_bd.add(access)
        session_bd.commit()
        return 1
    except:
        return 0
    

def GetAccesses(gate_id):
    accesses = []
    
    gate = session_bd.query(GateAccess).filter(GateAccess.gate_id==gate_id).all()
    
    for line in gate:
        # a = [line.user_id, line.gate_id, line.time_opened]
        accesses.append(line)
    
    return accesses


app = Flask(__name__)


def generateCode(user, token):
    size = 12
    code = ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k = size))    
    return str(user+token+code)


@app.route("/")
def default():
    return render_template("AdminAppWelcome.html")

@app.route("/admin/login")
def demo():
    """Step 1: User Authorization.
    Redirect the user/resource owner to the OAuth provider (i.e. Github)
    using an URL with a few key OAuth parameters.
    """
    github = OAuth2Session(client_id_admin, redirect_uri="http://localhost:7000/admin/callback")
    authorization_url, state = github.authorization_url(authorization_base_url)
    #print(authorization_url)
    #print(state)
    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route("/admin/callback", methods=["GET"])
def callback():
    """ Step 3: Retrieving an access token.
    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """

    #print("CALLBACK")

    #print(request.url)
    github = OAuth2Session(client_id_admin, state=session['oauth_state'], redirect_uri="http://localhost:7000/admin/callback")
    #print(github.authorized)
    token = github.fetch_token(token_url, client_secret=client_secret,
                               authorization_response=request.url)

    # At this point you can fetch protected resources but lets save
    # the token and show how this is done from a persisted token
    # in /profile.
    session['oauth_token'] = token

    return redirect(url_for('.profile'))    

@app.route("/admin/profile", methods=["POST", "GET"])
def profile():
    """Fetching a protected resource using an OAuth 2 token.
    """
    github = OAuth2Session(client_id_admin, token=session['oauth_token'])
    info = github.get('https://fenix.tecnico.ulisboa.pt/api/fenix/v1/person').json()
    
    token = session['oauth_token']
    global global_token
    global_token = token
    ist_id = info['username']
    if ist_id in admin_id:
        return render_template("index.html")
    else :
        return render_template("AdminWebAppDenied.html")

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
        return render_template("ServerOffline.html")
    status = response.status_code
    if(status == 201):
        response_Json = response.json()
        return render_template("GateCreated.html", secret = response_Json['secret'])
    if(status == 200):
        response_Json = response.json()
        return render_template("GateNotCreated.html", message = response_Json['response'])
    if(status == 500):
        return render_template("ServerError.html")
    if(status == 400):
        return "There was a problem with the json formating"


@app.route("/admin/gateList", methods = ['GET'])
def listGate():
    try:
        response = requests.get('http://localhost:8000/gateList')
    except requests.exceptions.ConnectionError:
        return render_template("ServerOffline.html")
    response_Json = response.json()
    gate_info = [[]] * 4
    try:
        gate_info[0] = response_Json['gate_id']
        gate_info[1] = response_Json['secret']
        gate_info[2] = response_Json['location']
        gate_info[3] = response_Json['gate_opens']
    except:
        print("Wrong data format")
        return render_template("ServerError.html")
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

@app.route("/user/getEntries", methods =['GET'])
def getEntriesEndpoint():
    request_json = request.get_json()
    token = json.loads(request_json)
   
    ist_id, user_token = Authenticate(token)
    if ist_id == None:
        abort(403)
    try:
        response = requests.get('http://localhost:8500/getEntries', json = {'ist_id': ist_id})
    except requests.exceptions.ConnectionError:
        abort(503)
    response_json = response.json()
    response_send = json.dumps(response_json)
    return response_send, 200
    


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
        gate_id = request_json['gate_id']
        code = request_json['code']
        code = code.strip('\"')
    except:
        abort(400)
    auth, user_id = checkCodeData(code)
    success = AddGate(gate_id, auth)
    if auth == 1:
        requests.post('http://localhost:8500/newEntry', json = {'ist_id': user_id, 'gate_id': gate_id})
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
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "1"
    
    

    app.secret_key = os.urandom(24)
    app.run(port=7000, debug=True)