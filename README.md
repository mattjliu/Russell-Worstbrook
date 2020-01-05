# Russell-Worstbrook
Russell Worstbook is an application built with [Flask](http://flask.palletsprojects.com/en/1.1.x/), [Twilio](https://www.twilio.com/docs/sms) and [nba_api](https://github.com/swar/nba_api) that notifies you via sms of bad boxscore stats for any given nba player after each game. 

# Setup and Installation

### You will need
* A Twilio account with a Twilio phone number, SID and authentication token
* A method of deployment (such as a Linux server hosted in the cloud)

### Installation
1. Clone this repo
```console
$ git clone https://github.com/mattjliu/Russell-Worstbrook.git
```

2. Setup a virtualenv and install dependencies
```console
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

3. Update config.yaml to include the appropriate fields
  * flask/secret: A generated secret key for your Flask app
  * twilio/sid: Your Twilio SID provided to you after activating your Twilio account
  * twilio/token: Your Twilio authentification token
  * twilio/phone_number: Your Twilio phone number
  * users/phone_number: This user's phone number (must be unique among users)
  * users/player: This user's player of choice (defaults to Russell Westbrook)
  * users/new_user: Indicates wheter this user is a new user (send a welcome message if true)
  
4. Create the initial database of users
```console
$ python model.py
```
This should create a `users.db` file in your working directory

5. Local testing

Using [ngrok](https://ngrok.com/product), you can test and demo the chatbot locally. Simply do steps 1-4 on your local machine and run
```console
$ python bot.py   # To run the Flask application
$ ngrok http 5000 # To obtain a public https url
```
Copy and paste the `Forwarding` https:// url (with `/bot` appended to the end) from the ngrok output into the `A messasge comes in` field of your Twilio console. You can then respond with commands to your Twilio number to test the chatbot.

# Production Deployment
To deploy the app, you will need a production-ready web server such as [nginx](https://www.nginx.com/) and a WSGI application server such as [gunicorn](https://gunicorn.org/) to handle the python code.

`bot.py` contains the Flask app that controls the chatbot that users can use to set their players. `daily_msg.py` is the script that sends notifications to users after their player plays a game.

Since both processes must be running all the time and preferrably restart after crashing, it is advisable to use a process supervisor (on Linux) such as `supervisord` or `systemd` for both commands.

For example, using `gunicorn`, the commands in questions are
```console
$ /venv/bin/gunicorn bot:app
$ /venv/bin/python3 daily_msg.py
```

Be sure to update the `A message comes in` field of your phone number in the Twilio console with your production server's IP address with `/bot` appended to the end.

# Usage
You can respond `!set PLAYER_NAME` to set a new player. You can also respond `!player` to view your current player.
<p align="center">
 <img src="/screenshots/screenshot1.png" width="400"/>
</p>
