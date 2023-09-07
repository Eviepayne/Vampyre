from pyrogram import enums
from pyrogram.errors import FloodWait, UserNotParticipant
import logging

class Methods():
    def __init__(self):
        pass

  # Is_banned
    def is_banned(bot, chatid, userid):
        """Returns ban status

            Args:
                bot (Client): Bot
                chatid (int): chatid
                userid (int): userid

            Returns:
                bool: If the user is banned or not
            """
        try:
            chatmember = bot.get_chat_member(chatid, userid)
        # If user not here, they aren't removed. ban them
        except UserNotParticipant as e:
            return False
        except Exception as e:
            bot.logger.error(f"Could not get chatmember object during ban_user() | Reason: {e}")
        if chatmember.restricted_by:
            return True

  # Create username
    def create_username(user):
        if user.username:
            return user.username
        name=""
        if user.first_name:
            name = name + user.first_name
        if user.last_name:
            name = name + user.last_name
        return name

  # is_admin ========================================================================================
    def is_admin(bot, message): # TODO - replace all instances of this with is_admin_of_chat
        logger = logging.getLogger("Vampyre.is_admin")

        if Methods.is_owner(bot, message.from_user.id):
            return True

        logger.debug(f"Message.from_user.id: {message.from_user.id}")

        try:
            logger.debug(f"Getting chatmember object")
            ChatMember = bot.get_chat_member(message.chat.id, message.from_user.id)

        except UserNotParticipant as e:
            return False

        except Exception as e:
            bot.logger.error(f"Could not get chatmember object while is_admin(bot, message). Reason: {e}")
            return False

        if ChatMember.status == enums.ChatMemberStatus.ADMINISTRATOR or ChatMember.status == enums.ChatMemberStatus.OWNER:
            logger.debug("User is admin")
            return True

        logger.debug("User is not admin")

    def is_admin_of_chat(bot, message, chatid, userid):
        bot.logger.info("is_admin_of_chat")

        if Methods.is_owner(bot, userid):
            return True

        logger.debug(f"userid: {userid}")

        try:
            logger.debug(f"Getting chatmember object")
            ChatMember = bot.get_chat_member(chatid, userid)

        except UserNotParticipant as e:
            return False

        except Exception as e:
            bot.logger.error(f"Could not get chatmember object while is_admin_of_chat(bot, message, chatid, userid). Reason: {e}")
            return False

        if ChatMember.status == enums.ChatMemberStatus.ADMINISTRATOR or ChatMember.status == enums.ChatMemberStatus.OWNER:
            logger.debug("User is admin")
            return True

  # is_owner ========================================================================================
    # def is_owner(bot, message):
    #     logger = logging.getLogger("Vampyre.is_owner")
    #     logger.debug(f"Message.from_user.id: {message.from_user.id} bot.owner:{bot.bot_owner}")
    #     if str(message.from_user.id) == bot.bot_owner:
    #         logger.debug(f"User is owner")
    #         return True
    #     logger.debug(f"User is not owner")
    
#===============================================================
# is_owner 

    def is_owner(bot, userid):
        bot.logger.info("is_owner")
        bot.logger.debug(f"bot.owner:{bot.bot_owner}")
        if str(userid) == str(bot.bot_owner):
            bot.logger.info(f"User is owner")
            return True
        bot.logger.info(f"User is not owner")

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
        bot.logger.info("get_id_from_mention")
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
