import sqlite3, os, logging, argparse, time, threading, textwrap
from pyrogram import filters, enums, types, errors
from Classes.Keyboard import Keyboard
from Classes.Callback import Callback
from Classes.ArgparseOverride import ArgumentParser
from Classes.Manager import HandlerManager

lastupdate = {}
lastusersindex = {}
handler_lock = threading.Lock()

class Handlers():

    def __init__(self):
        pass
    
  # Message Sweep =====================================================================================
    def messagesweep(bot, message):
        """Deletes Messages

        Args:
            bot (Class): The Bot
            message (message | CallbackQuery): The contents being sent via Handler
        """

     # Handle CallbackQueries
        if type(message) is types.CallbackQuery and not Handlers.is_admin(bot, message.message.chat.id, message.from_user.id):
            return
        elif type(message) is types.CallbackQuery:
            callback_actions = {button.text: button.callback_data for row in message.message.reply_markup.inline_keyboard for button in row if hasattr(button, 'text') and hasattr(button, 'callback_data')}
            selectedguid = message.data
            for guid in callback_actions.values():
                data, handler = Callback.ReadCallback(guid)
                if guid == selectedguid:
                    deletelist = data['deletelist']
                Callback.DestroyCallback(bot, guid, handler)
            if selectedguid == callback_actions['Delete Messages']:
                deletelist.append(message.message.id)
                try:
                    bot.delete_messages(message.message.chat.id, deletelist)
                except Exception as e:
                    bot.send_message(message.message.chat.id, f"We failed to delete the following messages:\n{deletelist}\nThis was the issue: {e}")
            else:
                deletelist.clear()
                deletelist.append(message.message.id)
                bot.delete_messages(message.message.chat.id, deletelist)
            return
        
     # Delete original message   
        bot.delete_messages(message.chat.id, message.id)

     # Return if not admin
        if not Handlers.is_admin(bot, message.chat.id, message.from_user.id):
            bot.delete_messages(message.chat.id, message.id)
            return

     # Create argparse and overwrite
        parser = ArgumentParser(description='Delete messages in this group')

        helpdialog = textwrap.dedent(
        """
        **Delete Messages in This Group**

        To delete a target message, reply to the message with command: `/del 1`.

        **Commands**

        `/del` [-h | help] 
        Display the __Help Dialog__.

        `/del number` (when not replying to a message)
        Delete the specified number of messages above.

        `/del` (when replying to a message)
        Delete all messages up to and including the replied message.

        `/del number` (when replying to a message)
        Delete the specified number of messages after, including the replied message.

        **Arguments**

        --Positional Arguments:--
        `number`  
        The number of messages to delete.

        --Optional Arguments:--
        `-h`, `--help`  
        Show the help message.
        """)
        parser.add_argument('number', type=int, nargs='?', default=None, help='The number of messages to delete')
        command = message.text.split()
        try:
            args = parser.parse_args(command[1:])
        except Exception as e:
            bot.send_message(message.chat.id, f"Invalid Argument\n{helpdialog}")
            return

     # If no reply and no number
        if not message.reply_to_message and args.number is None:
            bot.send_message(message.chat.id, helpdialog)
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
                    if sanitycheck == 1000:
                        # TODO - Benchmark the sanity check to ensure we aren't waiting too long
                        break
                    targetmessageid -= 1
                    currentmessageid -= 1
                    continue
                deletelist.append(currentmessageid)
                sanitycheck = 0
                currentmessageid -= 1

     # If has reply and no number
        if message.reply_to_message and args.number is None:
            currentmessageid = message.id
            while currentmessageid >= message.reply_to_message.id:
                currentmessage = bot.get_messages(message.chat.id, currentmessageid)
                if currentmessage.empty: # We need to do this since we're appending messages to a list and providing a number to the user
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
                    if sanitycheck == 100:
                        break
                    targetmessageid -= 1
                    currentmessageid -= 1
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
        threading.Thread(target=Handlers.messagesweepcleanup, args=(bot, statusmessage, guiddelete, guidcancel)).start()

    # Cleanup for messagesweep
    def messagesweepcleanup(bot, statusmessage, guiddelete, guidcancel):
        """Cleanup after Callback is made
        This is added in a new function for threading purposes

        Args:
            bot (Class): The Bot
            statusmessage (message): The Message the bot is using to facilitate the original method
            guiddelete (Str guid): The Delete Callback trigger
            guidcancel (Str guid): The Cancel Callback trigger
        """
        time.sleep(30)
        with handler_lock:
            manager = HandlerManager()
            handlerdelete = manager.get_handler(guiddelete)
            handlercancel = manager.get_handler(guidcancel)
            if handlerdelete:
                Callback.DestroyCallback(bot, guiddelete, handlerdelete)
                Callback.DestroyCallback(bot, guidcancel, handlercancel)
            bot.delete_messages(statusmessage.chat.id, statusmessage.id)

  # is_admin =====================================================================================
    def is_admin(bot, chatid, userid):
        """Check if a user in a chat is an admin/owner

        Args:
            bot (Class): The Bot
            chatid (Int): Chat Unique Identifier
            userid (int): User Unique Identifier

        Returns:
            Bool: True/False
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
        """Show a user's ID

        Args:
            bot (Class): The Bot
            message (message): The message
        """

      # Create argparse
        parser = ArgumentParser(description='Returns the Unique identifier')

        helpdialog = textwrap.dedent(
        """
        **Show Unique IDs for users and chats**

        **Commands**

        `/id` [-h | help] 
        Display the __Help Dialog__.

        `/id`
        Show your own ID

        `/id @user`
        Show the ID of the user you mentioned

        `/id` (when replying to a message)
        Show the ID of the user you replied to

        `/id -c`
        Show the current chat's ID.

        `/id -m` (when replying to a message)
        Show the ID of the message you're replying to

        **Arguments**

        --Optional Arguments:--
        `-h`, `--help`  
        Show the help message.

        `-c`, `--chat`
        Show that chat's ID

        `-m`, `--message`
        Show the message ID, Requires that you're replying the message
        """)
        parser.add_argument('username', type=str, nargs='?', default=None, help='User to get the ID of')
        parser.add_argument('-c', action='store_true', help='get the chats ID')
        parser.add_argument('-m', action='store_true', help='Get the message ID')
        command = message.text.split()
        try:
            args = parser.parse_args(command[1:])
        except Exception as e:
            bot.send_message(message.chat.id, f"Invalid Argument\n{helpdialog}")

      # Delete the original command
        bot.delete_messages(message.chat.id, message.id)

      # Getting the chat ID
        if args.c:
            bot.send_message(message.chat.id, message.chat.id)
            return

      # Getting your own id
        if not message.reply_to_message and args.username is None:
            bot.send_message(message.chat.id, message.from_user.id)
            return
      
      # Getting id from reply
        if message.reply_to_message and args.username is None:
            bot.send_message(message.chat.id, message.reply_to_message.from_user.get_user_id)
            return
        
        if message.reply_to_message and args.m is not None:
            bot.send_message(message.chat.id, message.reply_to_message.id)

      # Getting id from mention/text mention  
        if not message.reply_to_message and args.username is not None:
            if message.mentioned == True:
                user = bot.get_users(args.username)
            elif next((obj for obj in message.entities if obj.type == enums.MessageEntityType.TEXT_MENTION),None):
                text_mention = next((obj for obj in message.entities if obj.type == enums.MessageEntityType.TEXT_MENTION),None)
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

