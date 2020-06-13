from typing import List

from config import started_at, ended_at
from twitch_credentials import CLIENT_ID, CLIENT_SECRET


def get_token(session):
    return session.post(
        "https://id.twitch.tv/oauth2/token",
        params={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'client_credentials'
        }
    )


def get_users(session, logins: List[str], headers):
    return session.get(
        f"https://api.twitch.tv/helix/users",
        params=[('login', login) for login in logins],
        headers=headers
    )


def get_clips(session, broadcaster_id: str, headers):
    return session.get(
        "https://api.twitch.tv/helix/clips",
        params={
            'broadcaster_id': broadcaster_id,
            'first': 50,
            'started_at': started_at,
            'ended_at': ended_at
        },
        headers=headers
    )
