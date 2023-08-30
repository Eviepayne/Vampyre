import uuid, importlib, inspect, sys, logging, Classes
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from pyrogram import filters
from Classes.Methods import Methods

class HandlerManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HandlerManager, cls).__new__(cls)
            cls._instance.handlers = {}
            cls._instance.filters = {}
            cls._instance.data_store = {}
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

    def unload_filters(self, bot):
        """Unloads all handlers

        Args:
            bot (client): bot object passed from message handler
        """
        bot.logger.info("Unloading Filters")
        logger = logging.getLogger("Vampyre.unload_filters")
        logger.debug("Getting all filters from handlermanager")
        guids = [guid for guid in self.filters]
        logger.debug("Cleaning up filters from handlermanager")
        for guid in guids:
            handler = self.get_filter(guid)
            logger.debug(f"Destroying filter - guid: {guid} | filter: {handler}")
            self.DestroyFilter(bot, guid, handler)

    def load_handlers(self, bot):
        """Loads all handlers from Handlers class

        Args:
            bot (client): bot object passed from message handler
        """
        bot.logger.info("Loading Handlers")
        logger = logging.getLogger("Vampyre.load_handlers")
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

    def load_filters(self, bot):
        """Loads all filters from database, then creates the filter handlers

        Args:
            bot (client): bot object passed from message handler
        """
        bot.logger.info("Loading Filters")
        logger = logging.getLogger("Vampyre.load_filters")
        logger.debug("Getting all chats from database")
        chatids = bot.get_chats()
        for chatid in chatids:
            logger.debug(f"Getting filters for: {chatid}")
            chatfilters = bot.get_filters(chatid)
            logger.debug(f"Chat filters: {chatfilters}")
            logger.debug("Creating chat filter handlers")
            for cf in chatfilters:
                self.Createfilter(bot, filters.regex(cf[1]), cf[2])
        logger.debug("All filters Loaded")

 # Manage Handlers ===============================================
  # Store Handlers
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

    def store_filter(self, guid, handler, data=None):
        """Stores Handler for later use
        Args:
            guid (String): Global Unique Identifier, generate from str(uuid.uuid4())
            handler (Handler): Returned from bot.add_handler
            data (Dict): All data stored in the handler from kwargs 
        """
        logger = logging.getLogger("Vampyre.store_handler")
        logger.debug("Storing handler and Data")
        self.filters[guid] = handler
        self.data_store[guid] = data

  # Get Handlers/Data
    def get_filter(self, guid):
        """Gets the filter for the guid

        Args:
            guid (Str): Global unique identifier for a related Handler

        Returns:
            Handler: Filter
        """
        logger = logging.getLogger("Vampyre.get_filter")
        logger.debug("Returning Filter")
        return self.filters.get(guid)
    
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

  # Remove Handlers from store
    def unregister_filter(self, guid):
        """Removes a handler

        Args:
            guid (Str): Global unique identifier for a related Handler
        """
        logger = logging.getLogger("Vampyre.unregister_handler")
        logger.debug("Removing handler")
        self.filters.pop(guid, None)
        self.data_store.pop(guid, None)

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
        messagehandler = bot.add_handler(MessageHandler(function, messagefilter), 5)
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
    def Createfilter(self, bot, messagefilter, actions):
        """Creates a filter handler

        Args:
            bot (bot): the bot
            function (function): The function the handler should trigger
            messagefilter (filter): A filter from the pyrogram.filters module

        Returns:
            string: guid
        """
        logger = logging.getLogger("Vampyre.CreateFilter")
        logger.debug("Generating GUID")
        guid = str(uuid.uuid4())
        logger.debug("Creating Handler method")
        def filtersactions(bot, message):
            if Methods.is_admin(bot, message):
                return

            bot.logger.debug("Filtering message")
            if "delete" in actions:
                bot.delete_messages(message.chat.id, message.id)
            if "ban" in actions:
                bot.ban_chat_mamber(message.chat.id, message.from_user.id)
            # if "untrust" in actions:
                #     sql(f"INSERT OR REPLACE INTO [{message.chat.id}] (id, istrusted) VALUES ({message.from_user.id},0)", mode="INSERT")
                # if "trust" in actions:
                #     sql(f"INSERT OR REPLACE INTO [{message.chat.id}] (id, istrusted) VALUES ({message.from_user.id},1)", mode="INSERT")
                # if "warn" in actions:
                #     bot.logger.debug("Warned user")
                # if "message" in actions:
                #     username = re.compile(r"(?i)(\%name)")
                #     newmsg = re.sub(username, getname(bot,message),actions['message'])
                #     bot.send_message(message.chat.id, newmsg)
                # if "notify" in actions:
                #     actionlog(bot, message, name, mode="Admins")
        messagehandler = bot.add_handler(MessageHandler(filtersactions, messagefilter))
        logger.debug("Storing Handler")
        self.store_filter(guid, messagehandler)
        return guid

    def DestroyFilter(self, bot, guid, handler):
        """Destroys a Filter Handler

        Args:
            bot (Class): Bot Object
            guid (Str): Global unique identifier for a related Message
            handler (Handler): The Handler Object to be destroyed
        """
        logger = logging.getLogger("Vampyre.DestroyFilter")
        logger.debug("Deleting from filter store")
        self.unregister_filter(guid)
        logger.debug("Removing handler")
        bot.remove_handler(*handler)