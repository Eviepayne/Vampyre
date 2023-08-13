from bot_utilities import trusted, getname, getuser, texttype, admin, owner, sql, getid, getchats, chatsadmined
from bot_actions import filtermsg, allowedchannels, sendimg, sendvid, deletemessage, actionlog, msgowners, msgadmins, ban
from bot_actions import limbolist
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
from pyrogram.handlers import MessageHandler
from pyrogram import filters, enums
from contextlib import redirect_stdout
import Responses as resp
import time,sqlite3,json,re,argparse,sys,io

## Load globals
global statusantiraid
filterhandlers = []
antiraidchats = []
linkfilter = r'(?i)(h\s*t\s*t\s*p)|(h\s*\w\s*\w\s*p\:)|(h\s*\w\s*\w\s*p\s*s\:)|(\:\s*\/\s*\/)|(w\s*w\s*w\s*\.)|(w\s*w\s*w\s*d\s*o\s*t)|(\.\s*g\s*g)|(g\s*g\s*\/)|(d\s*o\s*t\s*g\s*g)|(\.\s*c\s*o\s*m)|(c\s*o\s*m\s*\/)|(d\s*o\s*t\s*c\s*o\s*m)|(\.\s*x\s*y\s*z)|(x\s*y\s*z\s*\/)|(d\s*o\s*t\s*x\s*y\s*z)|(\.\s*n\s*z)|(\s+n\s*z\s+)|(\s*n\s*z\s*\/)|(d\s*o\s*t\s*n\s*z)|(\.\s*t\s*v)|(\s*t\s*v\s*\/)|(d\s*o\s*t\s*t\s*v)|(\.\s*o\s*r\s*g)|(\s*o\s*r\s*g\s*\/)|(d\s*o\s*t\s*o\s*r\s*g)|(v\s*m\s*\.\s*t\s*i\s*k\s*t\s*o\s*k)'
invitefilter = r'(?i)(t\s*\.m\s*e)|(t\s*d\s*o\s*t\s*m\s*e)|(t\s*m\s*e\s*\/)|(\/\s*j\s*o\s*i\s*n\s*c\s*h\s*a\s*t\s*\/)(.{16})|(^\/.{16}$)|(^.{16}\/$)'
defaultfilters = json.dumps([("Link Filter",linkfilter,{"delete":0,"notify":0,},1),("Invite Filter",invitefilter,{"delete":0,"notify":0,},1)])

## Load methods
# Filter template
    # [
    # (name,
    # regexstring,
    # {actions:actionsetting,},
    # Enabledboolean)
    # ]

# filterupdate(bot, message=None):
    # # This will update all the default filters in the database.
    # getchats(bot)

# def filtermanager(bot, message):# command for managing filters
    # if not admin(bot,message):
    #     return
    # contents = message.text.split(r" ")
    # if "-a" in contents:
    #     print("adding filter")
    # if "-r" in contents:
    #     print("deleting filter")
    # if "-u" in contents:
    #     print("updating filter")

def commandcleaner(bot, message):
    time.sleep(6)
    deletemessage(bot, message, message.chat.id, message.id)

def messagesweep(bot, message):
    """
    Usage: [NUMBER]
        /del                              - Help Dialog
        /del number (no replied message)  - Delete the number of messages above
        /del (replying to message)        - Delete all messages up to (including) the replied message.
        /del number (replying to message) - Delete the number of messages after (including) the replied message.
    Args:
        bot (class): Class Representing the bot
        message (message): Object representing the message that triggers the command
    """
    # Return of not admin
    if not admin(bot, message):
        deletemessage(bot, message, message.chat.id, message.id)
        return

# Create argparse
    parser = argparse.ArgumentParser(description='Delete messages in this group')

    helpdialog = """
 Delete messages in this group.
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
    args = parser.parse_args(command[1:])

# If no reply and no number
    if not message.reply_to_message and args.number is None:
        bot.send_message(message.chat.id, f"```{helpdialog}```", enums.ParseMode.MARKDOWN)
        deletemessage(bot, message, message.chat.id, message.id)
        return

# If no reply and has number
    if not message.reply_to_message and args.number is not None:
        currentmessageid = message.id
        targetmessageid = message.id - args.number
        while currentmessageid >= targetmessageid:
            currentmessage = bot.get_messages(message.chat.id, currentmessageid)
            if currentmessage.empty:
                targetmessageid -= 1
                currentmessageid -= 1
                continue
            deletemessage(bot, message, message.chat.id, currentmessageid)
            currentmessageid -= 1
        return

# If has reply and no number
    if message.reply_to_message and args.number is None:
        currentmessageid = message.id
        deletemessage(bot, message, message.chat.id, message.id)
        while currentmessageid >= message.reply_to_message.id:
            deletemessage(bot, message, message.chat.id, currentmessageid)
            currentmessageid -= 1
        return

# If has reply and number
    if message.reply_to_message and args.number is not None:
        currentmessageid = message.reply_to_message.id
        deletemessage(bot, message, message.chat.id, message.id)
        while currentmessageid >= message.reply_to_message.id - args.number + 1:
            deletemessage(bot, message, message.chat.id, currentmessageid)
            currentmessageid -= 1
        return

def updatefilters(bot, message=None):
    if message != None and not owner(bot,message):
        print("Not owner, will not load filters")
        return
    unloadfilters(bot,message)
    loadfilters(bot, message)

def unloadfilters(bot, message=None):
    if message != None and not owner(bot,message):
        print("Not owner, will not load filters")
        return
    for i in filterhandlers:
        bot.remove_handler(*i)

def loadfilters(bot, message=None, chatids=None):
    if message != None and not owner(bot,message):
        print("Not owner, will not load filters")
        return
    x = getchats(bot) if chatids is None else chatids
    for i in x:
        try:
            y = sql(f"SELECT keywords FROM [{i}] WHERE id = 'chat_settings'")
            filterlist = json.loads(y[0][0])
            try:
                for f in filterlist:
                    filterhandlers.append(bot.add_handler(MessageHandler(filtermsg, filters.regex(f[1]) & filters.chat(i)), group=-1))
            except Exception as e:
                print(e)
                continue
        except Exception as e:
            print(e)
            continue

def enableantiraid(bot, message):
    if not owner(bot,message) and not admin(bot,message):
        return
    global statusantiraid
    if 'statusantiraid' not in globals():
        statusantiraid = bot.add_handler(MessageHandler(antiraid, filters.all))
        antiraidchats.append(message.chat.id)
    elif message.chat.id not in globals()['antiraidchats']:
        antiraidchats.append(message.chat.id)
    else:
        msg = bot.send_message(message.chat.id, "Anti-raid already on")
        time.sleep(5)
        deletemessage(bot, message, message.chat.id, msg.id)
        return
    deletemessage(bot,message,message.chat.id, message.id)

def disableantiraid(bot, message):
    if not owner(bot,message) and not admin(bot,message):
        return
    global statusantiraid
    if 'statusantiraid' not in globals() and message.chat.id not in globals()['antiraidchats']:
        msg = bot.send_message(message.chat.id, "Antiraid not on")
        time.sleep(5)
        deletemessage(bot, message, message.chat.id, msg.id)
        return
    elif message.chat.id in globals()['antiraidchats']:
        antiraidchats.remove(message.chat.id)
        if len(antiraidchats) == 0:
            bot.remove_handler(*statusantiraid)
            del statusantiraid
    deletemessage(bot,message,message.chat.id, message.id)

def antiraid(bot, message):
    if trusted(bot,message):
        return
    if message.chat.id not in antiraidchats:
        return
    deletemessage(bot,message,message.chat.id, message.id)

def noproblemb(bot, message):
    bot.send_message(message.chat.id, "No problem cuz")

def trust(bot,message):
    bot.delete_messages(message.chat.id, message.id)
    if not admin(bot,message):
        return
    for i in message.entities:
        if i.type == "text_mention":
            user = i.user

        elif i.type == "mention":
            user = bot.get_users(message.text.split(r" ")[1])

        if i.type in ["text_mention", "mention"]:
            try:
                sql(f"INSERT OR REPLACE INTO [{message.chat.id}] (id, istrusted) VALUES ({user.id},1)", mode="INSERT")
                msg = bot.send_message(message.chat.id,"User is now trusted")
                time.sleep(5)
                bot.delete_messages(message.chat.id, msg.id)
            except:
                bot.send_message(message.chat.id, "Vlad fucked up tell him to take a look")

def untrust(bot,message):
    bot.delete_messages(message.chat.id, message.id)
    if not admin(bot,message):
        return
    for i in message.entities:
        if i.type == "text_mention":
            user = i.user

        elif i.type == "mention":
            user = bot.get_users(message.text.split(r" ")[1])

        if i.type in ["text_mention", "mention"]:
            try:
                sql(f"INSERT OR REPLACE INTO [{message.chat.id}] (id, istrusted) VALUES ({user.id},0)", mode="INSERT")
                msg = bot.send_message(message.chat.id,"User is now untrusted")
                time.sleep(5)
                bot.delete_messages(message.chat.id, msg.id)
            except:
                bot.send_message(message.chat.id, "Vlad fucked up tell him to take a look")

def forwardrm(bot, message):
    if admin(bot,message):
        return
    if not message.forward_from_chat:
        return
    deletemessage(bot, message, message.chat.id, message.id)

def pedobait(bot, message):
    deletemessage(bot, message, message.chat.id, message.id)
    x = sql(f"SELECT isbait FROM universe WHERE id = {message.from_user.id}")
    try:
        if bool(x[0][0]):
            bot.send_message(message.chat.id, f"{getname(bot, message)} is a pedohunter")
        else:
            raise Exception
    except:
        bot.send_message(message.chat.id, "Never seen this man in my life")

def isadmin(bot,message):
    if admin(bot,message):
        bot.send_message(message.chat.id, "You are an admin")
    else:
        bot.send_message(message.chat.id, "You are NOT an admin")

def banuser(bot, message):
    deletemessage(bot, message, message.chat.id, message.id)
    if '-g' in texttype(bot,message):
        msg = message.text.split(r" ")
        msg.remove('-g')
        x = chatsadmined(bot, message)
        if x is None: return
        for i in x:
            ban(bot,message,i,msg)
    elif '-u' in texttype(bot,message):
        if not owner(bot,message):
            return
        msg = message.text.split(r" ")
        msg.remove('-u')
        chats = getchats(bot)
        for chat in chats:
            ban(bot,message,chat,msg)
    elif not admin(bot, message):
        return
    else:
        ban(bot,message,message.chat.id)

def servicerm(bot, message):
    if message.left_chat_member is not None and message.left_chat_member.id == bot.get_me().id:
        return
    elif message.new_chat_members is not None:
        for i in message.new_chat_members:
            if i.id != bot.get_me().id:
                deletemessage(bot, message, message.chat.id, message.id)
            else:
                allowedchannels(bot, message)
    else:
        deletemessage(bot, message, message.chat.id, message.id)

def isowner(bot, message):
    deletemessage(bot, message, message.chat.id, message.id)
    if owner(bot, message):
        bot.send_message(message.chat.id, f"{getname(bot, message)} is my owner")
    else:
        bot.send_message(message.chat.id, f"{getname(bot, message)} is NOT my owner")

def istrusted(bot, message):
    deletemessage(bot, message, message.chat.id, message.id)
    if len(message.text.split(r" ")) < 2:
        if trusted(bot,message):
            msg = bot.send_message(message.chat.id, "You are trusted")
        else:
            msg = bot.send_message(message.chat.id, "Who ARE you")
    else:
        x = sql(f"SELECT istrusted FROM [{message.chat.id}] WHERE id = {getid(bot, message)}")
        try:
            if bool(x[0][0]):
                msg = bot.send_message(message.chat.id, f"{getname(bot, message, getid(bot,message))} is Trusted")
            else:
                raise Exception
        except:
            msg = bot.send_message(message.chat.id, f"{getname(bot, message, getid(bot,message))} is NOT Trusted")
    time.sleep(20)
    deletemessage(bot, message, message.chat.id, msg.id)

def invade(bot,message):
    if not owner(bot, message):
        return
    ID = message.text.split(r" ")[1]
    try:
        bot.add_chat_members(ID, message.from_user.id)
    except:
        bot.send_message(message.chat.id, f"Failed to join {bot.get_chat(ID)}")

def getidh(bot, message):
    deletemessage(bot, message, message.chat.id, message.id)
    if len(message.text.split(r" ")) < 2:
        msg = bot.send_message(message.chat.id, message.from_user.id)
    else:
        msg = bot.send_message(message.chat.id, getid(bot,message))
    time.sleep(20)
    deletemessage(bot, message, message.chat.id, msg.id)

def getchid(bot, message):
    deletemessage(bot, message, message.chat.id, message.id)
    msg = bot.send_message(message.chat.id, message.chat.id)
    time.sleep(20)
    deletemessage(bot, message, message.chat.id, msg.id)

def getchatlist(bot,message):
    if not owner(bot,message):
        return
    x = getchats(bot)
    a =[]
    msg = "This bot is in the following chats:\n\n"
    for i in x:
        try:
            name = bot.get_chat(i).title
        except:
            name = "--privatechat--"
        a.append(f"{name} | {i}")
    chats = "\n\n".join(a)
    bot.send_message(message.chat.id, f"{msg}{chats}")

def newchat(bot, callback_query):
    if "cancel" in callback_query.data:
        sql(f"DELETE FROM universe WHERE id = {callback_query.message.chat.id}", mode="INSERT")
        hand = limbolist[f"{callback_query.message.chat.id}"]
        bot.remove_handler(*hand)
        bot.delete_messages(callback_query.message.chat.id, callback_query.message.id)
        bot.leave_chat(callback_query.message.chat.id)
    elif 'deny' in callback_query.data:
        match = re.search(r"(\-\d*\b)", callback_query.message.text)
        hand = limbolist[f"{match.group()}"]
        bot.remove_handler(*hand)
        sql(f"INSERT OR REPLACE INTO universe (id, chatunauth) VALUES ({match.group()},1)", mode="INSERT")
        bot.send_message(match.group(),"Sorry the owner denied your request. Goodbye.")
        bot.leave_chat(match.group())
        bot.delete_messages(callback_query.message.chat.id, callback_query.message.id)
    elif 'request' in callback_query.data:
        sql(f"DELETE FROM universe WHERE id = {callback_query.message.chat.id}", mode="INSERT")
        reply_markup=InlineKeyboardMarkup(
            [
                [
                InlineKeyboardButton("Accept", callback_data="accept"),
                InlineKeyboardButton("Deny", callback_data="deny")
                ],
            ])
        msgowners(bot,callback_query.message, f"A request was sent from {callback_query.message.chat.title} | {callback_query.message.chat.id} by this user: {getname(bot,callback_query.message,callback_query.from_user.id)}", reply_markup = reply_markup)
        deletemessage(bot, callback_query.message, callback_query.message.chat.id, callback_query.message.id)
        msg = bot.send_message(callback_query.message.chat.id, "We're asking the owners now.")
        time.sleep(10)
        deletemessage(bot, callback_query.message, callback_query.message.chat.id, msg.id)

def addchat(bot, callback_query):
    deletemessage(bot, callback_query.message, callback_query.message.chat.id, callback_query.message.id)
    match = re.search(r"(\-\d*\b)", callback_query.message.text)
    try:
        sql(f"CREATE TABLE IF NOT EXISTS [{match.group()}] (id PRIMARY KEY,keywords,keyactions,istrusted,ingroups,activethresh)", mode="INSERT")
        sql(f"INSERT OR REPLACE INTO universe (id, chatauth) VALUES ({match.group()},1)", mode="INSERT")
        sql(f"INSERT or REPLACE INTO [{match.group()}] (id,keywords) VALUES ('chat_settings','{defaultfilters}')", mode="INSERT")
        hand = limbolist[f"{match.group()}"]
        bot.remove_handler(*hand)
        #loadfilters(bot,chatids=[match.group()])
        updatefilters(bot)
    except Exception as e:
        bot.leave_chat(match.group())
        bot.send_message(match.group(), "Request was accepted but something went wrong. The owners have been notified of the error.")
        msgowners(bot, callback_query.message, f"Failed to add this chat: {match.group()}\n======================\n{e}")
        return
    bot.send_message(match.group(), "Request has been accepted!\nIf you haven't already, please make me an admin.\nI require those permissions to work.")

def helpbot(bot, message):
    bot.send_message(message.chat.id, f"{resp.HELP_DIALOG}")
    deletemessage(bot, message, message.chat.id, message.id)

def leave(bot, message):
    if owner(bot,message):
        ID = message.text.split(r" ")
        ID = ID[1] if len(ID) > 1 else message.chat.id
        try:
            bot.leave_chat(ID)
            msgowners(bot,message, f"We left the chat")
        except:
            msgowners(bot,message, f"Failed to leave chat")
    else:
        msg = bot.send_message(message.chat.id, "You are not authorized to use the /leave command")
        time.sleep(5)
        try:
            bot.delete_messages(message.chat.id, msg.id)
        except:

# def linkrm(bot, message):
    # filtermsg(bot, message, 'Link Removed:')

    # actions = {}
    # enabled = 1
    # linkfilter = r'(?i)(h\s*t\s*t\s*p)|(h\s*\w\s*\w\s*p\:)|(h\s*\w\s*\w\s*p\s*s\:)|(\:\s*\/\s*\/)|(w\s*w\s*w\s*\.)|(w\s*w\s*w\s*d\s*o\s*t)|(\.\s*g\s*g)|(g\s*g\s*\/)|(d\s*o\s*t\s*g\s*g)|(\.\s*c\s*o\s*m)|(c\s*o\s*m\s*\/)|(d\s*o\s*t\s*c\s*o\s*m)|(\.\s*x\s*y\s*z)|(x\s*y\s*z\s*\/)|(d\s*o\s*t\s*x\s*y\s*z)|(\.\s*n\s*z)|(\s*n\s*z\s*\/)|(d\s*o\s*t\s*n\s*z)|(\.\s*t\s*v)|(\s*t\s*v\s*\/)|(d\s*o\s*t\s*t\s*v)|(\.\s*o\s*r\s*g)|(\s*o\s*r\s*g\s*\/)|(d\s*o\s*t\s*o\s*r\s*g)|(v\s*m\s*\.\s*t\s*i\s*k\s*t\s*o\s*k)'
    # bot.add_handler(MessageHandler())
    # filtermsg(bot, message, "link filter", linkfilter, actions, enabled)

# def inviterm(bot, message):# Default Invite filter
    # if admin(bot, message):
    #     return
    # print("Legacy filter was used")
    # log = filtermsg(bot, message, 'Invite Removed:')
    # msgadmins(bot,message, log)

# def snaprm(bot, message):# Being replaced with SQL entry
    # filtermsg(bot, message, 'Snapbeg Removed:')

# def pedorm(bot, message):# Being replaced with SQL entry
    # x = sql(f"SELECT isbait FROM universe WHERE id = {message.from_user.id}")
    # try:
    #     if admin(bot,message) or bool(x[0][0]):
    #         return
    #     else:
    #         raise Exception
    # except:
    #     filtermsg(bot, message, "Pedophile removed:")
    #     bot.kick_chat_member(message.chat.id, message.from_user.id)
    #     bot.send_message(message.chat.id, f"Pedophile Removed: {getname(bot, message)}\nThey either sent a blacklisted invite, or said a blacklisted word such as 'pyt'")
            pass