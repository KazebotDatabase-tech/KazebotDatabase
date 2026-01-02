import os
import json
import asyncio
import time
from datetime import datetime
from pathlib import Path
import secrets
import io
from flask import Flask
from threading import Thread

# Keep-alive for Render
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot is online!"

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    Thread(target=lambda: app_web.run(host="0.0.0.0", port=port)).start()

# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ---------------- ENV & DIRECTORIES ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))

if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN missing!")

FILES_DIR = Path("files")
ASSETS_DIR = Path("assets")
KEYS_FILE = Path("keys.json")

FILES_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)

if not KEYS_FILE.exists():
    KEYS_FILE.write_text(json.dumps({"keys": {}, "users": {}}, indent=2))

PH_TIME = lambda: datetime.now().strftime("%Y-%m-%d %I:%M %p")

# ---------------- KEY SYSTEM ----------------
def load_keys():
    try:
        data = json.loads(KEYS_FILE.read_text())
        if "keys" not in data: data["keys"] = {}
        if "users" not in data: data["users"] = {}
        return data
    except:
        KEYS_FILE.write_text(json.dumps({"keys": {}, "users": {}}, indent=2))
        return {"keys": {}, "users": {}}

def save_keys(data):
    KEYS_FILE.write_text(json.dumps(data, indent=2))

def make_key(length=8):
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"
    return "".join(secrets.choice(chars) for _ in range(length))

def generate_full_key():
    return "Kaze-" + make_key()

def get_key(manual_key=None):
    return manual_key.strip() if manual_key else generate_full_key()

def parse_duration(text):
    text = text.lower().strip()
    if text in ("life", "lifetime"):
        return None
    if text.endswith("d"):
        return int(text[:-1]) * 86400
    if text.endswith("h"):
        return int(text[:-1]) * 3600
    return 86400

async def is_user_authorized(uid):
    data = load_keys()
    kid = data["users"].get(str(uid))
    if not kid: return False
    info = data["keys"].get(kid)
    if not info: return False
    exp = info.get("expires_at")
    return exp is None or time.time() <= exp

# ---------------- FILE MAP & GENERATOR ----------------
FILE_MAP = {
    "valorant": FILES_DIR / "Valorant.txt",
    "roblox": FILES_DIR / "Roblox.txt",
    "codm": FILES_DIR / "CODM.txt",
    "crossfire": FILES_DIR / "Crossfire.txt",
    "facebook": FILES_DIR / "Facebook.txt",
    "gmail": FILES_DIR / "Gmail.txt",
    "mtacc": FILES_DIR / "Mtacc.txt",
    "gaslite": FILES_DIR / "gaslite.txt",
    "bloodstrike": FILES_DIR / "Bloodstrike.txt",
    "random": FILES_DIR / "Random.txt",
    "100082": FILES_DIR / "100082.txt",
}

user_cool = {}
COOLDOWN = 30

def extract_lines(path, n=500, max_limit=500):
    if not path.exists():
        return "", 0
    lines = path.read_text(errors="ignore").splitlines()
    if not lines:
        return "", 0
    take_n = min(n, max_limit)
    take = lines[:take_n]
    remain = lines[take_n:]
    path.write_text("\n".join(remain) + "\n")
    return "\n".join(take), len(take)

async def send_alert(bot, user, typ, count):
    try:
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"📢 New Generation\n"
            f"User: {user.first_name} ({user.id})\n"
            f"Type: {typ.upper()}\n"
            f"Lines: {count}\n"
            f"Time: {PH_TIME()}"
        )
    except:
        pass

# ---------------- COMMANDS ----------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await is_user_authorized(user.id):
        await update.message.reply_text(
            f"💫 *WELCOME, {user.full_name}!* 💫\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔐 *PREMIUM KEY REQUIRED*\n"
            "Please redeem a valid key to access the generator.\n\n"
            "📩 Buy key: @KAZEHAYAMODZ",
            parse_mode="Markdown"
        )
        return

    keyboard = [
        [InlineKeyboardButton("⚡ Generate Accounts", callback_data="menu_generate")],
        [InlineKeyboardButton("🛠 Tools Hub", callback_data="menu_tools")],
        [InlineKeyboardButton("📢 Channel", callback_data="menu_channel")],
    ]
    await update.message.reply_text(
        "✨ *MAIN MENU* ✨\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Choose an option below:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def genkey_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return await update.message.reply_text("⛔ Forbidden")

    args = context.args
    manual_key = None
    duration = "1d"

    if len(args) == 1:
        if args[0].lower() in ("life", "lifetime") or args[0].lower().endswith(("d", "h")):
            duration = args[0]
        else:
            manual_key = args[0]
    elif len(args) == 2:
        manual_key, duration = args

    key = get_key(manual_key)
    seconds = parse_duration(duration)

    data = load_keys()
    data["keys"][key] = {
        "owner": None,
        "created_at": time.time(),
        "expires_at": None if seconds is None else time.time() + seconds
    }
    save_keys(data)

    exp_text = "♾ Lifetime" if seconds is None else datetime.fromtimestamp(time.time() + seconds).strftime("%Y-%m-%d %I:%M %p")

    await update.message.reply_text(
        f"✨ KEY GENERATED ✨\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔑 Key: `{key}`\n"
        f"📅 Expires: {exp_text}\n\n"
        f"Example: /key `{key}`",
        parse_mode="Markdown"
    )

async def key_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usage: /key <YOUR_KEY>", parse_mode="Markdown")

    key = context.args[0].strip()
    data = load_keys()
    info = data["keys"].get(key)

    if not info:
        return await update.message.reply_text("❌ Invalid key.")

    if "used" not in info: info["used"] = False
    if "owner" not in info: info["owner"] = None

    if info["used"] and info["owner"] != update.effective_user.id:
        return await update.message.reply_text("❌ Key already used.")

    exp = info.get("expires_at")
    if exp and time.time() > exp:
        return await update.message.reply_text("⏳ Key expired.")

    info["used"] = True
    info["owner"] = update.effective_user.id
    data["users"][str(update.effective_user.id)] = key
    save_keys(data)

    exp_text = "♾ Lifetime" if exp is None else datetime.fromtimestamp(exp).strftime("%Y-%m-%d %I:%M %p")
    await update.message.reply_text(
        f"🏆 *PREMIUM ACTIVATED!* 🏆\n"
        f"🔑 Key: `{key}`\n"
        f"📅 Expires: {exp_text}\n\n"
        "Type /start to begin!",
        parse_mode="Markdown"
    )

# (Keep your other commands: mytime_cmd, panel_cmd, revoke_cmd, broadcast_cmd)

# ---------------- CALLBACK HANDLER ----------------
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user = q.from_user
    data = q.data

    # Menu navigation
    if data == "menu_generate":
        keyboard = [
            [InlineKeyboardButton("🎮 Valorant", callback_data="valorant"), InlineKeyboardButton("🤖 Roblox", callback_data="roblox")],
            [InlineKeyboardButton("✨ CODM", callback_data="codm"), InlineKeyboardButton("🔥 Gaslite", callback_data="gaslite")],
            [InlineKeyboardButton("📘 Facebook", callback_data="facebook"), InlineKeyboardButton("📧 Gmail", callback_data="gmail")],
            [InlineKeyboardButton("♨️ Bloodstrike", callback_data="bloodstrike"), InlineKeyboardButton("🎲 Random", callback_data="random")],
            [InlineKeyboardButton("📌 100082", callback_data="100082")],
            [InlineKeyboardButton("⬅ Back", callback_data="back_to_home")],
        ]
        return await q.edit_message_text("⚡ Select account type:", reply_markup=InlineKeyboardMarkup(keyboard))

    if data == "menu_tools":
        keyboard = [
            [InlineKeyboardButton("📄 TXT Divider", callback_data="tool_divider")],
            [InlineKeyboardButton("🧹 Dupe Remover", callback_data="tool_dupe")],
            [InlineKeyboardButton("🔗 URL Cleaner", callback_data="tool_url")],
            [InlineKeyboardButton("⬅ Back", callback_data="back_to_home")],
        ]
        return await q.edit_message_text("🛠 Tools Hub", reply_markup=InlineKeyboardMarkup(keyboard))

    if data == "menu_channel":
        return await q.edit_message_text(
            "📢 Channel:\nhttps://t.me/+wkXVYyqiRYplZjk1",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅ Back", callback_data="back_to_home")]])
        )

    if data == "back_to_home":
        keyboard = [
            [InlineKeyboardButton("⚡ Generate Accounts", callback_data="menu_generate")],
            [InlineKeyboardButton("🛠 Tools Hub", callback_data="menu_tools")],
            [InlineKeyboardButton("📢 Channel", callback_data="menu_channel")],
        ]
        return await q.edit_message_text("🏠 Main Menu", reply_markup=InlineKeyboardMarkup(keyboard))

    # Generation from buttons
    if data in FILE_MAP:
        if not await is_user_authorized(user.id):
            return await q.message.reply_text("❌ Unauthorized.")

        now = time.time()
        if user.id != ADMIN_CHAT_ID:
            last = user_cool.get(user.id, 0)
            if now - last < COOLDOWN:
                remain = int(COOLDOWN - (now - last))
                return await q.message.reply_text(f"⏳ Cooldown: {remain}s")

        user_cool[user.id] = now
        max_lines = 999999 if user.id == ADMIN_CHAT_ID else 500

        loading = await q.message.reply_text(f"🔥 Generating {data.upper()}... ({'UNLIMITED' if user.id == ADMIN_CHAT_ID else '500'} lines)")
        await asyncio.sleep(2)
        await loading.delete()

        content, count = extract_lines(FILE_MAP[data], n=1000, max_limit=max_lines)
        await send_alert(context.bot, user, data, count)

        if count == 0:
            return await q.message.reply_text("⚠️ Stock empty!")

        bio = io.BytesIO(content.encode('utf-8'))
        bio.name = f"{data.upper()}_{count}_lines.txt"

        caption = (
            f"🎉 GENERATED!\n\n"
            f"Type: {data.upper()}\n"
            f"Lines: {count}\n"
            f"User: {'OWNER 🔥' if user.id == ADMIN_CHAT_ID else 'Premium'}\n"
            f"Time: {PH_TIME()}\n\n"
            "@KAZEHAYAMODZ"
        )
        await q.message.reply_document(document=bio, filename=bio.name, caption=caption)

# ---------------- OWNER CUSTOM GENERATE ----------------
async def owner_generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return await update.message.reply_text("⛔ Owner only!")

    if len(context.args) < 2:
        return await update.message.reply_text(
            f"Usage: /generate <type> <lines>\n"
            f"Example: /generate codm 2000\n"
            f"Types: {', '.join(FILE_MAP.keys())}"
        )

    typ = context.args[0].lower()
    if typ not in FILE_MAP:
        return await update.message.reply_text("Invalid type!")

    try:
        requested = int(context.args[1])
        if requested < 1:
            raise ValueError
    except:
        return await update.message.reply_text("Lines must be positive number!")

    await update.message.reply_text(f"👑 Generating {requested} lines of {typ.upper()}...")
    content, count = extract_lines(FILE_MAP[typ], n=requested, max_limit=999999)
    await send_alert(context.bot, update.effective_user, typ, count)

    if count == 0:
        return await update.message.reply_text("⚠️ No stock!")

    bio = io.BytesIO(content.encode('utf-8'))
    bio.name = f"OWNER_{typ.upper()}_{count}_lines.txt"
    caption = f"👑 OWNER GENERATE\nType: {typ.upper()}\nGot: {count}/{requested}\nTime: {PH_TIME()}"
    await update.message.reply_document(bio, filename=bio.name, caption=caption)

# ---------------- ERROR HANDLER ----------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"Error: {context.error}")
    try:
        await context.bot.send_message(ADMIN_CHAT_ID, f"Bot Error:\n{context.error}")
    except:
        pass

# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("genkey", genkey_cmd))
    app.add_handler(CommandHandler("key", key_cmd))
    app.add_handler(CommandHandler("mytime", mytime_cmd))
    app.add_handler(CommandHandler("panel", panel_cmd))
    app.add_handler(CommandHandler("revoke", revoke_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("generate", owner_generate))  # Owner custom

    # All callbacks (menus + generation)
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^(menu_|back_|tool_)"))
    app.add_handler(CallbackQueryHandler(menu_callback))  # For game buttons

    app.add_error_handler(error_handler)

    print("BOT RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
