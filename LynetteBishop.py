import asyncio
import configparser
import json
import logging
import shelve

from nextcord.ext import commands

from MiyafujiYoshika import Yoshika, Eila

bot = commands.Bot(command_prefix='!ly2 ')

logging.basicConfig(level=logging.INFO)


class BishopCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = configparser.ConfigParser()
        self.config.read('secrets.ini')
        self.hooks = {}
        self.load_hooks()
        pass

    def add_hook(self, unique, hook):
        self.load_hooks()
        self.hooks[unique] = hook
        with open("hooks.json", "w") as f:
            json.dump(self.hooks, f)

    def load_hooks(self):
        with open("hooks.json") as f:
            self.hooks = json.load(f)

    @commands.command("webhook-list")
    @commands.is_owner()
    async def webhook_list(self, ctx, new_hook="", new_hookname=""):
        """
        Lists or Adds a Hook.

        :param new_hook: The hook URL.
        :param new_hookname: The hook shortname
        :return:
        """
        if new_hook != "" and new_hookname != "":
            self.add_hook(new_hookname, new_hook)
            msg = "\n".join(": ".join([k, v]) for k, v in self.hooks.items())
            msg = f"Added hook.\nAll hooks:\n" \
                  f"```{msg}```"
            await ctx.send(msg)
        else:
            self.load_hooks()
            msg = "\n".join(": ".join([k, v]) for k, v in self.hooks.items())
            msg = f"Hooks Listed:\n" \
                  f"```{msg}```"
            await ctx.send(msg)

    @commands.command("stalk", aliases=["follow"])
    @commands.is_owner()
    async def tweet_add(self,
                        ctx: commands.Context,
                        twitter_username: str,
                        webhook_name: str,
                        nsfw: bool = False):
        """
        Adds a new Username to be tracked into the bot

        :param webhook_name: The Webhook Shortname, added in
        :param nsfw:
        :param twitter_username: Twitter Username
        """
        uu = await self.yoshika.get_user(twitter_username, webhook="", nsfw=nsfw)
        if len(uu) == 0:
            return await ctx.send(f"__{twitter_username}__ Not found.")
        name = uu[0]

        if webhook_name in list(self.hooks.keys()):
            name.webhook = self.hooks[webhook_name]
            name.nsfw = nsfw
            self.yoshika.users[str(name.id)] = name
            with shelve.open("LynetteStore", "w") as f:
                f[str(name.id)] = name.dict()
            return await ctx.send(f"Added: __{name.screen_name}__ | NSFW: {nsfw}")
        else:
            return await ctx.send(f"Token Name: __{webhook_name}__ Not found.")

    @commands.command("unstalk", aliases=["unfollow"])
    @commands.is_owner()
    async def tweet_remove(self, ctx: commands.Context, *twitter_username):
        """
        Adds a new Username to be tracked into the bot

        :param twitter_username: Twitter Username
        """
        names = await self.yoshika.get_user(twitter_username, webhook="", nsfw=False)
        if len(list(names.keys())) > 0:
            for name in names:
                if self.yoshika.users.get(str(name.id)):
                    del self.yoshika.users[str(name.id)]
                    with shelve.open("LynetteStore", "w") as f:
                        del f[str(name.id)]
            return await ctx.send(f"Removed: {', '.join([name.screen_name for name in names])}.")
        else:
            return await ctx.send(f"Cannot Remove: {', '.join(twitter_username)}.")

    @commands.Cog.listener()
    async def on_ready(self):
        print("OK")
        secrets = {'consumer_key': self.config["KEYS"]['consumer_key'],
                   'consumer_secret': self.config["KEYS"]['consumer_secret'],
                   'access_token': self.config["KEYS"]['access_token'],
                   'access_token_secret': self.config["KEYS"]['access_token_secret']}
        self.yoshika = Yoshika(secrets, asyncio.get_running_loop())
        with shelve.open("LynetteStore", "c") as f:
            for k, v in f.items():
                self.yoshika.users[k] = Eila(**v)
        asyncio.get_running_loop().create_task(self.yoshika.run())


if __name__ == '__main__':
    cog = BishopCog(bot)
    bot.add_cog(cog)
    bot.run(cog.config['DISCORD']['token'])
