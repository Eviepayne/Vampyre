import sqlite3, os, logging, argparse, time
from pyrogram import filters, enums, types, errors
from Classes.Keyboard import Keyboard
from Classes.Callback import Callback
from Classes.ArgparseOverride import ArgumentParser
from Classes.Manager import HandlerManager

lastupdate = {}
lastusersindex = {}

class Handlers():

    def __init__(self):
        pass
    
  # Message Sweep =====================================================================================
    def messagesweep(bot, message):
        """Deletes messages

        Args:
            bot (bot): bot class
            message (message): message object
        """

     # Handle CallbackQueries
        if type(message) is types.CallbackQuery and Handlers.is_admin(bot, message.message.chat.id, message.from_user.id):
            inline_keyboard = message.message.reply_markup.inline_keyboard
            callback_actions = {button.text: button.callback_data for row in inline_keyboard for button in row if hasattr(button, 'text') and hasattr(button, 'callback_data')}
            selectedguid = message.data
            data, handler = Callback.ReadCallback(selectedguid)
            deletelist = data['deletelist']
            for guid in callback_actions.values():
                data, handler = Callback.ReadCallback(guid)
                Callback.DestroyCallback(bot, guid, handler)
            if selectedguid == callback_actions['Delete Messages']:
                deletelist.append(message.message.id)
                try:
                    bot.delete_messages(message.message.chat.id, deletelist)
                except Exception as e:
                    bot.send_message(message.message.chat.id, f"We failed to delete the following messages:\n{deletelist}\nThis was the issue: {e}")

            if selectedguid == callback_actions['Cancel Operation']:
                deletelist.clear()
                deletelist.append(message.message.id)
                bot.delete_messages(message.message.chat.id, deletelist)

            return

     # Return if not admin
        if not Handlers.is_admin(bot, message.chat.id, message.from_user.id):
            return

        bot.delete_messages(message.chat.id, message.id) # I think this caused the bug.
        # by the time we go to calculate the first message is empty.
        # If this isnt it, I also changed the current >= target so it only checks if its greater.

     # Create argparse and overwrite
        parser = ArgumentParser(description='Delete messages in this group')

        helpdialog = """
      Delete messages in this group.
      To delete a target message, reply to the message with command: /del 1
    
        /del [-h]                         
        - Help Dialog
        
        /del number (no replied message)  
        - Delete the number of messages above
        
        /del (replying to message)       
        - Delete all messages up to (including) the replied message.
        
        /del number (replying to message)
        - Delete the number of messages after (including) the replied message.

      positional arguments:
      number      The number of messages to delete

      optional arguments:
      -h, --help  show this help message
        """
        parser.add_argument('number', type=int, nargs='?', default=None, help='The number of messages to delete')
        command = message.text.split()
        try:
            args = parser.parse_args(command[1:])
        except Exception as e:
            bot.send_message(message.chat.id, f"{e}\n\nMake sure you're using this command correctly\n{helpdialog}")
            return


     # If no reply and no number
        if not message.reply_to_message and args.number is None:
            bot.send_message(message.chat.id, f"```{helpdialog}```")
            return

     # Bot sending original message to let user know it's working.
        statusmessage = bot.send_message(message.chat.id, "We are gathering messages to delete")

     # Instantiate messages to delete list and sanity check
        deletelist = []
        sanitycheck = 0        
        
     # If no reply and has number
        if not message.reply_to_message and args.number is not None:
            currentmessageid = message.id
            targetmessageid = message.id - args.number
            while currentmessageid > targetmessageid:
                currentmessage = bot.get_messages(message.chat.id, currentmessageid)
                if currentmessage.empty:
                    sanitycheck += 1
                    targetmessageid -= 1
                    currentmessageid -= 1
                    if sanitycheck == 101:
                        break
                    continue
                deletelist.append(currentmessageid)
                sanitycheck = 0
                currentmessageid -= 1

     # If has reply and no number
        if message.reply_to_message and args.number is None:
            currentmessageid = message.id
            targetmessageid = message.reply_to_message
            while currentmessageid >= message.reply_to_message.id:
                currentmessage = bot.get_messages(message.chat.id, currentmessageid)
                if currentmessage.empty:
                    currentmessageid -= 1
                    continue
                deletelist.append(currentmessageid)
                currentmessageid -= 1
                
     # If has reply and number
        if message.reply_to_message and args.number is not None:
            currentmessageid = message.reply_to_message.id
            targetmessageid = message.reply_to_message.id - args.number
            while currentmessageid > targetmessageid:
                currentmessage = bot.get_messages(message.reply_to_message.chat.id, currentmessageid)
                if currentmessage.empty:
                    sanitycheck += 1
                    targetmessageid -= 1
                    currentmessageid -= 1
                    if sanitycheck == 100:
                        break
                    continue
                deletelist.append(currentmessageid)
                sanitycheck = 0
                currentmessageid -= 1

     # Create callback to confirm deletion
        guiddelete = Callback.CreateCallback(bot, Handlers.messagesweep, deletelist=deletelist)
        guidcancel = Callback.CreateCallback(bot, Handlers.messagesweep, deletelist=deletelist)
        Delete = Keyboard.create_button(text="Delete Messages",callback_data=guiddelete)
        Cancel = Keyboard.create_button(text="Cancel Operation",callback_data=guidcancel)
        keyboard = Keyboard.create_keyboard(Delete, Cancel)
        bot.edit_message_text(statusmessage.chat.id, statusmessage.id, f"Confirm deleting {len(deletelist)} messages", reply_markup=keyboard)
        # Timeout for callback
        time.sleep(30)
        manager = HandlerManager()
        handlerdelete = manager.get_handler(guiddelete)
        handlercancel = manager.get_handler(guidcancel)
        if handlerdelete:
            Callback.DestroyCallback(bot, guiddelete, handlerdelete)
            Callback.DestroyCallback(bot, guidcancel, handlercancel)
            bot.delete_messages(statusmessage.chat.id, statusmessage.id)
        

  # is_admin =====================================================================================
    def is_admin(bot, chatid, userid):
        """Returns true if user is admin

        Args:
            bot (bot): bot class
            chatid (int): Unique Identifier for the chat
            userid (int): Unique Identifier for the user

        Returns:
            Bool: Returns True if the user is an administrator or owner
        """
        try:
            ChatMember = bot.get_chat_member(chatid, userid)
        except errors.FloodWait as e:
            bot.send_message(chatid, "We are being rate limited. Please wait.")
            return False
        
        if ChatMember.status == enums.ChatMemberStatus.ADMINISTRATOR or ChatMember.status == enums.ChatMemberStatus.OWNER:
            return True

  # get user id =====================================================================================
    def get_user_id(bot, message):
        """Returns a user id

        Args:
            bot (bot): bot Class Object
            message (message): Message Object
        """

      # Create argparse
        parser = ArgumentParser(description='Returns the Unique identifier for the user', exit_on_error=False)

        helpdialog = """
       Returns the Unique identifier for the user
    
        /id [-h]                         
        - Help Dialog
        
        /id  
        - Gets the sending user's ID
        
        /id (replying to message)     
        - Gets the id of the user from the reply message
        
        /id @username
        - Get's the ID of the user mentioned

       positional arguments:
       @username      The mentioned user to return ID

       optional arguments:
       -h, --help  show this help message
        """
        parser.add_argument('username', type=str, nargs='?', default=None, help='User to get the ID of')
        parser.add_argument('-c', action='store_true', help='get the chats ID')
        command = message.text.split()
        try:
            args = parser.parse_args(command[1:])
        except Exception as e:
            bot.send_message(message.chat.id, f"Invalid input, please ensure you're using this command correctly:\n{helpdialog}")

        if args.c:
            bot.delete_messages(message.chat.id, message.id)
            bot.send_message(message.chat.id, f"{message.chat.id}")
            return

      # Getting your own id
        if not message.reply_to_message and args.username is None:
            bot.delete_messages(message.chat.id, message.id)
            bot.send_message(message.chat.id, f"{message.from_user.id}")
            return
      
      # Getting id from reply
        if message.reply_to_message and args.username is None:
            bot.delete_messages(message.chat.id, message.id)
            bot.send_message(message.chat.id, f"{message.reply_to_message.from_user.id}")
            return
        
      # Getting id from mention/text mention  
        if not message.reply_to_message and args.username is not None:
            bot.delete_messages(message.chat.id, message.id)
            if message.mentioned == True:
                user = bot.get_users(args.username)
            else:
                text_mention = next(
                    (obj for obj in message.entities if obj.type == enums.MessageEntityType.TEXT_MENTION),None
                )
                user = text_mention.user
            bot.send_message(message.chat.id, user.id)

  # allmessages =====================================================================================
    def all_messages(bot, message):
        """
        This method is called on ALL messages
        It should be as light as possible to prevent overloading the bot
        """
        global lastupdate
        global lastusersindex
        now = int(time.time())

        # update user info
        if now - lastupdate.get(message.from_user.id, 0) > 300:
            bot.update_user(message.chat.id, message.from_user.id)
            lastupdate.update({message.from_user.id: now})

        # update chat info
        if now - lastupdate.get(message.chat.id, 0) > 300:
            bot.update_chat(message.chat.id)
            lastupdate.update({message.chat.id: now})

        # update user index
        bot.update_users(message.chat.id)

