'''
    v1.1
    Automated Vaccine Appointment Schedular 

    Algorithm overview:
        1. if token expired goto 2 else 3
        2. Login
            a. Send OTP
            b. fetch message extract OTP
            c. Verify OTP get token
        3. get vaccine availability
        4. get beneficiary
        5. get captcha
        6. schedule appointment
'''
import os
import re
import hashlib
import base64
import json
import requests
import html
import argparse
from time import sleep
from datetime import datetime, timedelta

import sys
from signal import signal, SIGINT
from sys import exit

import jwt

from dotenv import dotenv_values

from bs4 import BeautifulSoup

from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF, renderPM

from captcha_solver import CaptchaSolver

from ipaddress import IPv4Address
from pyairmore.request import AirmoreSession
from pyairmore.services.messaging import MessagingService


class Utitlity:
    def get_sms_history(self, service):
        messages = service.fetch_message_history()
        return messages

    def get_cowin_sms(self, messages, otp_sent_at):
        for message in messages:
            if ('cowin' in message.content.lower() and message.datetime > otp_sent_at):
                return message.content
        return None

    def extract_otp(self, message):
        match = re.search('\d{6}', message)
        if (match):
            print('Extracted OTP:', match.group())
            return match.group()
        return None

    def get_sha256(self, text):
        return hashlib.sha256(text.encode()).hexdigest()

    def unescape_svg(self, svg_text):
        return html.unescape(svg_text)

    def save_captcha_svg(self, svg_text):
        with open('captcha.svg', 'w') as f:
            f.write(svg_text)

    def svg_to_png(self):
        drawing = svg2rlg("captcha.svg")
        renderPM.drawToFile(drawing, "captcha.png", fmt="PNG")

    def is_token_valid(self, token):
        if (token):
            decoded = jwt.decode(token, options={"verify_signature": False})
            if (datetime.fromtimestamp(decoded['exp']) < datetime.now()):
                return False
            return True
        return False


class AVAS(Utitlity):
    def __init__(self, env, skip_notify, manual_otp, interval):
        self.skip_notify = skip_notify
        self.manual_otp = manual_otp
        self.interval = interval
        self.cowin_token = None
        self.config = dotenv_values(env)
        self.load_records_json()
        if (not self.manual_otp):
            self.set_airmore_session()
            self.set_messaging_service()
    
    def set_airmore_session(self):
        ip = IPv4Address(self.config['AIRMORE_IP_ADDRESS'])
        self.session = AirmoreSession(ip)

    def set_messaging_service(self):
        self.service = MessagingService(self.session)
    
    def load_records_json(self):
        with open(self.config['USER_LIST'], 'r') as f:
            self.user_list = json.load(f)
        
        with open(self.config['VACCINE_AVAILABILITY_SENT_RECORDS'], 'r') as f:
            self.availability_sent_records = json.load(f)

        with open(self.config['VACCINE_APPOINTMENT_SCHEDULED_RECORDS'], 'r') as f:
            self.registered_records = json.load(f)
    
    def send_sms(self, user_mobile, text):
        api = self.config['TWILIO_SMS_API'].format(self.config['TWILIO_SMS_API_KEY'])

        payload='To=+91{}&MessagingServiceSid={}&Body={}'.format(user_mobile, self.config['TWILIO_MESSAGING_SID'], text)

        headers = {
            'Authorization': 'Basic {}'.format(self.config['TWILIO_REQUEST_AUTHORIZATION']),
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.request("POST", api, headers=headers, data=payload)

        return response.status_code
    
    # def solve_captcha(self, filename='captcha.png'):
    #     solver = CaptchaSolver('antigate', api_key=self.config['ANTI_CAPTCHA_API_KEY'])
    #     raw_data = open(filename, 'rb').read()
    #     captcha_text = solver.solve_captcha(raw_data)
    #     return captcha_text
    def solve_captcha(self, captcha_svg):
        soup = BeautifulSoup(captcha_svg,'html.parser')

        model = json.loads(base64.b64decode(self.config['CAPTCHA_MODEL'].encode('ascii')))
        captcha = {}

        for path in soup.find_all('path',{'fill' : re.compile("#")}):
            encoded_string = path.get('d').upper()
            index = re.findall('M(\d+)',encoded_string)[0]
            encoded_string = re.findall("([A-Z])", encoded_string)
            encoded_string = "".join(encoded_string)
            captcha[int(index)] =  model.get(encoded_string)

        captcha = sorted(captcha.items())
        captcha_text = ''

        for char in captcha:
            captcha_text += char[1]

        return captcha_text
    
    def send_otp(self, phone):
        payload = {
            "secret": self.config['COWIN_OTP_GENERATE_SECRET'],
            "mobile": phone
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:86.0) Gecko/20100101 Firefox/86.0',
            'Origin': 'https://selfregistration.cowin.gov.in',
            'Referer': 'https://selfregistration.cowin.gov.in/'
        }

        response = requests.request("POST", self.config['COWIN_GENERATE_OTP_API'], headers=headers, data=json.dumps(payload))

        print('Send OTP reponse:', response.status_code)

        if (response.status_code == 200):
            return response.json()['txnId']
        
        return None
    
    def verify_otp_and_get_token(self, otp, txn_id):
        otp_sha256 = self.get_sha256(otp)

        payload = {
            "otp": otp_sha256,
            "txnId": txn_id
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:86.0) Gecko/20100101 Firefox/86.0',
            'Origin': 'https://selfregistration.cowin.gov.in',
            'Referer': 'https://selfregistration.cowin.gov.in/'
        }

        response = requests.request("POST", self.config['COWIN_VERIFY_OTP_API'], headers=headers, data=json.dumps(payload))

        print('Verify OTP reponse:', response.status_code)

        if (response.status_code == 200):
            return response.json()['token']
        
        return None
    
    def get_vaccine_availabilities(self, user):
        payload = {}

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:86.0) Gecko/20100101 Firefox/86.0',
            'Origin': 'https://selfregistration.cowin.gov.in',
            'Referer': 'https://selfregistration.cowin.gov.in/'
        }

        todays_date = datetime.now().strftime("%d-%m-%Y")

        if (user['search_by'] == 'pincode'):
            url = self.config['COWIN_AVAILABILITY_BY_PIN_API'].format(user['pincode'], todays_date)
        else:
            url = self.config['COWIN_AVAILABILITY_BY_DISTRICT_API'].format(user['district_id'], todays_date)

        response = requests.request("GET", url, headers=headers, data=payload)

        print('CoWin Response:', response.status_code)

        if (response.status_code == 200):
            return response.json()
        
        return None

    def get_beneficiaries(self):
        payload = {}

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:86.0) Gecko/20100101 Firefox/86.0',
            'Origin': 'https://selfregistration.cowin.gov.in',
            'Referer': 'https://selfregistration.cowin.gov.in/',
            'Authorization': 'Bearer {}'.format(self.cowin_token)
        }

        response = requests.request("GET", self.config['COWIN_BENEFICIARY_API'], headers=headers, data=payload)

        print('Beneficiary reponse:', response.status_code)

        if (response.status_code == 200):
            return response.json()

        return None
    
    def generate_captch(self):
        payload = {}

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:86.0) Gecko/20100101 Firefox/86.0',
            'Origin': 'https://selfregistration.cowin.gov.in',
            'Referer': 'https://selfregistration.cowin.gov.in/',
            'Authorization': 'Bearer {}'.format(self.cowin_token)
        }

        response = requests.request("POST", self.config['COWIN_GENERATE_CAPTCHA_API'], headers=headers, data=json.dumps(payload))

        print('Captcha reponse:', response.status_code)

        if (response.status_code == 200):
            return response.json()['captcha']

        return None
    
    def schedule_appointment(self, center_id, session_id, beneficiary_id, slot, captcha_text, dose=1):
        payload = {
            "center_id": center_id,
            "session_id": session_id,
            "beneficiaries": [
                beneficiary_id
            ],
            "slot": slot,
            "captcha": captcha_text,
            "dose": dose
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:86.0) Gecko/20100101 Firefox/86.0',
            'Origin': 'https://selfregistration.cowin.gov.in',
            'Referer': 'https://selfregistration.cowin.gov.in/',
            'Authorization': 'Bearer {}'.format(self.cowin_token)
        }

        response = requests.request("POST", self.config['COWIN_SCHEDULE_API'], headers=headers, data=json.dumps(payload))

        print('Schedule Appointment reponse:', response.status_code)

        if (response.status_code == 200):
            return response.text
        else:
            print('Schedule Appointment response:', response.text)
        
        return None
    
    def cowin_login(self, user):
        print("Logging in CoWin...")
        otp_sent_at = datetime.now()
        txn_id = self.send_otp(user["login_mobile"])

        if (txn_id):
            otp = None
            if (not self.manual_otp):
                # Check for SMS upto 200 sec
                for i in range(200):
                    messages = self.get_sms_history(self.service)
                    message = self.get_cowin_sms(messages, otp_sent_at)
                    if (message):
                        otp = self.extract_otp(message)
                        break
                    sleep(1)
            else:
                otp = input('Enter OTP: ')
            
            if (otp):
                token = self.verify_otp_and_get_token(otp, txn_id)
                if (token):
                    print('Login successful...')
                    return token
                else:
                    print('Token extraction Failed!')
            else:
                print('OTP extraction Failed!')
        else:
            print("Send OTP Faild!")
        
        return None

    def do_schedule_appointment(self, user, availability):
        print("Scheduling vaccine appointment...")
        beneficiaries = self.get_beneficiaries()

        for beneficiary in beneficiaries['beneficiaries']:
            if (beneficiary["beneficiary_reference_id"] == user["beneficiary_reference_id"]):
                captcha_svg_text = self.generate_captch()
                # captcha_svg = self.unescape_svg(captcha_svg_text)
                # self.save_captcha_svg(captcha_svg)
                # self.svg_to_png()
                captcha_text = self.solve_captcha(captcha_svg_text)
                print('Solved Captcha Text:', captcha_text)

                for appointment in beneficiary['appointments']:
                    if (user['dose'] == appointment['dose']):
                        if (user['beneficiary_reference_id'] not in self.registered_records.keys()):
                            self.registered_records[user['beneficiary_reference_id']] = {}
                        self.registered_records[user['beneficiary_reference_id']]['scheduled_dose{}'.format(user['dose'])] = True
                        print('User {}({}) already have an appointment for dose {} at {} on {}'.format(beneficiary['name'], beneficiary['beneficiary_reference_id'], user['dose'], appointment['name'], appointment['date']))
                        return

                for center in availability:
                    if (user['dose'] == 1 and center['available_capacity_dose1'] > 0) or (user['dose'] == 2 and center['available_capacity_dose2'] > 0):
                        response = self.schedule_appointment(center['center_id'], center['session_id'], beneficiary["beneficiary_reference_id"], center['slots'][1], captcha_text, user['dose'])
                        if (response):
                            if (user['beneficiary_reference_id'] not in self.registered_records.keys()):
                                self.registered_records[user['beneficiary_reference_id']] = {}
                            self.registered_records[user['beneficiary_reference_id']]['scheduled_dose{}'.format(user['dose'])] = True

                            template = "Beneficiary {}({}), Vaccine is registered for Dose {} at {},{} on {}".format(beneficiary['name'], beneficiary['beneficiary_reference_id'], user['dose'], center['name'], center['pincode'], center['date'])
                            print(template)
                            self.send_sms(user, template)
                            print('Sent Appointment Scheduled SMS to:', user['mobile'])

    def extract_availabilities(self, data, user):
        availabilities = []

        for center in data['centers']:
            for session in center['sessions']:
                capacity = session['available_capacity_dose1'] if user['dose'] == 1 else session['available_capacity_dose2'];
                if (session['min_age_limit'] == int(user['min_age']) and capacity > 0):
                    extended_details = {
                        "center_id": center['center_id'],
                        "name": center['name'],
                        "fee_type": center['fee_type'],
                        "address": center['address'],
                        "state_name": center['state_name'],
                        "district_name": center['district_name'],
                        "block_name": center['block_name'],
                        "pincode": center['pincode']
                    }
                    extended_details.update(session)
                    availabilities.append(extended_details)

        return availabilities
    
    def get_availability_text(self, availabilities):
        availability_text = ''
        template = '\nCenter Name:{},\n Address:{},\n Fee Type:{},\n Available Dose 1:{},\n Available Dose 2:{},\n Date:{},\n Vaccine:{},\n Min Age:{}\n\n'

        for availability in availabilities:
            address = '{},{},{},{},{}'.format(availability['address'], availability['state_name'], availability['district_name'], availability['block_name'], availability['pincode'])
            availability_text += template.format(availability['name'], address, availability['fee_type'], availability['available_capacity_dose1'], availability['available_capacity_dose2'], availability['date'], availability['vaccine'], availability['min_age_limit'])
        
        return availability_text
    
    def send_availabilities(self, user, availabilities):
        availability_text = self.get_availability_text(availabilities)
        response_code = self.send_sms(user, availability_text)

        if (response_code == 201):
            print('Sent Availability to:', user['mobile'])
            if (user['mobile'] not in self.availability_sent_records.keys()):
                self.availability_sent_records[user['mobile']] = {}
            
            for availability in availabilities:
                if (availability['center_id'] not in self.availability_sent_records[user['mobile']].keys()):
                    self.availability_sent_records[user['mobile']][availability['center_id']] = {}

                if (availability['date'] not in self.availability_sent_records[user['mobile']][availability['center_id']].keys()):
                    self.availability_sent_records[user['mobile']][availability['center_id']][availability['date']] = {}
                
                self.availability_sent_records[user['mobile']][availability['center_id']][availability['date']] = {
                    "capacity_dose1": availability["available_capacity_dose1"],
                    "capacity_dose2": availability["available_capacity_dose2"],
                    "timestamp": datetime.utcnow().timestamp()
                }
    
    def filter_sent_availability(self, user, availabilities):
        if (user['mobile'] not in self.availability_sent_records.keys()):
            return availabilities
        
        filtered_availabilities = []
        
        for availability in availabilities:
            if (availability['center_id'] not in self.availability_sent_records[user['mobile']].keys()):
                filtered_availabilities.append(availability)
            elif (availability['date'] not in self.availability_sent_records[user['mobile']][availability['center_id']].keys()):
                filtered_availabilities.append(availability)

            sent_at = datetime.fromtimestamp(self.availability_sent_records[user['mobile']][availability['center_id']][availability['date']]['timestamp'])
            
            if ((datetime.utcnow() - sent_at).seconds >= 600):
                filtered_availabilities.append(availability)

        return filtered_availabilities
    
    def is_beneficiary_registered(self, user):
        if (user['beneficiary_reference_id'] not in self.registered_records.keys()):
            return False
        return self.registered_records[user['beneficiary_reference_id']].get('scheduled_dose{}'.format(user['dose']), False)
    
    def update_records(self):
        with open(self.config['USER_LIST'], 'w') as f:
            json.dump(self.user_list, f)
        
        with open(self.config['VACCINE_AVAILABILITY_SENT_RECORDS'], 'w') as f:
            json.dump(self.availability_sent_records, f)

        with open(self.config['VACCINE_APPOINTMENT_SCHEDULED_RECORDS'], 'w') as f:
            json.dump(self.registered_records, f)
    
    def handler(self, signal_received, frame):
        # Handle any cleanup here
        self.update_records()
        print('SIGINT or CTRL-C detected. Exiting gracefully')
        exit(0)

    def start(self):
        signal(SIGINT, self.handler)
        while(True):
            for user in self.user_list:
                if (not self.is_token_valid(self.cowin_token)):
                    self.cowin_token = self.cowin_login(user)
                
                if (self.cowin_token is None):
                    print('Login failed, skipping...')
                    continue
                
                data = self.get_vaccine_availabilities(user)

                if (data is not None):
                    availabilities = self.extract_availabilities(data, user)
                    if (user['search_by'] == 'pincode'):
                        print('Found availabilities for age {} at pincode-{}: {}'.format(user['min_age'], user['pincode'], len(availabilities)))
                    else:
                        print('Found availabilities for age {} at district ID-{}: {}'.format(user['min_age'], user['district_id'], len(availabilities)))

                    if (len(availabilities) > 0):
                        if (not self.skip_notify):
                            filtered_availabilities = self.filter_sent_availability(user, availabilities)

                            if (len(filtered_availabilities) > 0):
                                self.send_availability(user, filtered_availabilities)

                        if (not self.is_beneficiary_registered(user)):
                            self.do_schedule_appointment(user, availabilities)
                        else:
                            print('Beneficiary:{} with phone:{} already registered for dose:{}'.format(user['beneficiary_reference_id'],user['mobile'], user['dose']))
            self.update_records()
            sleep(self.interval)

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-env',
        type=str,
        nargs='?',
        default='prod.env',
        help='Environment variable file name'
    )
    parser.add_argument(
        '-skip_notify',
        type=bool,
        nargs='?',
        default=False,
        choices=[True, False],
        help='If given True it will not send vaccine availability sms'
    )
    parser.add_argument(
        '-manual_otp',
        type=bool,
        nargs='?',
        default=False,
        choices=[True, False],
        help='Whether to enter OTP manually or extract automatically'
    )
    parser.add_argument(
        '-interval',
        type=int,
        nargs='?',
        default=30,
        help='Time interval in seconds between each check(default: 30sec)'
    )
    return parser.parse_args()

if __name__ == '__main__':
    print('Version: 1.1')
    args = get_args()
    AVAS(args.env, args.skip_notify, args.manual_otp, args.interval).start()
