from pyrogram import enums
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
        if Methods.is_owner(bot, message):
            return True

        try:
            ChatMember = bot.get_chat_member(message.chat.id, message.chat.from_user.id)

        except errors.FloodWait as e:
            bot.send_message(chatid, "We are being rate limited. Please wait.")
            return False
        
        if ChatMember.status == enums.ChatMemberStatus.ADMINISTRATOR or ChatMember.status == enums.ChatMemberStatus.OWNER:
            return True

  # is_owner ========================================================================================
    def is_owner(bot, message):
        logger = logging.getLogger("Vampyre.is_owner")
        logger.debug(f"Message.from_user.id: {message.from_user.id} bot.owner:{bot.bot_owner}")
        if str(message.from_user.id) == bot.bot_owner:
            logger.debug(f"User is owner")
            return True