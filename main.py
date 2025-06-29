import discord
from discord.ext import commands
from discord.ui import View, Button
import json
import os
import random
import asyncio
from datetime import datetime, timedelta

# Constants
MAX_PULLS = 50
COOLDOWN_MINUTES = 30

# Load JSON helpers
def load_json(filename):
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            json.dump({}, f)
    with open(filename, "r") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

cards = load_json("cards.json")
inventory = load_json("inventory.json")
pull_timers = load_json("pull_timers.json")
banner_prefs = load_json("banner_prefs.json")

# Rarity animations
rarity_animations = {
    "C": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif",
    "R": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif",
    "RR": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif",
    "RRR": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif",
    "SP": "https://media.tenor.com/JcMSVVkgfgMAAAAM/genshin-wish.gif",
    "SR": "https://media.tenor.com/JcMSVVkgfgMAAAAM/genshin-wish.gif",
    "SSR+": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif",
    "ALT+": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif",
    "TOH": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif",
}

# Rarity weights
rarity_weights = {
    "C": 60,
    "R": 20,
    "RR": 10,
    "RRR": 5,
    "SP": 2,
    "SR": 1.5,
    "SSR+": 0.8,
    "ALT+": 0.6,
    "TOH": 0.1,
}

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def draw_card(group):
    filtered = [c for c in cards if c["group"] == group]
    rarities = list(rarity_weights.keys())
    weights = list(rarity_weights.values())
    rarity = random.choices(rarities, weights=weights, k=1)[0]
    options = [c for c in filtered if c["rarity"] == rarity]
    return random.choice(options) if options else random.choice(filtered)

def generate_embed(card, user):
    embed = discord.Embed(
        title=f"{card['name']} â€“ {card['rarity']}",
        description=f"{card['title']} | ðŸ’¥ {card['attack']} | ðŸ›¡ {card['defense']} | ðŸ’° Â¥{card['value']}",
        color=discord.Color.gold() if card['rarity'] in ["SSR+", "TOH"] else discord.Color.blue()
    )
    embed.set_footer(text=f"Pulled by {user} | UID: {card['uid']}")
    return embed

def can_pull(user_id):
    now = datetime.utcnow()
    pulls = pull_timers.get(str(user_id), {"count": 0, "reset_time": str(now)})
    reset_time = datetime.fromisoformat(pulls["reset_time"])
    if now >= reset_time:
        pull_timers[str(user_id)] = {"count": 0, "reset_time": str(now + timedelta(minutes=COOLDOWN_MINUTES))}
        save_json("pull_timers.json", pull_timers)
        return True
    return pulls["count"] < MAX_PULLS

def record_pull(user_id, amount):
    pulls = pull_timers.get(str(user_id))
    if pulls:
        pulls["count"] += amount
        save_json("pull_timers.json", pull_timers)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def banner(ctx):
    embed = discord.Embed(title="Which banner would you like to gacha on?")
    embed.set_image(url="https://cdn.discordapp.com/attachments/1383855862673571891/1386320198222479506/Untitled133_20250622200308.png")
    view = View()
    view.add_item(Button(label="EN Banner", style=discord.ButtonStyle.primary, custom_id="en"))
    view.add_item(Button(label="JP Banner", style=discord.ButtonStyle.secondary, custom_id="jp"))
    async def button_callback(interaction):
        banner_prefs[str(interaction.user.id)] = "EN" if interaction.data["custom_id"] == "en" else "JP"
        save_json("banner_prefs.json", banner_prefs)
        await interaction.response.send_message(f"Banner set to {banner_prefs[str(interaction.user.id)]}", ephemeral=True)
    for item in view.children:
        item.callback = button_callback
    await ctx.send(embed=embed, view=view)

@bot.command()
async def gacha(ctx):
    user_id = str(ctx.author.id)
    group = banner_prefs.get(user_id, "EN")
    if not can_pull(user_id):
        return await ctx.send("Youâ€™ve reached the 50 pull limit! Please wait 30 minutes.")
    card = draw_card(group)
    record_pull(user_id, 1)
    await ctx.send(rarity_animations.get(card["rarity"], ""))
    await asyncio.sleep(6)
    await ctx.send(embed=generate_embed(card, ctx.author.display_name))
    user_inv = inventory.get(user_id, [])
    user_inv.append(card)
    inventory[user_id] = user_inv
    save_json("inventory.json", inventory)

@bot.command()
async def gacha10(ctx):
    user_id = str(ctx.author.id)
    group = banner_prefs.get(user_id, "EN")
    if not can_pull(user_id):
        return await ctx.send("Youâ€™ve reached the 50 pull limit! Please wait 30 minutes.")
    if pull_timers[user_id]["count"] + 10 > MAX_PULLS:
        return await ctx.send("This 10-pull would exceed your 50 pull limit!")
    cards_pulled = []
    for _ in range(10):
        cards_pulled.append(draw_card(group))
    record_pull(user_id, 10)
    rarities = [c["rarity"] for c in cards_pulled]
    best = max(rarities, key=lambda r: list(rarity_weights.keys()).index(r))
    await ctx.send(rarity_animations.get(best, ""))
    await asyncio.sleep(6)
    for i, card in enumerate(cards_pulled):
        await ctx.send(embed=generate_embed(card, ctx.author.display_name))
    inventory[user_id] = inventory.get(user_id, []) + cards_pulled
    save_json("inventory.json", inventory)

@bot.command()
async def view(ctx, uid: str):
    for user_cards in inventory.values():
        for card in user_cards:
            if card["uid"] == uid:
                await ctx.send(embed=generate_embed(card, ctx.author.display_name))
                return
    await ctx.send("Card not found!")

bot.run(os.getenv("DISCORD_TOKEN"))
