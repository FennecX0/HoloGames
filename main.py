import discord
from discord.ext import commands
from discord import app_commands, tasks
from discord import app_commands
from discord.ui import View, Button
import json
import os
import random
import asyncio
from datetime import datetime, timedelta

# === Utility Functions ===
def load_json(filename):
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write("{}")
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# === Load Files ===
cards = load_json("cards.json")
inventory = load_json("inventory.json")
pull_timers = load_json("pull_timers.json")
banner_prefs = load_json("banner_prefs.json")

# === Rarity & Animation Settings ===
rarity_weights = {
    "C": 79,
    "R": 50,
    "RR": 20,
    "RRR": 10,
    "SP": 1,
    "SR": 4,
    "SSR": 2,
    "SSR+": 1,
    "ALT": 0.1,
    "ALT+": 0.1,
    "TOH": 0.01
}

rarity_animations = {
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

# === Banner Setup ===
banner_pages = [
    {
        "group": "EN",
        "image": "https://cdn.discordapp.com/attachments/1383855862673571891/1386320198222479506/Untitled133_20250622200308.png"
    },
    {
        "group": "JP",
        "image": "https://cdn.discordapp.com/attachments/1383855862673571891/1386320188110143589/Untitled135_20250622201347.png"
    }
]

# === Bot Setup ===
intents = discord.Intents.default()
bot = discord.Bot(intents=intents)
tree = bot.tree

class BannerView(View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
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

    @discord.ui.button(label="Choose This Banner", style=discord.ButtonStyle.success)
    async def choose(self, interaction: discord.Interaction, button: discord.ui.Button):
        banner_prefs[str(self.user_id)] = banner_pages[self.page]["group"]
        save_json("banner_prefs.json", banner_prefs)
        await interaction.response.send_message(f"You selected **{banner_pages[self.page]['group']}** banner!", ephemeral=True)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(0, self.page - 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = min(len(banner_pages) - 1, self.page + 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    def get_embed(self):
        data = banner_pages[self.page]
        embed = discord.Embed(title="Choose a banner to summon from:", color=discord.Color.blurple())
        embed.set_image(url=data["image"])
        embed.set_footer(text=f"Page {self.page + 1} of {len(banner_pages)}")
        return embed

# === Slash Commands ===

@tree.command(name="banner", description="Select a gacha banner")
async def banner_command(interaction: discord.Interaction):
    view = BannerView(interaction.user.id)
    embed = view.get_embed()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@tree.command(name="gacha", description="Pull a single card")
async def gacha(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    selected_banner = banner_prefs.get(uid, "EN")
    available = [c for c in cards if c["group"] == selected_banner]
    rarities = list(rarity_weights.keys())
    weights = list(rarity_weights.values())
    rarity = random.choices(rarities, weights=weights)[0]
    pool = [c for c in available if c["rarity"] == rarity]
    if not pool:
        await interaction.response.send_message("No cards available for this banner!", ephemeral=True)
        return
    card = random.choice(pool)
    anim = rarity_animations.get(card["rarity"], None)
    await interaction.response.send_message(anim)
    await asyncio.sleep(6)
    embed = discord.Embed(title=f"You pulled a {card['rarity']} card!", description=f"**{card['name']}**
ðŸ’¥ ATK: `{card['attack']}` | ðŸ›¡ DEF: `{card['defense']}`
ðŸ’´ Value: Â¥{card['value']}", color=discord.Color.gold())
    embed.set_footer(text=card["title"] if "title" in card else "")
    await interaction.followup.send(embed=embed)
    # Save to inventory
    inventory.setdefault(uid, []).append(card)
    save_json("inventory.json", inventory)

@tree.command(name="inventory", description="Check your inventory")
async def check_inventory(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    inv = inventory.get(uid, [])
    if not inv:
        await interaction.response.send_message("You have no cards!", ephemeral=True)
        return
    text = "
".join([f"[{i+1}] {c['name']} ({c['rarity']})" for i, c in enumerate(inv[:10])])
    await interaction.response.send_message(f"Your Top 10 Cards:
{text}", ephemeral=True)

# === Bot Startup ===

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}")

bot.run(os.getenv("DISCORD_TOKEN"))
@tree.command(name="gacha10", description="Pull 10 cards at once")
async def gacha10(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    now = datetime.utcnow()
    pulls = pull_timers.get(uid, {"count": 0, "reset": now.isoformat()})

    reset_time = datetime.fromisoformat(pulls["reset"])
    if now >= reset_time:
        pulls = {"count": 0, "reset": (now + timedelta(minutes=30)).isoformat()}

    if pulls["count"] + 10 > 50:
        remaining = (reset_time - now).seconds // 60
        await interaction.response.send_message(f"You've reached the 50 pull limit. Try again in {remaining} minutes.", ephemeral=True)
        return

    pulls["count"] += 10
    pull_timers[uid] = pulls
    save_json("pull_timers.json", pull_timers)

    selected_banner = banner_prefs.get(uid, "EN")
    available = [c for c in cards if c["group"] == selected_banner]
    results = []
    rarities = list(rarity_weights.keys())
    weights = list(rarity_weights.values())

    for _ in range(10):
        rarity = random.choices(rarities, weights=weights)[0]
        pool = [c for c in available if c["rarity"] == rarity]
        if pool:
            results.append(random.choice(pool))

    # Determine animation level
    highest = max(results, key=lambda x: list(rarity_weights.keys()).index(x["rarity"]))
    anim = rarity_animations.get(highest["rarity"], None)
    await interaction.response.send_message(anim)
    await asyncio.sleep(6)

    # Create embed for 10 pulls
    embed = discord.Embed(title=f"ðŸŽ‰ 10-Pull Results ({selected_banner})", color=discord.Color.blurple())
    for card in results:
        embed.add_field(
            name=f"{card['name']} [{card['rarity']}]",
            value=f"ATK: `{card['attack']}` | DEF: `{card['defense']}` | Â¥{card['value']}",
            inline=False
        )
    await interaction.followup.send(embed=embed)

    # Save to inventory
    inventory.setdefault(uid, []).extend(results)
    save_json("inventory.json", inventory)

    # Bot Runs
    bot.run(os.getenv("DISCORD_TOKEN"))
