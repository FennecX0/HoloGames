import discord
from discord.ext import commands
from discord.ui import View, Button
import json
import random
import asyncio
import os
import time

# Load or initialize files
def load_json(filename, default):
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

cards = load_json("cards.json", [])
inventory = load_json("inventory.json", {})
pull_timers = load_json("pull_timers.json", {})
banner_prefs = load_json("banner_prefs.json", {})

rarity_weights = {
    "C": 79,
    "R": 50,
    "RR": 20,
    "RRR": 10,
    "SP": 1,
    "SR": 4,
    "SSR": 2,
    "SSR+": 1,
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
    "ALT+": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif",
    "TOH": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif"
}

JP_MEMBERS = ["Pekora", "Fubuki", "Suisei", "Miko", "Marine", "Korone", "Aqua", "Shion", "Ayame", "Sora", "AZKi", "Polka", "Lamy", "Flare"]

def get_banner_cards(region):
    if region == "JP":
        return [card for card in cards if any(jp in card["name"] for jp in JP_MEMBERS)]
    else:
        return [card for card in cards if all(jp not in card["name"] for jp in JP_MEMBERS)]

def draw_card(region):
    pool = get_banner_cards(region)
    rarities = list(rarity_weights.keys())
    weights = list(rarity_weights.values())
    rarity = random.choices(rarities, weights=weights, k=1)[0]
    filtered = [c for c in pool if c["rarity"] == rarity]
    return random.choice(filtered) if filtered else random.choice(pool)

def format_card(card):
    return f"[{card['uid']}] {card['rarity']} | {card['name']} | ATK: {card['attack']} | DEF: {card['defense']} | ¥{card['value']} | {card['archetype']}"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def banner(ctx):
    embed = discord.Embed(title="Which banner would you like to gacha on?")
    embed.set_image(url="https://cdn.discordapp.com/attachments/1383855862673571891/1386320198222479506/Untitled133_20250622200308.png")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1383855862673571891/1386320188110143589/Untitled135_20250622201347.png")

    class BannerView(View):
        @discord.ui.button(label="EN Banner", style=discord.ButtonStyle.primary)
        async def en(self, interaction, button):
            banner_prefs[str(ctx.author.id)] = "EN"
            save_json("banner_prefs.json", banner_prefs)
            await interaction.response.send_message("✅ EN banner selected!", ephemeral=True)

        @discord.ui.button(label="JP Banner", style=discord.ButtonStyle.secondary)
        async def jp(self, interaction, button):
            banner_prefs[str(ctx.author.id)] = "JP"
            save_json("banner_prefs.json", banner_prefs)
            await interaction.response.send_message("✅ JP banner selected!", ephemeral=True)

    await ctx.send(embed=embed, view=BannerView())

@bot.command()
async def gacha(ctx):
    uid = str(ctx.author.id)
    region = banner_prefs.get(uid, "EN")

    timer = pull_timers.get(uid, {"pulls": 0, "time": time.time()})
    if time.time() - timer["time"] > 1800:
        timer = {"pulls": 0, "time": time.time()}
    if timer["pulls"] >= 50:
        remaining = int(1800 - (time.time() - timer["time"]))
        await ctx.send(f"⏳ You've reached the 50 pull limit. Please wait {remaining // 60}m {remaining % 60}s.")
        return

    timer["pulls"] += 1
    pull_timers[uid] = timer
    save_json("pull_timers.json", pull_timers)

    card = draw_card(region)
    anim = rarity_animations.get(card["rarity"], "")

    msg = await ctx.send(anim)
    await asyncio.sleep(6)
    await msg.delete()

    embed = discord.Embed(
        title=f"{ctx.author.display_name} pulled a {card['rarity']}!",
        description=f"**{card['name']}**\nUID: `{card['uid']}`\n⚔️ {card['attack']} | 🛡 {card['defense']} | 💰 ¥{card['value']}\n🔮 {card['archetype']}",
        color=discord.Color.gold() if card['rarity'] in ["SSR", "TOH"] else discord.Color.blue()
    )
    if "title" in card:
        embed.set_footer(text=card["title"])
    await ctx.send(embed=embed)

    inventory.setdefault(uid, []).append(card)
    save_json("inventory.json", inventory)

@bot.command()
async def inventory(ctx):
    uid = str(ctx.author.id)
    user_cards = inventory.get(uid, [])
    if not user_cards:
        await ctx.send("Your inventory is empty!")
        return

    pages = [user_cards[i:i+10] for i in range(0, len(user_cards), 10)]
    page_index = 0

    class InvView(View):
        def __init__(self):
            super().__init__()
            self.value = None

        @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
        async def next(self, interaction, button):
            nonlocal page_index
            page_index = (page_index + 1) % len(pages)
            await interaction.response.edit_message(embed=make_embed(), view=self)

        @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
        async def prev(self, interaction, button):
            nonlocal page_index
            page_index = (page_index - 1) % len(pages)
            await interaction.response.edit_message(embed=make_embed(), view=self)

    def make_embed():
        embed = discord.Embed(title=f"{ctx.author.display_name}'s Inventory (Page {page_index+1}/{len(pages)})")
        embed.description = "\n".join(format_card(card) for card in pages[page_index])
        total = sum(card["value"] for card in user_cards)
        embed.set_footer(text=f"WataCoins: ¥{total}")
        return embed

    await ctx.send(embed=make_embed(), view=InvView())

@bot.command()
async def view(ctx, uid: str):
    for card in cards:
        if card["uid"] == uid:
            embed = discord.Embed(
                title=f"{card['name']} [{card['rarity']}]",
                description=f"⚔️ ATK: `{card['attack']}`\n🛡 DEF: `{card['defense']}`\n💰 ¥{card['value']}\n🔮 Archetype: {card['archetype']}\nUID: `{card['uid']}`",
                color=discord.Color.green()
            )
            if "title" in card:
                embed.set_footer(text=card["title"])
            await ctx.send(embed=embed)
            return
    await ctx.send("❌ Card not found.")

bot.run(os.getenv("DISCORD_TOKEN"))
