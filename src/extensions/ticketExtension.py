import discord

from discord import app_commands
from discord.ext import commands

from services.dbService import *

from utils.embedUtil import makeEmbed

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

    @app_commands.command(name="등록", description="이 서버를 등록합니다!")
    @app_commands.guild_install()
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def register(self, interaction: discord.Interaction):
        con, cur = await loadDB()
        await cur.execute("SELECT * FROM guilds WHERE id = ?", (interaction.guild.id,))
        exists = await cur.fetchone()

        if exists:
            await closeDB(con, cur)
            return await interaction.response.send_message(embed=makeEmbed("error", "오류", "이미 등록된 서버입니다!"), ephemeral=True)
        
        await cur.execute("INSERT INTO guilds (id) VALUES (?)", (interaction.guild.id,))
        await con.commit()
        await closeDB(con, cur)
        return await interaction.response.send_message(embed=makeEmbed("info", "등록 성공", "성공적으로 서버를 등록했습니다!"), ephemeral=True)

async def setup(bot):
    await bot.add_cog(ticketExtension(bot))