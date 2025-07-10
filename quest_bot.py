import json
import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

DB_PATH = "progress.json"
FAKE_CODES = {f"fake{i}" for i in range(1, 11)}

def load_db():
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(db):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def format_progress(user_pieces):
    found = sorted(user_pieces)
    missing = [str(i) for i in range(1, 11) if i not in found]
    text = f"🧩 Знайдено: {', '.join(map(str, found))}\n🔍 Ще залишилось: {', '.join(missing)}"
    if len(found) == 10:
        text += "\n🎯 УРА! Ти зібрав всю картину!"
    return text

def start(update: Update, context: CallbackContext):
    db = load_db()
    user_id = str(update.effective_user.id)
    text = update.message.text
    args = context.args if context.args else text.split()[1:]
    
    if not args:
        update.message.reply_text("Привіт! Скануй QR-коди, щоб зібрати частини картини!")
        return

    code = args[0].lower()
    if code in FAKE_CODES:
        update.message.reply_text("😅 Це фейковий код! Шукай далі справжні частини.")
        return

    if code.startswith("piece"):
        piece_arg = code.replace("piece", "")
        if not piece_arg.isdigit() or not (1 <= int(piece_arg) <= 10):
            update.message.reply_text("Невідома частина картини.")
            return

        piece = int(piece_arg)
        db.setdefault(user_id, [])
        if piece not in db[user_id]:
            db[user_id].append(piece)
            save_db(db)
            update.message.reply_text(f"🎉 Ти знайшов частину #{piece}!")
        else:
            update.message.reply_text(f"✅ Частина #{piece} вже знайдена.")

        img_path = os.path.join("images", "pieces", f"piece{piece}.jpg")
        if os.path.exists(img_path):
            with open(img_path, "rb") as img_file:
                context.bot.send_photo(chat_id=update.effective_chat.id, photo=img_file)
        else:
            update.message.reply_text("(Зображення частини не знайдено)")

        progress_text = format_progress(db[user_id])
        update.message.reply_text(progress_text)

        if len(db[user_id]) == 10:
            full_img_path = os.path.join("images", "full", "full.jpg")
            if os.path.exists(full_img_path):
                with open(full_img_path, "rb") as full_img:
                    context.bot.send_photo(chat_id=update.effective_chat.id, photo=full_img)
                update.message.reply_text("🎉 Вітаємо! Ти зібрав всю картину!")
            else:
                update.message.reply_text("(Повне зображення не знайдено)")
        return

    update.message.reply_text("🤔 Я не впізнаю цей код. Це не частина і не фейк.")

def progress(update: Update, context: CallbackContext):
    db = load_db()
    user_id = str(update.effective_user.id)
    user_pieces = db.get(user_id, [])
    progress_text = format_progress(user_pieces)
    update.message.reply_text(progress_text)

def resetme(update: Update, context: CallbackContext):
    db = load_db()
    user_id = str(update.effective_user.id)
    if user_id in db:
        del db[user_id]
        save_db(db)
        update.message.reply_text("🔁 Твій прогрес очищено. Почни заново!")
    else:
        update.message.reply_text("🤔 У тебе ще не було прогресу.")

def error_handler(update, context):
    print(f"⚠️ Виникла помилка: {context.error}")

def main():
    TOKEN = os.getenv("TOKEN")
    if not TOKEN:
        print("❌ Помилка: Змінна середовища TOKEN не задана.")
        return

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("progress", progress))
    dp.add_handler(CommandHandler("resetme", resetme))
    dp.add_error_handler(error_handler)

    print("Бот запущено...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
