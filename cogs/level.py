import discord
from discord.ext import tasks, commands
from pymongo import MongoClient
import random
from linkdb import *

mongo_client = MongoClient(link_db)
db = mongo_client["tgm_db"]
collection = db["tgm_levels"]

class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.collection = collection
        self.cooldown_users = set()
        self.xp_task.start()

    def cog_unload(self):
        self.xp_task.cancel()

    @tasks.loop(seconds=30)
    async def xp_task(self):
        self.cooldown_users.clear()

    @xp_task.before_loop
    async def before_xp_task(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self, message):
        guild_id = 1309556200844689459
        
        if user_data["level"] >= 150:
            return
        
        if message.author.bot or not message.guild or message.guild.id != guild_id:
            return

        user_id = str(message.author.id)
        user_data = self.collection.find_one({"user_id": user_id})

        if not user_data:
            user_data = {
                "user_id": user_id,
                "username": message.author.name,
                "level": 1,
                "xp": 0
            }
            self.collection.insert_one(user_data)

        if user_id in self.cooldown_users:
            return

        xp_gain = random.randint(5, 25)
        new_xp = user_data["xp"] + xp_gain
        level = user_data["level"]
        level_up = False

        if new_xp >= level * 100:
            new_xp = 0
            level += 1
            level_up = True

            # Przykład: dodaj role przy poziomach
            role_ids = {
                5: 111111111111111111,
                15: 222222222222222222,
                30: 333333333333333333,
                50: 444444444444444444,
            }
            if level in role_ids:
                role = message.guild.get_role(role_ids[level])
                if role:
                    await message.author.add_roles(role)

        self.collection.update_one(
            {"user_id": user_id},
            {"$set": {"xp": new_xp, "level": level, "username": message.author.name}}
        )

        if level_up:
            await message.channel.send(f"{message.author.mention} Gratulacje! Wbiłeś poziom {level}!")

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

            progress_bar = "[" + "█" * int(20 * progress) + " " * (20 - int(20 * progress)) + f"] {int(progress * 100)}%"

            xp_emoji = discord.PartialEmoji(animated=True, name="xp", id=1170497037339476018)
            level_emoji = discord.PartialEmoji(animated=True, name="lvl", id=1170499855068696717)
            progress_emoji = discord.PartialEmoji(animated=True, name="prg", id=1170499275306827826)

            embed = discord.Embed(
                title=f"Karta postępu użytkownika @{user.display_name}", color=0xA751ED
            )
            embed.add_field(name=f"{level_emoji} Poziom:", value=level, inline=True)
            embed.add_field(name=f"{xp_emoji} XP:", value=f"{xp}/{xp_needed}", inline=True)
            embed.add_field(name=f"{progress_emoji} Postęp:", value=progress_bar, inline=False)
            embed.set_thumbnail(url=user.display_avatar.url)

            await ctx.respond(embed=embed)
        else:
            await ctx.respond("Użytkownik nie został znaleziony w bazie.")

    @discord.slash_command(description="Top 10 na serwerze!")
    async def leaderboard(self, ctx):
        top_users = list(self.collection.find().sort("xp", -1).limit(10))
        embed = discord.Embed(title="🏆 Leaderboard", color=discord.Color.gold())

        for position, user in enumerate(top_users, start=1):
            name = user.get("username", f"Użytkownik {user['user_id']}")
            embed.add_field(
                name=f"{position}. {name}",
                value=f"Level: {user['level']} | XP: {user['xp']}",
                inline=False
            )

        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Level(bot))
