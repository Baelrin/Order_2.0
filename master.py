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
    Reads the configuration from a JSON file.

    Returns:
        dict: The configuration as a dictionary.
    Raises:
        FileNotFoundError: If the config.json file does not exist.
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
    Get members with the old role.

    Args:
        guild (discord.Guild): The guild to check for members with the old role.

    Returns:
        List[discord.Member]: A list of members with the old role.
    """
    old_role = guild.get_role(OLD_ROLE_ID)
    return old_role.members if old_role else []


async def send_message(channel, message):
    """
    Send a message to a Discord channel.

    Args:
        channel (discord.Channel): The channel to send the message to.
        message (str): The message to send.
    """
    await channel.send(message)
    await asyncio.sleep(1)


async def send_messages(channel, messages):
    """
    Send multiple messages to a Discord channel.

    Args:
        channel (discord.Channel): The channel to send the messages to.
        messages (List[str]): The messages to send.
    """
    tasks = [send_message(channel, message) for message in messages]
    await asyncio.gather(*tasks)


async def change_role_and_send_message(member, old_role, new_role, channel):
    """
    Change a member's role and send them a congratulatory message.

    Args:
        member (discord.Member): The member to change the role for.
        old_role (discord.Role): The old role to remove.
        new_role (discord.Role): The new role to add.
        channel (discord.Channel): The channel to send the congratulatory message to.

    Raises:
        discord.Forbidden: If the bot does not have permission to change roles or send messages.
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
    Check if the command sender has the admin role.

    Args:
        ctx (commands.Context): The context of the command.

    Returns:
        bool: True if the sender has the admin role, False otherwise.
    """
    admin_role = ctx.guild.get_role(ADMIN_ROLE_ID)
    return admin_role in ctx.author.roles if admin_role else False


def check_join_time(member, threshold):
    """
    Check if a member's join time exceeds a threshold.

    Args:
        member (discord.Member): The member to check.
        threshold (int): The join time threshold in seconds.

    Returns:
        bool: True if the member's join time exceeds the threshold, False otherwise.
    """
    join_time = member.joined_at.astimezone(pytz.timezone(TIMEZONE))
    current_time = datetime.datetime.now(pytz.timezone(TIMEZONE))
    return (current_time - join_time).total_seconds() > threshold


def check_roles_and_channel(ctx):
    """
    Check if the required roles and channel exist in the guild.

    Args:
        ctx (commands.Context): The context of the command.

    Returns:
        bool: True if the roles and channel exist, False otherwise.
    """
    guild = ctx.guild
    old_role = guild.get_role(OLD_ROLE_ID)
    new_role = guild.get_role(NEW_ROLE_ID)
    channel = bot.get_channel(CHANNEL_ID)
    if not old_role or not new_role or not channel:
        logging.error("Role or channel not found.")
        return False
    return True


async def handle_command(ctx, threshold: int = JOIN_TIME_THRESHOLD):
    """
    Handle the execution of the bot command.

    Args:
        ctx (commands.Context): The context of the command.
        threshold (int, optional): The join time threshold. Defaults to JOIN_TIME_THRESHOLD.
    """
    if not check_admin_role(ctx):
        await ctx.send("У вас нет прав на выполнение этой команды.")
        return

    if not check_roles_and_channel(ctx):
        await ctx.send("Role or channel not found.")
        return

    guild = ctx.guild
    old_role = guild.get_role(OLD_ROLE_ID)
    new_role = guild.get_role(NEW_ROLE_ID)
    channel = bot.get_channel(CHANNEL_ID)

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
    Bot command handler for 'C'.

    Args:
        ctx (commands.Context): The context of the command.
        threshold (int, optional): The join time threshold. Defaults to JOIN_TIME_THRESHOLD.
    """
    await handle_command(ctx, threshold)


@bot.command()
async def c(ctx, threshold: int = JOIN_TIME_THRESHOLD):
    """
    Bot command handler for 'c'.

    Args:
        ctx (commands.Context): The context of the command.
        threshold (int, optional): The join time threshold. Defaults to JOIN_TIME_THRESHOLD.
    """
    await handle_command(ctx, threshold)


@bot.event
async def on_ready():
    """
    Event handler for when the bot is ready.
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
