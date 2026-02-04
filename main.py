import discord
from discord.ext import commands
import asyncio
import logging
from dotenv import load_dotenv
import os
import webserver
import datetime
from math import floor 

load_dotenv()
token = os.environ['discordkey']
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
prefix_symbol = '/'
bot = commands.Bot(command_prefix=prefix_symbol, intents=intents, help_command=None)

template_file = open("template.txt", "r")
template = template_file.read().splitlines()
template_file.close()

taken_nodes_file = open("taken nodes.txt", "r")
taken_nodes_full = taken_nodes_file.read().splitlines()
taken_nodes = [line[:2] for line in taken_nodes_full]
taken_nodes_file.close()

channel_file = open("channel_name.txt", "r")
bg_channel = channel_file.readline().replace('\n', '')
channel_file.close()

async def Dips(ctx, bg): 
    global current_state_message
    try:
        node = int(ctx.message.content[len(prefix_symbol) + len('disp') + 1:])
        if node > 50 or node < 37:
            await ctx.channel.send("Not valid number, try between 37 and 50", delete_after=5.0)
        elif any(f"{node}" == taken_node for taken_node in taken_nodes[taken_nodes.index(f"{bg}."):taken_nodes.index(f"{bg +1}.")]):
            await ctx.channel.send("The node's already taken", delete_after=5.0)
        else:
            current_state_message = UpdateList(bg, ctx.author.nick, node, True)
            await ctx.channel.purge()
            await ctx.channel.send(current_state_message)
    except ValueError:
        await ctx.channel.send(f"Not a number (write it like this: \"{prefix_symbol}dips{bg} NUMBER\"", delete_after=5.0)

async def GiveUpNode(ctx, bg):
    global current_state_message
    try:
        node = int(ctx.message.content[len(prefix_symbol) + len('disp') + 1:])
        if node > 50 or node < 37:
            await ctx.channel.send("Not valid number, try between 37 and 50", delete_after=5.0)
        else:
            final_message = current_state_message.replace('\\n', '\n').splitlines()
            occupied_line = final_message[(bg - 1)*(len(template) + 1) + template.index(f"{node}") + 1]
            try:
                first_delimiter = occupied_line.index(' ') + 1
                occupier = occupied_line[first_delimiter:] 
                if ctx.author.nick != occupier:
                    await ctx.channel.send("It's not your node", delete_after=5.0)
                else:
                    current_state_message = UpdateList(bg, ctx.author.nick, node, False)
                    await ctx.channel.purge()
                    await ctx.channel.send(current_state_message)
            except ValueError:
                await ctx.channel.send("There's no John Cena, it's actually empty", delete_after=5.0)
           
    except ValueError:
        await ctx.channel.send(f"Not a number (write it like this: \"{prefix_symbol}nah{bg} NUMBER\"", delete_after=5.0)

def UpdateDate():
    time_of_call = datetime.datetime.now(datetime.UTC)
   
    dates_file = open("dates.txt", "r")
    all_dates = dates_file.readlines()
    for single_date in all_dates:
        if single_date == '':
            all_dates.remove(single_date)
    dates_file.close()

    dates = []
    for date in all_dates:
        try:
            month = int(date[:2])
            day = int(date[3:5])
            year = int(date[6:10])
            hour = int(date[11:13])
            minute = int(date[14:16])
            dates.append(datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, tzinfo=datetime.UTC))
        except ValueError:
            print("Couldn't convert dates (formatting issue) - won't auto update this time")
            return
        
    for date in dates:
        if date < time_of_call:
            dates.remove(date)

    next_restart_time = min(dates)
    dates_wfile = open("dates.txt", "w")
    for date in dates:
        dates_wfile.write(f"{str(date.month).zfill(2)}/{str(date.day).zfill(2)}/{date.year} {str(date.hour).zfill(2)}:{str(date.minute).zfill(2)}\n")
    return next_restart_time

def FillTemplate():
    final_message = ""
    for i in range(0, len(template)*3):
        if (i % len(template)) == 0:
            final_message += f"==============={int(floor(i/len(template)) + 1)}================\n" + template[0] + '\n'
        else:
            if (template[i % len(template)][:2] in taken_nodes[taken_nodes.index(f"{floor(i/len(template)) + 1}."):taken_nodes.index(f"{floor(i/len(template)) + 2}.")]):
                for j in range(0, len(taken_nodes)):
                    if template[i % len(template)][:2] == taken_nodes[j]:
                        final_message += taken_nodes_full[j] + '\n'
                        break
            else:
                final_message += template[i % len(template)] + '\n'
    return final_message

def UpdateList(bg: int, username, node, take: bool):
    if take:
        line = f"{node} {username}"
        taken_nodes_full.insert(taken_nodes_full.index(f"{bg}.") + 1, line)
        taken_nodes.insert(taken_nodes.index(f"{bg}.") + 1, f"{node}")
    else:
        taken_bg_nodes = taken_nodes_full[taken_nodes_full.index(f"{bg}.") + 1:taken_nodes_full.index(f"{bg + 1}.")]
        taken_bg_nodes = [bg_node[:2] for bg_node in taken_bg_nodes]
        occupation_index = taken_bg_nodes.index(f"{node}")
       
        taken_nodes_full.pop(taken_nodes_full.index(f"{bg}.") + occupation_index + 1)
        taken_nodes.pop(taken_nodes.index(f"{bg}.") + occupation_index + 1)

    taken_nodes_file = open("taken nodes.txt", "w")
    taken_nodes_file.write('\n'.join(taken_nodes_full))
    taken_nodes_file.close()

    final_message = current_state_message.replace('\\n', '\n').splitlines()

    line = f"{node}"
    if take:
        line += f" {username}"
   
    final_message[(bg - 1)*(len(template) + 1) + template.index(f"{node}") + 1] = line
    return '\n'.join(final_message)

restarted_war = False
current_state_message = FillTemplate()
restart_datetime = UpdateDate()

#automatization of restarting war
@bot.event
async def on_ready():
    global restarted_war
    if not restarted_war:
        asyncio.create_task(restart_war())
        restarted_war = True

async def restart_war():
    global restart_datetime
    while True:
        time_now = datetime.datetime.now(datetime.UTC)
        seconds = (restart_datetime - time_now).total_seconds()
        await asyncio.sleep((restart_datetime - time_now).total_seconds())
        
        taken_nodes_file = open("taken nodes.txt", "w")
        taken_nodes_file.write('1.\n2.\n3.\n4.')
        taken_nodes_file.close()

        taken_nodes_full = ['1.', '2.', '3.', '4.']
        taken_nodes = ['1.', '2.', '3.', '4.']

        for channel in bot.get_all_channels():
            if channel.name == bg_channel and isinstance(channel, discord.TextChannel):
                live_channel = bot.get_channel(channel.id)
                new_bg = ''
                for i in range(1, 4):
                    new_bg += f"==============={i}================\n{'\n'.join(template)}\n"
                await live_channel.purge()
                await live_channel.send(new_bg)
                break

        restart_datetime = UpdateDate()

#spam handling
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.channel.name == bg_channel:
        await message.delete()

    await bot.process_commands(message)

#choosing
@bot.command(description="Choose the node")
async def dips1(ctx):
    if (ctx.channel.name == bg_channel):
        await Dips(ctx, 1)

@bot.command(description="Choose the node")
async def dips2(ctx):
    if (ctx.channel.name == bg_channel):
        await Dips(ctx, 2)

@bot.command(description="Choose the node")
async def dips3(ctx):
    if (ctx.channel.name == bg_channel):
        await Dips(ctx, 3)

#rechoosing
@bot.command(description="If you haven't consulted with anyone you're a scumbag for this")
async def retake1(ctx):
    if (ctx.channel.name == bg_channel):
        await ctx.channel.send("retake1")
    return

@bot.command(description="If you haven't consulted with anyone you're a scumbag for this")
async def retake2(ctx):
    if (ctx.channel.name == bg_channel):
        await ctx.channel.send("retake1")
    return

@bot.command(description="If you haven't consulted with anyone you're a scumbag for this")
async def retake3(ctx):
    if (ctx.channel.name == bg_channel):
        await ctx.channel.send("retake1")
    return

#give in the node
@bot.command(description="You can't actually take that one")
async def nah1(ctx):
    if (ctx.channel.name == bg_channel):
        await GiveUpNode(ctx, 1)

@bot.command(description="You can't actually take that one")
async def nah2(ctx):
    if (ctx.channel.name == bg_channel):
        await GiveUpNode(ctx, 2)

@bot.command(description="You can't actually take that one")
async def nah3(ctx):
    if (ctx.channel.name == bg_channel):
        await GiveUpNode(ctx, 3)
#help
@bot.command()
async def help(context):
    message = ''
    for i in range(1, 4):
        message += f"/dips{i} node_number - select node_number in {i}th bg\n"
    for i in range(1, 4):
        message += f"/nah{i} node_number - select node_number in {i}th bg\n"
    await context.send(message, delete_after=12.13)

#initialization
webserver.keep_alive()
bot.run(token, log_handler=handler)
