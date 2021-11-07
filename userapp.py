from flask import Flask, abort, request,  redirect, url_for, jsonify, render_template, session
from flask.templating import render_template
import os
from requests_oauthlib import OAuth2Session


app = Flask(__name__)

client_id = ""
client_secret = ""
authorization_base_url = 'https://fenix.tecnico.ulisboa.pt/oauth/userdialog'
token_url = 'https://fenix.tecnico.ulisboa.pt/oauth/access_token'


#@app.route("/")
#def default():
    #return render_template("UserAppWelcome.html")

@app.route("/login")
def userLogin():
    return 1
    

@app.route("/user")
def userOptions():
    render_template("UserAppOptions.html")

@app.route("/")
def demo():
    """Step 1: User Authorization.

    Redirect the user/resource owner to the OAuth provider (i.e. Github)
    using an URL with a few key OAuth parameters.
    """
    github = OAuth2Session(client_id, redirect_uri="http://localhost:2000/user")
    authorization_url, state = github.authorization_url(authorization_base_url)
    print(authorization_url)
    print(state)
    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state
    return redirect(authorization_url)


# Step 2: User authorization, this happens on the provider.

@app.route("/callback", methods=["GET"])
def callback():
    """ Step 3: Retrieving an access token.

    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """

    print("CALLABACK")

    print(request.url)
    github = OAuth2Session(client_id, state=session['oauth_state'], redirect_uri="http://localhost:2000/user")
    print(github.authorized)
    token = github.fetch_token(token_url, client_secret=client_secret,
                               authorization_response=request.url)

    # At this point you can fetch protected resources but lets save
    # the token and show how this is done from a persisted token
    # in /profile.
    session['oauth_token'] = token

    return redirect(url_for('.profile'))


@app.route("/profile", methods=["GET"])
def profile():
    """Fetching a protected resource using an OAuth 2 token.
    """
    github = OAuth2Session(client_id, token=session['oauth_token'])
    return jsonify(github.get('https://fenix.tecnico.ulisboa.pt/api/fenix/v1/person').json())




if __name__ == "__main__":
    app.run(port=2000, debug=True)
   # This allows us to use a plain HTTP callback
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "1"

    app.secret_key = os.urandom(24)
    app.run(debug=True)