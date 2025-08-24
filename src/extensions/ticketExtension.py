import asyncio
import io
import traceback

from datetime import *

import discord

from discord import app_commands
from discord.ext import commands

import chat_exporter

from services.dbService import *

from models.ticketModel import Ticket
from models.ticketTypeModel import TicketType

from utils.embedUtil import makeEmbed

lock = asyncio.Lock()
rateLimits = {}
WINDOW = 1

async def checkRate(userId):
    now = asyncio.get_event_loop().time()
    async with lock:
        lastTime = rateLimits.get(userId)
        if lastTime and now - lastTime < 5:
            return False
        return True
    
async def addRate(userId):
    now = asyncio.get_event_loop().time()
    async with lock:
        rateLimits[userId] = now

async def cleanUpLoop():
    while True:
        await asyncio.sleep(10)
        now = asyncio.get_event_loop().time()
        async with lock:
            for userId, lastTime in list(rateLimits.items()):
                if now - lastTime >= 5:
                    del rateLimits(userId)

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

async def createTicket(interaction: discord.Interaction, ticketTypeId):
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

class CreateTicketButton(discord.ui.View):
    def __init__(self, buttonLabel, ticketTypes: list[TicketType]):
        super().__init__()

        if len(ticketTypes) == 1:  
            self.add_item(discord.ui.Button(label=buttonLabel, style=discord.ButtonStyle.blurple, custom_id=f"TICKET_OPEN_{ticketTypes[0]}"))
            return
        
        self.add_item(discord.ui.Select(custom_id="TICKET_OPEN", placeholder=buttonLabel, min_values=1, max_values=1, options=[
            discord.SelectOption(label=ticketType.name, value=f"TICKET_OPEN_{ticketType.id}") for ticketType in ticketTypes
        ]))

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
        self.cleanUpTask = bot.loop.create_task(cleanUpLoop())

    def cog_unload(self):
        self.cleanUpTask.cancel()

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

        tickets = await TicketType.findByGuildId(interaction.guild.id)
        if len(tickets) <= 1:
            if len(tickets) < 0:
                ticket = await TicketType.createInstance(interaction.guild.id, "기본 티켓", True, 1, None)
            else:
                ticket = tickets[0]

            await interaction.channel.send(embed=embed, view=CreateTicketButton(buttonLabel, [ticket]))
            return await interaction.response.send_message(embed=makeEmbed("info", "성공", "티켓 안내 메시지를 전송하였습니다!"), ephemeral=True)
        else:
            view = discord.ui.View(timeout=120)
            select = discord.ui.Select(placeholder="사용할 티켓 종류를 선택해주세요", min_values=1, max_values=len(tickets), options=[
                discord.SelectOption(label=ticket.name, value=ticket.id) for ticket in tickets
            ])
            
            async def callback(mInteraction: discord.Interaction):
                values = select.values
                selectedTicketTypes = [ticket for ticket in tickets if str(ticket.id) in values]
                await interaction.channel.send(embed=embed, view=CreateTicketButton(buttonLabel, selectedTicketTypes))
                return await interaction.edit_original_response(embed=makeEmbed("info", "성공", "티켓 안내 메시지를 전송하였습니다!"), view=None)
            
            select.callback = callback
            view.add_item(select)

            return await interaction.response.send_message(view=view, ephemeral=True)
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data["custom_id"]
            parts = custom_id.split("_")

            if parts[0] == "TICKET":
                if parts[1] == "OPEN":
                    if not await checkRate(interaction.user.id):
                        return await interaction.response.send_message(embed=makeEmbed("error", "오류", "요청이 너무 빠릅니다!"), ephemeral=True)
                    
                    await addRate(interaction.user.id)
                    await createTicket(interaction)
                
                elif parts[1] == "CLOSE":
                    try:
                        ticket = await Ticket.findByChannelId(interaction.channel.id)
                        if ticket.status == "closed":
                            return await interaction.response.send_message(embed=makeEmbed("error", "오류", "이미 닫힌 티켓입니다!"), ephemeral=True)
                        try:
                            member = await interaction.guild.fetch_member(ticket.user)
                            await interaction.channel.set_permissions(member, overwrite=discord.PermissionOverwrite(read_messages=False))
                        except discord.NotFound:
                            pass
                        ticket.status = "closed"
                        await ticket.save()
                        return await interaction.response.send_message(embed=makeEmbed("info", "성공", "티켓이 닫혔습니다!"), view=closedButton())
                    except:
                        print(traceback.print_exc())
                        return await interaction.response.send_message(embed=makeEmbed("error", "오류", "티켓을 닫을 수 없습니다!"), ephemeral=True)
                    
                elif parts[1] == "REOPEN":
                    try:
                        ticket = await Ticket.findByChannelId(interaction.channel.id)
                        if ticket.status != "closed":
                            return await interaction.response.send_message(embed=makeEmbed("error", "오류", "닫힌 티켓이 아닙니다!"), ephemeral=True)
                        
                        overwrites = {}
                        member = await interaction.guild.fetch_member(ticket.user)
                        overwrites[member] = ticketOverwrite
                        overwrites[interaction.guild.default_role] = discord.PermissionOverwrite(read_messages=False)
                        await interaction.channel.edit(overwrites=overwrites)

                        ticket.status = "open"
                        await ticket.save()

                        return await interaction.response.send_message(embed=makeEmbed("info", "성공", "티켓을 다시 열었습니다!"), view=CloseTicketButton())
                    except discord.NotFound:
                        return await interaction.response.send_message(embed=makeEmbed("error", "오류", "유저가 서버를 나가서 티켓을 다시 열 수 없습니다!"), ephemeral=True)
                    except:
                        print(traceback.print_exc())
                        return await interaction.response.send_message(embed=makeEmbed("error", "오류", "티켓을 다시 열 수 없습니다!"), ephemeral=True)
                    
                elif parts[1] == "DELETE":
                    try:
                        ticket = await Ticket.findByChannelId(interaction.channel.id)
                        if ticket.status != "closed":
                            return await interaction.response.send_message(embed=makeEmbed("error", "오류", "닫힌 티켓이 아닙니다!"), ephemeral=True)
                        
                        transcription = await chat_exporter.export(interaction.channel)
                        fileBuffer = io.BytesIO(transcription.encode("utf-8"))
                        file = discord.File(fp=fileBuffer, filename="transcription.html")
                        await interaction.user.send(file=file)

                        await interaction.channel.delete()
                        ticket.status = "deleted"
                        await ticket.save()
                    except:
                        print(traceback.print_exc())
                        await interaction.response.send_message(embed=makeEmbed("error", "오류", "티켓을 삭제할 수 없습니다!"), ephemeral=True)

async def setup(bot):
    await bot.add_cog(ticketExtension(bot))