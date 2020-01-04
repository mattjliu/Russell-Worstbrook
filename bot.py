from model import app, db, User
from flask import Flask, request, session
from twilio.twiml.messaging_response import MessagingResponse
from nba_api.stats.static import players


@app.route('/bot', methods=['GET', 'POST'])
def response_bot():
    in_msg = request.values.get('Body', '').lower()
    resp = MessagingResponse()
    out_msg = resp.message()

    from_number = request.values.get('From')
    from_user = User.query.filter_by(phone_number=from_number).first()

    if from_user:
        if in_msg == '!player':
            out_msg.body(f'Current player: {from_user.player}')
            return str(resp)

        elif in_msg[:5] == '!set ':
            new_player = in_msg[5:]
            matched_players = players.find_players_by_full_name(new_player)

            if len(matched_players) == 0:
                out_msg.body('No players found by that name!')
                return str(resp)
            elif len(matched_players) == 1:
                from_user.player = matched_players[0]['full_name']
                db.session.commit()
                out_msg.body(f'Successfully set {from_user.player}!')
                return str(resp)
            else:
                out_msg.body('Couldn\'t find that player, try again!')
                return str(resp)
        else:
            out_msg.body('Sorry, that isn\'t a valid option!')
            return str(resp)
    else:
        out_msg.body('You are not a valid user!')
        return str(resp)


if __name__ == '__main__':
    app.run(debug=True)
