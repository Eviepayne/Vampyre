import uuid
from pyrogram.handlers import CallbackQueryHandler
from pyrogram import filters
from Classes.Manager import HandlerManager

class Callback():

    def CreateCallback(bot, originfunction, **kwargs):
        manager = HandlerManager()
        guid = str(uuid.uuid4())
        callbackhandler = bot.add_handler(CallbackQueryHandler(originfunction, filters.regex(rf"{guid}")))
        manager.add_handler(guid, callbackhandler, kwargs)
        return guid

    def ReadCallback(guid):
        manager = HandlerManager()
        data = manager.get_data(guid)
        handler = manager.get_handler(guid)
        return data, handler

    def DestroyCallback(bot, guid, handler):
        manager = HandlerManager()
        manager.remove_handler(guid)
        bot.remove_handler(*handler)