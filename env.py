import yaml

with open('config.yaml', 'r') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

SECRET_KEY = config['flask']['secret']

TWILIO_SID = config['twilio']['sid']
TWILIO_TOKEN = config['twilio']['token']
TWILIO_PHONE_NUMBER = config['twilio']['phone_number']

USERS = config['users']
