from flask import Flask, request, jsonify
import json
import requests
from datetime import datetime

app = Flask(__name__)

def send_sms(user, availability):
    api = "https://rest.clicksend.com/v3/sms/send"

    payload = {
        "messages": [
            {
                "body":availability,
                "to":user['mobile']
            }  
        ]
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic YWJoaXNoZWsua3VtYXIyMDE4ZkB2aXRhbHVtLmFjLmluOjIwRDkxRkMyLTMwQjQtOTcyRi1DRDZDLUQ2N0ZGNkUyMEYwMA=='
    }

    response = requests.request("POST", api, headers=headers, data=json.dumps(payload))

    if (response.status_code == 200):
        print('Sending Availability to:', user['mobile'])

    return response.status_code

def get_vaccine_availabilities(data, user):
    found = False
    availability = ''
    template = 'Center Name:{},\n Address:{},\n Fee Type:{},\n Available Dose:{},\n Date:{},\n Vaccine:{},\n Min Age:{}\n\n\n'
    for center in data['centers']:
        for session in center['sessions']:
            if (session['min_age_limit'] == int(user['min_age']) and session['available_capacity'] > 0 and center['pincode'] == int(user['pincode'])):
                found = True
                address = '{},{},{},{},{}'.format(center['address'], center['state_name'], center['district_name'], center['block_name'], center['pincode'])
                availability += template.format(center['name'], address, center['fee_type'], session['available_capacity'], session['date'], session['vaccine'], session['min_age_limit'])
    
    if (found):
        return availability
    return None

def vaccine_notifier():
    user_base = [
         {
              "mobile": "9472363651",
              "email": "abhishekk728@yahoo.com",
              "pincode": "843302",
              "min_age": "45",
              "max_age": "100"
         }
    ]

    cowin_api = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin?pincode={}&date={}"

    for user in user_base:
        todays_date = datetime.now().strftime("%d-%m-%Y")
        format_cowin_api = cowin_api.format(user["pincode"], todays_date)

        payload={}
        headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:86.0) Gecko/20100101 Firefox/86.0',
        }
        response = requests.request("GET", format_cowin_api, headers=headers, data=payload)

        print('CoWin Response:', response.status_code)

        try:
            data = response.json()
        except Exception as e:
            continue

        availability = get_vaccine_availabilities(data, user)
        if (availability):
            send_sms(user, availability)

    return 'Its Yoo'

@app.route('/notify_me/', methods=['GET'])
def respond():
    return vaccine_notifier()

# A welcome message to test our server
@app.route('/')
def index():
    return "<h1>Welcome to our server !!</h1>"

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)