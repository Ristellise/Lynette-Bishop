import asyncio
import html
import random
from typing import List

import aiohttp
import dateutil.parser
from bs4 import BeautifulSoup
from peony.data_processing import JSONData

from .Common import AsyncResolver, JsonEmbed
from .Fantia import FantiaResolver


class TwitterCardResolver(AsyncResolver):

    def __init__(self, CardLink, Link, nsfw=False):
        super().__init__(Link, nsfw)
        print(CardLink)
        self.loop = asyncio.get_running_loop()
        self.cardLink = CardLink
        self.nsfw = nsfw

    async def get_embeds(self) -> List[JsonEmbed]:
        async with aiohttp.ClientSession(headers=self.agent) as session:
            async with session.get(self.cardLink) as response:
                if response.status == 200:
                    soup = BeautifulSoup(await response.text(), "lxml")
                    metas = soup.find_all("meta")
                    embes = [JsonEmbed()]
                    for i in metas:
                        prop = i.get('name')
                        if not prop:
                            prop = i.get('property')
                        if prop == "twitter:image":
                            url = i.get('content')
                            if self.nsfw:
                                # noinspection HttpUrlsUsage
                                url = url.replace('http://', '').replace('https://', '')
                                url = f"https://images.weserv.nl/?blur=5&url={url}"
                            embes[0].set_image(url=url)
                        elif prop == "og:title":
                            embes[0].title = i.get('content')
                        elif prop == "twitter:title" and not embes[0].title:
                            embes[0].title = i.get('content')
                        elif prop == "og:description":
                            embes[0].description = i.get('content')
                        elif prop == "og:url":
                            print(i)
                            embes[0].url = i.get('content')
                    embes[0].set_footer(text=f"Lynette Bishop V2 [Twitter Cards]",
                                        icon_url=f"https://i.ibb.co/52h6qnk/icon004sw.jpg?cache=pants")
                    return embes


class TwitterResolver(AsyncResolver):
    DATEP = dateutil.parser.parser()
    DEFAULTRESOLVER = TwitterCardResolver
    SITES = {
        "ecs.toranoana.jp": {"nsfw": False},
        "youtu.be": {"nsfw": False},
        "youtube.com": {"nsfw": False},
        "ec.toranoana.jp": {"nsfw": True},
        "fantia.jp": {"nsfw": False, "resolver": FantiaResolver},
        "animatetimes.com": {"nsfw": False}
    }
    SITESDOMAINS = list(SITES.keys())

    def __init__(self, twitterBody, nsfw=None, recursion=0):
        super().__init__(None, nsfw)
        if nsfw is None:
            nsfw = []
        self.base: JSONData = twitterBody
        self.nsfw = nsfw
        self.recurse = recursion

    def get_embed_from_media(self, sourceUser, media) -> JsonEmbed:
        embed = JsonEmbed()
        if str(sourceUser.id) in self.nsfw:
            # Yes, shutup pycharm, that's why we are replacing!
            # noinspection HttpUrlsUsage
            link = media['media_url'].replace('http://', '').replace('https://', '')
            link = f"https://images.weserv.nl/?blur=5&url={link}"
        else:
            link = f"{media['media_url']}?name=orig"
        embed.set_image(link)
        return embed

    async def get_embeds(self) -> dict:
        bust = random.randint(0, 10000)
        if self.recurse > 1:
            return {}
        embeds = []
        # Figure out which to target for media
        media_target = self.base
        webhook_target = self.base
        if self.base.get("retweeted_status", None):
            media_target = self.base.retweeted_status

        # Extract Media
        medias = media_target.get("extended_entities", {}).get("media", [])
        for media in medias:
            embeds.append(self.get_embed_from_media(media_target.user, media))
        if len(embeds) == 0:
            embeds.append(JsonEmbed())
            description_text = media_target.get("full_text", "")
        else:
            description_text = " ".join(media_target.get("full_text", "").split(" ")[:-1])

        # Text extraction
        outerlinks = media_target.get("entities", {}).get("urls", [])
        top_embed = embeds[0]
        if not description_text:
            description_text = media_target.get("text", "")
        description_text = html.unescape(description_text)
        for outerlink in outerlinks:
            description_text = description_text.replace(outerlink['url'], outerlink['expanded_url'])

        username = f"{media_target['user']['name']} (@{media_target['user']['screen_name']})"
        avatar_url = media_target['user']['profile_image_url_https'].replace("_normal", "")
        top_embed.set_author(name=username,
                             url=f"https://twitter.com/{media_target['user']['screen_name']}",
                             icon_url=avatar_url)
        # Title
        if media_target['id'] != webhook_target['id']:
            title = "Retweet"
        else:
            if self.recurse > 0:
                title = "Quoted Tweet"
            elif self.base.get("quoted_status", None) is None:
                title = "Tweet"
            else:
                title = "Reply Tweet"
        top_embed._title = title

        # Embed Fields
        fields = []
        if media_target.get('retweet_count', 0) > 0:
            fields.append({"name": "Retweets", "value": str(media_target.get("retweet_count", 0)), "inline": True})
        if media_target.get('favorite_count', 0) > 0:
            fields.append({"name": "Likes", "value": str(media_target.get("favorite_count", 0)), "inline": True})
        if len(fields) > 0:
            top_embed._fields = fields

        # Timestamp
        dt = self.DATEP.parse(webhook_target["created_at"])
        top_embed._timestamp = dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')

        # Footer
        top_embed.set_footer(text=f"Lynette Bishop V2 [Twitter]",
                             icon_url=f"https://i.ibb.co/52h6qnk/icon004sw.jpg?cache={bust}")
        hasQuote = True if self.base.get("quoted_status", None) else False
        prep = {"embeds": embeds, "quoted": hasQuote, "recursion": self.recurse + 1, "target": webhook_target}

        # Examine outer links
        if len(embeds) == 1 and not embeds[0].has_image:
            for link in outerlinks:
                for domain in self.SITESDOMAINS:
                    if link['display_url'].startswith(domain):
                        resolver = self.SITES[domain].get("resolver", self.DEFAULTRESOLVER)
                        nsfw = self.SITES[domain].get("nsfw", False)
                        prep['embeds'].extend(await resolver(link['expanded_url'], nsfw).get_embeds())
                        description_text.replace(link['expanded_url'], "")
        top_embed._description = description_text
        return prep
