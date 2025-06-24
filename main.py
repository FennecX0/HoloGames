import discord
from discord.ext import commands
import json
import random
import asyncio
import os
import time

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

def load_json(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

cards = load_json("cards.json")
inventory = load_json("inventory.json")
pull_timers = load_json("pull_timer.json")
banner_prefs = load_json("banner_prefs.json")

rarity_weights = {
    "C": 79, "R": 50, "RR": 20, "RRR": 10, "SP": 1, "SR": 4,
    "SSR": 2, "SSR+": 1, "ALT": 0.10, "ALT+": 0.1, "TOH": 0.01
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

banner_images = {
    "EN": "https://cdn.discordapp.com/attachments/1383855862673571891/1386320198222479506/Untitled133_20250622200308.png",
    "JP": "https://cdn.discordapp.com/attachments/1383855862673571891/1386320188110143589/Untitled135_20250622201347.png"
}

def draw_card(user_id):
    banner = banner_prefs.get(str(user_id), "EN")
    pool = [card for card in cards if card["group"] == banner]
    rarities = list(rarity_weights.keys())
    weights = list(rarity_weights.values())
    while True:
        rarity = random.choices(rarities, weights=weights, k=1)[0]
        possible = [card for card in pool if card["rarity"] == rarity]
        if possible:
            return random.choice(possible)

def check_limit(user_id):
    now = time.time()
    info = pull_timers.get(user_id, {"count": 0, "last": now})
    if now - info["last"] > 1800:
        info = {"count": 0, "last": now}
    if info["count"] >= 50:
        return False, int(1800 - (now - info["last"]))
    return True, info

def update_timer(user_id, pulls):
    info = pull_timers.get(user_id, {"count": 0, "last": time.time()})
    now = time.time()
    if now - info["last"] > 1800:
        info = {"count": 0, "last": now}
    info["count"] += pulls
    pull_timers[user_id] = info
    save_json("pull_timer.json", pull_timers)

@bot.event
async def on_ready():
    print(f"âœ… Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command()
async def banner(ctx):
    embed = discord.Embed(title="ðŸŽ´ Choose Your Banner", description="Type `!enbanner` or `!jpbanner` to pull from a banner.")
    embed.set_image(url=banner_images["EN"])
    await ctx.send(embed=embed)
    await ctx.send(embed=discord.Embed().set_image(url=banner_images["JP"]))

@bot.command()
async def enbanner(ctx):
    banner_prefs[str(ctx.author.id)] = "EN"
    save_json("banner_prefs.json", banner_prefs)
    await ctx.send("âœ… You are now pulling from the **EN** banner.")

@bot.command()
async def jpbanner(ctx):
    banner_prefs[str(ctx.author.id)] = "JP"
    save_json("banner_prefs.json", banner_prefs)
    await ctx.send("âœ… You are now pulling from the **JP** banner.")

@bot.command()
async def gacha(ctx):
    user_id = str(ctx.author.id)
    ok, info = check_limit(user_id)
    if not ok:
        await ctx.send(f"ðŸ•’ You've reached your 50 pull limit! Try again in {info} seconds.")
        return
    card = draw_card(user_id)
    anim = rarity_animations.get(card["rarity"], "")
    await ctx.send(anim)
    await asyncio.sleep(6)
    embed = discord.Embed(
        title=f"{card['name']} - {card['rarity']}",
        description=f"ðŸŽ´ {card['title']} | ðŸ’¥ {card['attack']} | ðŸ›¡ {card['defense']} | ðŸ’° Â¥{card['value']}",
        color=discord.Color.gold()
    )
    embed.set_footer(text=f"Pulled by {ctx.author.display_name} | UID: {card['uid']}")
    await ctx.send(embed=embed)
    inventory.setdefault(user_id, []).append(card["uid"])
    update_timer(user_id, 1)
    save_json("inventory.json", inventory)

bot.run(os.getenv("DISCORD_TOKEN")
