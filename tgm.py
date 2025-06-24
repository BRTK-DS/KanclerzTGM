import discord
import os
from private import *

intents = discord.Intents.all()
intents.members = True
bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}!")
    
initial_extensions = []

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        initial_extensions.append("cogs." + filename[:-3])
        
if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)
        
bot.run(TKN)