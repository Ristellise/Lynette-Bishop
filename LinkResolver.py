import asyncio
import html
import random
from typing import List

import aiohttp
import dateutil.parser
import validators.url
from bs4 import BeautifulSoup
from peony.data_processing import JSONData


class JsonEmbed:

    def __init__(self,
                 title=None,
                 description=None,
                 url=None,
                 timestamp=None,
                 color=None):
        self._footer = None
        self._title = title
        self._type = "rich"
        self._description = description
        self._url = url
        self._fields = None
        self._timestamp = timestamp
        self._color = color
        self._image = None
        self._author = None

    def set_footer(self, text, icon_url=None):
        self._footer = {"text": text}
        if icon_url:
            self._footer["icon_url"] = icon_url

    def json(self):
        tmp = {}
        for k, v in self.__dict__.items():
            if k.startswith("_") and isinstance(v, (str, int, dict, list, float)):
                tmp[k.strip("_")] = v
        return tmp

    def set_image(self, url=None):
        if url:
            self._image = {"url": url}

    def set_author(self, name=None, url=None, icon_url=None):
        self._author = {}
        if name:
            self._author["name"] = name
        if url:
            self._author["url"] = url
        if icon_url:
            self._author["icon_url"] = icon_url

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        if validators.url(value, public=True):
            self._url = value
        else:
            raise Exception(f"URL: {value} not valid public url.")

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        self._description = value

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value


class Resolver:
    agent = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36 "
                           "LynetteBishopTwitterResolver/0.5.1"}

    def __init__(self, Link, nsfw=False):
        pass

    def get_embeds(self) -> List[JsonEmbed]:
        raise NotImplementedError()


class AsyncResolver(Resolver):

    async def get_embeds(self) -> List[JsonEmbed]:
        raise NotImplementedError()


class TwitterCardResolver(AsyncResolver):

    def __init__(self, CardLink, Link, nsfw=False):
        super().__init__(Link, nsfw)
        print(CardLink)
        self.loop = asyncio.get_running_loop()
        self.cardLink = CardLink

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
                            embes[0].set_image(url=i.get('content'))
                        elif prop == "og:title":
                            embes[0].title = i.get('content')
                        elif prop == "og:description":
                            embes[0].description = i.get('content')
                        elif prop == "og:url":
                            print(i)
                            embes[0].url = i.get('content')
                    embes[0].set_footer(text=f"Lynette Bishop V2 [Twitter Cards]",
                                        icon_url=f"https://i.ibb.co/52h6qnk/icon004sw.jpg?cache=pants")
                    return embes


class FantiaResolver(AsyncResolver):

    def __init__(self, Link: str, nsfw=False):
        super().__init__(Link)
        self.nsfw = nsfw
        self.loop = asyncio.get_running_loop()
        self.fantiaLink: str = Link

    async def get_embeds(self):
        embeds = [JsonEmbed()]
        main_em = embeds[0]
        url = f"https://fantia.jp/api/v1/posts/{self.fantiaLink.split('/')[-1]}"
        async with aiohttp.ClientSession(headers=self.agent) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    status = await response.json()
                    post = status.get("post", {})
                    comment = post.get("blog_comment", "<No Comment>")
                    post.get("blog_comment", "<No Comment>")
                    image = post.get('thumb', {}).get('original')
                    fields = []
                    main_em.title = post.get('title', '<No Title?>')
                    fanclub = post.get('fanclub', {})
                    main_em.set_author(
                        name=fanclub.get('fanclub_name_with_creator_name', "<No Creator?>"),
                        url=f"https://fantia.jp{fanclub.get('uri', {}).get('show')}")
                    main_em.url = self.fantiaLink
                    main_em.description = comment
                    if image:
                        main_em.set_image(url=image)
                    likes = post.get('likes_count', 0)
                    if likes:
                        fields.append(
                            {"name": "Likes", "value": str(likes), "inline": True})
                    main_em._fields = fields
        embeds[0].set_footer(text=f"Lynette Bishop V2 [Fantia]",
                             icon_url=f"https://i.ibb.co/52h6qnk/icon004sw.jpg?cache=pants")
        return embeds


class TwitterResolver(AsyncResolver):
    DATEP = dateutil.parser.parser()
    DEFAULTRESOLVER = TwitterCardResolver
    SITES = {
        "ecs.toranoana.jp": {"nsfw": False},
        "youtu.be": {"nsfw": False},
        "youtube.com": {"nsfw": False},
        "ec.toranoana.jp": {"nsfw": True},
        "fantia.jp": {"nsfw": False, "resolver": FantiaResolver}
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

        # Text extraction
        outerlinks = media_target.get("entities", {}).get("urls", [])
        top_embed = embeds[0]
        print(media_target)
        text = media_target.get("full_text", "")
        if not text:
            text = media_target.get("text", "")
        text = html.unescape(text)
        for outerlink in outerlinks:
            text = text.replace(outerlink['url'], outerlink['expanded_url'])
        top_embed._description = text
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
        if len(embeds) == 1:
            for link in outerlinks:
                for domain in self.SITESDOMAINS:
                    if link['display_url'].startswith(domain):
                        resolver = self.SITES[domain].get("resolver", self.DEFAULTRESOLVER)
                        nsfw = self.SITES[domain].get("nsfw", False)
                        prep['embeds'].extend(await resolver(link['expanded_url'], nsfw).get_embeds())
        return prep
