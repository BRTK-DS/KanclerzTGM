import discord
from discord.ext import commands
from pymongo import MongoClient
from linkdb import *

mongo_client = MongoClient(link_db)
db = mongo_client["tgm_db"]
collection = db["tgm_levels"]

class LevelAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.collection = MongoClient(link_db)["tgm_db"]["tgm_levels"]

    def _get_user_data(self, user_id: str):
        return self.collection.find_one({"user_id": user_id})

    def _ensure_user_data(self, user: discord.User):
        user_id = str(user.id)
        data = self._get_user_data(user_id)
        if not data:
            data = {
                "user_id": user_id,
                "username": user.name,
                "level": 1,
                "xp": 0
            }
            self.collection.insert_one(data)
        return data

    @discord.slash_command(description="Dodaj XP użytkownikowi.")
    @discord.default_permissions(administrator=True)
    async def add_xp(self, ctx, user: discord.User, xp: int):
        data = self._ensure_user_data(user)
        new_xp = data["xp"] + xp
        self.collection.update_one(
            {"user_id": str(user.id)},
            {"$set": {"xp": new_xp, "username": user.name}}
        )
        await ctx.respond(f"✅ Dodano {xp} XP dla {user.mention}. Teraz ma {new_xp} XP.")

    @discord.slash_command(description="Ustaw konkretną ilość XP.")
    @discord.default_permissions(administrator=True)
    async def set_xp(self, ctx, user: discord.User, xp: int):
        self._ensure_user_data(user)
        self.collection.update_one(
            {"user_id": str(user.id)},
            {"$set": {"xp": xp, "username": user.name}}
        )
        await ctx.respond(f"✅ Ustawiono {xp} XP dla {user.mention}.")

    @discord.slash_command(description="Ustaw konkretny poziom.")
    @discord.default_permissions(administrator=True)
    async def set_level(self, ctx, user: discord.User, level: int):
        self._ensure_user_data(user)
        self.collection.update_one(
            {"user_id": str(user.id)},
            {"$set": {"level": level, "username": user.name}}
        )
        await ctx.respond(f"✅ Ustawiono poziom {level} dla {user.mention}.")

def setup(bot):
    bot.add_cog(LevelAdmin(bot))