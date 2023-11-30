from datetime import datetime
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext
)
from bs4 import BeautifulSoup
import logging
import requests
import pytz

# UTC to MST(Moscow Standard Time)
mst = pytz.timezone('Europe/Moscow')

# Premier League Table URL
table_url = "https://www.skysports.com/premier-league-table"

# Premier League Fixtures URL
fixtures_url = "https://api.football-data.org/v4/competitions/PL/matches"

# Premier League Player stats - Goal
goal_url = "https://api.football-data.org/v4/competitions/PL/scorers"

# from football-data.org
api_key = 'b85297ee6f4b49adb48da70a7762b4b2'
headers = {'X-Auth-Token': api_key}

# from bot-father
access_token = "6703689653:AAHSC8W2uiz3WN0yWkBZfdRjM1vDDnQ54n0"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Here is EPL bot\n" + "/help will help you!")


def help(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("/table - EPL table\n" + "/fixtures - EPL fixtures\n" + "/goal - EPL scorers")


def get_table_data():
    req = requests.get(table_url)
    req.raise_for_status()
    soup = BeautifulSoup(req.text, "html.parser")

    table_element = soup.find("table", class_="standing-table__table")
    if table_element:
        rows = table_element.find_all("tr")

        team_names = []

        for idx, row in enumerate(rows[1:], start=1):
            team_name = row.find("td", class_="standing-table__cell standing-table__cell--name").get_text(strip=True)
            team_names.append(f"{idx}. {team_name}")

        return team_names
    else:
        return "Not found"


def table(update: Update, context: CallbackContext) -> None:
    team_names = get_table_data()
    reply = "2023/2024 Season\n" + "\n".join(team_names)
    update.message.reply_text(reply)


def get_fixtures_data():
    try:
        today = datetime.now(mst)
        response = requests.get(fixtures_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        fixtures_data = []
        matches_count = 0
        current_date = None

        for fixture in sorted(data.get('matches', []), key=lambda x: x['utcDate']):
            fixture_date_utc = datetime.strptime(fixture['utcDate'], "%Y-%m-%dT%H:%M:%SZ")
            fixture_date_utc = pytz.utc.localize(fixture_date_utc)

            fixture_date_mst = fixture_date_utc.astimezone(mst)

            if fixture_date_mst > today:
                formatted_date = fixture_date_mst.strftime('%a %d %b %H:%M')

                if formatted_date != current_date:
                    fixtures_data.append(f"\n{formatted_date} :")

                fixture_text = f"-{fixture['homeTeam']['shortName']} vs {fixture['awayTeam']['shortName']}"
                fixtures_data.append(fixture_text)
                matches_count += 1
                current_date = formatted_date

            if matches_count == 8:
                break

        return fixtures_data

    except Exception as e:
        print(f"Not found {e}")
        return "Not found"


def fixtures(update: Update, context: CallbackContext) -> None:
    fixtures_data = get_fixtures_data()
    reply = "2023/2024 Season\n" + "\n".join(fixtures_data)
    update.message.reply_text(reply)


def get_goal_data():
    try:
        response = requests.get(goal_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        player_names = []
        player_teams = []

        for rank, scorer in enumerate(data.get('scorers', []), start=1):
            player_name = scorer.get('player', {}).get('name', 'Unknown Player')
            player_team = scorer.get('team', {}).get('shortName', 'Unknown Player')
            goals = scorer.get('goals')
            player_teams.append(player_team)
            player_names.append(f"{rank}. [{player_team}] : {player_name} - {goals} goals")

        return player_names

    except Exception as e:
        print(f"Not found {e}")
        return "Not found"


def goal(update: Update, context: CallbackContext) -> None:
    player_names = get_goal_data()
    reply = "2023/2024 Season\n" + "\n".join(player_names)
    update.message.reply_text(reply)


def echo(update: Update, context: CallbackContext) -> None:
    try:
        text = update.message.text
        reply = "this is not a command\n" + "/table\n" + "/fixtures\n" + "/goal"

        if 'table' in text:
            team_names = get_table_data()
            reply = "2023/2024 Season\n" + "\n".join(team_names)
        elif 'fixtures' in text:
            fixtures_data = get_fixtures_data()
            reply = "2023/2024 Season\n" + "\n".join(fixtures_data)
        elif 'goal' in text:
            player_names = get_goal_data()
            reply = "2023/2024 Season\n" + "\n".join(player_names)

        update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"Error {e}")

updater = Updater(access_token)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help))
dispatcher.add_handler(CommandHandler("table", table))
dispatcher.add_handler(CommandHandler("fixtures", fixtures))
dispatcher.add_handler(CommandHandler("goal", goal))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

updater.start_polling()
updater.idle()
