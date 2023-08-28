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
        self.file_handler = logging.FileHandler('Vampyre.log')
        self.logger.addHandler(self.file_handler)
        self.file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        
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

    def instantiate_chat(self,chat):
        try:
            self.sql(f"INSERT OR REPLACE INTO [chats] (id, type, title, username, first_name, last_name, bio, description, invite_link, user_index_date) VALUES ({chat.id}, '{chat.type}', '{chat.title}', '{chat.username}', '{chat.first_name}', '{chat.last_name}', '{chat.bio}', '{chat.description}', '{chat.invite_link}', 1)", mode="Write")
            self.update_users(chat.id,force=True)
        except Exception as e:
            self.logger.critical(f"Could not instantiate chat info: {e}")
        
        # write the default filters
        # FilterManager = FilterManager()
        # messagefilters = []
        # try:
        #     self.sql(f"UPDATE [chats] set filters='{json.dumps(FilterManager.defaultfilters)}'")
        # except Exception as e:
        #     print(e)

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