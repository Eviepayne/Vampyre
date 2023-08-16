from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def callbackbutton(bot,message): # refactor to actual settings options
    reply_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("first", callback_data = '1')],
        [
            InlineKeyboardButton("second", callback_data = '2'),
            InlineKeyboardButton("third", callback_data = '3'),
        ]
    ])
    bot.send_message(message.chat.id, f"pick one:", reply_markup=reply_buttons)

def callbacktest(bot, callback_query): # refactor for settings navigation
    callback_query.answer(f"Button contains: '{callback_query.data}'", show_alert=True)

# Create settings menus