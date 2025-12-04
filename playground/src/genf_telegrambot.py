import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import os
from GENF import GENF





class TelegramBot:
    def __init__(self):
        self.genf = GENF()
        self.names = self.genf.read_bq('SELECT full_name FROM genf.members')['full_name'].tolist()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = []
        # Create buttons for each name, 2 names per row
        for i in range(0, len(self.names), 2):
            row = []
            row.append(InlineKeyboardButton(self.names[i], callback_data=f"name_{i}"))
            if i + 1 < len(self.names):
                row.append(InlineKeyboardButton(self.names[i + 1], callback_data=f"name_{i + 1}"))
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            'Velg ditt navn fra listen:',
            reply_markup=reply_markup
        )

    async def button_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer()

            name_index = int(query.data.split('_')[1])
            selected_name = self.names[name_index]
            user_id = query.from_user.id

            df = pd.DataFrame({'user_id': [user_id], 'name': [selected_name]})
            self.genf.to_bq(df, 'userid_names', 'genf', 'replace')

            await query.edit_message_text(f'Du har valgt: {selected_name}')
        except Exception as e:
            await query.edit_message_text(f'Beklager, det oppstod en feil. Prøv igjen.')
            print(f'Error: {e}')


def main():

    bot = TelegramBot()
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CallbackQueryHandler(bot.button_click))

    # Start bot
    application.run_polling()


if __name__ == '__main__':
    main()