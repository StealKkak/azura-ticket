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
                    del rateLimits[userId]

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
    overwrites = {}
    overwrites[interaction.user] = ticketOverwrite
    overwrites[interaction.guild.default_role] = discord.PermissionOverwrite(read_messages=False)
    
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
        overwrites[interaction.guild.default_role] = discord.PermissionOverwrite(read_messages=False)
        overwrites[interaction.user] = ticketOverwrite
        for role in ticketType.role:
            overwrites[discord.Object(role)] = ticketOverwrite
    else:
        category = None

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
        self.bot: commands.Bot = bot
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
            if len(tickets) == 0:
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
                    
                    if len(parts) > 2:
                        ticketTypeId = parts[2]
                    else:
                        ticketTypeId = interaction.data.get("values")[0]

                    ticketType = await TicketType.findById(ticketTypeId)
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

                        try:
                            category = await interaction.guild.fetch_channel(ticketType.closedTicketCategory)
                        except discord.NotFound:
                            return await interaction.response.send_message(embed=makeEmbed("error", "오류", "닫은 티켓 카테고리 설정이 유효하지 않아 티켓을 닫을 수 없습니다!"), view=discord.ui.View(discord.ui.Button(label="티켓 삭제", style=discord.ButtonStyle.danger, custom_id="TICKET_DELETE_ERROR")), ephemeral=True)

                        ticket.status = "closed"
                        await ticket.save()
                        await interaction.channel.edit(category=category)
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