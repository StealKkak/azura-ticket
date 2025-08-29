import asyncio
import json
import os
import traceback

from datetime import *

import aiohttp
import discord

from bot import bot

from services.dbService import *

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
domain = os.getenv("DOMAIN") 
redirect_uri = domain + "/api/auth/login"

async def exchangeToken(code):
    url = "https://discord.com/api/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri
    }

    async with aiohttp.ClientSession() as session:
        tries = 0
        max_tries = 3
        while tries < max_tries:
            try:
                async with session.post(url=url, data=data, headers=headers) as res:
                    if res.status == 429:
                        resData = await res.json()
                        retry_after = resData.get("retry_after", 1) + 2
                        print(f"Rate limited! Retrying after {retry_after} seconds...")
                        await asyncio.sleep(retry_after)
                        continue

                    resData = await res.json()
                    if "error" in resData:
                        print(f"Error from Discord API: {resData["error_description"] if 'error_description' in resData else resData["error"]}")
                        return None
                    
                    return resData
                
            except aiohttp.ClientConnectionError as e:
                tries += 1
                print(f"Connection error occured, retring... ({tries}/{max_tries})")
                await asyncio.sleep(2)

            except Exception as e:
                print(f"An unexcpeted error occured: {e}")
                break

    return None
    
async def fetchAccessToken(refresh_token):
    url = "https://discord.com/api/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    async with aiohttp.ClientSession() as session:
        tries = 0
        max_tries = 3
        while tries < max_tries:
            try:
                async with session.post(url=url, data=data, headers=headers) as res:
                    if res.status == 429:
                        resData = await res.json()
                        retry_after = resData.get("retry_after", 1) + 2
                        print(f"Rate limited! Retrying after {retry_after} seconds...")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    resData = await res.json()
                    if "error" in resData:
                        print(f"Error from Discord API: {resData.get('error_description', resData['error'])}")
                        return None
                    
                    con, cur = await loadDB()
                    await cur.execute("UPDATE users SET refresh_token = ? WHERE refresh_token = ?", (resData["refresh_token"], refresh_token))
                    await con.commit()
                    await closeDB(con, cur)
                    return resData["access_token"]
                
            except aiohttp.ClientConnectionError:
                tries += 1
                print(f"Connection error occurred, retrying... ({tries}/{max_tries})")
                await asyncio.sleep(2)

            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                break
    return None

async def getAccessToken(user_id):
    con, cur = await loadDB()
    await cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = await cur.fetchone()
    await closeDB(con, cur)

    if not row:
        return None
    
    refresh_token = row["refresh_token"]
    return await fetchAccessToken(refresh_token)

async def getUserInfo(access_token):
    url = "https://discord.com/api/users/@me"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    tries = 0
    max_tries = 3

    async with aiohttp.ClientSession() as session:
        while tries < max_tries:
            try:
                async with session.get(url, headers=headers) as res:
                    if res.status == 429:
                        resData = await res.json()
                        retry_after = resData.get("retry_after", 1) + 2
                        print(f"Rate limited! Retrying after {retry_after} seconds...")
                        await asyncio.sleep(retry_after)
                        continue

                    if res.status == 200:
                        user_data = await res.json()
                        return user_data
                    else:
                        text = await res.text()
                        print(f"Failed to get user info: {res.status} {text}")
                        return None

            except aiohttp.ClientConnectionError:
                tries += 1
                print(f"Connection error occurred, retrying... ({tries}/{max_tries})")
                await asyncio.sleep(2)

            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                break

    return None


async def fetchUserGuilds(token: str):
    tries = 0
    max_tries = 3
    url = "https://discord.com/api/users/@me/guilds"

    while tries < max_tries:
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {token}"}
                async with session.get(url, headers=headers) as res:
                    if res.status != 429:
                        if not res.ok:
                            data = await res.json()
                            print("Discord API error:", data)
                            return None
                        else:
                            return await res.json()
                    else:
                        data = await res.json()
                        retry_after = data.get("retry_after", 1) + 2
                        await asyncio.sleep(retry_after)
        except Exception as e:
            print(f"Error during token exchange: {e}")
            return None
        tries += 1

    print("Token exchange failed after 3 tries")
    return None

def filterAdminGuilds(guilds):
    adminGuilds = []
    for guild in guilds:
        permissions = int(guild.get("permissions", 0))
        # 관리자 권한 비트(3번째, 0x8) 체크
        if (permissions & 0x8) == 0x8:
            adminGuilds.append(guild)
    return adminGuilds

async def getUserGuilds(userId):
    con, cur = await loadDB()
    await cur.execute("SELECT * FROM users WHERE id = ?", (userId,))
    user = await cur.fetchone()
    await closeDB(con, cur)

    guildsListRaw = user["guilds"]
    guildList = json.loads(guildsListRaw) if guildsListRaw else None

    if (
        not guildList
        or datetime.fromisoformat(guildList["last_update"]) + timedelta(minutes=30) < datetime.now()
    ):
        accessToken = await getAccessToken(userId)
        if not accessToken:
            return {"success": False, "error": {"code": 401, "message": "Refresh token expired"}}

        guilds = await fetchUserGuilds(accessToken)
        if not guilds:
            return {"success": False, "error": {"code": 500, "message": "Failed to fetch guilds"}}

        filtered_guilds = filterAdminGuilds(guilds)
        new_guild_list = {
            "last_update": datetime.now().isoformat(),
            "guilds": [{"id": g["id"], "name": g["name"], "icon": g["icon"]} for g in filtered_guilds],
        }

        con, cur = await loadDB()
        await cur.execute("UPDATE users SET guilds = ? WHERE id = ?", (json.dumps(new_guild_list, indent=2), userId),)
        await con.commit()
        await closeDB(con, cur)

        return {"success": True, "data": new_guild_list["guilds"]}

    return {"success": True, "data": guildList["guilds"]}


async def refreshGuildList(userId: str):
    con, cur = await loadDB()
    await cur.execute("SELECT * FROM users WHERE id = ?", (userId,))
    user = await cur.fetchone()
    await closeDB(con, cur)

    if not user:
        print("User not found")
        return

    accessToken = await getAccessToken(userId)
    if not accessToken:
        return {"success": False, "error": {"code": 401, "message": "Refresh token expired"}}

    guilds = await fetchUserGuilds(accessToken)
    if not guilds:
        return {"success": False, "error": {"code": 500, "message": "Failed to fetch guilds"}}

    filteredGuilds = filterAdminGuilds(guilds)
    new_guild_list = {
        "last_update": datetime.now().isoformat(),
        "guilds": [{"id": g["id"], "name": g["name"], "icon": g["icon"]} for g in filteredGuilds],
    }

    con, cur = await loadDB()
    await cur.execute("UPDATE users SET guilds = ? WHERE id = ?", (json.dumps(new_guild_list, indent=2), userId),)
    await con.commit()
    await closeDB(con, cur)

    return {"success": True, "data": new_guild_list["guilds"]}

async def isGuildAdmin(guild_id, username) -> bool:
    try:
        guild = await bot.fetch_guild(guild_id)
    except discord.NotFound:
        return False
    except:
        traceback.print_exc()
        return False
    
    try:
        member = await guild.fetch_member(username)
    except discord.NotFound:
        return False
    except:
        traceback.print_exc()
        return False
    
    if member.guild_permissions.administrator:
        return True
    else:
        return False