from twilio.rest import Client
from env import TWILIO_SID, TWILIO_TOKEN, TWILIO_PHONE_NUMBER

client = Client(TWILIO_SID, TWILIO_TOKEN)


def send_sms(msg, to_phone, media=None):
    message = client.messages.create(
        from_=TWILIO_PHONE_NUMBER,
        to=to_phone,
        body=msg,
        media_url=media,
    )
    return message.sid
