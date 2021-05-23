# AVAS
Automated Vaccine Appointment Schedular

This is python script which can notifiy vaccine availability in your given pincode/district and also automatically schedules the appointment for vaccination.

> Note: This will work online when used in Android Phones, although this can be used in ios if there's an alternative for Termux app on ios to use python

## How to use?
To use this script follow the below steps:

1. Install Airmore application from Google play store (<a href='https://play.google.com/store/apps/details?id=com.airmore'>Click here</a>)
2. Install Termux application from Google play store (<a href='https://play.google.com/store/apps/details?id=com.termux'>Click here</a>)
3. Install Python 3.x in Termux from <a href='https://wiki.termux.com/wiki/Python'>here</a>
4. Download all the AVAS files and copy into the phone internal storage
5. Edit the `users.json` and enter the details of the user for which you want schedule and notify for vaccine availability.
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
* `mobile` : Provide mobile number on which you to sent vaccine availability sms at the given pincode or district center's
* `email` : Provide any email (It doesn't send any emails right now)
* `pincode` : Provide pincode if `search_by` value is `pincode` otherwise remove this key
* `district_id` : Provide district_id if `search_by` value is `district` otherwise remove this key (Get the district_id from here: https://avas.herokuapp.com/)
* `min_age` : Takes minimum age limit for which vaccine should be searched, it takes either `18` or `45`
* `max_age` : Provide any value (This is not used as of now)
* `dose` : Provide `1` if registering for first dose else provide `2` if registering for second dose

> Note: Whichever mobile number is provided in `login_mobile` the script should be run on that phone only and it should be same in every user entry.

6. On Termux cd to the path where you have downloaded the files
7. Run the command to install dependencies: `bash install.sh`
8. Open the Airmore application, click on the 3 dot icon Get IP and copy the IP ADDRESS only, then keep the app running in background
9. Now open the `prod.env` file paste the IP in the `AIRMORE_IP_ADDRESS` value and fill out the API keys for Twilio SMS (https://www.twilio.com/sms) and Anti-Captcha (https://anti-captcha.com/).
10. Run the command on Termux: `python avas.py prod.env`
