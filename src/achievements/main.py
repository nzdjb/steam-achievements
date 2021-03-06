"""Main"""
from json import loads, dumps
from os import getenv

from functools import cache

from funcy import omit
import requests

import boto3


def handler(event, _):
    parameters = event.get('pathParameters')
    if not parameters or not parameters.get('app_id'):
        return response(400, 'No.')
    message = achievements(
        parameters.get('app_id'),
        parameters.get('steam_id', None)
    )
    return response(message=message)


def response(code=200, message=''):
    # return dumps({'responseCode': code, 'message': message})
    return message


def achievements(app_id, steam_id=None):
    player_data = {}
    if(is_valid_user(steam_id)):
        api = API_BASE + 'ISteamUserStats/GetPlayerAchievements/v0001'
        user_resp = requests.get(
            api,
            params=params(app_id) | {'steamid': steam_id}
        )
        player_data = create_map(
            'apiname',
            loads(user_resp.text).get('playerstats').get('achievements')
        )
    return dumps(
        [
            {'apiname': k}
            | v
            | stats_map(app_id)[k]
            | player_data.get(k, {})
            for k, v
            in schema_map(app_id).items()
        ]
    )


@cache
def schema_map(app_id):
    api = API_BASE + 'ISteamUserStats/GetSchemaForGame/v0002'
    schema_resp = requests.get(api, params=params(app_id))
    schema = loads(schema_resp.text) \
        .get('game') \
        .get('availableGameStats') \
        .get('achievements')
    return create_map('name', schema)


@cache
def stats_map(app_id):
    api = API_BASE + \
        "ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002"
    stats_resp = requests.get(api, params={'gameid': app_id})
    stats = loads(stats_resp.text) \
        .get('achievementpercentages') \
        .get('achievements')
    return create_map('name', stats)


def params(app_id):
    return {
        'key': api_key(),
        'appid': app_id
    }


def is_valid_user(user):
    return user is not None


def create_map(index, list):
    return {entry[index]: omit(entry, index) for entry in list}


@cache
def api_key():
    param = getenv('STEAM_API_PARAMETER')
    return boto3.client('ssm') \
        .get_parameter(Name=param) \
        .get('Parameter') \
        .get('Value')


API_BASE = 'http://api.steampowered.com/'
