import datetime
import time
from pathlib import Path
from typing import NamedTuple

import aiohttp
import asyncio

from config import *
from twitch_api import get_token, get_clips, get_users
from twitch_credentials import CLIENT_ID


class OAuthToken(NamedTuple):
    access_token: str
    expires_in: int
    retrieved_at: datetime.datetime


oauth_token = None


def get_headers():
    return {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {oauth_token.access_token}'
    }


async def set_global_token(session):
    token_response = await get_token(session)
    token_response_dict = await token_response.json()

    global oauth_token
    oauth_token = OAuthToken(
        token_response_dict['access_token'],
        token_response_dict['expires_in'],
        datetime.datetime.now()
    )
    print(f"Set oauth_token: {oauth_token}")


def get_clip_file(clip, clips_dir):
    file_name = clip['created_at'].replace(':', '-') + '_' + clip['id']
    return clips_dir / (file_name + '.mp4')


async def download_clip(session, clip, clip_file):
    thumbnail_url = clip['thumbnail_url']
    mp4_index = thumbnail_url.index("-preview-")
    mp4_url = thumbnail_url[:mp4_index] + '.mp4'
    async with session.get(mp4_url) as resp:
        data = await resp.read()

        file_name = clip['created_at'].replace(':', '-') + '_' + clip['id']
        with clip_file.open('wb') as f:
            f.write(data)
        print(f"Saved clip to {file_name}")


async def main():
    clips_dir = Path(clips_directory)
    clips_dir.mkdir(exist_ok=True)

    async with aiohttp.ClientSession() as session:
        global oauth_token
        if oauth_token is None:
            await set_global_token(session)

        broadcaster_user = await get_users(session, [broadcaster], get_headers())
        broadcaster_id = (await broadcaster_user.json())['data'][0]['id']
        print(f"Found broadcaster_id for {broadcaster}: {broadcaster_id}")

        cycle_time = time.time()
        while True:
            if (datetime.datetime.now() - oauth_token.retrieved_at).seconds > oauth_token.expires_in - 10:
                await set_global_token(session)

            clips = await get_clips(session, broadcaster_id, get_headers())
            clips_data = (await clips.json())['data']

            clips_to_save = []
            for clip in clips_data:
                clipper = clip['creator_name']
                if clipper in clippers and not get_clip_file(clip, clips_dir).is_file():
                    clips_to_save.append(clip)

            await asyncio.gather(
                asyncio.sleep(5),
                *[
                    download_clip(session, clip_data, get_clip_file(clip, clips_dir))
                    for clip_data in clips_to_save
                ]
            )
            current_time = time.time()
            print(f"Cycle took {current_time - cycle_time:.3f}s")
            cycle_time = current_time


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
