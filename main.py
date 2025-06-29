import discord
from discord.ext import commands
from discord.ui import View, Button
import json
import os
import random
import asyncio
from datetime import datetime, timedelta

# === Load JSON Files ===
def load_json(filename):
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write("{}" if filename.endswith(".json") else "[]")
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

cards = load_json("cards.json")
inventory = load_json("inventory.json")
pull_timers = load_json("pull_timers.json")
banner_prefs = load_json("banner_prefs.json")

# === Bot Setup ===
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# === Rarity and Cutscenes ===
rarity_weights = {
    "C": 79, "R": 50, "RR": 20, "RRR": 10, "SP": 1,
    "SR": 4, "SSR": 2, "SSR+": 1, "ALT": 0.1, "ALT+": 0.1, "TOH": 0.01
}
rarity_cutscenes = {
    "C": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif",
    "R": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif",
    "RR": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif",
    "RRR": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif",
    "SP": "https://media.tenor.com/JcMSVVkgfgMAAAAM/genshin-wish.gif",
    "SR": "https://media.tenor.com/JcMSVVkgfgMAAAAM/genshin-wish.gif",
    "SSR": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif",
    "SSR+": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif",
    "ALT": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif",
    "ALT+": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif",
    "TOH": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif"
}

banner_pages = [
    {
        "name": "Hololive English",
        "image": "https://cdn.discordapp.com/attachments/1383855862673571891/1386320198222479506/Untitled133_20250622200308.png",
        "group": "EN"
    },
    {
        "name": "Hololive JP",
        "image": "https://cdn.discordapp.com/attachments/1383855862673571891/1386320188110143589/Untitled135_20250622201347.png",
        "group": "JP"
    }
]

class BannerView(View):
    def __init__(self, ctx, user_id):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.user_id = user_id
        self.page = 0
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        self.add_item(Button(label="Choose This Banner", style=discord.ButtonStyle.success, custom_id="choose"))
        if self.page > 0:
            self.add_item(Button(label="Previous", style=discord.ButtonStyle.secondary, custom_id="prev"))
        if self.page < len(banner_pages) - 1:
            self.add_item(Button(label="Next", style=discord.ButtonStyle.secondary, custom_id="next"))

    async def interaction_check(self, interaction):
        return interaction.user.id == self.user_id

    @discord.ui.button(label="Choose This Banner", style=discord.ButtonStyle.success, custom_id="choose")
    async def choose(self, interaction: discord.Interaction, button: discord.ui.Button):
        banner_prefs[str(self.user_id)] = banner_pages[self.page]["group"]
        save_json("banner_prefs.json", banner_prefs)
        await interaction.response.send_message(f"Banner set to {banner_pages[self.page]['group']}", ephemeral=True)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, custom_id="prev")
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary, custom_id="next")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < len(banner_pages) - 1:
            self.page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    def get_embed(self):
        data = banner_pages[self.page]
        embed = discord.Embed(title="Which banner would you like to gacha on?", color=discord.Color.blue())
        embed.set_image(url=data["image"])
        embed.set_footer(text=f"Page {self.page + 1} of {len(banner_pages)}")
        return embed

@bot.command()
async def banner(ctx):
    view = BannerView(ctx, ctx.author.id)
    await ctx.send(embed=view.get_embed(), view=view)

# === Run Bot ===
bot.run(os.getenv("DISCORD_TOKEN"))
