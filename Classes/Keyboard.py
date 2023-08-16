from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

class Keyboard:

    def create_button(**kwargs): # This exists so when I import the InlineKeyboardButton type, it's only in the class and not anywhere else
        return InlineKeyboardButton(**kwargs)

    def create_keyboard(*buttons):
        buttonscount = len(buttons)
        if buttonscount == 1:
            cols = 1
        elif buttonscount == 2:
            cols = 2
        elif buttonscount == 10:
            cols = 3
        elif buttonscount > 2 and buttonscount < 8:
            cols = min(4, (buttonscount + 1) // 2)
            if buttonscount % 2 == 0 and buttonscount > 4:
                cols = min(4, cols)
        elif buttonscount == 8:
            cols = 4
        else:
            cols = 3

        rows = (buttonscount + cols - 1) // cols
        keyboard = []

        button_index = 0
        for row in range(rows):
            row_buttons = []
            for col in range(cols):
                if button_index < buttonscount: # TODO - I might be able to remove this if check. Test it.
                    row_buttons.append(buttons[button_index]) # Append the existing button object
                    button_index += 1 # TODO - I might be able to remove this as well, if I can remove the above instantiation
                else:
                    break
            keyboard.append(row_buttons)

        return InlineKeyboardMarkup(keyboard)
