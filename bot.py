import asyncio
import os
import discord
from discord.ext import commands
from ical_parser import Event, Calendar, check_refresh, refresh_calendar, CALENDAR
import datetime
from utils import *


HELP_MESSAGE = """
### Commands:

- `>help` - Show this message
- `>today` [t, td, timetable] - Display the current timetable
- `>tomorrow` [tmr] - Display the timetable for tomorrow
"""

bot = commands.Bot(
    command_prefix='>',
    intents=discord.Intents.all()
)
bot.remove_command('help')
calendar = Calendar(Settings["calendar_file"])


async def update_calendar(fp):

    if not check_refresh(fp):
        return

    refresh_calendar(fp, CALENDAR)
    # the most stupid thing I've ever done
    calendar.__init__(fp)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')

    # cursed code, if you understand asyncio loops feel free to change
    while True:
        await update_calendar(fp = Settings["calendar_file"])
        await asyncio.sleep(60)


@bot.command(aliases=["h"])
async def help(ctx):
    await ctx.send(HELP_MESSAGE)

@bot.command(alias=["t", "td", "timetable"])
async def today(ctx, *, date=datetime.date.today(), datef="Today"):
    # written for extra commands like tomorrow, fd, monday, tuesday, ect to just swap out the
    # date check and formatting of datef
    response = f"# Events {datef}:\n"

    event: Event

    for i, event in enumerate(calendar.events_on_day(date)):
        uid = event.start_time.strftime(f"{i}%d")

        response += f"### [{uid}]    {event.summary}\n"

        if event.location:
            response += "   Location: " + event.location + "\n"

        if event.start_time.date() == event.end_time.date():
            response += event.start_time.strftime("   Time: %H:%M") + " - " + event.end_time.strftime("%H:%M\n")

        else:
            response += event.start_time.strftime("   Start: %d/%m/%Y, %H:%M:%S\n")
            response += event.end_time.strftime("   End: %d/%m/%Y, %H:%M:%S\n")

    response += f"\nLast updated: {calendar.last_refresh}"

    await ctx.send(response)


@bot.command(alias=["tm", "tmr"])
async def tomorrow(ctx):
    await today(ctx, date=datetime.date.today() + datetime.timedelta(days=1), datef="Tomorrow")


@bot.command(alias=["d", "dts"])
async def details(ctx, uid: str):
    date = datetime.date.today()
    target_day = datetime.datetime.strptime(f"{date.year}{date.month}{uid[1:]}", "%Y%m%d")

    events = calendar.events_on_day(target_day)
    event: Event = events[int(uid[0])]

    message = f"{event.summary}"


bot.run(os.environ['TOKEN'])
