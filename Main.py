import os
import io
import json
import discord
from discord.ext import commands
import pytesseract
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# إعداد الصلاحيات
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data/points.json"

def load_data():
    if not os.path.exists("data"):
        os.makedirs("data")
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def add_points(user_id: int, points: int) -> int:
    data = load_data()
    str_id = str(user_id)
    data[str_id] = data.get(str_id, 0) + points
    save_data(data)
    return data[str_id]

def parse_image_text(text: str) -> tuple[int, list[str]]:
    total_points = 0
    reasons = []
    text_clean = text.lower()

    # 🔨 الباند
    if any(k in text_clean for k in ["باند", "بان", "ban", "banned"]):
        if any(k in text_clean for k in ["شهر", "30 يوم", "month"]):
            total_points += 5
            reasons.append("باند شهر (+5 نقاط)")
        elif any(k in text_clean for k in ["أسبوعين", "اسبوعين", "14 يوم"]):
            total_points += 4
            reasons.append("باند أسبوعين (+4 نقاط)")
        elif any(k in text_clean for k in ["أسبوع", "اسبوع", "7 أيام", "7 ايام"]):
            total_points += 3
            reasons.append("باند أسبوع (+3 نقاط)")
        elif any(k in text_clean for k in ["3 أيام", "3 ايام", "ثلاثة أيام"]):
            total_points += 2
            reasons.append("باند 3 أيام (+2 نقاط)")
        elif any(k in text_clean for k in ["يوم", "24 ساعة"]):
            total_points += 1
            reasons.append("باند يوم (+1 نقطة)")

    # 🔇 الميوت
    if any(k in text_clean for k in ["ميوت", "كتم", "mute", "timeout"]):
        if any(k in text_clean for k in ["يومين", "2 يوم", "2 أيام"]):
            total_points += 2
            reasons.append("ميوت يومين (+2 نقاط)")
        elif any(k in text_clean for k in ["يوم", "24 ساعة"]):
            total_points += 1
            reasons.append("ميوت يوم (+1 نقطة)")

    # 🎫 التكت
    if any(k in text_clean for k in ["تكت", "تذكرة", "ticket", "استلام"]):
        total_points += 1
        reasons.append("استلام تكت (+1 نقطة)")

    return total_points, reasons

@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول باسم: {bot.user.name}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.attachments:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
                await message.add_reaction("🔍")
                try:
                    image_bytes = await attachment.read()
                    image = Image.open(io.BytesIO(image_bytes))
                    extracted_text = pytesseract.image_to_string(image, lang="ara+eng")
                    points_earned, reasons = parse_image_text(extracted_text)

                    if points_earned > 0:
                        new_total = add_points(message.author.id, points_earned)
                        reasons_str = "\n• ".join(reasons)
                        embed = discord.Embed(title="🎯 احتساب نقاط جديد", color=discord.Color.green())
                        embed.add_field(name="المستخدم", value=message.author.mention, inline=True)
                        embed.add_field(name="النقاط المضافة", value=f"**+{points_earned}**", inline=True)
                        embed.add_field(name="المجموع الحالي", value=f"**{new_total}**", inline=True)
                        embed.add_field(name="التفاصيل", value=f"• {reasons_str}", inline=False)
                        await message.reply(embed=embed)
                        await message.remove_reaction("🔍", bot.user)
                        await message.add_reaction("✅")
                    else:
                        await message.remove_reaction("🔍", bot.user)
                        await message.add_reaction("❓")
                except Exception as e:
                    print(f"Error: {e}")
                    await message.remove_reaction("🔍", bot.user)
                    await message.add_reaction("❌")

    await bot.process_commands(message)

@bot.command(name="نقاطي")
async def my_points(ctx):
    data = load_data()
    user_points = data.get(str(ctx.author.id), 0)
    await ctx.reply(f"📊 مجموع نقاطك الحالي هو: **{user_points}** نقطة.")

TOKEN = os.getenv("MTU0NDYyODYzNjQyMDY3MzU4Ng.GtQ7eB.bWb6SRJw2rllAZ6d9N10aY6_SPH0ZMGp_PWxQw") or "ضع_التوكن_هنا"
bot.run(TOKEN)
