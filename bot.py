import os
import json
import gspread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from google.oauth2.service_account import Credentials
from flask import Flask, request
import threading

TOKEN = "8766294344:AAF60xhy0S_G2eSwghOPiqSAYGSlGxk6mWE"
CHAT_ID = "8319031203"
SPREADSHEET_ID = "1bhMsAp5Wo4GOB0pj8gSoGKmDqESS1kwN3e5rRhq87sw"

SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

def get_sheet_client():
    creds_json = os.environ.get("GOOGLE_CREDS")
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("~")
    sheet_name = parts[0]
    row_index = int(parts[1])
    action = parts[2]

    try:
        client = get_sheet_client()
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.worksheet(sheet_name)
        
        headers = sheet.row_values(1)
        wadiya_col = -1
        for i, h in enumerate(headers):
            if h.strip() == "وضعية":
                wadiya_col = i + 1

        colors = {
            "confirmer": {"text": "مؤكد", "alert": "✅ تم تأكيد الطلب", "status": "✅ مؤكد", "color": (0.718, 0.882, 0.804)},
            "annuler":   {"text": "ملغاة", "alert": "❌ تم إلغاء الطلب", "status": "❌ ملغاة", "color": (0.957, 0.800, 0.800)},
            "tel1":      {"text": "اتصال 1", "alert": "📞 تم تسجيل اتصال 1", "status": "📞 اتصال 1", "color": (0.788, 0.855, 0.973)},
            "tel2":      {"text": "اتصال 2", "alert": "📞 تم تسجيل اتصال 2", "status": "📞 اتصال 2", "color": (0.988, 0.898, 0.804)},
        }

        info = colors.get(action)
        if info and wadiya_col > 0:
            sheet.update_cell(row_index, wadiya_col, info["text"])

        cb_base = f"{sheet_name}~{row_index}"
        
        if action in ["confirmer", "annuler"]:
            new_keyboard = InlineKeyboardMarkup([])
        elif action == "tel1":
            new_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ مؤكد", callback_data=f"{cb_base}~confirmer"),
                 InlineKeyboardButton("❌ ملغاة", callback_data=f"{cb_base}~annuler")],
                [InlineKeyboardButton("📞 اتصال 2", callback_data=f"{cb_base}~tel2")]
            ])
        elif action == "tel2":
            new_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ مؤكد", callback_data=f"{cb_base}~confirmer"),
                 InlineKeyboardButton("❌ ملغاة", callback_data=f"{cb_base}~annuler")],
                [InlineKeyboardButton("📞 اتصال 1", callback_data=f"{cb_base}~tel1")]
            ])

        old_text = query.message.text
        new_text = old_text.replace("✅ تم التسجيل", f"✅ تم التسجيل\n\n🔔 الحالة: {info['status']}")
        
        await query.edit_message_text(new_text, reply_markup=new_keyboard)

    except Exception as e:
        print(f"Error: {e}")

app = Flask(__name__)

@app.route("/health")
def health():
    return "ok"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CallbackQueryHandler(button_handler))
    application.run_polling()

if __name__ == "__main__":
    main()
