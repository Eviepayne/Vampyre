import uuid
from pyrogram.handlers import CallbackQueryHandler
from pyrogram import filters
from Classes.Manager import HandlerManager

class Callback():

    def CreateCallback(bot, function, **kwargs):
        """Creates a Callback Handler, Stores kwargs, and returns the guid for the callback trigger

        Args:
            bot (Class): Bot Object
            function (function): The function the Callback Should Trigger

        Returns:
            guid: Global unique identifier for a related Callback
        """
        manager = HandlerManager()
        guid = str(uuid.uuid4())
        callbackhandler = bot.add_handler(CallbackQueryHandler(function, filters.regex(rf"{guid}")))
        manager.add_handler(guid, callbackhandler, kwargs)
        return guid

    def ReadCallback(guid):
        """Reads Callback content

        Args:
            guid (Str): Global unique identifier for a related Callback

        Returns:
            dict: kwargs
        """
        manager = HandlerManager()
        data = manager.get_data(guid)
        handler = manager.get_handler(guid)
        return data, handler

    def DestroyCallback(bot, guid, handler):
        """Destroys a Callback Handler

        Args:
            bot (Class): Bot Object
            guid (Str): Global unique identifier for a related Callback
            handler (Handler): The Handler Object to be destroyed
        """
        manager = HandlerManager()
        manager.remove_handler(guid)
        bot.remove_handler(*handler)