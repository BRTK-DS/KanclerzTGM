import discord
from discord import guild_only, PermissionOverwrite, Interaction
from discord.ext import commands

from private import ticket_category_id
from permissioncontroller import PermissionController, ModuleName

class TicketModal(discord.ui.Modal):
    def __init__(self, moderator_roles: PermissionController):
        super().__init__(title="Utwórz ticket")
        self.moderator_roles = moderator_roles
        self.add_item(discord.ui.InputText(label="Proszę, opisz krótko swój problem", placeholder="Wpisz tutaj", style=discord.InputTextStyle.long))


    async def callback(self, interaction: Interaction):
        category = interaction.guild.get_channel(ticket_category_id)
        member = interaction.user
        overwrites = {interaction.guild.default_role: PermissionOverwrite(view_channel=False, send_messages=True),
                      member: PermissionOverwrite(view_channel=True)}
        moderator_role_ids = self.moderator_roles.get_roles_with_permission(ModuleName.MODERATOR)
        for role_id in moderator_role_ids:
            role = interaction.guild.get_role(role_id)
            if role:
                overwrites[role] = PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await interaction.guild.create_text_channel(
            name=f"{interaction.user.name}-ticket",
            category=category,
            overwrites=overwrites,
            reason=f"Ticket stworzony przez użytkownika {member.display_name}"
        )

        description = self.children[0].value
        embed = discord.Embed(title=f"Ticket", color=0x33cc33)
        embed.add_field(name="Opis", value=description)

        await channel.send(content=f"<@{member.id}>", embed=embed)
        await interaction.response.send_message(f"Utworzono ticket <#{channel.id}>", ephemeral=True)


class CreateTicketView(discord.ui.View):
    def __init__(self, moderator_roles: PermissionController):
        super().__init__(timeout=None)
        self.moderator_roles = moderator_roles
    
    @discord.ui.button(label="Utwórz ticket", style=discord.ButtonStyle.green, custom_id="create_ticket_button")
    async def button_callback(self, button, interaction: Interaction):
        # TODO: system sprawdzania czy ten użytkownik nie posiada już ticketa
        await interaction.response.send_modal(TicketModal(self.moderator_roles))

class TicketControlModal(discord.ui.Modal):
    def __init__(self, cog):
        super().__init__(title="Zamknij ticket")
        self.cog = cog

        self.add_item(discord.ui.InputText(
            label="Podaj powód zamknięcia ticketa (opcjonalnie)",
            placeholder="Wpisz tutaj",
            required=False
        ))

    async def callback(self, interaction: discord.Interaction):
        reason = self.children[0].value
        await self.cog._close_ticket(interaction, reason)
        await interaction.response.defer(ephemeral=True)

class CloseTicketView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        self.moderator_roles = PermissionController()

    @discord.ui.button(label="Zamknij ticket", style=discord.ButtonStyle.red, custom_id="close_ticket_button")
    async def close_ticket_button(self, button, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Nie masz uprawnień administratora, aby zamknąć ticket.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(TicketControlModal(self.cog))

class TicketAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.moderator_roles = PermissionController()

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(CreateTicketView(self.moderator_roles))
        self.bot.add_view(CloseTicketView(self))

    async def _is_ticket_channel(self, channel):
        if not isinstance(channel, discord.TextChannel):
            return "❌ To nie jest kanał tekstowy."
        elif channel.category_id != ticket_category_id:
            return "❌ To nie jest kanał-ticket."
        return None

    async def _do_close_ticket(self, channel, author, reason = None):
        is_ticket_channel = await self._is_ticket_channel(channel)

        if is_ticket_channel is not None:
            return is_ticket_channel

        await channel.delete(reason=f"Closing ticket by {author}")
        # TODO: Loguj usunięte tickety na kanale mod-log
        return None

    async def _close_ticket(self, interaction: discord.Interaction, reason: str = None):
        channel = interaction.channel
        author = interaction.user

        return await self._do_close_ticket(channel=channel, author=author, reason=reason)

    @discord.slash_command(description="Tworzy menu do otwierania ticketów.")
    @discord.default_permissions(administrator=True)
    @guild_only()
    async def create_ticket_menu(self, ctx, channel: discord.TextChannel):
        embed = discord.Embed(title="Utwórz ticket", color=0xA751ED, description="Utwórz ticket, aby zadać pytanie, zgłosić błąd lub uzyskać pomoc innego typu")
        await channel.send(embed=embed, view=CreateTicketView(self.moderator_roles))
        await ctx.respond(f"✅ Utworzone nowe menu na kanale <#{channel.id}>.", ephemeral=True)

    @discord.slash_command(description="Dodaje użytkownika do ticketa.")
    @discord.default_permissions(administrator=True)
    @guild_only()
    async def add(self, ctx, member: discord.Member, channel: discord.TextChannel):
        # TODO: dostosuj w kodzie nazwę kategorii, aby pasowała do rzeczywistej nazwy
        if channel.category.id != ticket_category_id:
            await ctx.respond("Wskazany kanał nie znajduje się w kategorii tickety")
        else:
            if member in channel.overwrites:
                await ctx.respond("Ten użytkownik już ma dostęp do tego ticketa")

            await channel.set_permissions(member, view_channel=True)
            await ctx.respond(f"✅ Dodano użytkownika <@{member.id}> do ticketa <#{channel.id}>.", ephemeral=True)

    @discord.slash_command(description="Tworzy menu umożliwiające zamknięcie ticketa przez moderatorów")
    @guild_only()
    async def close_request(self, ctx):
        channel = ctx.channel
        is_ticket_channel = await self._is_ticket_channel(channel)

        if is_ticket_channel is not None:
            await ctx.respond(is_ticket_channel, ephemeral=True)
            return

        embed = discord.Embed(title="Kontrola ticketa", color=0xff9900, description="Kliknij w przycisk poniżej, aby zamknąć ticket")
        await ctx.send(embed=embed, view=CloseTicketView(self))
        await ctx.respond("✅ Utworzono panel kontrolny ticketa", ephemeral=True)


    @discord.slash_command(description="Zamyka ticket")
    @discord.default_permissions(administrator=True)
    @guild_only()
    async def close(self, ctx, reason: str = None):
        channel = ctx.channel
        author = ctx.author
        result = await self._do_close_ticket(channel=channel, author=author, reason=reason)

        if result is not None:
            ctx.respond(result, ephemeral=True)

    @discord.slash_command(description="Blokuje ticket")
    @discord.default_permissions(administrator=True)
    @guild_only()
    async def block(self, ctx):
        channel = ctx.channel
        is_ticket_channel = await self._is_ticket_channel(channel)

        if is_ticket_channel is not None:
            await ctx.respond(is_ticket_channel, ephemeral=True)
            return

        await channel.set_permissions(ctx.guild.default_role, view_channel=False, send_messages=False)
        # TODO: Loguj zablokowanie ticketa na kanale mod-log
        await ctx.respond("🔒 Pomyślnie zablokowano kanał", ephemeral=False)

    @discord.slash_command(description="Odblokowywuje ticket")
    @discord.default_permissions(administrator=True)
    @guild_only()
    async def unlock(self, ctx):
        channel = ctx.channel
        is_ticket_channel = await self._is_ticket_channel(channel)

        if is_ticket_channel is not None:
            await ctx.respond(is_ticket_channel, ephemeral=True)
            return

        await channel.set_permissions(ctx.guild.default_role, view_channel=False, send_messages=True)
        # TODO: Loguj zablokowanie ticketa na kanale mod-log
        await ctx.respond("🔓 Pomyślnie odblokowano kanał", ephemeral=False)






def setup(bot):
    bot.add_cog(TicketAdmin(bot))