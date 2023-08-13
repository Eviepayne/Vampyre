from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import enums
import sqlite3

# def entities(filter, bot, message, **types): To be added later
    # if types is None and message.entities > 0:
    #     return True
    # if "mention" in types and "mention" in message.entities:
    #     return True
    # if "hashtag" in types and "hashtag" in message.entities:
    #     return True
    # if "cashtag" in types and "cashtag" in message.entities:
    #     return True
    # if "bot_command" in types and "bot_command" in message.entities:
    #     return True
    # if "url" in types and "url" in message.entities:
    #     return True
    # if "email" in types and "email" in message.entities:
    #     return True
    # if "phone_number" in types and "phone_number" in message.entities:
    #     return True
    # if "bold" in types and "bold" in message.entities:
    #     return True
    # if "italic" in types and "italic" in message.entities:
    #     return True
    # if "underline" in types and "underline" in message.entities:
    #     return True
    # if "strikethrough" in types and "strikethrough" in message.entities:
    #     return True
    # if "code" in types and "code" in message.entities:
    #     return True
    # if "pre" in types and "pre" in message.entities:
    #     return True
    # if "text_link" in types and "text_link" in message.entities:
    #     return True
    # if "text_mention" in types and "text_mention" in message.entities:
    #     return True
    # return False

def sql(query, mode=None):
    d = sqlite3.connect("vampyre.db")
    c = d.cursor()
    c.execute(query)
    if mode is None:
        output = c.fetchall()
    if mode == "INSERT":
        d.commit()
    c.close()
    d.close()
    if mode == None:
        return output

def trusted(bot, message):
    if owner(bot,message):
        return True
    if admin(bot, message):
        return True
    x = sql(f"SELECT istrusted FROM [{message.chat.id}] WHERE id = {message.from_user.id}")
    try:
        if bool(x[0][0]):
            return True
    except:
        print("Trusted failed")

def admin(bot, message, chat=None):
    if chat is None:
        chat = message.chat.id

    for i in bot.get_chat_members(chat,filter=enums.ChatMembersFilter.ADMINISTRATORS):
        if i.user == message.from_user:
            return True


    # for i in bot.get_chat_members(chat,filter=enums.ChatMembersFilter.ADMINISTRATORS):
    #     print(i)
    #     if i.status in [enums.ChatMembersFilter.ADMINISTRATORS] and i.user.id == message.from_user.id:
    #         return True

    return owner(bot, message)

def getuser(bot, message, ID=None):
    if ID is None:
        return bot.get_chat_member(message.chat.id, message.from_user.id).user
    else:
        return bot.get_chat_member(message.chat.id, ID).user

def getusermember(bot, message, ID=None):
    if ID is None:
        return bot.get_chat_member(message.chat.id, message.from_user.id)
    else:
        return bot.get_chat_member(message.chat.id, ID)

def getchats(bot):
    x = sql("SELECT id FROM universe WHERE id LIKE '-%'")
    a = []
    for i in x:
        try:
            a.append(i[0])
        except:
            print("Chat object could not be returned")
    return a

def getid(bot, message):
    for i in message.entities:
        if i.type == "text_mention":
            return i.user.id
        elif i.type == "mention":
            return bot.get_users(message.text.split(r" ")[1]).id
        elif i.type == "phone_number":
            return message.text.split(r" ")[1]

def texttype(bot, message):
    if message.text is None:
        return message.caption
    else:
        return message.text

def getname(bot, message, ID=None):
    if getuser(bot, message, ID).username is not None:
        return f"@{getuser(bot, message, ID).username}"
    if getuser(bot, message, ID).last_name is None:
        return f"{getuser(bot, message, ID).first_name}"
    else:
        return f"{getuser(bot, message, ID).first_name} {getuser(bot, message, ID).last_name}"

def owners(bot, message):
    owners = []
    x = sql(f"SELECT isowner FROM universe")
    for i in x[0]:
        owners.append[i]
    return owners

def owner(bot, message):
    x = sql(f"SELECT isowner FROM universe WHERE id = {message.from_user.id}")
    try:
        if bool(x[0][0]):
            return True
    except:
        pass

def chatsadmined(bot,message):
    chats = getchats(bot)
    return [chat for chat in chats if admin(bot,message, chat)]