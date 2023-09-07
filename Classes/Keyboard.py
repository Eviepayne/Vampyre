from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

class Keyboard:

    def create_button(**kwargs): # This exists so I don't have to import keyboardbuttons everywhere
        return InlineKeyboardButton(**kwargs)

    def create_keyboard(*buttons):
        # get the number of buttons I created
        buttonscount = len(buttons)

        # determine the number of columns based on the number of buttons
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

        # calculate the number of rows based on the number of columns and buttons
        rows = (buttonscount + cols - 1) // cols
        # instantiate keyboard object
        keyboard = []

        # Set starter location in the grid
        button_index = 0
        # Every Row, Create the row object, and create each column
        for row in range(rows):
            row_buttons = []
            # Each column if the index is less than how many buttons we have
            # create a button for the cell
            for col in range(cols):
                if button_index < buttonscount:
                    row_buttons.append(buttons[button_index])
                    button_index += 1
                else:
                    break
            # when the row is finished, add it to the keyboard
            keyboard.append(row_buttons)
        # When keyboard is done, return it
        return InlineKeyboardMarkup(keyboard)
