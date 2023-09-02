#!python3
## Modules
import sqlite3, json, os, configparser, time, jurigged, logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import filters, idle
from pyrogram.handlers import MessageHandler, CallbackQueryHandler, ChatMemberUpdatedHandler
from Classes.Client import Client
from Classes.Handlers import Handlers
from Classes.HandlerManager import HandlerManager


# Startup ===========================================
# Set data path and check if it exists
datapath = "data"
if not os.path.exists(datapath):
    os.mkdir(datapath)
    first_startup = True
else:
    first_startup = False


# Load Configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Instantiate bot
bot = Client(
    flog = config.get('bot', 'flog'),
    slog = config.get('bot', 'slog'),
    glog = config.get('bot', 'glog'),
    name = config.get('bot', 'app_name'),
    api_id = config.get('bot', 'api_id'),
    api_hash = config.get('bot', 'api_hash'),
    bot_token = config.get('bot', 'bot_token'),
    bot_owner = config.get('bot', 'bot_owner'),
    app_version = "Vampyre 1.1.1" # Updated ban command and patched SQL injection
    )

# Initialize data base
if not os.path.exists(os.path.join(bot.db_path)):
    bot.logger.warning("Could not find database, creating it")
    bot.initialize_database()
bot.logger.info("Vampyre is Initialized")

# Create HandlerManager
HandlerManager = HandlerManager()

# Create scheduler
scheduler = AsyncIOScheduler()

# Main method =======================================
def main(first_startup):
    bot.logger.info("Starting Vampyre")
    # Defining scheduled actions
    async def scheduled_actions(): # TODO - This is a workaround for loading filters after a chat instantiates. Need a better way
        # Reload Filters
        Handler_manager.unload_filters(bot)
        Handler_manager.load_filters(bot)

    Handler_manager = HandlerManager
    scheduler.add_job(scheduled_actions, 'interval', minutes=10)
    
    # Setting Jurigged watcher
    jurigged.watch(pattern="./Classes/*.py")

    # Loading Filters and Handlers
    Handler_manager.load_handlers(bot) # Group 5
    Handler_manager.load_filters(bot) # Group 0

    # Adding all handlers
    bot.add_handler(MessageHandler(Handlers.all_messages),10)
    bot.add_handler(ChatMemberUpdatedHandler(Handlers.all_chatmemberupdates),10)

    # Starting scheduled actions
    scheduler.start()
    bot.logger.info("Vampyre is Ready")

bot.run(main(first_startup))

    ### Notes
    # Rate limites https://limits.tginfo.me/en
    # filter manager handler here
    # handle the command /filters and other arguments
    # include /filters test arg to test input
   
    # Add LinkFilter Handlers here
    # Should be a method that gathers a list of universal filters as well as chat specific filters.
    ## filters = gatherallfilters() Needs to return chatid and filter string
    ## for filter in filters
    ## bot.add_handler(MessageHandler(Handlers.LinkFilter, filtercontent, chatid))
    # A filter is a tuple that contains, a name (string), a filter (regex or normal string), a list of actions (dict), and a status if enabled (boolean)
    # The dict is of different actions (string), The action option if the action supports it (int).
    # Example Filter for deleting everything:
    # (
    #   "deleteitall",
    #   r".*",
    #   {delete:1},
    #   1
    # )
  
    # add handlers cleanup for restarting the bot.
    # add init handler for stopping and restarting bot.



    ### CallbackQuery Handlers
    
    ### This is where I need to Refactor things

    # ## initalization
    # # load filters
    # loadfilters(bot) # TODO Figure out how to dynamically have different filters in the bot

    # ## Commands
    # # bot owner commands
    # bot.add_handler(MessageHandler(leave,filters.command(["leave","l"]))) # TODO - Review implementation
    # bot.add_handler(MessageHandler(getchatlist,filters.command(["chats","chl"]))) # TODO - Review implementation
    # bot.add_handler(MessageHandler(invade,filters.command(["invade","in"]))) # TODO - Review implementation
    # bot.add_handler(MessageHandler(trust,filters.command(["trust","t"]))) # TODO - Review implementation
    # bot.add_handler(MessageHandler(untrust,filters.command(["untrust","ut"]))) # TODO - Review implementation
    # bot.add_handler(MessageHandler(banuser,filters.command(["ban", "b"]))) # TODO - Review implementation
    # bot.add_handler(MessageHandler(enableantiraid,filters.command(["antiraid","ar"]))) # TODO - Review implementation
    # bot.add_handler(MessageHandler(disableantiraid,filters.command(["disableantiraid","dar"]))) # TODO - Review implementation
    # bot.add_handler(MessageHandler(loadfilters,filters.command("load"))) # TODO - Review implementation
    # bot.add_handler(MessageHandler(updatefilters,filters.command("update"))) # TODO - Review implementation
    # bot.add_handler(MessageHandler(unloadfilters,filters.command("unload"))) # TODO - Review implementation
    # #bot.add_handler(MessageHandler(controlpanel,filters.command("settings","control")))
    # # normie commands
    # bot.add_handler(MessageHandler(helpbot,filters.command(["help","start","h"]))) # TODO - Review implementation
    # bot.add_handler(MessageHandler(getidh,filters.command(["getid","id"]))) # TODO - Review implementation
    # bot.add_handler(MessageHandler(getchid,filters.command(["getchid","chid"]))) # TODO - Review implementation
    # bot.add_handler(MessageHandler(isowner,filters.command(["isowner","io"]))) # TODO - Review implementation
    # bot.add_handler(MessageHandler(istrusted,filters.command(["istrusted","it"]))) # TODO - Review implementation
    # bot.add_handler(MessageHandler(pedobait,filters.command("bait"))) # TODO - Review implementation

    # ## Message Filters
    # bot.add_handler(MessageHandler(servicerm,filters.service)) # TODO - Review implementation
    # bot.add_handler(MessageHandler(commandcleaner,filters.regex(r"(?i)(^\/.*$)"))) # TODO - Review implementation
    # bot.add_handler(MessageHandler(forwardrm,filters.forwarded)) # TODO - Review implementation
    # bot.add_handler(MessageHandler(noproblemb,filters.regex(r"(?i)(?=.*thanks)(?=.*@vladtheimplier_bot)"))) # TODO - Review implementation
