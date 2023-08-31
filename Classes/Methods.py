from pyrogram import enums, errors
import logging
class Methods():
    def __init__(self):
        pass
    
  # is_admin ========================================================================================
    def is_admin(bot, message):
        """Check if a user in a chat is an admin/owner

        Args:
            bot (Class): The Bot
            chatid (Int): Chat Unique Identifier
            userid (int): User Unique Identifier

        Returns:
            Bool: True/False
        """
        logger = logging.getLogger("Vampyre.is_admin")
        if Methods.is_owner(bot, message):
            return True
        logger.debug(f"Message.from_user.id: {message.from_user.id}")
        try:
            logger.debug(f"Getting chatmember object")
            ChatMember = bot.get_chat_member(message.chat.id, message.from_user.id)
        except Exception as e: # TODO - Properly handle floods if we trigger any
            send_message(chatid, "We are being rate limited. Try again later.")
            return False
        
        if ChatMember.status == enums.ChatMemberStatus.ADMINISTRATOR or ChatMember.status == enums.ChatMemberStatus.OWNER:
            logger.debug("User is admin")
            return True
        logger.debug("User is not admin")

  # is_owner ========================================================================================
    def is_owner(bot, message):
        logger = logging.getLogger("Vampyre.is_owner")
        logger.debug(f"Message.from_user.id: {message.from_user.id} bot.owner:{bot.bot_owner}")
        if str(message.from_user.id) == bot.bot_owner:
            logger.debug(f"User is owner")
            return True
        logger.debug(f"User is not owner")

  # username_to_id ==================================================================================
    def get_id_from_mention(bot, message, username=None):
        """Returns an id from text that contains a username
        If theres a mention, text_mention or just a string of the username, it returns the id

        Args:
            bot (bot): bot
            username (string): username of the user
            message (message): message

        Returns:
            int: id
            bool: False
        """
        # Try to get mention or text_mention
        text_mention = next((obj for obj in message.entities if obj.type == enums.MessageEntityType.TEXT_MENTION),None)
        if text_mention:
            return text_mention.user.id
        elif username is not None:
            try:
                user = bot.get_users(username)
                return user.id
            except Exception as e:
                return False
        else:
            return False
