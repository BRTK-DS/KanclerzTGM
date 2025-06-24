import discord
from discord.ext import tasks, commands
from pymongo import MongoClient
import random
from linkdb import *

mongo_client = MongoClient(link_db)
db = mongo_client["div_db"]
collection = db["div_levels"]

class level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.collection = MongoClient(link_db)["div_db"]["div_levels"]
        self.cooldown_users = set()
        self.xp_task.start()

    def cog_unload(self):
        self.xp_task.cancel()
        
    def get_user_info(self, message):
        # Look for a user id entry
        user_id = str(message.author.id)
        

    @tasks.loop(seconds=30)
    async def xp_task(self):
        for user_id in self.cooldown_users.copy():
            self.cooldown_users.remove(user_id)

    @xp_task.before_loop
    async def before_xp_task(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self, message):

        # Ignore bot's message, and ignore DMs
        if message.author.bot:
            return
        
        user_id = str(message.author.id)
        user_data = self.collection.find_one({"user_id": user_id})
        
        if not user_data:
            user_data = {
                "user_id": user_id,
                "level": 1,
                "xp": 0
            }
            self.collection.insert_one(user_data)
            
        xp_gain = random.randint(5,25)
        new_xp = user_data["xp"] + xp_gain
        level = user_data["level"]
        
        if user_id in self.cooldown_users:
            return

        # Check if a user has a new level
        level_up = False
        if new_xp >= level * 100:
            new_xp = 0
            level += 1
            level_up = True
            
            if level == 5: 
                role_id = 123 # Waiting for Role ID
                role = message.guild.get_role(role_id)
                await message.author.add_roles(role)

            if level == 15:
                role_id = 123 # Waiting for Role ID
                role = message.guild.get_role(role_id)
                await message.author.add_roles(role)

            if level == 30:
                role_id = 123 # Waiting for Role ID
                role = message.guild.get_role(role_id)
                await message.author.add_roles(role)

            if level == 50:
                role_id = 123 # Waiting for Role ID
                role = message.guild.get_role(role_id)
                await message.author.add_roles(role)
            
        self.collection.update_one(
            {"user_id": user_id},
            {"$set": {"xp": new_xp, "level": level}}
        )
        
        if level_up:
            await message.channel.send(
                f"{message.author.mention} Gratulacje! Wbiłeś poziom {level}!"
            )
            
        self.cooldown_users.add(user_id)

    @discord.slash_command(description="Sprawdź swój poziom na serwerze.")
    async def poziom(self, ctx, user: discord.User = None):
        user = user or ctx.author
        user_id = str(user.id)
        user_data = self.collection.find_one({"user_id": user_id})

        if user_data is not None:
            level = user_data["level"]
            xp = user_data["xp"]
            xp_needed = level * 100
            progress = xp / xp_needed

            progress_bar = "["
            filled = int(20 * progress)
            progress_bar += "█" * filled
            progress_bar += " " * (20 - filled)
            progress_bar += f"] {int(progress * 100)}%"

            xp_emoji = discord.PartialEmoji(
                animated=True, name="xp", id="1170497037339476018"
            )
            level_emoji = discord.PartialEmoji(
                animated=True, name="lvl", id="1170499855068696717"
            )
            progress_emoji = discord.PartialEmoji(
                animated=True, name="prg", id="1170499275306827826"
            )

            embed = discord.Embed(
                title=f"Karta postępu użytkownika @{user.display_name}", color=0xA751ED
            )
            embed.add_field(name=f"{level_emoji} Poziom:", value=level, inline=True)
            embed.add_field(
                name=f"{xp_emoji} XP:", value=f"{xp}/{xp_needed}", inline=True
            )
            embed.add_field(
                name=f"{progress_emoji} Postęp:", value=progress_bar, inline=False
            )
            embed.set_thumbnail(url=user.display_avatar.url)

            await ctx.respond(embed=embed)
        else:
            await ctx.respond("Użytkownik nie został znaleziony w bazie.")
            
def setup(bot):
    bot.add_cog(level(bot))