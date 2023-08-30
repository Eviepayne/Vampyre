import sqlite3, os, logging, time, json
from pyrogram import Client as PyrogramClient
from pyrogram import errors, enums

#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Client(PyrogramClient):

    def __init__(self, bot_owner, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_name = f"{self.name}.db"
        self.db_path = os.path.join("data", self.db_name)
        self.bot_owner = bot_owner
        # Root Logging
        self.logger = logging.getLogger('Vampyre')
        self.logger.setLevel(logging.DEBUG)
        # Stdout Logger
        self.stdout_handler = logging.StreamHandler()
        self.logger.addHandler(self.stdout_handler)
        self.stdout_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        # File logs
        self.file_handler = logging.FileHandler(os.path.join("data", "Vampyre.log"))
        self.logger.addHandler(self.file_handler)
        self.file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        # DefaultFilters
        self.LinkFilter = r'(?i)(h\s*t\s*t\s*p)|(h\s*\w\s*\w\s*p\:)|(h\s*\w\s*\w\s*p\s*s\:)|(\:\s*\/\s*\/)|(w\s*w\s*w\s*\.)|(w\s*w\s*w\s*d\s*o\s*t)|(\.\s*g\s*g)|(g\s*g\s*\/)|(d\s*o\s*t\s*g\s*g)|(\.\s*c\s*o\s*m)|(c\s*o\s*m\s*\/)|(d\s*o\s*t\s*c\s*o\s*m)|(\.\s*x\s*y\s*z)|(x\s*y\s*z\s*\/)|(d\s*o\s*t\s*x\s*y\s*z)|(\.\s*n\s*z)|(\s+n\s*z\s+)|(\s*n\s*z\s*\/)|(d\s*o\s*t\s*n\s*z)|(\.\s*t\s*v)|(\s*t\s*v\s*\/)|(d\s*o\s*t\s*t\s*v)|(\.\s*o\s*r\s*g)|(\s*o\s*r\s*g\s*\/)|(d\s*o\s*t\s*o\s*r\s*g)|(v\s*m\s*\.\s*t\s*i\s*k\s*t\s*o\s*k)'
        self.invitefilter = r'(?i)(t\s*\.m\s*e)|(t\s*d\s*o\s*t\s*m\s*e)|(t\s*m\s*e\s*\/)|(\/\s*j\s*o\s*i\s*n\s*c\s*h\s*a\s*t\s*\/)(.{16})|(^\/.{16}$)|(^.{16}\/$)'
        self.defaultfilters =[
        ("LinkFilter",self.LinkFilter,{"delete":0,"notify":0,},1),
        ("InviteFilter",self.invitefilter,{"delete":0,"notify":0,},1)
        ]
        
 # Access database ===============================================
    def sql(self, query, mode=None):
        if mode is None:
            mode = "Read"
        else:
            mode = "Write"
        self.logger.debug(f"Connecting to DB in {mode} mode")
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        self.logger.debug(f"Executing Query: {query}")
        self.cursor.execute(query)
        if mode == "Read":
            output = self.cursor.fetchall()
            self.logger.debug(f"Retrieved output: {output}")
        if mode == "Write":
            self.connection.commit()
            self.logger.debug(f"Query Written")
        self.cursor.close()
        self.connection.close()
        self.logger.debug(f"Connection Closed")
        if mode == "Read":
            self.logger.debug(f"Returning output")
            return output

  # Instantiate database objects =================================
    def initialize_database(self):
        self.logger.debug("Creating Database")
        try:
            self.logger.debug("Creating chats table")
            self.sql("CREATE TABLE chats (id INTEGER, 'type' TEXT, title TEXT, username TEXT, first_name TEXT, last_name TEXT, bio TEXT, description TEXT, invite_link TEXT, filters TEXT, user_index_date INTEGER, chat_auth INTEGER, CONSTRAINT chats_PK PRIMARY KEY (id))", mode="Write")
            self.logger.debug("Creating users table")
            self.sql("CREATE TABLE users (id INTEGER, first_name TEXT, last_name TEXT, username TEXT, last_message INTEGER, universal_ban INTEGER, is_bot_owner INTEGER, universal_mute INTEGER, CONSTRAINT users_PK PRIMARY KEY (id))", mode="Write")
            self.logger.debug("Creating chat memberships table")
            self.sql("CREATE TABLE chat_memberships ('user' INTEGER, chat INTEGER, CONSTRAINT chat_memberships_PK PRIMARY KEY ('user', chat), CONSTRAINT chat_memberships_FK FOREIGN KEY ('user') REFERENCES users(id), CONSTRAINT chat_memberships_FK_1 FOREIGN KEY (chat) REFERENCES chats(id))", mode="Write")
        except Exception as e:
            self.logger.critical(f"Could not create database: {e}")
            quit()

    def instantiate_user(self, chatid, userid):
        try:
            ChatMember = self.get_chat_member(chatid, userid)
            self.sql(f"INSERT OR REPLACE INTO [users] (id, first_name, last_name, username) VALUES ({ChatMember.user.id}, '{ChatMember.user.first_name}', '{ChatMember.user.last_name}', '{ChatMember.user.username}')",mode="Write")
            #self.sql(f"INSERT OR REPLACE INTO [chat_memberships] (user, chat) VALUES ('{userid}', '{chatid}')")
        except Exception as e:
            self.logger.critical(f"Could not instantate user {ChatMember.user.username} from {chatid}: {e}")

    def instantiate_chat(self,chat): # TODO - When new filters are introduced, instantiate new filters
        try:
            self.sql(f"INSERT OR REPLACE INTO [chats] (id, type, title, username, first_name, last_name, bio, description, invite_link, user_index_date, filters) VALUES ({chat.id}, '{chat.type}', '{chat.title}', '{chat.username}', '{chat.first_name}', '{chat.last_name}', '{chat.bio}', '{chat.description}', '{chat.invite_link}', 1, '{json.dumps(self.defaultfilters)}')", mode="Write")
            self.update_users(chat.id, force=True)
        except Exception as e:
            self.logger.critical(f"Could not instantiate chat info: {e}")
        
    def instantiate_filters(self,chatid): # TODO - parse existing filters, overwrite default filters
        try:
            self.sql(f"UPDATE [chats] set filters='{json.dumps(self.defaultfilters)} WHERE id = {chatid}'")
        except Exception as e:
            self.send_message(chatid, f"Failed to instantiate chat filters: {e}")

  # Update database objects ======================================
    def update_user(self, chatid, userid, message=None):
        # Check if user needs instantiation
        if not self.sql(f"SELECT id FROM users WHERE id LIKE {userid}"):
            self.instantiate_user(chatid, userid)
            return
        # update user info
        try:
            ChatMember = self.get_chat_member(chatid, userid)
            self.sql(f"UPDATE [users] set username='{ChatMember.user.username}', first_name='{ChatMember.user.first_name}', last_name='{ChatMember.user.last_name}' WHERE id = {ChatMember.user.id}", mode="Write")
            # If this is from a message by them, update their last message
            if message is not None and ChatMember.user.id == message.from_user.id:
                self.sql (f"UPDATE [users] set last_message={int(time.time())}",mode="Write")
        except Exception as e:
            self.logger.critical(f"Could not update user index from chat {chatid}: {e}")

    def update_chat(self,chatid):
        chat = self.get_chat(chatid)
        chatid_from_db = self.sql(f"SELECT id FROM chats WHERE id LIKE {chatid}")
        if not chatid_from_db:
            self.instantiate_chat(chat)
            return
        try:
            self.sql(f"UPDATE [chats] set type='{chat.type}', title='{chat.title}', username='{chat.username}', first_name='{chat.first_name}', last_name='{chat.last_name}', bio='{chat.bio}', description='{chat.description}', invite_link='{chat.invite_link}' WHERE id = {chat.id}", mode="Write")
        except Exception as e:
            self.logger.critical(f"Could not update chat info: {e}")
    
    def update_users(self, chatid, force=False):
        last_date = self.sql(f"SELECT user_index_date FROM chats WHERE id LIKE {chatid}")
        if int(time.time() - last_date[0][0] > 3600 or force == True):
            try:
                ChatMembers = self.get_chat_members(chatid)
                for ChatMember in ChatMembers:
                    self.update_user(chatid, ChatMember.user.id)
                self.sql(f"UPDATE [chats] SET user_index_date={int(time.time())}", mode="Write")
            except Exception as e:
                self.logger.critical(f"Could not update user index from chat {chatid}: {e}")
    
    def update_filters(self, chatid, filters):
        try:
            chat_filter_raw = self.sql(f"SELECT filters FROM chats WHERE id LIKE {chatid}")
        except Exception as e:
            self.send_message(chatid, f"Failed to Get the chat filters: {e}")
        chat_filters = json.loads(chat_filter_raw[0][0])
        for f in filters:
            chat_filters.append(f)
        try:
            self.sql(f"UPDATE [chats] set filters='{json.dumps(chat_filters)} WHERE id = {chatid}'")
        except Exception as e:
            self.send_message(chatid, f"Failed to update chat filters: {e}")

  # Read from database ===========================================
    def get_chats(self):
        """Gets a list of chats in the database

            Returns:
                list: Array of uuids for chats
            """
        search = self.sql("SELECT id FROM chats WHERE id LIKE '-%'")
        chats = []
        for chat in search:
            try:
                chats.append(chat[0])
            except:
                pass
        return chats
    
    def get_filters(self, chatid):
        try:
            query = self.sql(f"SELECT filters FROM [chats] WHERE id = '{chatid}'")
            filters = json.loads(query[0][0])
            self.logger.debug(filters)
            return filters
        except Exception as e:
            self.send_message(chatid, f"Failed to read chat filters: {e}")