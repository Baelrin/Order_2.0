import asyncio
import datetime
import json
import logging
import os

import discord
import pytz
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv("token.env")


def read_config():
    """
    Reads the configuration file and loads it as a JSON object.
    If the file is not found, logs an error and raises a FileNotFoundError.
    """
    try:
        with open("config.json") as f:
            return json.load(f)
    except FileNotFoundError as e:
        logging.error(f"Failed to read configuration file: {e}")
        raise


config = read_config()

TOKEN = os.getenv("TOKEN")
ADMIN_ROLE_ID = config["ADMIN_ROLE_ID"]
OLD_ROLE_ID = config["OLD_ROLE_ID"]
NEW_ROLE_ID = config["NEW_ROLE_ID"]
CHANNEL_ID = config["CHANNEL_ID"]
JOIN_TIME_THRESHOLD = config["JOIN_TIME_THRESHOLD"]
TIMEZONE = config["TIMEZONE"]
PREFIX = config["PREFIX"]
LOG_FILE = config["LOG_FILE"]

logging.basicConfig(filename=LOG_FILE, level=logging.INFO)

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=PREFIX, intents=intents)


async def get_members_with_old_role(guild):
    """
    Retrieves members with a specified old role within a guild.
    If the role is not found, returns an empty list.
    """
    old_role = guild.get_role(OLD_ROLE_ID)
    return old_role.members if old_role else []


async def send_message(channel, message):
    """
    Sends a message to a specified channel and then sleeps for 1 second.
    """
    await channel.send(message)
    await asyncio.sleep(1)


async def send_messages(channel, messages):
    """
    Concurrently sends multiple messages to a specified channel.
    """
    tasks = [send_message(channel, message) for message in messages]
    await asyncio.gather(*tasks)


async def change_role_and_send_message(member, old_role, new_role, channel):
    """
    Changes the role of a member from old_role to new_role and sends a congratulations message.
    Logs an error if the operation is forbidden.
    """
    try:
        await member.remove_roles(old_role)
        await member.add_roles(new_role)
        await channel.send(
            f"{member.mention}, поздравляю с новым титулом! Теперь ты житель. Живи во имя Рэйвенхолда!"
        )
    except discord.Forbidden as e:
        logging.error(f"Error changing role and sending message: {e}")
        raise


def check_admin_role(ctx):
    """
    Checks if the author of the context has the admin role.
    Returns True if the admin role is present, else False.
    """
    admin_role = ctx.guild.get_role(ADMIN_ROLE_ID)
    return admin_role in ctx.author.roles if admin_role else False


def check_join_time(member, threshold):
    """
    Checks if a member's join time exceeds a specified threshold.
    Returns True if the condition is met, else False.
    """
    join_time = member.joined_at.astimezone(pytz.timezone(TIMEZONE))
    current_time = datetime.datetime.now(pytz.timezone(TIMEZONE))
    return (current_time - join_time).total_seconds() > threshold


async def handle_command(ctx, threshold: int = JOIN_TIME_THRESHOLD):
    """
    Handles a command to change roles based on join time and admin role check.
    Sends appropriate feedback messages upon success or failure.
    """
    if not check_admin_role(ctx):
        await ctx.send("У вас нет прав на выполнение этой команды.")
        return

    guild = ctx.guild
    old_role = guild.get_role(OLD_ROLE_ID)
    new_role = guild.get_role(NEW_ROLE_ID)
    channel = bot.get_channel(CHANNEL_ID)

    if not old_role or not new_role or not channel:
        logging.error("Role or channel not found.")
        await ctx.send("Role or channel not found.")
        return

    members = await get_members_with_old_role(guild)
    if tasks := [
        change_role_and_send_message(member, old_role, new_role, channel)
        for member in members
        if check_join_time(member, threshold)
    ]:
        await asyncio.gather(*tasks)
    else:
        await ctx.send("Достойных кандидатов не нашлось, милорд.")


@bot.command()
async def C(ctx, threshold: int = JOIN_TIME_THRESHOLD):
    """
    Command handler for uppercase 'C'. Delegates to handle_command.
    """
    await handle_command(ctx, threshold)


@bot.command()
async def c(ctx, threshold: int = JOIN_TIME_THRESHOLD):
    """
    Command handler for lowercase 'c'. Delegates to handle_command.
    """
    await handle_command(ctx, threshold)


@bot.event
async def on_ready():
    """
    Event handler for when the bot is ready.
    Logs the bot's name or an error if the bot details are missing.
    """
    if bot.user is not None:
        logging.info(f"Logged in as {bot.user.name}")
    else:
        logging.info("User is None")


try:
    if TOKEN is None:
        raise ValueError("Token is None")
    bot.run(TOKEN)
except discord.LoginFailure as e:
    logging.error(f"Failed to run bot: {e}")
    raise
