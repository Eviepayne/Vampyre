from bot_utilities import trusted, texttype, sql, getname, getuser, admin, getid
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.handlers import MessageHandler
from pyrogram.errors import FloodWait
from pyrogram import filters
import os, time, re, json, multiprocessing

## Load globals
limbolist = {}

## Load methods
def limbo(bot, message):
    print("Limbo triggered")
    message.stop_propagation()

def filtermsg(bot, message):
    if trusted(bot, message):
        return
    x = sql(f"SELECT keywords FROM [{message.chat.id}] WHERE id = 'chat_settings'")
    importjson = json.loads(x[0][0])
    for i in importjson:
        if not bool(i[3]):
            continue
        pattern = re.compile(fr"{i[1]}")
        matches = pattern.finditer(texttype(bot,message))
        for match in matches:
            if match:
                filteractions(bot, message, i[2], i[0])
                return

def filteractions(bot, message, actions, name):
    #bot.send_message(message.chat.id, "Filter executed")
    if "bait" in actions:
        x = sql(f"SELECT isbait FROM universe WHERE id = {message.from_user.id}")
        try:
            if bool(x[0][0]):
                return
            else:
                raise Exception
        except:
            print(f"Failed to ban user")
    if "delete" in actions:
        deletemessage(bot, message, message.chat.id, message.message_id)
    if "ban" in actions:
        bot.kick_chat_member(message.chat.id, message.from_user.id)
    if "untrust" in actions:
        sql(f"INSERT OR REPLACE INTO [{message.chat.id}] (id, istrusted) VALUES ({message.from_user.id},0)", mode="INSERT")
    if "trust" in actions:
        sql(f"INSERT OR REPLACE INTO [{message.chat.id}] (id, istrusted) VALUES ({message.from_user.id},1)", mode="INSERT")
    if "warn" in actions:
        print("Warned user (placeholder for when this is implemented)")
    if "message" in actions:
        username = re.compile(r"(?i)(\%name)")
        newmsg = re.sub(username, getname(bot,message),actions['message'])
        bot.send_message(message.chat.id, newmsg)
    if "notify" in actions:
        actionlog(bot, message, name, mode="Admins")

def ban(bot,message,chat, msg=None):
    if len(message.entities) < 1:
        ID = msg[1] if msg is not None else message.text.split(r" ")[1]
    elif len(message.entities) >= 2:
        ID = getid(bot, message)
    else:
        msgadmins(bot, message, f"Something went wrong. The log was sent to Vlad")
        msgowners(bot, message, f"Vlad you fucking spastic you fucked up.\nHere's the entities in attempted ban:\n{message.entities}")
        return
    bot.kick_chat_member(chat, ID)
    try:
        notif = ' '.join(msg[2:])
    except:
        notif = ' '.join(message.text.split(' ')[2:])
    bot.send_message(chat, f"User: {getname(bot, message, ID)} has been banned\nReason: {notif}")
    actionlog(bot,message, "Banned user:")

def deletemessage(bot, message, chatid, msgid):
    try:
        bot.delete_messages(chatid, msgid)
    except:
        msgowners(bot,message, f"Failed to delete message:\n{message.chat.title} | {message.chat.id}\nMessage: {texttype(bot, message)}")

def allowedchannels(bot, message):
    x = sql(f"SELECT chatauth,chatunauth FROM universe WHERE id = {message.chat.id}")
    if x == []:
        reply_markup=InlineKeyboardMarkup(
            [
                [
                InlineKeyboardButton("Request", callback_data="request"),
                InlineKeyboardButton("Cancel", callback_data="cancel")
                ]
            ])
        sql(f"INSERT OR REPLACE INTO universe (id,limbo) VALUES ({message.chat.id},1)", mode="INSERT")
        limbohandler = bot.add_handler(MessageHandler(limbo,filters.all & filters.chat(message.chat.id)),group=-2)
        limbolist[f"{message.chat.id}"]=limbohandler
        msg = bot.send_message(message.chat.id, f"Hi, I don't recognize this chat. To use this bot you can make a request to the owner.", reply_markup=reply_markup)
    try:
        if bool(x[0][0]):
            return
        bot.send_message(message.chat.id, "Sorry this chat is unauthorized")
        bot.leave_chat(message.chat.id)
    except:
        pass
    #     print(x)
    #     print("Chat is unauthorized")
        # def wait_for_response():
        #     time.sleep(30)
        #     bot.send_message(message.chat.id, "Sorry ran out of time to respond. Leaving...")
        #     bot.leave_chat(message.chat.id)
        # p = multiprocessing.Process(target=wait_for_response)
        # limbolist[f"{message.chat.id}"]=p
        # p.start()
        # p.join()
        # bot.send_message(message.chat.id, f"This chat is unauthorized to use this bot.\nShould you want to use this bot, you can host it yourself.\nDetails are not yet public, but will be eventually.\n\nYou can reach out to @VladTheImplier for more info.\nYour chat Id is: {message.chat.id}")
        # bot.leave_chat(message.chat.id)
        # msgowners(bot, message, f"left the chat: {message.chat.title}")
        # re-enable once systemd integration is done
        # print(f"Leaving chat...\nTitle: {message.chat.title}", end=" | ")
        # print(f"Id: {message.chat.id}\n==================================")

def sendimg(bot, message, caption=None):
    file = bot.download_media(message.photo['file_id'])
    try:
        with open(file, 'rb') as f:
            bot.send_photo(message.chat.id, f, caption=caption)
    except FloodWait as e:
        print(f"Ratelimit!! Waiting {e.x} seconds")
        time.sleep(e.x)
        msg = bot.send_message(message.chat.id, "We got ratelimited. Image failed to send.")
        time.sleep(10)
        deletemessage(bot, message, message.chat.id, msg.message_id)
    finally:
        os.remove(file)

def sendvid(bot, message, caption=None):
    file = bot.download_media(message.video['file_id'])
    try:
        with open(file, 'rb') as f:
            bot.send_video(message.chat.id, f, caption=caption)
    except FloodWait as e:
        print(f"Ratelimit!! Waiting {e.x} seconds")
        time.sleep(e.x)
        msg = bot.send_message(message.chat.id, "We got ratelimited. Video failed to send.")
        time.sleep(10)
        deletemessage(bot, message, message.chat.id, msg.message_id)
    finally:
        os.remove(file)

def actionlog(bot, message, name, mode=None):
    msg = f"{name}\nChat: {message.chat.title} | id: {message.chat.id}\nuser: {getname(bot, message)} | id: {getuser(bot, message).id}\nMessage: {texttype(bot, message)}"
    ## uncomment this here once bot has systemd integration
    #print(msg)
    if mode == "Owners":
        msgowners(bot, message, msg)
    if mode == "Admins":
        msgadmins(bot, message, msg)
    return msg

def msgowners(bot,message, msg, reply_markup=None):
    x = sql("SELECT id FROM universe WHERE isowner = 1")
    for i in x[0]:
        bot.send_message(i, msg, reply_markup=reply_markup)

def msgadmins(bot,message, msg):
    for i in bot.get_chat_members(message.chat.id,filter="administrators"):
        if i['user']['is_bot'] is False:
            try:
                bot.send_message(i['user']['id'], msg)
            except:
                print("We tried to DM an admin but it failed.")