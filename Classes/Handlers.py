import sqlite3, os, logging, time, threading, textwrap, re, jurigged # Threading is here so callback cleanups don't have issues handling 2 threads
from pyrogram import filters, enums, types
from pyrogram.errors import FloodWait, MessageDeleteForbidden
from Classes.Keyboard import Keyboard
from Classes.ArgparseOverride import ArgumentParser
from Classes.HandlerManager import HandlerManager
from Classes.Methods import Methods

# These globals are volatile and unimportant. 
# They are only modified in the allmessages handler

lastupdate = {}
lastfilterupdate = {}
handler_lock = threading.Lock()
update_lock = threading.Lock()

class Handlers():

    def __init__(self):
        pass
    
  # Message Sweep ===================================================================================
    def messagesweep(bot, message):
        """Deletes Messages

        Args:
            bot (Class): The Bot
            message (message | CallbackQuery): The contents being sent via Handler
        """
        Handler_Manager = HandlerManager()
     # Handle CallbackQueries
        if type(message) is types.CallbackQuery and not Methods.is_admin(bot, message):
            return
        elif type(message) is types.CallbackQuery:
            callback_actions = {button.text: button.callback_data for row in message.message.reply_markup.inline_keyboard for button in row if hasattr(button, 'text') and hasattr(button, 'callback_data')}
            selectedguid = message.data
            for guid in callback_actions.values():
                data, handler = Handler_Manager.ReadCallback(guid)
                if guid == selectedguid:
                    deletelist = data['deletelist']
                Handler_Manager.DestroyCallback(bot, guid, handler)
            if selectedguid == callback_actions['Delete Messages']:
                bot.delete_messages(message.message.chat.id, message.message.id)
                try:
                    bot.delete_messages(message.message.chat.id, deletelist)
                except MessageDeleteForbidden as e:
                    sections = [deletelist[i:i + 10] for i in range(0, len(deletelist), 10)]
                    for section in sections:
                        try:
                            bot.delete_messages(message.message.chat.id, section)
                        except MessageDeleteForbidden as e:
                            for msgid in section:
                                try:
                                    bot.delete_messages(message.message.chat.id, msgid)
                                except MessageDeleteForbidden as e:
                                    bot.send_message(message.message.chat.id, "We have deleted everything we can that Telegram will let us")
                                    break
                            break
                    bot.send_message(message.message.chat.id, f"The Messages are too old to delete")
                except Exception as e:
                    bot.send_message(message.message.chat.id, f"We failed to delete the following messages for an unknown reasdon:\n{deletelist}\nThis was the issue: {e}")

            else:
                deletelist.clear()
                deletelist.append(message.message.id)
                bot.delete_messages(message.message.chat.id, deletelist)
            return
        
     # Delete original message   
        bot.delete_messages(message.chat.id, message.id)

     # Return if not admin
        if not Methods.is_admin(bot, message):
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
        guiddelete = Handler_Manager.CreateCallback(bot, Handlers.messagesweep, deletelist=deletelist)
        guidcancel = Handler_Manager.CreateCallback(bot, Handlers.messagesweep, deletelist=deletelist)
        Delete = Keyboard.create_button(text="Delete Messages",callback_data=guiddelete)
        Cancel = Keyboard.create_button(text="Cancel Operation",callback_data=guidcancel)
        keyboard = Keyboard.create_keyboard(Delete, Cancel)
        bot.edit_message_text(statusmessage.chat.id, statusmessage.id, f"Confirm deleting {len(deletelist)} messages", reply_markup=keyboard)        
        threading.Thread(target=Handlers.messagesweepcleanup, args=(bot, statusmessage, guiddelete, guidcancel)).start()
    messagesweep.filter = filters.command(["del","d","delete"])

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
        time.sleep(10)
        with handler_lock:
            Handler_Manager = HandlerManager()
            handlerdelete = Handler_Manager.get_handler(guiddelete)
            handlercancel = Handler_Manager.get_handler(guidcancel)
            if handlerdelete:
                Handler_Manager.DestroyCallback(bot, guiddelete, handlerdelete)
                Handler_Manager.DestroyCallback(bot, guidcancel, handlercancel)
            bot.delete_messages(statusmessage.chat.id, statusmessage.id)

  # Ban users =======================================================================================
    def ban_user(bot, message):
      # Delete command
        bot.delete_messages(message.chat.id, message.id)
        
      # Check if admin
        if not Methods.is_admin(bot, message):
            return

      # Create argparse
        parser = ArgumentParser(description='Bans a user')
        helpdialog = textwrap.dedent(
            """
            **Ban users**

            **Commands**

            `/ban` [-h | help] 
            Display the __Help Dialog__.

            `/ban` [username | id]
            Ban the user

            `/ban` [username | id] `-r`
            Provides a reason

            `/ban` [username | id] `-g`
            Ban the user globally (Everywhere you admin)

            `/ban` [username | id] `-u`
            Ban the user in universe (Everywhere Vampyre is in)
            """
            )
        parser.add_argument('username', type=str, nargs='?', default=None, help='User to get the ID of')
        #parser.add_argument('-g', action='store_true', help='Ban Globally (all chats you admin in) - Only works if Vampyre is in the group')
        #parser.add_argument('-u', action='store_true', help='Ban in Universe (all chats Vampyre is in) - Only the owners of the bot can do this')
        parser.add_argument('-r', nargs='*', help='get or set ban reason')
        parser.add_argument('-d', action='store_true')
        command = message.text.split()
        try:
            args = parser.parse_args(command[1:])
        except Exception as e:
            bot.send_message(message.chat.id, f"Invalid Argument\n{helpdialog}")

      # quit if theres no username
        if args.username is None:
            bot.send_message(message.chat.id, helpdialog)
            return

      # get id/chatmember object of the user
        userid = Methods.get_id_from_mention(bot, message, args.username)
        chatmember = bot.get_chat_member(message.chat.id, userid)
        
      # If we couldn't get the id
        if not userid:
            bot.send_message(message.chat.id, "User evaded ban :(")  
            return

      # Banning user flow - TODO - Implement Global/Universal logic
       # Dry Run banning
        if not chatmember.restricted_by and args.d:
                bot.send_message(message.chat.id, f"Bang! they got banned. (just kiddin this time)")
                ban_state = True

       # Actual banning
        elif not chatmember.restricted_by:
            try:
                #bot.ban_chat_member(message.chat.id, userid)
                ban_state = True
            except Exception as e:
                bot.send_message(message.chat.id, f"Failed to ban user: {e}") # TODO - if failed, try to restrict user permissions
                return

       # Already banned
        elif chatmember.restricted_by:
            bot.send_message(message.chat.id, f"This user is already banned")
            ban_state = None

      # Reason storing flow
        if args.r:
            reason = ' '.join(args.r)
           # banned in dryrun
            if ban_state and args.d:
                bot.send_message(message.chat.id, f"Provided reason: {reason}")
           # banned
            elif ban_state:
                bot.update_ban_reason(message.chat.id, userid, reason)
                bot.send_message(message.chat.id, f"Reason: {reason}")
            else:
                reason = bot.get_ban_reason(chatid, userid)
                bot.send_message(message.chat.id, {f"Reason: {reason}"})

    ban_user.filter = filters.command(["ban", "b"])

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
            bot.send_message(message.chat.id, f"Chat ID: {message.chat.id}", parse_mode=enums.ParseMode.DISABLED)
            return

      # Getting your own id
        if not message.reply_to_message and args.username is None:
            bot.send_message(message.chat.id, f"Your ID: {message.from_user.id}", parse_mode=enums.ParseMode.DISABLED)
            return
        
      # Getting the message ID
        if message.reply_to_message and args.m is not None:
            bot.send_message(message.chat.id, f"Message ID: {message.reply_to_message.id}", parse_mode=enums.ParseMode.DISABLED)
            return
        
      # Getting id from reply
        if message.reply_to_message and args.username is None:
            bot.send_message(message.chat.id, f"Users's ID: {message.reply_to_message.from_user.id}", parse_mode=enums.ParseMode.DISABLED)
            return

        if not message.reply_to_message and args.username is not None:
            userid = Methods.get_id_from_mention(bot, message, args.username)
            if userid:
                bot.send_message(message.chat.id, f"User's ID: {userid}")
            else: # TODO - refactor resolver to use an expensive search if all else fails
                bot.send_message(message.chat.id, "Could not get user's ID")
    get_user_id.filter = filters.command(["id", "i", "getid"])

  # Reload handlers =================================================================================
    def reload_handlers(bot, message):
       # Delete original message
        bot.delete_messages(message.chat.id, message.id)

       # Check if user is owner
        if not Methods.is_owner(bot, message):
            bot.logger.debug(f"User: type: {message.from_user.id} Owner: type: {bot.bot_owner}" )
            return
        
       # Unload and reload handlers/filters
        bot.logger.info("Reloading Handlers/Filters")
        Handler_Manager = HandlerManager()
        with handler_lock:
            Handler_Manager.unload_handlers(bot)
            Handler_Manager.load_handlers(bot)
            Handler_Manager.unload_filters(bot)
            Handler_Manager.load_filters(bot)
        bot.send_message(message.chat.id, "Handlers/Filters reloaded")
    reload_handlers.filter = filters.command(["r","rb","restart"])

  # Change logging level ============================================================================
    def log_adjust(bot, message):
       # Delete original message
        bot.delete_messages(message.chat.id, message.id)

       # Check if owner
        if not Methods.is_owner(bot, message):
            return

       # create argparse
        parser = ArgumentParser(description='Adjust the logging level in the bot')
        helpdialog = textwrap.dedent(
            """
            **Set the logging level**
            **Examples**
            
            `/log -gfsd`
            Reset all logging to debug

            `/log -fsi`
            Set file and stdout logs to info

            **Commands**

            `/log` [-h | help] 
            Display the __Help Dialog__.

            `/log -c`
            Sets the logging level to CRITICAL

            `/log -w`
            Sets the logging level to WARNING

            `/log -e`
            Sets the logging level to ERROR

            `/log -i`
            Sets the logging level to INFO

            `/log -d`
            Sets the logging level to DEBUG

            `/log -f`
            Sets the logging level For the log file

            `/log -s`
            Sets the logging level for Stdout

            `/log -t`
            Sends a test of the logs available and sends a message of the current level
            """)
        parser.add_argument('-c', action='store_true', help='CRITICAL')
        parser.add_argument('-w', action='store_true', help='WARNING')
        parser.add_argument('-e', action='store_true', help='ERROR')
        parser.add_argument('-i', action='store_true', help='INFO')
        parser.add_argument('-d', action='store_true', help='DEBUG')
        parser.add_argument('-f', action='store_true', help='Sets Filehandler Level')
        parser.add_argument('-s', action='store_true', help='Sets stdout Level')
        parser.add_argument('-g', action='store_true', help='Sets the global log level')
        parser.add_argument('-t', action='store_true', help='Test the log')
        command = message.text.split()
        try:
            args = parser.parse_args(command[1:])
        except Exception as e:
            bot.send_message(message.chat.id, f"Invalid Argument\n{helpdialog}")
       
       # Test logging level
        if args.t:
            bot.logger.critical("critical")
            bot.logger.warning("warning")
            bot.logger.error("error")
            bot.logger.info("info")
            bot.logger.debug("debug")
            return

       # Stdout level
        if args.s:
            if args.c:
                bot.stdout_handler.setLevel(logging.CRITICAL)
                bot.send_message(message.chat.id,"Logging set to critical")
            elif args.w:
                bot.stdout_handler.setLevel(logging.WARNING)
                bot.send_message(message.chat.id,"Logging set to warning")
            elif args.e:
                bot.stdout_handler.setLevel(logging.ERROR)
                bot.send_message(message.chat.id,"Logging set to error")
            elif args.i:
                bot.stdout_handler.setLevel(logging.INFO)
                bot.send_message(message.chat.id,"Logging set to info")
            elif args.d:
                bot.stdout_handler.setLevel(logging.DEBUG)
                bot.send_message(message.chat.id,"Logging set to debug")
            else:
                bot.send_message(message.chat.id,message.chat.id, helpdialog)
      
       # File level
        if args.f:
            if args.c:
                bot.file_handler.setLevel(logging.CRITICAL)
                bot.send_message(message.chat.id,"Logging set to critical")
            elif args.w:
                bot.file_handler.setLevel(logging.WARNING)
                bot.send_message(message.chat.id,"Logging set to warning")
            elif args.e:
                bot.file_handler.setLevel(logging.ERROR)
                bot.send_message(message.chat.id,"Logging set to error")
            elif args.i:
                bot.file_handler.setLevel(logging.INFO)
                bot.send_message(message.chat.id,"Logging set to info")
            elif args.d:
                bot.file_handler.setLevel(logging.DEBUG)
                bot.send_message(message.chat.id,"Logging set to debug")
            else:
                bot.send_message(message.chat.id,message.chat.id, helpdialog)
       
       # Global level
        if args.g:
            if args.c:
                bot.logger.setLevel(logging.CRITICAL)
                bot.send_message(message.chat.id,"Logging set to critical")
            elif args.w:
                bot.logger.setLevel(logging.WARNING)
                bot.send_message(message.chat.id,"Logging set to warning")
            elif args.e:
                bot.logger.setLevel(logging.ERROR)
                bot.send_message(message.chat.id,"Logging set to error")
            elif args.i:
                bot.logger.setLevel(logging.INFO)
                bot.send_message(message.chat.id,"Logging set to info")
            elif args.d:
                bot.logger.setLevel(logging.DEBUG)
                bot.send_message(message.chat.id,"Logging set to debug")
            else:
                bot.send_message(message.chat.id,message.chat.id, helpdialog)

    log_adjust.filter = filters.command(["log", "l"])

  # test handler ====================================================================================
    def test_handler(bot, message):
        pass
    #test_handler.filter = filters.command(["t", "test"])

  # allmessages =====================================================================================
    
    # NOTE You can't merge these, the objects are not the same

    def all_messages(bot, message):
        bot.logger.debug(f"Running update: {message}")
        with update_lock:
            Handler_Manager = HandlerManager()
            global lastupdate
            now = int(time.time())

            # updatin last message
            bot.logger.debug("Updating chat membership")
            bot.update_lastmessage(message.chat.id, message.from_user.id, int(time.time()))
            
            # update user info
            if now - lastupdate.get(message.from_user.id, 0) > 300:
                bot.update_user(message.chat.id, message.from_user.id, message=message)
                lastupdate.update({message.from_user.id: now})

            # update chat info
            if now - lastupdate.get(message.chat.id, 0) > 300:
                bot.logger.debug("updating chat")
                bot.update_chat(message.chat.id)
                lastupdate.update({message.chat.id: now})

            # update user index
            bot.update_users(message.chat.id)

    def all_chatmemberupdates(bot, ChatMemberUpdated):
        bot.logger.debug(f"Running update: {ChatMemberUpdated}")
        with update_lock:
            Handler_Manager = HandlerManager()
            global lastupdate
            global lastusersindex
            now = int(time.time())

            # update user info
            if now - lastupdate.get(ChatMemberUpdated.from_user.id, 0) > 300:
                bot.update_user(ChatMemberUpdated.chat.id, ChatMemberUpdated.from_user.id)
                lastupdate.update({ChatMemberUpdated.from_user.id: now})

            # update chat info
            if now - lastupdate.get(ChatMemberUpdated.chat.id, 0) > 300:
                bot.update_chat(ChatMemberUpdated.chat.id)
                lastupdate.update({ChatMemberUpdated.chat.id: now})

            # update chat memberships
            if now - lastupdate.get(ChatMemberUpdated.chat.id, 0) > 300:
                bot.instantiate_chat_membership(ChatMemberUpdated.chat.id, ChatMemberUpdated.from_user.id)
                lastupdate.update({ChatMemberUpdated.chat.id: now})
