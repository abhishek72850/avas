[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]

-----------------------------

# AVAS
Automated Vaccine Appointment Schedular

For faster reply to queries join <a href='https://t.me/avas_channel'>Telegram</a> Group.

This is python script which can notifiy vaccine availability in your given pincode/district and also automatically schedules the appointment for vaccination.

> Note: This will work online when used in Android Phones, although this can be used in ios if there's an alternative for Termux app on ios to use python

## Features
- Schedules Vaccine Appointment Automatically
- Supports booking of slots for multiple person
- Sends Vaccine Availability SMS using Twilio
- Supports vaccine search by pincode or district
- Can notify multiple persons at once

### Algorithm overview:
```
        1. If token expired goto 2 else 3
        2. Login
            a. Send OTP
            b. fetch message extract OTP
            c. Verify OTP get token
        3. gets vaccine availability
        4. gets beneficiary
        5. get and solve captcha
        6. schedule appointment
```

## How to use?
To use this script follow the below steps:

### Installing APPs
1. Install Airmore application from Google play store (<a href='https://play.google.com/store/apps/details?id=com.airmore'>Click here</a>)
2. Install Termux application from Google play store (<a href='https://play.google.com/store/apps/details?id=com.termux'>Click here</a>)

### Clone Repository
3. Run below command on Termux to install git and clone repository
    ```
    pkg up && pkg install git && git clone https://github.com/abhishek72850/avas.git
    ```
### Add user details    
4. Open `users.json` on any editor and enter the details of the user for which you want schedule and notify for vaccine availability.
* Sample User:
    ```json
    [
      {
        "search_by": "pincode",
        "beneficiary_reference_id": "72255782401234",
        "login_mobile": "1234567890",
        "mobile": "1234567890",
        "email": "email@gmail.com",
        "pincode": "800001",
        "district_id": "312",
        "min_age": "18",
        "max_age": "44",
        "dose": 1
      }
    ]
    ```
* `search_by` : Takes by how you want to search for vaccine availability it can be either `pincode` or `district`
* `beneficiary_reference_id` : Provide beneficiary ref id, you can get this by logging in CoWin portal
* `login_mobile` : Provide mobile number through which you will registering the given `beneficiary_reference_id`
> Note: given beneficiary reference id should be added under this account registered using the mobile number present in login_mobile
* `mobile` : Provide mobile number on which you to sent vaccine availability sms at the given pincode or district center's
* `email` : Provide any email (It doesn't send any emails right now)
* `pincode` : Provide pincode if `search_by` value is `pincode` otherwise remove this key
* `district_id` : Provide district_id if `search_by` value is `district` otherwise remove this key (Get the district_id from here: https://avas.herokuapp.com/)
* `min_age` : Takes minimum age limit for which vaccine should be searched, it takes either `18` or `45`
* `max_age` : Provide any value (This is not used as of now)
* `dose` : Provide `1` if registering for first dose else provide `2` if registering for second dose

> Note: Whichever mobile number is provided in `login_mobile` the script should be run on that phone only and it should be same in every user entry.

### Environment Variable file setup
5. Open the Airmore application, click on the 3 dot icon Get IP and copy the IP ADDRESS only and keep the app running in background
6. Open the `prod.env` on any editor then:
    - Paste the IP in the `AIRMORE_IP_ADDRESS` value
    - Fill out the API keys for Twilio SMS (https://www.twilio.com/sms). (**If you don't have or want Twilio skip this step**)

### Execute Program
7. On Termux cd to the path where you have cloned the repo
8. Run the command to install dependencies:
    ```
    bash install.sh
    ```
9. Run this command to exceute scheduler:
    (Note: If you don't have Twilio API keys, give the `-skip_notify` value `True`)
    ```
    python avas.py -env prod.env -skip_notify False
    ```
    - `-env`: Provide the environment file
    - `-skip_notify`: Specifies when to send vaccine availability sms or not

[contributors-shield]: https://img.shields.io/github/contributors/abhishek72850/avas.svg?style=for-the-badge
[contributors-url]: https://github.com/abhishek72850/avas/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/abhishek72850/avas.svg?style=for-the-badge
[forks-url]: https://github.com/abhishek72850/avas/network/members
[stars-shield]: https://img.shields.io/github/stars/abhishek72850/avas.svg?style=for-the-badge
[stars-url]: https://github.com/abhishek72850/avas/stargazers
[issues-shield]: https://img.shields.io/github/issues/abhishek72850/avas.svg?style=for-the-badge
[issues-url]: https://github.com/abhishek72850/avas/issues
