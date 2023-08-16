class HandlerManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HandlerManager, cls).__new__(cls)
            cls._instance.handlers = {}
            cls._instance.data_store = {}
        return cls._instance

    def add_handler(self, guid, handler, data):
        self.handlers[guid] = handler
        self.data_store[guid] = data

    def get_handler(self, guid):
        return self.handlers.get(guid)

    def get_data(self, guid):
        return self.data_store.get(guid)

    def remove_handler(self, guid):
        handler = self.handlers.pop(guid, None)
        data = self.data_store.pop(guid, None)
        return handler, data
