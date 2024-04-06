import asyncio
import datetime
import json
import logging
import os
import random

import discord
import pytz
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv("token.env")


def read_config():
    """
    Reads and returns the configuration from the 'config.json' file.

    :return: The JSON object containing the configuration.
    :raises FileNotFoundError: If the configuration file does not exist.
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
    Fetches all members with the OLD_ROLE from the guild.

    :param guild: The Discord guild to search within.
    :return: A list of members who have the OLD_ROLE or an empty list if the role does not exist.
    """
    old_role = guild.get_role(OLD_ROLE_ID)
    return old_role.members if old_role else []


async def change_role_and_send_message(member, old_role, new_role, channel):
    """
    Removes the old role from a member, assigns them a new role, and sends a randomized message in a specified channel.

    :param member: The member to update roles for.
    :param old_role: The role to remove from the member.
    :param new_role: The role to add to the member.
    :param channel: The channel to send the message in.
    :raises discord.Forbidden: If the bot does not have permission to change roles or send messages.
    """
    try:
        await member.remove_roles(old_role)
        await member.add_roles(new_role)
        with open("messages.json", "r") as file:
            messages = json.load(file)
        message = random.choice(messages)
        await channel.send(message.format_map({"member": member.mention}))
    except discord.Forbidden as e:
        logging.error(f"Error changing role and sending message: {e}")
        raise


def check_admin_role(ctx):
    """
    Checks if the command sender has the admin role.

    :param ctx: The context of the command.
    :return: True if the sender has the admin role, False otherwise.
    """
    admin_role = ctx.guild.get_role(ADMIN_ROLE_ID)
    return admin_role in ctx.author.roles if admin_role else False


def check_join_time(member, threshold):
    """
    Checks if a member's join time exceeds the specified threshold.

    :param member: The member to check.
    :param threshold: The join time threshold in seconds.
    :return: True if the member's join time exceeds the threshold, False otherwise.
    """
    join_time = member.joined_at.astimezone(pytz.timezone(TIMEZONE))
    current_time = datetime.datetime.now(pytz.timezone(TIMEZONE))
    return (current_time - join_time).total_seconds() > threshold


async def handle_command(ctx, threshold: int = JOIN_TIME_THRESHOLD):
    """
    Handles the custom bot command by checking for the admin role, searching for members with the OLD_ROLE,
    and updating their roles if their join time exceeds the specified threshold.

    :param ctx: The context of the command.
    :param threshold: The join time threshold in seconds.
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
    await handle_command(ctx, threshold)


@bot.command()
async def c(ctx, threshold: int = JOIN_TIME_THRESHOLD):
    await handle_command(ctx, threshold)


@bot.event
async def on_ready():
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
