import discord from discord.ext import commands from discord.ui import View, Button import json import os import random import asyncio

--- Load Data ---

def load_json(filename): if not os.path.exists(filename): with open(filename, "w") as f: f.write("{}") with open(filename, "r", encoding="utf-8") as f: return json.load(f)

def save_json(filename, data): with open(filename, "w", encoding="utf-8") as f: json.dump(data, f, indent=2)

cards = load_json("cards.json") inventory = load_json("inventory.json") banner_prefs = load_json("banner_prefs.json")

rarity_weights = { "C": 79, "R": 50, "RR": 20, "RRR": 10, "SP": 4, "SR": 3, "SSR+": 2, "ALT+": 1, "TOH": 0.2 }

rarity_animations = { "C": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif", "R": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif", "RRR": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif", "SR": "https://media.tenor.com/JcMSVVkgfgMAAAAM/genshin-wish.gif", "SP": "https://media.tenor.com/JcMSVVkgfgMAAAAM/genshin-wish.gif", "SSR+": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif", "TOH": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif" }

banners = [ { "name": "EN", "image": "https://cdn.discordapp.com/attachments/1383855862673571891/1386320198222479506/Untitled133_20250622200308.png" }, { "name": "JP", "image": "https://cdn.discordapp.com/attachments/1383855862673571891/1386320188110143589/Untitled135_20250622201347.png" } ]

--- Bot Setup ---

intents = discord.Intents.default() intents.message_content = True bot = commands.Bot(command_prefix="!", intents=intents)

--- Draw Logic ---

def draw_card(group): rarities = list(rarity_weights.keys()) weights = list(rarity_weights.values()) rarity = random.choices(rarities, weights=weights)[0] group_cards = [card for card in cards if card.get("rarity") == rarity and card.get("group") == group] return random.choice(group_cards) if group_cards else None

--- Save Card to Inventory ---

def add_to_inventory(user_id, card): if str(user_id) not in inventory: inventory[str(user_id)] = [] inventory[str(user_id)].append(card) save_json("inventory.json", inventory)

--- Banner Selection View ---

class BannerSelector(View): def init(self, user_id): super().init(timeout=60) self.user_id = user_id self.index = 0 self.message = None

async def update_banner(self, interaction):
    banner = banners[self.index]
    embed = discord.Embed(title="Which banner would you like to gacha on?", color=discord.Color.blurple())
    embed.set_image(url=banner["image"])
    await interaction.response.edit_message(embed=embed, view=self)

@discord.ui.button(label="Previous", style=discord.ButtonStyle.gray)
async def previous(self, interaction: discord.Interaction, button: Button):
    if interaction.user.id != self.user_id:
        return
    self.index = (self.index - 1) % len(banners)
    await self.update_banner(interaction)

@discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
async def next(self, interaction: discord.Interaction, button: Button):
    if interaction.user.id != self.user_id:
        return
    self.index = (self.index + 1) % len(banners)
    await self.update_banner(interaction)

@discord.ui.button(label="Choose this Banner", style=discord.ButtonStyle.green)
async def choose(self, interaction: discord.Interaction, button: Button):
    if interaction.user.id != self.user_id:
        return
    chosen = banners[self.index]
    banner_prefs[str(self.user_id)] = chosen["name"]
    save_json("banner_prefs.json", banner_prefs)
    await interaction.response.edit_message(content=f"✅ You selected **{chosen['name']}** banner! Use `!gacha` or `!gacha10`.", embed=None, view=None)

--- Commands ---

@bot.command() async def banner(ctx): view = BannerSelector(user_id=ctx.author.id) banner = banners[0] embed = discord.Embed(title="Which banner would you like to gacha on?", color=discord.Color.blurple()) embed.set_image(url=banner["image"]) await ctx.send(embed=embed, view=view)

@bot.command() async def gacha(ctx): group = banner_prefs.get(str(ctx.author.id), "EN") card = draw_card(group) if not card: await ctx.send("No card could be pulled. Try again later.") return

anim = rarity_animations.get(card['rarity'], None)
if anim:
    msg = await ctx.send(anim)
    await asyncio.sleep(6)
    await msg.delete()

embed = discord.Embed(
    title=f"{card['name']} — {card['rarity']}",
    description=f"🏷 {card.get('title', 'Hololive Member')}\n💴 {card['value']} | 💥 {card['attack']} | 🛡 {card['defense']}",
    color=discord.Color.gold() if card['rarity'] in ["TOH", "SSR+"] else discord.Color.blue()
)
embed.set_footer(text=f"Pulled by {ctx.author.display_name} | UID: {card['uid']}")

await ctx.send(embed=embed)
add_to_inventory(ctx.author.id, card)

@bot.command(name="gacha10") async def gacha10(ctx): group = banner_prefs.get(str(ctx.author.id), "EN") pulled = [] for _ in range(10): card = draw_card(group) if card: pulled.append(card) add_to_inventory(ctx.author.id, card)

# pick highest rarity animation
highest = max(pulled, key=lambda x: list(rarity_weights.keys()).index(x["rarity"]))
anim = rarity_animations.get(highest['rarity'], None)
if anim:
    msg = await ctx.send(anim)
    await asyncio.sleep(6)
    await msg.delete()

for i, card in enumerate(pulled, start=1):
    embed = discord.Embed(
        title=f"{card['name']} — {card['rarity']}",
        description=f"🏷 {card.get('title', 'Hololive Member')}\n💴 {card['value']} | 💥 {card['attack']} | 🛡 {card['defense']}",
        color=discord.Color.gold() if card['rarity'] in ["TOH", "SSR+"] else discord.Color.blue()
    )
    embed.set_footer(text=f"Pulled by {ctx.author.display_name} | UID: {card['uid']} | Card {i}/10")
    await ctx.send(embed=embed)

--- Run ---

bot.run(os.getenv("DISCORD_TOKEN"))
