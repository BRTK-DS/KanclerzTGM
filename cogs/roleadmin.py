import discord
from discord import guild_only
from discord.ext import commands
from permissioncontroller import PermissionController
from enum import Enum
from permissioncontroller import ModuleName


class TicketAction(Enum):
    ADD = "Add"
    REMOVE = "Remove"


class RoleAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.moderator_roles = PermissionController()

    @discord.slash_command(
        description="Przypisuje lub usuwa danej roli dostęp do danego modułu"
    )
    @discord.default_permissions(administrator=True)
    @guild_only()
    async def modrole(
        self,
        ctx,
        action: discord.Option(TicketAction),
        role: discord.Role,
        module: discord.Option(ModuleName),
    ):
        if action == TicketAction.ADD:
            self.moderator_roles.add_role_permission(str(role.id), module)
            await ctx.respond(
                f"Rola {role.name} otrzymała dostęp do modułu {module.value}",
                ephemeral=True,
            )
        else:
            self.moderator_roles.remove_role_permission(str(role.id), module)
            await ctx.respond(
                f"Rola {role.name} utraciła dostęp do modułu {module.value}",
                ephemeral=True,
            )


def setup(bot):
    bot.add_cog(RoleAdmin(bot))
