import traceback

from datetime import *

import discord

from discord import app_commands
from discord.ext import commands

from services.dbService import *

from utils.embedUtil import makeEmbed


ticketOverwrite = discord.PermissionOverwrite(
    read_messages=True,
    send_messages=True,
    embed_links=True,
    attach_files=True,
    read_message_history=True,
    mention_everyone=True,
    use_external_emojis=True,
    add_reactions=True,
    use_application_commands=True,
)

class CreateTicketButton(discord.ui.View):
    def __init__(self, buttonLabel):
        super().__init__()
        self.add_item(discord.ui.Button(label=buttonLabel, style=discord.ButtonStyle.blurple, custom_id="TICKET_OPEN"))

class CloseTicketButton(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(label="티켓 닫기", style=discord.ButtonStyle.danger, custom_id="TICKET_CLOSE"))

class closedButton(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(label="다시 열기", style=discord.ButtonStyle.blurple, custom_id="TICKET_REOPEN"))
        self.add_item(discord.ui.Button(label="티켓 삭제", style=discord.ButtonStyle.danger, custom_id="TICKET_DELETE"))

async def isRegisterdGuild(guildId):
    con, cur = await loadDB()
    await cur.execute("SELECT * FROM guilds WHERE id = ?", (guildId,))
    exists = await cur.fetchone()
    await closeDB(con, cur)
    return bool(exists)

async def sendUnregisterdGuildError(interaction):
    await interaction.response.send_message(embed=makeEmbed("error", "오류", "등록되지 않은 서버입니다!"), ephemeral=True)

class ticketExtension(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="등록", description="이 서버를 등록합니다!")
    @app_commands.guild_install()
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def register(self, interaction: discord.Interaction):
        if await isRegisterdGuild(interaction.guild.id):
            return await interaction.response.send_message(embed=makeEmbed("error", "오류", "이미 등록된 서버입니다!"), ephemeral=True)
        
        con, cur = await loadDB()
        await cur.execute("SELECT * FROM guilds WHERE id = ?", (interaction.guild.id,))
        exists = await cur.fetchone()
        await cur.execute("INSERT INTO guilds (id) VALUES (?)", (interaction.guild.id,))
        await con.commit()
        await closeDB(con, cur)
        return await interaction.response.send_message(embed=makeEmbed("info", "등록 성공", "성공적으로 서버를 등록했습니다!"), ephemeral=True)
    
    @app_commands.command(name="티켓", description="티켓 버튼을 전송합니다!")
    @app_commands.guild_install()
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def sendTicketButton(self, interaction: discord.Interaction):
        if not await isRegisterdGuild(interaction.guild.id):
            return await sendUnregisterdGuildError(interaction)
        
        con, cur = await loadDB()
        await cur.execute("SELECT * FROM guilds WHERE id = ?", (interaction.guild.id,))
        row = await cur.fetchone()
        await closeDB(con, cur)

        title = row["title"]
        description = row["description"]
        buttonLabel = row["button_label"]

        embed = makeEmbed("info", title, description)
        await interaction.channel.send(embed=embed, view=CreateTicketButton(buttonLabel))
        return await interaction.response.send_message(embed=makeEmbed("info", "성공", "티켓 안내 메시지를 전송하였습니다!"), ephemeral=True)
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data["custom_id"]
            parts = custom_id.split("_")

            if parts[0] == "TICKET":
                if parts[1] == "OPEN":
                    overwrites = {}
                    overwrites[interaction.user] = ticketOverwrite
                    overwrites[interaction.guild.default_role] = discord.PermissionOverwrite(read_messages=False)
                    try:
                        channel = await interaction.guild.create_text_channel(name=f"{interaction.user.name} 님의 티켓", overwrites=overwrites)

                        await interaction.response.defer(ephemeral=True)

                        con, cur = await loadDB()
                        await cur.execute("INSERT INTO tickets (guild, user, channel, open_time) VALUES (?, ?, ?, ?)", (interaction.guild.id, interaction.user.id, channel.id, datetime.now().isoformat()))
                        await con.commit()
                        await closeDB(con, cur)

                        await channel.send(embed=makeEmbed("info", "티켓 닫기", "티켓을 닫으시려면 아래 버튼을 눌러주세요!"), view=CloseTicketButton(), content="@everyone")
                    except Exception as e:
                        print(traceback.print_exc())
                        try:
                            return await interaction.response.send_message(embed=makeEmbed("error", "오류", "티켓 생성 실패"), ephemeral=True)
                        except:
                            return await interaction.followup.send(embed=makeEmbed("error", "오류", "티켓 생성 실패"))

                    return await interaction.followup.send(embed=makeEmbed("info", "성공", f"티켓 생성을 성공하였습니다!\n{channel.jump_url}"), ephemeral=True)

async def setup(bot):
    await bot.add_cog(ticketExtension(bot))