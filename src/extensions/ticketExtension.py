import aiofiles
import aiofiles.os
import asyncio
import os
import sys
import traceback

from datetime import *

import discord

from discord import app_commands
from discord.ext import commands

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import azura_chat_exporter

from bs4 import BeautifulSoup

import services.configService as setting

from services.dbService import *

from models.ticketModel import Ticket
from models.ticketTypeModel import TicketType

from utils.embedUtil import makeEmbed

domain = os.getenv("DOMAIN")

rateLimitLock = asyncio.Lock()
rateLimits = {}
WINDOW = 1

async def checkRate(userId):
    now = asyncio.get_event_loop().time()
    async with rateLimitLock:
        lastTime = rateLimits.get(userId)
        if lastTime and now - lastTime < 5:
            return False
        return True
    
async def addRate(userId):
    now = asyncio.get_event_loop().time()
    async with rateLimitLock:
        rateLimits[userId] = now

async def cleanUpLoop():
    while True:
        await asyncio.sleep(10)
        now = asyncio.get_event_loop().time()
        async with rateLimitLock:
            for userId, lastTime in list(rateLimits.items()):
                if now - lastTime >= 5:
                    del rateLimits[userId]

closingTicketLock = asyncio.Lock()
closingTickets: set[int] = set()

async def isClosingTicket(channelId) -> bool:
    async with closingTicketLock:
        return channelId in closingTickets

async def appendClosingTicket(channelId):
    async with closingTicketLock:
        closingTickets.add(channelId)

async def delClosingTicket(channelId):
    async with closingTicketLock:
        closingTickets.discard(channelId)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

async def getAttachDir(guildId, channelId, attachId):
    path = os.path.join(BASE_DIR, "static", "attachments", str(guildId), str(channelId), str(attachId))
    await aiofiles.os.makedirs(path, exist_ok=True)
    return path

async def getTranscriptDir(guildId):
    path = os.path.join(BASE_DIR, "transcripts", str(guildId))
    await aiofiles.os.makedirs(path, exist_ok=True)
    return path

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

async def createTicket(interaction: discord.Interaction, ticketTypeId, answer1 = None, answer2 = None, answer3 = None):
    await interaction.response.send_message(embed=makeEmbed("info", "잠시만 기다려주세요", "티켓을 열고 있습니다..."), ephemeral=True)

    ticketType = await TicketType.findById(ticketTypeId)
    if not ticketType:
        return await interaction.edit_original_response(embed=makeEmbed("error", "오류", "현재 열려고 하는 티켓의 설정이 삭제되었습니다! 관리자에게 문의해주세요."))
    
    if ticketType.ticketCategory:
        try:
            category = await interaction.guild.fetch_channel(ticketType.ticketCategory)
        except discord.NotFound:
            return await interaction.edit_original_response(embed=makeEmbed("error", "오류", "티켓 카테고리 설정이 잘못되었습니다! 관리자에게 문의해주세요."))
        except:
            traceback.print_exc()
            return await interaction.edit_original_response(embed=makeEmbed("error", "오류", "알 수 없는 오류입니다!"))
        
        overwrites = category.overwrites.copy()
    else:
        category = None
        overwrites = {}

    guildRoles = await interaction.guild.fetch_roles()
    overwrites[interaction.guild.default_role] = discord.PermissionOverwrite(read_messages=False)
    overwrites[interaction.user] = ticketOverwrite
    for roleId in ticketType.role:
        role = discord.utils.get(guildRoles, id=roleId)
        if role:
            overwrites[role] = ticketOverwrite

    if not ticketType.dupTicket:
        openTickets = await Ticket.findOpenTicket(interaction.guild.id, interaction.user.id, ticketType.id)
        if openTickets:
            for openTicket in openTickets:
                try:
                    await interaction.guild.fetch_channel(openTicket.channel)
                    return await interaction.edit_original_response(embed=makeEmbed("error", "오류", "한 번에 한 개의 티켓만 열 수 있습니다!"))
                except discord.NotFound:
                    openTicket.status = "deleted"
                    await openTicket.save()
                    continue

    try:
        ticketChannel = await interaction.guild.create_text_channel(name=f"{interaction.user}님의 티켓", reason="티켓 생성", category=category, overwrites=overwrites)
        ticket = await Ticket.createInstance(interaction.guild.id, interaction.user.id, ticketChannel.id, "open", ticketType=ticketType.id)
    except discord.Forbidden:
        return await interaction.edit_original_response(embed=makeEmbed("error", "오류", "봇의 권한이 부족합니다! 관리자에게 문의해주세요."))
    except:
        traceback.print_exc()
        return await interaction.edit_original_response(embed=makeEmbed("error", "오류", "알 수 없는 오류입니다!"))
    
    embed = makeEmbed("info", "성공", "티켓이 생성되었습니다!")
    if ticketType.survey1:
        embed.add_field(name=ticketType.survey1, value=answer1, inline=False)
    if ticketType.survey2:
        embed.add_field(name=ticketType.survey2, value=answer2, inline=False)
    if ticketType.survey3:
        embed.add_field(name=ticketType.survey3, value=answer3, inline=False)
    
    await ticketChannel.send(content="@everyone", embed=embed, view=discord.ui.View().add_item(discord.ui.Button(style=discord.ButtonStyle.red, label="티켓 닫기", custom_id=f"TICKET_CLOSE_{interaction.user.id}_{ticketTypeId}")))
    return await interaction.edit_original_response(embed=makeEmbed("info", "성공", f"티켓이 생성되었습니다!"), view=discord.ui.View().add_item(discord.ui.Button(label="티켓으로 가기", style=discord.ButtonStyle.url, url=ticketChannel.jump_url)))

async def transcriptTicket(interaction: discord.Interaction):
    async for message in interaction.channel.history(limit=None):
        for attachment in message.attachments:
            if attachment.size <= 5 * 1024 * 1024:
                attach_dir = await getAttachDir(interaction.guild.id, interaction.channel.id, attachment.id)
                await aiofiles.os.makedirs(attach_dir, exist_ok=True)
                file_path = os.path.join(attach_dir, attachment.filename)

                if not await aiofiles.os.path.exists(file_path):
                    await attachment.save(file_path)
                    print(f"Saved file: {file_path}")
                else:
                    print(f"Skipped {attachment.filename}, already exists")
            else:
                print(f"Skipped {attachment.filename}, file too large ({attachment.size} bytes)")

    transcript = await azura_chat_exporter.export(interaction.channel)
    transcript = transcript.replace(
        "https://media.discordapp.net/attachments",
        f"{domain}/static/attachments/{interaction.guild.id}"
    )

    soup = BeautifulSoup(transcript, "html.parser")

    for style_tag in soup.find_all("style"):
        style_tag.decompose()

    new_link_tag = soup.new_tag("link", rel="stylesheet", href="/static/css/style.css")
    soup.head.append(new_link_tag)

    transcript = str(soup)

    transcriptDir = await getTranscriptDir(interaction.guild.id)
    path = os.path.join(transcriptDir, f"{interaction.channel.id}.html")
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(transcript) 

class CreateTicketButton(discord.ui.View):
    def __init__(self, buttonLabel, ticketTypes: list[TicketType]):
        super().__init__()

        if len(ticketTypes) == 1:  
            self.add_item(discord.ui.Button(label=buttonLabel, style=discord.ButtonStyle.blurple, custom_id=f"TICKET_OPEN_{ticketTypes[0].id}"))
            return
        
        self.add_item(discord.ui.Select(custom_id="TICKET_OPEN", placeholder=buttonLabel, min_values=1, max_values=1, options=[
            discord.SelectOption(label=ticketType.name, value=ticketType.id) for ticketType in ticketTypes
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

class ticketExtension(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.cleanUpTask = bot.loop.create_task(cleanUpLoop())

    def cog_unload(self):
        self.cleanUpTask.cancel()

    @app_commands.command(name="설정", description="티켓을 설정합니다!")
    @app_commands.guild_install()
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def setting(self, interaction: discord.Interaction):
        return await interaction.response.send_message(f"{domain}/dashboard/{interaction.guild.id}", ephemeral=True)
    
    @app_commands.command(name="티켓", description="티켓 버튼을 전송합니다!")
    @app_commands.guild_install()
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def sendTicketButton(self, interaction: discord.Interaction, 제목:str = "티켓 열기", 내용:str = "아래 버튼을 눌러 문의를 위한 개인 채널을 생성하세요!", 버튼라벨:str = "💌ㅣ티켓 열기"):
        embed = makeEmbed("info", 제목, 내용)

        tickets = await TicketType.findByGuildId(interaction.guild.id)
        if len(tickets) <= 1:
            if len(tickets) == 0:
                ticket = await TicketType.createInstance(interaction.guild.id, "기본 티켓", True, 1, None)
            else:
                ticket = tickets[0]

            await interaction.channel.send(embed=embed, view=CreateTicketButton(버튼라벨, [ticket]))
            return await interaction.response.send_message(embed=makeEmbed("info", "성공", "티켓 안내 메시지를 전송하였습니다!"), ephemeral=True)
        else:
            view = discord.ui.View(timeout=120)
            select = discord.ui.Select(placeholder="사용할 티켓 종류를 선택해주세요", min_values=1, max_values=len(tickets), options=[
                discord.SelectOption(label=ticket.name, value=ticket.id) for ticket in tickets
            ])
            
            async def callback(mInteraction: discord.Interaction):
                values = select.values
                selectedTicketTypes = [ticket for ticket in tickets if str(ticket.id) in values]
                await interaction.channel.send(embed=embed, view=CreateTicketButton(버튼라벨, selectedTicketTypes))
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
                    
                    if len(parts) > 2:
                        ticketTypeId = parts[2]
                    else:
                        ticketTypeId = interaction.data.get("values")[0]

                    ticketType = await TicketType.findById(ticketTypeId)
                    if not ticketType:
                        return await interaction.response.send_message(embed=makeEmbed("error", "오류", "현재 열려고 하는 티켓의 설정이 삭제되었습니다! 관리자에게 문의해주세요."), ephemeral=True)
                    
                    if ticketType.survey1 or ticketType.survey2 or ticketType.survey3:
                        modal = discord.ui.Modal(title="양식을 작성해주세요!", timeout=120)
        
                        if ticketType.survey1:
                            survey1Input = discord.ui.TextInput(label=ticketType.survey1, required=True, placeholder="작성해주세요!")
                            modal.add_item(survey1Input)

                        if ticketType.survey2:
                            survey2Input = discord.ui.TextInput(label=ticketType.survey2, required=True, placeholder="작성해주세요!")
                            modal.add_item(survey2Input)

                        if ticketType.survey3:
                            survey3Input = discord.ui.TextInput(label=ticketType.survey3, required=True, placeholder="작성해주세요!")
                            modal.add_item(survey3Input)

                        async def onSubmit(mInteraction: discord.Interaction):
                            try:
                                survey1Value = survey1Input.value
                            except NameError:
                                survey1Value = None

                            try:
                                survey2Value = survey2Input.value
                            except NameError:
                                survey2Value = None

                            try:
                                survey3Value = survey3Input.value
                            except NameError:
                                survey3Value = None

                            if not await checkRate(mInteraction.user.id):
                                return await mInteraction.response.send_message(embed=makeEmbed("error", "오류", "요청이 너무 빠릅니다!"), ephemeral=True)
                            
                            await addRate(mInteraction.user.id)
                            await createTicket(mInteraction, ticketTypeId, survey1Value, survey2Value, survey3Value)

                        modal.on_submit = onSubmit
                        return await interaction.response.send_modal(modal)

                    await addRate(interaction.user.id)
                    await createTicket(interaction, ticketTypeId)
                
                elif parts[1] == "CLOSE":
                    try:
                        ticket = await Ticket.findByChannelId(interaction.channel.id)
                        ticketType = await TicketType.findById(ticket.ticketType)

                        if not ticketType:
                            return await interaction.response.send_message(embed=makeEmbed("error", "오류", "삭제된 티켓 종류이기 때문에 티켓을 닫을 수 없습니다!"), view=discord.ui.View(discord.ui.Button(label="티켓 삭제", style=discord.ButtonStyle.danger, custom_id="TICKET_DELETE_ERROR")), ephemeral=True)

                        if not ticketType.userClose and not (interaction.user.guild_permissions.administrator or any(r.id in ticketType.role for r in interaction.user.roles)):
                            return await interaction.response.send_message(embed=makeEmbed("error", "오류", "관리자만 티켓을 닫을 수 있습니다!"), ephemeral=True)

                        if ticket.status == "closed":
                            return await interaction.response.send_message(embed=makeEmbed("error", "오류", "이미 닫힌 티켓입니다!"), ephemeral=True)
                        try:
                            member = await interaction.guild.fetch_member(ticket.user)
                            await interaction.channel.set_permissions(member, overwrite=discord.PermissionOverwrite(read_messages=False))
                        except discord.NotFound:
                            pass
                        
                        await interaction.response.defer()

                        try:
                            category = await interaction.guild.fetch_channel(ticketType.closedTicketCategory)
                        except:
                            category = None

                        ticket.status = "closed"
                        await ticket.save()
                        
                        if category:
                            await interaction.channel.edit(category=category)

                        return await interaction.followup.send(embed=makeEmbed("info", "성공", "티켓이 닫혔습니다!"), view=closedButton())
                    except:
                        traceback.print_exc()
                        return await interaction.response.send_message(embed=makeEmbed("error", "오류", "티켓을 닫을 수 없습니다!"), ephemeral=True)
                    
                elif parts[1] == "REOPEN":
                    ticket = await Ticket.findByChannelId(interaction.channel.id)
                    if ticket.status != "closed":
                        return await interaction.response.send_message(embed=makeEmbed("error", "오류", "닫힌 티켓이 아닙니다!"), ephemeral=True)
                    
                    ticketType = await TicketType.findById(ticket.ticketType)
                    if not ticketType:
                        return await interaction.response.send_message(embed=makeEmbed("error", "오류", "삭제된 티켓 종류이기 때문에 티켓을 다시 열 수 없습니다!"), ephemeral=True)
                    
                    if ticketType.ticketCategory:
                        try:
                            await interaction.channel.edit(category=category)
                        except discord.NotFound:
                            return await interaction.response.send_message(embed=makeEmbed("error", "오류", "유효하지 않은 티켓 카테고리 입니다!"))

                    try:
                        overwrites = {}
                        member = await interaction.guild.fetch_member(ticket.user)
                        overwrites[member] = ticketOverwrite
                        overwrites[interaction.guild.default_role] = discord.PermissionOverwrite(read_messages=False)
                        await interaction.channel.edit(overwrites=overwrites)
                    except discord.NotFound:
                        return await interaction.response.send_message(embed=makeEmbed("error", "오류", "유저가 서버를 나갔습니다!"), ephemeral=True)
                    except:
                        traceback.print_exc()
                        return await interaction.response.send_message(embed=makeEmbed("error", "오류", "알 수 없는 오류입니다!"), ephemeral=True)
                    
                    try:
                        category = await interaction.guild.fetch_channel(ticketType.ticketCategory)
                    except:
                        pass

                    ticket.status = "open"
                    await ticket.save()

                    return await interaction.response.send_message(embed=makeEmbed("info", "성공", "티켓을 다시 열었습니다!"), view=CloseTicketButton())
                    
                elif parts[1] == "DELETE":
                    view = discord.ui.View(timeout=120)
                    saveButton = discord.ui.Button(style=discord.ButtonStyle.blurple, label="💾ㅣ저장하기", custom_id="save")
                    deleteButton = discord.ui.Button(style=discord.ButtonStyle.danger, label="🗑️ㅣ삭제하기", custom_id="delete")
                    
                    async def callback(mInteraction: discord.Interaction):
                        if await isClosingTicket(interaction.channel.id):
                            return await mInteraction.response.send_message(embed=makeEmbed("error", "오류", "삭제하고 있는 티켓입니다!"), ephemeral=True)
                        try:
                            await interaction.edit_original_response(embed=makeEmbed("info", "티켓 삭제", "티켓을 삭제하고 있습니다..."), view=None)
                            await mInteraction.response.defer(ephemeral=True)

                            await appendClosingTicket(interaction.channel.id)

                            ticket = await Ticket.findByChannelId(mInteraction.channel.id)
                            if ticket.status != "closed":
                                return await interaction.edit_original_response(embed=makeEmbed("error", "오류", "닫힌 티켓이 아닙니다!"))

                            if mInteraction.data["custom_id"] == "save": #티켓 저장 여부: 참
                                file = await transcriptTicket(mInteraction)
                                status = "saved"

                                try:
                                    user = await interaction.guild.fetch_member(ticket.user)
                                    embed = makeEmbed("info", setting.serviceName, "티켓이 닫혔습니다!")
                                    embed.add_field(name="닫은 사람", value=interaction.user.mention)
                                    icon_url = interaction.guild.icon.url if interaction.guild.icon else None
                                    embed.set_author(name=interaction.guild.name, icon_url=None)
                                    await user.send(embed=embed, view=discord.ui.View().add_item(discord.ui.Button(style=discord.ButtonStyle.url, label="대화내옹 보기", url=f"{domain}/ticket/{interaction.guild.id}/{interaction.channel.id}")))
                                except discord.NotFound:
                                    pass
                                except:
                                    traceback.print_exc()
                            else:
                                status = "deleted"

                            await mInteraction.channel.delete()
                            ticket.closeTime = datetime.now()
                            ticket.status = status
                            await ticket.save()
                        except:
                            print(traceback.print_exc())
                            await interaction.edit_original_response(embed=makeEmbed("error", "오류", "티켓을 삭제할 수 없습니다!"))
                        finally:
                            await delClosingTicket(interaction.channel.id)

                    saveButton.callback = callback
                    deleteButton.callback = callback

                    view.add_item(saveButton)
                    view.add_item(deleteButton)

                    await interaction.response.send_message(embed=makeEmbed("info", "티켓 삭제", "티켓 대화내역을 저장하시겠습니까?"), ephemeral=True, view=view)

async def setup(bot):
    await bot.add_cog(ticketExtension(bot))