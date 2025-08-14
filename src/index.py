import asyncio
import logging

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from quart import Quart, request, render_template, jsonify

from routes.index import router

import services.configService as settings

from services.dbService import *

from utils.randomUtil import *

load_dotenv(override=True)

TOKEN = os.getenv("TOKEN")
PREFIX = os.getenv("PREFIX")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

app = Quart(__name__, template_folder="../views", static_folder="../static")
app.secret_key = os.getenv("SESSION_SECRETS", randomString(20))

@app.errorhandler(404)
async def notFound(e):
    if request.path.startswith("/api"):
        return jsonify({"error": "Service not found"}), 404
    return await render_template("error/404.html"), 404

@app.errorhandler(500)
async def serverError(e):
    if request.path.startswith("/api"):
        return jsonify({"error": "Internal server error"}), 500
    return render_template("error/500.html"), 500

app.register_blueprint(router)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

@bot.event
async def on_ready():
    extensions = ["ticketExtension"]
    for extension in extensions:
        try:
            await bot.load_extension(f"extensions.{extension}")
        except Exception as e:
            print(f"An unexpected error occurred while loading {extension}: {e}")
    await bot.tree.sync()
    print(f"Logged in as {bot.user.name}")

@app.before_serving
async def startUp():
    await initDB()
    asyncio.create_task(bot.start(TOKEN))

app.run("0.0.0.0", os.getenv("PORT"), True)