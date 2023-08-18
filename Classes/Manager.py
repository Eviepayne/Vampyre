class HandlerManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HandlerManager, cls).__new__(cls)
            cls._instance.handlers = {}
            cls._instance.data_store = {}
        return cls._instance

    def add_handler(self, guid, handler, data):
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
