import os
import sys

import discord
from discord.ext import commands

OWNER_ID = os.getenv("OWNER_ID")

class AdminExtension(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx:commands.Context):
        if str(ctx.author.id) == OWNER_ID:
            return True
        return False

    @commands.command()
    async def 서버리스트(self, ctx: commands.Context):
        async for guild in self.bot.fetch_guilds(limit=None):
            await ctx.send(f"서버 이름: {guild.name} / 서버 아이디: {guild.id}")

    @commands.command()
    async def 종료(self, ctx: commands.Context):
        sys.exit(0)

async def setup(bot):
    await bot.add_cog(AdminExtension(bot))