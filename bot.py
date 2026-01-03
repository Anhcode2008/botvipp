import os, json, time, asyncio, requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= CONFIG =================
TOKEN = "7541286377:AAEhLLd3oN2p0GB0rOLKNU_K95DV4gTUzlI"
ADMINS = [7903272808]

GETKEY_API   = "http://duan.smmanhcode.click/getkey.php?username={}"
CHECKKEY_API = "http://duan.smmanhcode.click/check.php?key={}&user={}"
FOLLOW_API   = "http://duan.smmanhcode.click/tienich/apiflvip.php?key=mua&username={}"
LIKE_API     = "http://duan.smmanhcode.click/tienich/apitym.php?link={}"

AUTO_DELAY = 300
API_TIMEOUT = 60

DATA = "data"
AUTO_FILE = f"{DATA}/auto.json"
AUTO_STATUS = f"{DATA}/auto_status.txt"
os.makedirs(DATA, exist_ok=True)

# ================= UTIL =================
def call_api(url):
    try:
        return requests.get(url, timeout=API_TIMEOUT).json()
    except Exception as e:
        print("API ERROR:", e)
        return None

def is_verified(uid):
    f = f"{DATA}/verify_{uid}.txt"
    return os.path.exists(f) and open(f).read().strip() == datetime.now().strftime("%Y-%m-%d")

def save_verify(uid):
    open(f"{DATA}/verify_{uid}.txt", "w").write(datetime.now().strftime("%Y-%m-%d"))

def auto_on():
    return os.path.exists(AUTO_STATUS) and open(AUTO_STATUS).read().strip() == "on"

def load_auto():
    if not os.path.exists(AUTO_FILE):
        return []
    return json.load(open(AUTO_FILE))

def save_auto(d):
    json.dump(d, open(AUTO_FILE, "w"), indent=2)

# ================= AUTO LOOP =================
async def auto_runner(app):
    while True:
        if auto_on():
            jobs = load_auto()
            now = time.time()
            time_str = datetime.now().strftime("%H:%M:%S|%d-%m-%Y")

            for j in jobs:
                if now - j["last"] < AUTO_DELAY:
                    continue

                api = FOLLOW_API.format(j["value"]) if j["type"] == "fl" else LIKE_API.format(j["value"])
                res = call_api(api)
                j["last"] = now

                if res and res.get("success"):
                    await app.bot.send_message(
                        j["chat_id"],
                        f"""🤖 AUTO BUFF THÀNH CÔNG
━━━━━━━━━━━━━━
👤 Username: {res.get('username','')}
🏷 Nickname: {res.get('nickname','')}
📊 Trước: {res.get('before')}
📈 Sau: {res.get('after')}
🚀 Tăng: +{res.get('increase')}
⏰ Lần buff mới nhất: {time_str}
━━━━━━━━━━━━━━"""
                    )
            save_auto(jobs)
        await asyncio.sleep(10)

# ================= COMMAND =================
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 BOT BUFF TIKTOK – VIP PRO\n\n"
        "🔑 /getkey – Lấy key\n"
        "✅ /key KEY – Xác thực\n"
        "👥 /fl username – Buff follow\n"
        "❤️ /tim link – Buff tim\n"
        "🤖 /auto on|off – Admin"
    )

async def getkey(update: Update, ctx):
    uid = update.effective_user.id
    r = call_api(GETKEY_API.format(uid))
    if r and r.get("status") == "success":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Lấy key", url=r["short_url"])]
        ])
        await update.message.reply_text("🔑 LẤY KEY HÔM NAY", reply_markup=kb)
    else:
        await update.message.reply_text("❌ Không lấy được key")

async def key(update: Update, ctx):
    uid = update.effective_user.id
    if not ctx.args:
        return await update.message.reply_text("❌ /key ABC123")
    r = call_api(CHECKKEY_API.format(ctx.args[0], uid))
    if r and r.get("status") == "success":
        save_verify(uid)
        await update.message.reply_text("✅ XÁC THỰC THÀNH CÔNG")
    else:
        await update.message.reply_text("❌ Key sai")

async def fl(update: Update, ctx):
    if not is_verified(update.effective_user.id):
        return await update.message.reply_text("🔒 /getkey để xác thực")
    if not ctx.args:
        return await update.message.reply_text("❌ /fl username")

    user = ctx.args[0]
    r = call_api(FOLLOW_API.format(user))
    if r and r.get("success"):
        await update.message.reply_text(f"✅ FOLLOW +{r['increase']}")
    a = load_auto()
    a.append({"chat_id": update.effective_chat.id, "type": "fl", "value": user, "last": time.time()})
    save_auto(a)

async def tim(update: Update, ctx):
    if not is_verified(update.effective_user.id):
        return await update.message.reply_text("🔒 /getkey để xác thực")
    if not ctx.args:
        return await update.message.reply_text("❌ /tim link")

    link = ctx.args[0]
    r = call_api(LIKE_API.format(link))
    if r and r.get("success"):
        await update.message.reply_text(f"✅ TIM +{r['increase']}")
    a = load_auto()
    a.append({"chat_id": update.effective_chat.id, "type": "tim", "value": link, "last": time.time()})
    save_auto(a)

async def auto_cmd(update: Update, ctx):
    if update.effective_user.id not in ADMINS:
        return await update.message.reply_text("❌ Không phải admin")
    if ctx.args and ctx.args[0] == "on":
        open(AUTO_STATUS, "w").write("on")
        await update.message.reply_text("✅ AUTO ON")
    else:
        if os.path.exists(AUTO_STATUS):
            os.remove(AUTO_STATUS)
        await update.message.reply_text("⛔ AUTO OFF")

# ================= RUN =================
async def main():
    print("🤖 BOT STARTED – POLLING")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("getkey", getkey))
    app.add_handler(CommandHandler("key", key))
    app.add_handler(CommandHandler("fl", fl))
    app.add_handler(CommandHandler("tim", tim))
    app.add_handler(CommandHandler("auto", auto_cmd))

    asyncio.create_task(auto_runner(app))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())


