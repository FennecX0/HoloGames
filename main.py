import discord 
from discord.ext import commands 
from discord.ui import View, Button 
import json 
import os 
import random 
import asyncio 
from datetime 
import datetime, timedelta

=== Load JSON Files ===

def load_json(filename): with open(filename, "r", encoding="utf-8") as f: return json.load(f)

def save_json(filename, data): with open(filename, "w", encoding="utf-8") as f: json.dump(data, f, indent=2)

cards = load_json("cards.json") inventory = load_json("inventory.json") pull_timers = load_json("pull_timers.json") if os.path.exists("pull_timers.json") else {} banner_prefs = load_json("banner_prefs.json") if os.path.exists("banner_prefs.json") else {}

=== Bot Setup ===

intents = discord.Intents.default() intents.message_content = True bot = commands.Bot(command_prefix="!", intents=intents)

rarity_weights = { "C": 60, "R": 20, "RR": 10, "RRR": 5, "SP": 2, "SR": 1.5, "SSR+": 1, "ALT+": 0.4, "TOH": 0.1 }

rarity_colors = { "C": 0x95a5a6, "R": 0x3498db, "RR": 0x9b59b6, "RRR": 0xe67e22, "SP": 0xf1c40f, "SR": 0xe74c3c, "SSR+": 0xd35400, "ALT+": 0x8e44ad, "TOH": 0xff00ff }

rarity_cutscenes = { "C": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif", "R": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif", "RR": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif", "RRR": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif", "SP": "https://media.tenor.com/JcMSVVkgfgMAAAAM/genshin-wish.gif", "SR": "https://media.tenor.com/JcMSVVkgfgMAAAAM/genshin-wish.gif", "SSR+": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif", "ALT+": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif", "TOH": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif" }

=== Helper Functions ===

def draw_card(group): filtered = [c for c in cards if c.get("group") == group] rarities = list(rarity_weights.keys()) weights = list(rarity_weights.values()) rarity = random.choices(rarities, weights=weights, k=1)[0] options = [c for c in filtered if c["rarity"] == rarity] return random.choice(options)

def can_pull(user_id): now = datetime.utcnow() user_data = pull_timers.get(str(user_id), {"pulls": 0, "reset_time": now.isoformat()}) reset_time = datetime.fromisoformat(user_data["reset_time"]) if now >= reset_time: pull_timers[str(user_id)] = {"pulls": 0, "reset_time": (now + timedelta(minutes=30)).isoformat()} save_json("pull_timers.json", pull_timers) return True return user_data["pulls"] < 50

def add_pull(user_id, amount): pull_timers[str(user_id)]["pulls"] += amount save_json("pull_timers.json", pull_timers)

def format_card(card): return f"{card['rarity']} — {card['name']}\n💥 ATK: {card['attack']} | 🛡 DEF: {card['defense']}\n💰 Value: ¥{card['value']}"

=== Commands ===

@bot.command() async def banner(ctx): embed = discord.Embed(title="Which banner would you like to gacha on?", color=discord.Color.purple()) embed.set_image(url="https://cdn.discordapp.com/attachments/1383855862673571891/1386320198222479506/Untitled133_20250622200308.png") view = View()

async def set_banner(interaction, choice):
    banner_prefs[str(interaction.user.id)] = choice
    save_json("banner_prefs.json", banner_prefs)
    await interaction.response.send_message(f"You selected **{choice}** banner! Use `!gacha` or `!gacha10` now.", ephemeral=True)

view.add_item(Button(label="EN Banner", style=discord.ButtonStyle.primary, custom_id="en"))
view.add_item(Button(label="JP Banner", style=discord.ButtonStyle.secondary, custom_id="jp"))

async def button_callback(interaction):
    if interaction.data["custom_id"] == "en":
        await set_banner(interaction, "EN")
    else:
        await set_banner(interaction, "JP")

for child in view.children:
    child.callback = button_callback

await ctx.send(embed=embed, view=view)

@bot.command() async def gacha(ctx): user_id = str(ctx.author.id) group = banner_prefs.get(user_id, "EN")

if not can_pull(user_id):
    return await ctx.send("🚫 You've reached your 50 pull limit! Please wait 30 minutes.")

card = draw_card(group)
add_pull(user_id, 1)

anim = rarity_cutscenes.get(card["rarity"])
cutscene = await ctx.send(anim)
await asyncio.sleep(6)
await cutscene.delete()

embed = discord.Embed(title=f"{card['name']} — {card['rarity']}", color=rarity_colors.get(card["rarity"], 0x000000))
embed.add_field(name="", value=f"{card['title']}\n💥 {card['attack']} | 🛡 {card['defense']} | 💰 ¥{card['value']}", inline=False)
embed.set_footer(text=f"Pulled by {ctx.author.name} | UID: {card['uid']}")
await ctx.send(embed=embed)

# Save to inventory
inventory.setdefault(user_id, []).append(card)
save_json("inventory.json", inventory)

@bot.command() async def gacha10(ctx): user_id = str(ctx.author.id) group = banner_prefs.get(user_id, "EN")

if not can_pull(user_id):
    return await ctx.send("🚫 You've reached your 50 pull limit! Please wait 30 minutes.")

cards_pulled = [draw_card(group) for _ in range(10)]
add_pull(user_id, 10)

# Choose highest rarity animation
rarities = list(rarity_weights.keys())[::-1]  # highest first
for rarity in rarities:
    if any(card["rarity"] == rarity for card in cards_pulled):
        anim = rarity_cutscenes[rarity]
        break
anim_msg = await ctx.send(anim)
await asyncio.sleep(6)
await anim_msg.delete()

for i, card in enumerate(cards_pulled, 1):
    embed = discord.Embed(title=f"{card['name']} — {card['rarity']}", color=rarity_colors.get(card["rarity"], 0x000000))
    embed.add_field(name=f"Card {i}/10", value=f"{card['title']}\n💥 {card['attack']} | 🛡 {card['defense']} | 💰 ¥{card['value']}", inline=False)
    embed.set_footer(text=f"Pulled by {ctx.author.name} | UID: {card['uid']}")
    await ctx.send(embed=embed)

# Save to inventory
inventory.setdefault(user_id, []).extend(cards_pulled)
save_json("inventory.json", inventory)

@bot.command() async def inventorycheck(ctx): user_id = str(ctx.author.id) user_inventory = inventory.get(user_id, []) if not user_inventory: return await ctx.send("🎒 Your inventory is empty.")

entries = [f"{c['rarity']} — {c['name']} | UID: {c['uid']}" for c in user_inventory]
pages = [entries[i:i+10] for i in range(0, len(entries), 10)]
page = 0

embed = discord.Embed(title=f"{ctx.author.name}'s Inventory", description="\n".join(pages[page]), color=0x3498db)
view = View()

async def next_callback(interaction):
    nonlocal page
    if page + 1 < len(pages):
        page += 1
        embed.description = "\n".join(pages[page])
        await interaction.response.edit_message(embed=embed, view=view)

async def prev_callback(interaction):
    nonlocal page
    if page > 0:
        page -= 1
        embed.description = "\n".join(pages[page])
        await interaction.response.edit_message(embed=embed, view=view)

next_btn = Button(label="Next", style=discord.ButtonStyle.primary)
next_btn.callback = next_callback
prev_btn = Button(label="Previous", style=discord.ButtonStyle.secondary)
prev_btn.callback = prev_callback

view.add_item(prev_btn)
view.add_item(next_btn)

await ctx.send(embed=embed, view=view)

@bot.command() async def view(ctx, uid): for user_cards in inventory.values(): for card in user_cards: if card["uid"] == uid: embed = discord.Embed(title=f"{card['name']} — {card['rarity']}", color=rarity_colors.get(card["rarity"], 0x000000)) embed.add_field(name=card['title'], value=f"💥 ATK: {card['attack']}\n🛡 DEF: {card['defense']}\n💰 Value: ¥{card['value']}", inline=False) embed.set_footer(text=f"UID: {card['uid']}") return await ctx.send(embed=embed) await ctx.send("❌ Card with that UID not found.")

bot.run(os.getenv("DISCORD_TOKEN"))
