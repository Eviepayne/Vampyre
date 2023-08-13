#!python3

## Modules
from pyrogram import Client, filters, idle
from pyrogram.filters import create
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from bot_handlers import forwardrm, noproblemb, commandcleaner, trust, untrust, messagesweep, loadfilters, unloadfilters, getchats
from bot_handlers import banuser, isowner, pedobait, servicerm, helpbot, getchid, getid, leave, invade, getidh, getchatlist
from bot_handlers import istrusted, sql, enableantiraid, disableantiraid, antiraid, updatefilters, isadmin, newchat, addchat
import sqlite3, json

import configparser
config = configparser.ConfigParser()
config.read('config.ini')

api_id = config.get('pyrogram', 'api_id')
api_hash = config.get('pyrogram', 'api_hash')
bot_token = config.get('pyrogram', 'bot_token')

## initalization
bot = Client(
        "Vampyre",
        api_id=api_id, api_hash=api_hash,
        bot_token=bot_token
        )

## Main
def main():

    ## initalization
    # load filters
    loadfilters(bot) # TODO Figure out how to dynamically have different filters in the bot

    ## Commands
    # Callback Queries
    bot.add_handler(CallbackQueryHandler(newchat,filters.regex(r"(?i)(request)|(cancel)|(deny)")))
    bot.add_handler(CallbackQueryHandler(addchat,filters.regex(r"(?i)(accept)")))
    # bot owner commands
    bot.add_handler(MessageHandler(leave,filters.command(["leave","l"])))
    bot.add_handler(MessageHandler(getchatlist,filters.command(["chats","chl"])))
    bot.add_handler(MessageHandler(invade,filters.command(["invade","in"])))
    # admin commands
    bot.add_handler(MessageHandler(messagesweep,filters.command(["del","d","delete"])))
    bot.add_handler(MessageHandler(trust,filters.command(["trust","t"])))
    bot.add_handler(MessageHandler(untrust,filters.command(["untrust","ut"])))
    bot.add_handler(MessageHandler(banuser,filters.command(["ban", "b"])))
    bot.add_handler(MessageHandler(enableantiraid,filters.command(["antiraid","ar"])))
    bot.add_handler(MessageHandler(disableantiraid,filters.command(["disableantiraid","dar"])))
    bot.add_handler(MessageHandler(loadfilters,filters.command("load")))
    bot.add_handler(MessageHandler(updatefilters,filters.command("update")))
    bot.add_handler(MessageHandler(unloadfilters,filters.command("unload")))
    #bot.add_handler(MessageHandler(controlpanel,filters.command("settings","control")))
    # normie commands
    bot.add_handler(MessageHandler(helpbot,filters.command(["help","start","h"])))
    bot.add_handler(MessageHandler(getidh,filters.command(["getid","id"])))
    bot.add_handler(MessageHandler(getchid,filters.command(["getchid","chid"])))
    bot.add_handler(MessageHandler(isowner,filters.command(["isowner","io"])))
    bot.add_handler(MessageHandler(istrusted,filters.command(["istrusted","it"])))
    bot.add_handler(MessageHandler(isadmin,filters.command(["isadmin","ia"])))
    bot.add_handler(MessageHandler(pedobait,filters.command("bait")))

    ## Message Filters
    bot.add_handler(MessageHandler(servicerm,filters.service))
    bot.add_handler(MessageHandler(commandcleaner,filters.regex(r"(?i)(^\/.*$)")))
    bot.add_handler(MessageHandler(forwardrm,filters.forwarded))
    bot.add_handler(MessageHandler(noproblemb,filters.regex(r"(?i)(?=.*thanks)(?=.*@vladtheimplier_bot)")))

    print("Ready")

bot.run(main())
