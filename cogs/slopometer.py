import discord
from discord.ext import commands

class slopometer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        # Podany poniżej kanał to #memy-tidzimi z serwera "Serwer TIDZIMIEGO"
        if reaction.message.channel.id != 1376823727035121674:
            return
        # Emoji, które powinno być na serwerze discord.
        if reaction.emoji.name == "slop":
            if reaction.count >= 15:
                await reaction.message.delete()

def setup(bot):
    bot.add_cog(slopometer(bot))
