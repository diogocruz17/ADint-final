import requests
import sys
import time

try:
    gate_id = sys.argv[1]
    secret = sys.argv[2]
    #print(gate_id, secret)
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

while (1):
    print("Type the user code: ")
    user_code=input()
    try:
        response = requests.get('http://localhost:7000/gate/codeCheck', json={'gate_id' : gate_id, 'code' : user_code })
    except requests.exceptions.ConnectionError:
        print("Couldn't reach server")
        exit(0)   
    if response.status_code == 202:
        print("!!! Code Valid !!!")
        print("Gate is open")
        for i in range(6,0,-1):
            time.sleep(1)
            print("The gate will close in %d seconds" % i)
        print("!!! Gate Closed !!!")
    if response.status_code == 400:
        print("Bad Request.")
    if response.status_code == 503:
        print("Couldn't reach server.")
    if response.status_code == 401:
        print("!!! Code Not Valid !!!")
