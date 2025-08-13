import discord

from discord import app_commands
from discord.ext import commands

class CreateTicketButton(discord.ui.View):
    def __init__(self, buttonLabel, style):
        super.__init__()
        self.add_item(discord.ui.Button(label=buttonLabel, style=style, custom_id="TICKET_OPEN"))

class CloseTicketButton(discord.ui.View):
    def __init__(self):
        super.__init__()
        self.add_item(discord.ui.Button(label="티켓 닫기", style=discord.ButtonStyle.danger, custom_id="TICKET_CLOSE"))

class closedButton(discord.ui.View):
    def __init__(self):
        super.__init__(self)
        self.add_item(discord.ui.Button(label="다시 열기", style=discord.ButtonStyle.blurple, custom_id="TICKET_REOPEN"))
        self.add_item(discord.ui.Button(label="티켓 삭제", style=discord.ButtonStyle.danger, custom_id="TICKET_DELETE"))

class ticketExtension(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(ticketExtension(bot))