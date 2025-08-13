import discord
import os

def makeEmbed(type, title, description):
    colors = {
        "info": discord.Color.blue(),
        "warn": discord.Color.yellow(),
        "error": discord.Color.red()
    }

    embed = discord.Embed(title=title, description=description, color=colors.get(type, type))
    embed.set_footer(text=f"Powered by {os.getenv("OWNER_NAME")}")
    return embed