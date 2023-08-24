from pyrogram import enums
class Methods():
    def __init__(self):
        pass
    
  # is_admin ========================================================================================
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