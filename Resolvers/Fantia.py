import asyncio

import aiohttp

from .Common import JsonEmbed, AsyncResolver


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

