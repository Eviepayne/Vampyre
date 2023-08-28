import uuid, importlib, inspect, sys, logging, Classes
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from pyrogram import filters

class HandlerManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HandlerManager, cls).__new__(cls)
            cls._instance.handlers = {}
            cls._instance.data_store = {}
            cls._instance.LinkFilter = r'(?i)(h\s*t\s*t\s*p)|(h\s*\w\s*\w\s*p\:)|(h\s*\w\s*\w\s*p\s*s\:)|(\:\s*\/\s*\/)|(w\s*w\s*w\s*\.)|(w\s*w\s*w\s*d\s*o\s*t)|(\.\s*g\s*g)|(g\s*g\s*\/)|(d\s*o\s*t\s*g\s*g)|(\.\s*c\s*o\s*m)|(c\s*o\s*m\s*\/)|(d\s*o\s*t\s*c\s*o\s*m)|(\.\s*x\s*y\s*z)|(x\s*y\s*z\s*\/)|(d\s*o\s*t\s*x\s*y\s*z)|(\.\s*n\s*z)|(\s+n\s*z\s+)|(\s*n\s*z\s*\/)|(d\s*o\s*t\s*n\s*z)|(\.\s*t\s*v)|(\s*t\s*v\s*\/)|(d\s*o\s*t\s*t\s*v)|(\.\s*o\s*r\s*g)|(\s*o\s*r\s*g\s*\/)|(d\s*o\s*t\s*o\s*r\s*g)|(v\s*m\s*\.\s*t\s*i\s*k\s*t\s*o\s*k)'
            cls._instance.invitefilter = r'(?i)(t\s*\.m\s*e)|(t\s*d\s*o\s*t\s*m\s*e)|(t\s*m\s*e\s*\/)|(\/\s*j\s*o\s*i\s*n\s*c\s*h\s*a\s*t\s*\/)(.{16})|(^\/.{16}$)|(^.{16}\/$)'
            cls._instance.defaultfilters =[
            ("LinkFilter",cls._instance.LinkFilter,{"delete":0,"notify":0,},1),
            ("InviteFilter",cls._instance.invitefilter,{"delete":0,"notify":0,},1)
            ]
        return cls._instance

 # Unloads and loads all Handlers ================================

    def unload_handlers(self, bot):
        """Unloads all handlers

        Args:
            bot (client): bot object passed from message handler
        """
        bot.logger.info("Unloading Handlers")
        logger = logging.getLogger("Vampyre.unload_handlers")
        logger.debug("Getting all handlers from handlermanager")
        guids = [guid for guid in self.handlers]
        logger.debug("Cleaning up handlers from handlermanager")
        for guid in guids:
            handler = self.get_handler(guid)
            logger.debug(f"Destroying Handler - guid: {guid} | handler: {handler}")
            self.DestroyMessage(bot, guid, handler)

    def load_handlers(self, bot):
        """Loads all handlers from Handlers class

        Args:
            bot (client): bot object passed from message handler
        """
        bot.logger.info("Loading Handlers")
        logger = logging.getLogger("Vampyre.reload_and_create_handlers")
        logger.debug("Getting all methods from the Handlers Class")
        methods = [method for name, method in inspect.getmembers(Classes.Handlers.Handlers, inspect.isfunction) if name != '__init__']
        logger.debug("Creating New Handlers")
        for method in methods:
            method_filter = getattr(method, 'filter', None)
            if method_filter:
                # may want to expand on this to load more handlers than just message handlers
                # We can add a method attribute for the type of handler it is so we can properly assign the handler type
                self.CreateMessage(bot, method, method_filter)
                logger.debug(f"Handler loaded for: {method}")
        logger.debug("All Handlers Loaded")

 # Manage Handlers ===============================================
    def store_handler(self, guid, handler, data=None):
        """Stores Handler for later use
        Args:
            guid (String): Global Unique Identifier, generate from str(uuid.uuid4())
            handler (Handler): Returned from bot.add_handler
            data (Dict): All data stored in the handler from kwargs 
        """
        logger = logging.getLogger("Vampyre.store_handler")
        logger.debug("Storing handler and Data")
        self.handlers[guid] = handler
        self.data_store[guid] = data

    def get_handler(self, guid):
        """Gets the handler for the guid

        Args:
            guid (Str): Global unique identifier for a related Handler

        Returns:
            Handler: Handler
        """
        logger = logging.getLogger("Vampyre.get_handler")
        logger.debug("Returning Handler")
        return self.handlers.get(guid)

    def get_data(self, guid):
        """Returns data for a related Handler

        Args:
            guid (Str): Global unique identifier for a related Handler

        Returns:
            dict: kwargs
        """
        logger = logging.getLogger("Vampyre.get_data")
        logger.debug("Returning data related to handler")
        return self.data_store.get(guid)
    
    def unregister_handler(self, guid):
        """Removes a handler

        Args:
            guid (Str): Global unique identifier for a related Handler
        """
        logger = logging.getLogger("Vampyre.unregister_handler")
        logger.debug("Removing handler")
        self.handlers.pop(guid, None)
        self.data_store.pop(guid, None)

 # Callbacks Handlers ============================================
    # Callbacks should always be unique and can be group 0
    def CreateCallback(self, bot, function, **kwargs):
        """Creates a Callback Handler, Stores kwargs, and returns the guid for the callback trigger

        Args:
            bot (Class): Bot Object
            function (function): The function the Callback Should Trigger

        Returns:
            guid: Global unique identifier for a related Callback
        """
        logger = logging.getLogger("Vampyre.CreateCallback")
        logger.debug("Generating GUID")
        guid = str(uuid.uuid4())
        logger.debug("Creating Callback Handler")
        callbackhandler = bot.add_handler(CallbackQueryHandler(function, filters.regex(rf"{guid}")))
        logger.debug("Storing Callback Handler")
        self.store_handler(guid, callbackhandler, kwargs)
        return guid

    def ReadCallback(self, guid):
        """Reads Callback content

        Args:
            guid (Str): Global unique identifier for a related Callback

        Returns:
            dict: kwargs
        """
        logger = logging.getLogger("Vampyre.ReadCallback")
        logger.debug("Grabbing handler Data")
        data = self.get_data(guid)
        logger.debug("Grabbing handler Guid")
        handler = self.get_handler(guid)
        logger.debug("Returning Data and Handler")
        return data, handler
    
    def DestroyCallback(self, bot, guid, handler):
        """Destroys a Callback Handler

        Args:
            bot (Class): Bot Object
            guid (Str): Global unique identifier for a related Callback
            handler (Handler): The Handler Object to be destroyed
        """
        logger = logging.getLogger("Vampyre.DestroyCallback")
        logger.debug("Deleting from handler store")
        self.unregister_handler(guid)
        logger.debug("Removing handler")
        bot.remove_handler(*handler)

 # Message Handlers ==============================================
    # Message Handlers can be group 0
    def CreateMessage(self, bot, function, messagefilter, **kwargs):
        """Creates a message handler

        Args:
            bot (bot): the bot
            function (function): The function the handler should trigger
            messagefilter (filter): A filter from the pyrogram.filters module

        Returns:
            string: guid
        """
        logger = logging.getLogger("Vampyre.CreateMessage")
        logger.debug("Generating GUID")
        guid = str(uuid.uuid4())
        logger.debug("Creating Handler")
        messagehandler = bot.add_handler(MessageHandler(function, messagefilter))
        logger.debug("Storing Handler")
        self.store_handler(guid, messagehandler, kwargs)
        return guid
    
    def ReadMessage(self, guid):
        """Reads MessageHandler content

        Args:
            guid (Str): Global unique identifier for a related Callback

        Returns:
            dict: kwargs
        """
        logger = logging.getLogger("Vampyre.ReadMessage")
        logger.debug("Getting Data")
        data = self.get_data(guid)
        logger.debug("Getting Handler")
        handler = self.get_handler(guid)
        logger.debug("returning Data and Handler")
        return data, handler
    
    def DestroyMessage(self, bot, guid, handler):
        """Destroys a Message Handler

        Args:
            bot (Class): Bot Object
            guid (Str): Global unique identifier for a related Message
            handler (Handler): The Handler Object to be destroyed
        """
        logger = logging.getLogger("Vampyre.DestroyMessage")
        logger.debug("Deleting from handler store")
        self.unregister_handler(guid)
        logger.debug("Removing handler")
        bot.remove_handler(*handler)

 # Filter Handlers ===============================================
    # Filter handlers should be in group -100

    # @classmethod
    # def updatefilters(bot, message=None):
    #     if message != None and not owner(bot,message):
    #         print("Not owner, will not load filters")
    #         return
    #     unloadfilters(bot,message)
    #     loadfilters(bot, message)

    # @classmethod
    # def unloadfilters(bot, message=None):
    #     if message != None and not owner(bot,message):
    #         print("Not owner, will not load filters")
    #         return
    #     for i in filterhandlers:
    #         bot.remove_handler(*i)

    # @classmethod
    # def loadfilters(bot, message=None):
    #     if message is not None and not bot.is_admin(message.chat.id, message.from_user.id):
    #         return
    #     chats = bot.get_chats()
    #     print(chats)
    #     for chat in chats:
    #         try:
    #             print(chat)
    #             messagefilters = bot.sql(f"SELECT filters FROM [chats] WHERE id = '{chat}'")
    #             print(messagefilters)
    #             return
    #             filterlist = json.loads(y[0][0])
    #             try:
    #                 for f in filterlist:
    #                     filterhandlers.append(bot.add_handler(MessageHandler(filtermsg, filters.regex(f[1]) & filters.chat(i)), group=-1))
    #             except Exception as e:
    #                 print(e)
    #                 continue
    #         except Exception as e:
    #             print(e)
    #             continue