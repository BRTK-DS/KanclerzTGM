import discord
from discord.ext import tasks, commands
from pymongo import MongoClient
import random
from linkdb import *
from private import guild_id

mongo_client = MongoClient(link_db)
db = mongo_client["tgm_db"]
collection = db["tgm_levels"]

# Funkcja licząca wymagane XP na dany poziom
def xp_needed_for_level(level, base_xp=1000, increase=500):
    return base_xp + increase * (level - 1)

class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.collection = MongoClient(link_db)["tgm_db"]["tgm_levels"]
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
        #guild_id = 1309556200844689459
        user_id = str(message.author.id)
        channel_id = 1367966124460736633
        
        if message.author.bot or not message.guild or message.guild.id != guild_id or message.channel.id == channel_id:
            return

        # Pobierz dane lub utwórz nowy wpis
        user_data = self.collection.find_one({"user_id": user_id})
        if not user_data:
            user_data = {
                "user_id": user_id,
                "username": message.author.name,
                "level": 1,
                "xp": 0
            }
            self.collection.insert_one(user_data)

        # Limit poziomu
        if user_data["level"] >= 150:
            return

        # Cooldown
        if user_id in self.cooldown_users:
            return

        # Dodaj XP
        xp_gain = random.randint(5, 25)
        new_xp = user_data["xp"] + xp_gain
        level = user_data["level"]
        level_up = False

        # Sprawdź awans na poziom (może być kilka naraz)
        role_ids = {
            10: 1366072867061629038,
            30: 1367969910264824029,
            50: 1387524614955208878,
            70: 1387524678251446272,
            100: 1387524704235028671,
            150: 1387524928470782022,
        }

        while new_xp >= xp_needed_for_level(level):
            new_xp -= xp_needed_for_level(level)  # zachowaj nadwyżkę
            level += 1
            level_up = True

            # Nadanie roli
            if level in role_ids:
                role = message.guild.get_role(role_ids[level])
                if role:
                    await message.author.add_roles(role)

        # Zapisz do bazy
        self.collection.update_one(
            {"user_id": user_id},
            {"$set": {"xp": new_xp, "level": level, "username": message.author.name}}
        )

        # Komunikaty
        if level_up:
            await message.channel.send(f"{message.author.mention} Gratulacje! Wbiłeś poziom {level}!")
            if level in role_ids and (role := message.guild.get_role(role_ids[level])):
                await message.channel.send(
                    f"{message.author.mention} Otrzymałeś rangę {role.mention}!",
                    allowed_mentions=discord.AllowedMentions(roles=False, users=True)
                )

        # Dodaj do cooldowna
        self.cooldown_users.add(user_id)

    @discord.slash_command(description="Sprawdź swój poziom na serwerze.")
    async def poziom(self, ctx, user: discord.User = None):
        user = user or ctx.author
        user_id = str(user.id)
        user_data = self.collection.find_one({"user_id": user_id})
        
        xp_emoji = discord.PartialEmoji(animated=True, name="xp_orb", id=1404463975130730596)

        if user_data is not None:
            level = user_data["level"]
            xp = user_data["xp"]
            xp_needed = xp_needed_for_level(level)
            progress = xp / xp_needed

            progress_bar = "[" + "█" * int(20 * progress) + " " * (20 - int(20 * progress)) + f"] {int(progress * 100)}%"

            embed = discord.Embed(
                title=f"Karta postępu użytkownika @{user.display_name}", color=0xA751ED
            )
            embed.add_field(name=f":bar_chart: Poziom:", value=level, inline=True)
            embed.add_field(name=f"{xp_emoji} XP:", value=f"{xp}/{xp_needed}", inline=True)
            embed.add_field(name=f":chart_with_upwards_trend: Postęp:", value=progress_bar, inline=False)
            embed.set_thumbnail(url=user.display_avatar.url)

            await ctx.respond(embed=embed)
        else:
            await ctx.respond("Użytkownik nie został znaleziony w bazie.")

    @discord.slash_command(description="Top 10 na serwerze!")
    async def leaderboard(self, ctx):
        top_users = list(
            self.collection.find().sort([("level", -1), ("xp", -1)]).limit(10)
        )
        embed = discord.Embed(title="🏆 Leaderboard", color=discord.Color.gold())

        for position, user in enumerate(top_users, start=1):
            name = user.get("username", f"Użytkownik {user['user_id']}")
            level = user.get("level", 0)
            xp = user.get("xp", 0)
            embed.add_field(
                name=f"#{position} — {name}",
                value=f"**Poziom:** {level} | **XP:** {xp}",
                inline=False
            )

        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Level(bot))