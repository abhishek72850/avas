from flask import Flask, request, jsonify
import json
import requests
import http.client
from datetime import datetime

app = Flask(__name__)

# A welcome message to test our server
@app.route('/')
def index():
    payload = {}

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:86.0) Gecko/20100101 Firefox/86.0',
    }

    url_a = "https://cdn-api.co-vin.in/api/v2/admin/location/states"
    url_b = "https://cdn-api.co-vin.in/api/v2/admin/location/districts/21"
    
    response_a = requests.request("GET", url_a, headers=headers, data=payload)
    response_b = requests.request("GET", url_b, headers=headers, data=payload)

    return "<h1>Responses: {} {}</h1>".format(response_a.status_code, response_b.status_code)

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
