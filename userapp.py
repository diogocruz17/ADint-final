from flask import Flask, abort, json, request,  redirect, url_for, jsonify, render_template, session
from flask.templating import render_template
import requests
import os
from requests_oauthlib import OAuth2Session
from werkzeug.wrappers import response
import time


app = Flask(__name__)

client_id = "851490151334144"
client_secret = "75qyTg+A8i/UnmzYkD7fo4xKB9rQGymUZcB9HA+c2QmhxMyFyPTp3kuNoJecAxqcrD7SZ9BlHpAIBPFOBmzQaw=="
authorization_base_url = 'https://fenix.tecnico.ulisboa.pt/oauth/userdialog'
token_url = 'https://fenix.tecnico.ulisboa.pt/oauth/access_token'

ist_id = ""
global_token =  ""



@app.route("/")
def default():
    return render_template("UserAppWelcome.html")

@app.route("/login")
def demo():
    """Step 1: User Authorization.
    Redirect the user/resource owner to the OAuth provider (i.e. Github)
    using an URL with a few key OAuth parameters.
    """
    github = OAuth2Session(client_id, redirect_uri="http://localhost:2000/callback")
    authorization_url, state = github.authorization_url(authorization_base_url)
    #print(authorization_url)
    #print(state)
    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route("/callback", methods=["GET"])
def callback():
    """ Step 3: Retrieving an access token.
    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """

    #print("CALLBACK")

    #print(request.url)
    github = OAuth2Session(client_id, state=session['oauth_state'], redirect_uri="http://localhost:2000/callback")
    #print(github.authorized)
    token = github.fetch_token(token_url, client_secret=client_secret,
                               authorization_response=request.url)

    # At this point you can fetch protected resources but lets save
    # the token and show how this is done from a persisted token
    # in /profile.
    session['oauth_token'] = token

    return redirect(url_for('.profile'))    

@app.route("/profile", methods=["POST", "GET"])
def profile():
    """Fetching a protected resource using an OAuth 2 token.
    """
    github = OAuth2Session(client_id, token=session['oauth_token'])
    info = github.get('https://fenix.tecnico.ulisboa.pt/api/fenix/v1/person').json()
    
    token = session['oauth_token']
    global global_token
    global_token = token
    ist_id = info['username']
    #print("global_token",global_token)


    
    json_data = json.dumps(token)
    
    try:
         response = requests.post('http://localhost:7000/user/newUser', json = json_data)
    except requests.exceptions.ConnectionError:
        print("Could't connect to Service. Exiting ...")
        return(render_template("ServerOffline.html"))
    
    if response.status_code == 500:
        print("Internal Error in Server. Exiting ...")
        return(render_template("ServerError.html"))
        
    return(render_template('UserAppOptions.html'))



@app.route("/user")
def userOptions():
    return render_template("UserAppOptions.html")

@app.route("/user/code")
def userCodeEndpoint():
    json_data = json.dumps(global_token)
    try:
        response = requests.get('http://localhost:7000/user/newCode', json = json_data)
    except requests.exceptions.ConnectionError:
        print("Could't connect to Service. Exiting ...")
        return render_template("ServerOffline.html")
    if response.status_code != 200:
        return render_template("ServerError.html")
    response_json = response.json()
    code = response_json['code']
    return render_template('UserAppCode.html', code = code)

@app.route("/user/entries")
def userEntriesEndpoint():
    json_data = json.dumps(global_token)
    try:
        response = requests.get('http://localhost:7000/user/getEntries', json = json_data)
    except requests.exceptions.ConnectionError:
        print("Could't connect to Service. Exiting ...")
        return render_template("ServerOffline.html")
    if response.status_code != 200:
        return render_template("ServerError.html")
    
    try:
        response_Json = response.json()
    except:
        print("Wrong data format")
        return render_template("ServerError.html")
    for a in response_Json:
        a[2] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(a[2]))

    return render_template("UserAppEntries.html", entries = response_Json)



if __name__ == "__main__":
    
   
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "1"

    app.secret_key = os.urandom(24)
    app.run(port=2000, debug=True)