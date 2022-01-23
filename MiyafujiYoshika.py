import asyncio
import configparser
import json
import logging
import typing

import aiohttp
import dateutil.parser
import peony
from peony import PeonyClient
from peony.data_processing import JSONData

from Resolvers.Twitter import TwitterResolver


class Eila:

    def __init__(self, **kwargs):
        self.properties = {}
        self.id = kwargs.get("id", None)
        self.screen_name = kwargs.get("screen_name", None)
        self.nsfw = kwargs.get("nsfw", False)
        self.webhook = kwargs.get("webhook", False)

    def dict(self):
        return {"id": self.id,
                "screen_name": self.screen_name,
                "nsfw": self.nsfw,
                "webhook": self.webhook}


class Yoshika:

    def __init__(self, secrets, loop):
        self.peony = PeonyClient(
            **secrets,
            user_agent="TwitterAndroid/6.41.0 (7160062-r-930) Pixel 3a/10 (Google;Pixel 3a;google;sargo;0;;0)",
            headers={"X-Twitter-Client": 'TwitterAndroid',
                     'X-Twitter-Client-Language': 'en',
                     'X-Twitter-Client-Version': '6.41.0',
                     'X-Twitter-API-Version': '5',
                     'Accept-Language': 'en',
                     }
        )
        self._session = None
        self.stream = None
        self.loop = loop
        self.datep = dateutil.parser.parser()
        self.users: typing.Dict[str, Eila] = {}

    @property
    async def session(self):
        if not self._session:
            self._session = aiohttp.ClientSession()
            self._session.headers.update({"user-agent": "LynetteBishop/1.0.0"})
        return self._session

    async def trigger_webhook(self, twitter_name, avatar_img, content, embeds, hook_url):
        webhook_dict = {"username": twitter_name,
                        "avatar_url": avatar_img,
                        "content": content,
                        "embeds": [i.json() for i in embeds]}
        sess = await self.session
        async with sess.post(hook_url, data=json.dumps(webhook_dict),
                             headers={"content-type": "application/json"}) as r:
            if r.status == 200 or r.status == 204:
                print("Webhook OK")
            else:
                print(f"Error: {r.status} {await r.text()}")

    async def tweet_details(self, tweet_body: JSONData, webhook_url=None):
        users_i = list(self.users.values())
        nsfw = [i.id for i in users_i if i.nsfw]
        resolver = TwitterResolver(tweet_body, nsfw=nsfw)
        result = await resolver.get_embeds()

        u = f"{result['target']['user']['name']} (@{result['target']['user']['screen_name']})"
        avu = result['target']['user']['profile_image_url_https'].replace("_normal", "")
        tweet_link = f"<https://twitter.com/{result['target']['user']['screen_name']}/status/{tweet_body.id}>"

        while result['quoted'] and len(result['embeds']) > 0:
            await self.trigger_webhook(
                u, avu, tweet_link,
                result['embeds'], webhook_url
            )
            result = await TwitterResolver(
                tweet_body.get("quoted_status", None), nsfw=nsfw,
                recursion=result['recursion']).get_embeds()
        await self.trigger_webhook(
            u, avu, tweet_link,
            result['embeds'], webhook_url
        )

    async def get_user(self, *names, webhook, nsfw=False):
        lookups = await self.peony.api.users.lookup.post(screen_name=names)
        resp = []
        for n_user in lookups:
            resp.append(Eila(id=str(n_user['id']),
                             screen_name=n_user['screen_name'],
                             nsfw=nsfw,
                             webhook=webhook))
        return resp

    async def stream_task(self):
        c_ids = self.users.copy()
        self.stream = self.peony.stream.statuses.filter.post(follow=list(self.users.keys()))
        print("Stream Started.")
        while True:
            if c_ids != self.users.copy():
                print("Stream updating...")
                ss = self.stream  # ugly? yes.
                self.stream = None
                ss.__exit__()
                self.stream = self.peony.stream.statuses.filter.post(follow=list(self.users.keys()))
                print("Stream Updated.")
                c_ids = self.users.copy()
            else:
                await asyncio.sleep(5)

    async def run(self):
        asyncio.get_running_loop().create_task(self.stream_task())
        logging.info("Yoshika Loop Started.")
        listen_ids = list(self.users.keys())

        # stream is an asynchronous iterator
        while True:
            if len(listen_ids) > 0:
                while True:
                    if self.stream is None:
                        await asyncio.sleep(1)
                        continue
                    try:
                        tweet = await self.stream.__anext__()
                    except Exception as e:
                        print(e)

                    else:
                        if peony.events.tweet(tweet) or peony.events.retweet(tweet):
                            if str(tweet.user.id) in self.users.keys():
                                r = self.users[str(tweet.user.id)]
                                await self.tweet_details(tweet, webhook_url=r.webhook)
            else:
                await asyncio.sleep(1)


async def main():
    config = configparser.ConfigParser()
    config.read('secrets.ini')
    secrets = {'consumer_key': config["KEYS"]['consumer_key'],
               'consumer_secret': config["KEYS"]['consumer_secret'],
               'access_token': config["KEYS"]['access_token'],
               'access_token_secret': config["KEYS"]['access_token_secret']}
    y = Yoshika(secrets, asyncio.get_running_loop())
    pp = await y.peony.api.statuses.show.get(id=1485203898809794561, tweet_mode='extended')
    await y.tweet_details(pp, webhook_url=config['DISCORD']['dev_webhook'])
    print(pp)


if __name__ == '__main__':
    asyncio.run(main())
