from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import playercareerstats, playergamelog, leaguedashplayerstats
from model import User, db
from sms import send_sms
from datetime import date, datetime, timedelta
import logging
import yaml
import pandas as pd
import random
import schedule
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s: %(message)s')
handler = logging.FileHandler('daily.log')
handler.setFormatter(formatter)
logger.addHandler(handler)


def get_last_game(player):
    for season_type in ['Regular Season', 'Playoffs']:
        games = playergamelog.PlayerGameLog(player_id=player['id'],
                                            season_type_all_star=season_type).get_data_frames()[0]
        if games.shape[0] == 0:
            return None
        else:
            last_game_dt = datetime.strptime(games.iloc[0]['GAME_DATE'], '%b %d, %Y').date()

            if last_game_dt >= (date.today() - timedelta(days=1)):
                return games.iloc[0]

    return None


def get_seasons(player):
    career = playercareerstats.PlayerCareerStats(player_id=player['id']) # Ensures we use past seasons such that the number of games is >100
    career_stats = career.get_data_frames()[0]

    n_seasons_history = (career_stats['GP'][::-1].cumsum() > 100).value_counts().loc[False] + 1
    n = min(n_seasons_history, len(career_stats.index))

    return career_stats['SEASON_ID'][-n:]


def get_player_gamelogs(player, seasons):
    gamelogs = pd.DataFrame()
    for season in seasons:
        for season_type in ['Regular Season', 'Playoffs']:
            gamelog = playergamelog.PlayerGameLog(player_id=player['id'],
                                                  season=season,
                                                  season_type_all_star=season_type)
            gamelogs = pd.concat([gamelogs, gamelog.get_data_frames()[0]], axis=0)
    gamelogs.reset_index(inplace=True)
    return gamelogs


def get_league_stats(seasons):
    league_stats = pd.DataFrame()
    for season in seasons:
        for season_type in ['Regular Season', 'Playoffs']:
            season_stats = leaguedashplayerstats.LeagueDashPlayerStats(season=season,
                                                                       season_type_all_star=season_type)
        league_stats = pd.concat([league_stats, season_stats.get_data_frames()[0]], axis=0)
    league_stats.reset_index(inplace=True)
    return league_stats


class MessageCreator:

    def __init__(self, FG, FGA, FG3, FG3A, FT, FTA, PTS, TOV, PLUS_MINUS):
        self.thresholds = {
            'FG': FG,
            'FGA': FGA,
            'FG3': FG3,
            'FG3A': FG3A,
            'FT': FT,
            'FTA': FTA,
            'PTS': PTS,
            'TOV': TOV,
            'PLUS_MINUS': PLUS_MINUS
        }

    def get_bad_stats(self, gamelog, player_gamelogs, league_stats):

        bad_stat_dict = {}

        # Get shooting percentage stats
        for stat in ['FG', 'FG3', 'FT']:
            made = stat + 'M'
            attempted = stat + 'A'
            pct = stat + '_PCT'

            pct_threshold = league_stats[pct].quantile(self.thresholds[stat])
            shot_threshold = player_gamelogs[attempted].quantile(self.thresholds[attempted])
            if (gamelog[pct] < pct_threshold) and (gamelog[attempted] > shot_threshold):
                bad_stat_dict[stat] = {'ratio': f'{gamelog[made]}/{gamelog[attempted]}', 'pct': gamelog[pct]}

        # Get turnover stats
        if gamelog['TOV'] > player_gamelogs['TOV'].quantile(self.thresholds['TOV']):
            bad_stat_dict['TOV'] = gamelog['TOV']

        # Get plus minus stats
        if gamelog['PLUS_MINUS'] < league_stats['PLUS_MINUS'].quantile(self.thresholds['PLUS_MINUS']):
            bad_stat_dict['PLUS_MINUS'] = gamelog['PLUS_MINUS']

        # Get points stats
        if gamelog['PTS'] < player_gamelogs['PTS'].quantile(self.thresholds['PTS']):
            bad_stat_dict['PTS'] = gamelog['PTS']

        return bad_stat_dict

    def create_message(self, player, opp_team, expressions, bad_stat_dict, WL, seed):

        random.seed(seed)

        msg = ''
        name = player[random.choice(['full_name', 'last_name', 'first_name'])]

        if bad_stat_dict == {}:
            msg += random.choice(expressions['good_game']).format(name)  # Good game expression
            msg += ' '
            msg += random.choice(expressions['time'])  # Time of game
            msg += '. '
            msg += random.choice(expressions['good_ending'])  # Good ending
            return msg

        else:

            msg += name

            # Define shooting fields (since shooting is different from the other stats)
            shooting_cfg = expressions['shooting']
            shooting_figure = random.choice(list(shooting_cfg['figure'].keys()))  # Chose random betwween ratio and pct
            shooting_verb = shooting_cfg['figure'][shooting_figure]['verb'][0]  # Get shooting verb
            shooting_format = shooting_cfg['figure'][shooting_figure]['format'][0]
            shooting_counter = 0

            n_stats = len(bad_stat_dict.keys())
            for i, key in enumerate(bad_stat_dict.keys()):  # iterate over bad stat keys

                if i == (n_stats - 1) and i != 0:
                    msg += ' and'
                elif i > 0:
                    msg += ','

                if key in expressions['shooting'].keys():  # Deal with shooting seperately
                    shooting_type = key
                    shooting_gamelog = bad_stat_dict[shooting_type]
                    shooting_msg = ''
                    if shooting_counter == 0:  # First shooting stat
                        shooting_msg += ' {}'.format(shooting_verb)  # Verb
                        shooting_msg += shooting_format.format(shooting_gamelog[shooting_figure])  # Stat
                        shooting_msg += ' {}'.format(random.choice(shooting_cfg[shooting_type]))  # Shooting type
                        msg += shooting_msg
                        shooting_counter += 1
                    else:
                        shooting_msg += shooting_format.format(shooting_gamelog[shooting_figure])  # Stat
                        shooting_msg += ' {}'.format(random.choice(shooting_cfg[shooting_type]))  # Shooting type
                        msg += shooting_msg

                else:  # Deal with other stats
                    stat_expression = random.choice(expressions[key]).format(bad_stat_dict[key])
                    msg += ' {}'.format(stat_expression)

            # Win/Loss against opp team
            opp_team_designation = random.choice([opp_team['city'], 'the {}'.format(opp_team['nickname'])])
            msg += ' '
            msg += random.choice(expressions[WL]).format(opp_team_designation)

            # Time of game
            msg += ' '
            msg += random.choice(expressions['time'])

            # Bad ending
            msg += '. '
            msg += random.choice(expressions['bad_ending'])
            return msg


def job():
    seed = datetime.now()  # Used for message creation

    with open('expressions.yaml', 'r', encoding="utf8") as file:
        expressions = yaml.load(file, Loader=yaml.FullLoader)

    creator = MessageCreator(FG=0.33, FGA=0.25, FG3=0.33, FG3A=0.25, FT=0.33, FTA=0.25, PTS=0.1, TOV=0.9, PLUS_MINUS=0.1)
    logger.info(f'================================== {date.today()} ==================================')

    for user in User.query.all():

        logger.info(f'User: {user}')
        player = players.find_players_by_full_name(user.player)[0]

        if user.new_user:
            user.new_user = False
            db.session.commit()
            welcome_msg = 'Welcome to Russell Worstbrook, your daily source of bad NBA stats!'
            try:
                send_sms(msg=welcome_msg, to_phone=user.phone_number)
                logger.debug('Welcome messasge sent. New user status updated')
            except Exception as e:
                logger.error(f'Unable to send welcome message, error: {e}')
                continue

        # Get last game
        try:
            last_game = get_last_game(player)
            if last_game is not None:
                logger.debug(f'Retrieved last game: {last_game.MATCHUP}, {last_game.GAME_DATE}')
            else:
                logger.debug('No game found within the past day')
                continue
        except Exception as e:
            logger.error(f'Unable to retrieve last game, error: {e}')
            continue

        # Get seasons
        try:
            seasons = get_seasons(player)
            logger.debug(f'Retrieved seasons: {list(seasons)}')
        except Exception as e:
            logger.error(f'Unable to retrieve seasons, error: {e}')
            continue

        # Get player gamelogs
        try:
            player_gamelogs = get_player_gamelogs(player, seasons)
            logger.debug('Retrieved player gamelogs')
        except Exception as e:
            logger.error(f'Unable to retrieve player gamelogs, error {e}')
            continue

        # Get league stats
        try:
            league_stats = get_league_stats(seasons)
            logger.debug('Retrieved league stats')
        except Exception as e:
            logger.error(f'Unable to retrieve league stats, error: {e}')
            continue

        bad_stats = creator.get_bad_stats(last_game, player_gamelogs, league_stats)
        opp_team = teams.find_team_by_abbreviation(last_game['MATCHUP'].split()[-1])
        msg = creator.create_message(player, opp_team, expressions, bad_stats, last_game['WL'], seed=seed)

        try:
            send_sms(msg=msg, to_phone=user.phone_number)
            logger.debug('Message created: {}'.format(msg.encode('ascii', 'ignore').decode('ascii')))
        except Exception as e:
            logger.error(f'Unable to send cusstom message, error: {e}')
            continue


if __name__ == '__main__':
    schedule.every().day.at("10:00").do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
