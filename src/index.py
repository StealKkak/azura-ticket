import asyncio
import logging

import os

from dotenv import load_dotenv
from hypercorn.config import Config
from hypercorn.asyncio import serve
from quart import Quart, request, render_template, jsonify
load_dotenv(override=True)

from routes.index import router

import services.configService as settings

from services.dbService import *

from utils.randomUtil import *

from bot import bot
import discord

TOKEN = os.getenv("TOKEN")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
PORT = os.getenv("PORT")

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
    return await render_template("error/500.html"), 500

@app.errorhandler(405)
async def methodNotAllowed(e):
    return jsonify({"error": "Method Not Allowed"}), 405

app.register_blueprint(router)

@bot.event
async def on_ready():
    extensions = ["ticketExtension", "adminExtension"]
    for extension in extensions:
        try:
            await bot.load_extension(f"extensions.{extension}")
        except Exception as e:
            print(f"An unexpected error occurred while loading {extension}: {e}")
    await bot.tree.sync()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Beta 버전입니다!"), status=discord.Status.online)
    print(f"Logged in as {bot.user.name}")

@app.before_serving
async def startUp():
    await initDB()
    asyncio.create_task(bot.start(TOKEN))


config = Config()
config.bind = [f"127.0.0.1:{PORT}"]

asyncio.run(serve(app, config))