
import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

DB_PATH = "progress.json"
FAKE_CODES = {f"fake{i}" for i in range(1, 11)}

def load_db():
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_PATH, "w") as f:
        json.dump(db, f)

def format_progress(user_pieces):
    found = sorted(user_pieces)
    missing = [str(i) for i in range(1, 11) if i not in found]
    text = f"🧩 Знайдено: {', '.join(map(str, found))}\n🔍 Ще залишилось: {', '.join(missing)}"
    if len(found) == 10:
        text += "\n🎯 УРА! Ти зібрав всю картину!"
    return text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user_id = str(update.effective_user.id)
    text = update.message.text
    args = context.args if context.args else text.split()[1:]
    if not args:
        await update.message.reply_text("Привіт! Скануй QR-коди, щоб зібрати частини картини!")
        return

    code = args[0].lower()
    if code in FAKE_CODES:
        await update.message.reply_text("😅 Це фейковий код! Шукай далі справжні частини.")
        return

    if code.startswith("piece"):
        piece_arg = code.replace("piece", "")
        if not piece_arg.isdigit() or not (1 <= int(piece_arg) <= 10):
            await update.message.reply_text("Невідома частина картини.")
            return

        piece = int(piece_arg)
        db.setdefault(user_id, [])
        if piece not in db[user_id]:
            db[user_id].append(piece)
            save_db(db)
            await update.message.reply_text(f"🎉 Ти знайшов частину #{piece}!")
        else:
            await update.message.reply_text(f"✅ Частина #{piece} вже знайдена.")

        img_path = os.path.join("images", "pieces", f"piece{piece}.jpg")
        if os.path.exists(img_path):
            with open(img_path, "rb") as img_file:
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=img_file)
        else:
            await update.message.reply_text("(Зображення частини не знайдено)")

        progress_text = format_progress(db[user_id])
        await update.message.reply_text(progress_text)

        if len(db[user_id]) == 10:
            full_img_path = os.path.join("images", "full", "full.jpg")
            if os.path.exists(full_img_path):
                with open(full_img_path, "rb") as full_img:
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=full_img)
                await update.message.reply_text("🎉 Вітаємо! Ти зібрав всю картину!")
            else:
                await update.message.reply_text("(Повне зображення не знайдено)")
        return

    await update.message.reply_text("🤔 Я не впізнаю цей код. Це не частина і не фейк.")

async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user_id = str(update.effective_user.id)
    user_pieces = db.get(user_id, [])
    progress_text = format_progress(user_pieces)
    await update.message.reply_text(progress_text)

async def resetme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user_id = str(update.effective_user.id)
    if user_id in db:
        del db[user_id]
        save_db(db)
        await update.message.reply_text("🔁 Твій прогрес очищено. Почни заново!")
    else:
        await update.message.reply_text("🤔 У тебе ще не було прогресу.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"⚠️ Виникла помилка: {context.error}")

def main():
    TOKEN = os.getenv("TOKEN")
    if not TOKEN:
        print("❌ Помилка: Змінна середовища TOKEN не задана.")
        return

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("progress", progress))
    app.add_handler(CommandHandler("resetme", resetme))
    app.add_error_handler(error_handler)

    print("Бот запущено...")
    app.run_polling()

if __name__ == "__main__":
    main()
