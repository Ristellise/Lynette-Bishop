from typing import List

import validators.url


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

    @property
    def has_image(self):
        return True if self._image else False

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