import uuid, importlib, inspect, sys
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

 # Meta logic to reload python modules and new code ==============
    # Python reload modules
    def reload_module(self, module_name):
        if module_name in sys.modules:
            print("Unloading Class")
            del sys.modules[module_name]
            print("loading Class")
        return importlib.import_module(module_name)

    def reload_and_create_handlers(self, bot):
        # Reload Handlers class
        reloaded_module = self.reload_module("Classes.Handlers")
        print("Class Loaded")
        print("Loading Handlers attributes")
        ReloadedHandlers = getattr(reloaded_module, "Handlers")
        
        # Get methods from class
        print("Loading methods for handlers")
        methods = [method for name, method in inspect.getmembers(ReloadedHandlers, inspect.isfunction) if name != '__init__']

        for method in methods:
            # gets the filter attribute
            method_filter = getattr(method, 'filter', None)
            print("Creating Handlers")
            if method_filter:
                self.CreateMessage(bot, method, method_filter)
        print("Done loading new code")

 # Manage Handlers ===============================================
    def add_handler(self, guid, handler, data=None):
        """Stores Handler for later use
        Args:
            guid (String): Global Unique Identifier, generate from str(uuid.uuid4())
            handler (Handler): Returned from bot.add_handler
            data (Dict): All data stored in the handler from kwargs 
        """
        self.handlers[guid] = handler
        self.data_store[guid] = data

    def get_handler(self, guid):
        """Gets the handler for the guid

        Args:
            guid (Str): Global unique identifier for a related Handler

        Returns:
            Handler: Handler
        """
        return self.handlers.get(guid)

    def get_data(self, guid):
        """Returns data for a related Handler

        Args:
            guid (Str): Global unique identifier for a related Handler

        Returns:
            dict: kwargs
        """
        return self.data_store.get(guid)
    
    def remove_handler(self, guid):
        """Removes a handler

        Args:
            guid (Str): Global unique identifier for a related Handler
        """
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
        guid = str(uuid.uuid4())
        callbackhandler = bot.add_handler(CallbackQueryHandler(function, filters.regex(rf"{guid}")))
        self.add_handler(guid, callbackhandler, kwargs)
        return guid

    def ReadCallback(self, guid):
        """Reads Callback content

        Args:
            guid (Str): Global unique identifier for a related Callback

        Returns:
            dict: kwargs
        """
        data = self.get_data(guid)
        handler = self.get_handler(guid)
        return data, handler
    
    def DestroyCallback(self, bot, guid, handler):
        """Destroys a Callback Handler

        Args:
            bot (Class): Bot Object
            guid (Str): Global unique identifier for a related Callback
            handler (Handler): The Handler Object to be destroyed
        """
        self.remove_handler(guid)
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
            _type_: _description_
        """
        guid = str(uuid.uuid4())
        messagehandler = bot.add_handler(MessageHandler(function, messagefilter))
        self.add_handler(guid, messagehandler, kwargs)
        return guid
    
    def ReadMessage(self, guid):
        """Reads MessageHandler content

        Args:
            guid (Str): Global unique identifier for a related Callback

        Returns:
            dict: kwargs
        """
        data = self.get_data(guid)
        handler = self.get_handler(guid)
        return data, handler
    
    def DestroyMessage(self, bot, guid, handler):
        """Destroys a Message Handler

        Args:
            bot (Class): Bot Object
            guid (Str): Global unique identifier for a related Message
            handler (Handler): The Handler Object to be destroyed
        """
        self.remove_handler(guid)
        bot.remove_handler(*handler)

 # Filter Handlers ===============================================
    # # Filter handlers should be in group -100

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
        if message is not None and not bot.is_admin(message.chat.id, message.from_user.id):
            return
        chats = bot.get_chats()
        print(chats)
        for chat in chats:
            try:
                print(chat)
                messagefilters = bot.sql(f"SELECT filters FROM [chats] WHERE id = '{chat}'")
                print(messagefilters)
                return
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