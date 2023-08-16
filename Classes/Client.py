import sqlite3, os, logging, time
from pyrogram import Client as PyrogramClient

class Client(PyrogramClient):

    def __init__(self, *args, logger, bot_owner, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_name = f"{self.name}.db"
        self.db_path = os.path.join("data", self.db_name)
        self.logger = logger
        self.file_handler = logging.FileHandler('Vampyre.log')
        self.file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(self.file_handler)
        self.bot_owner = bot_owner
        self.linkfilter = r'(?i)(h\s*t\s*t\s*p)|(h\s*\w\s*\w\s*p\:)|(h\s*\w\s*\w\s*p\s*s\:)|(\:\s*\/\s*\/)|(w\s*w\s*w\s*\.)|(w\s*w\s*w\s*d\s*o\s*t)|(\.\s*g\s*g)|(g\s*g\s*\/)|(d\s*o\s*t\s*g\s*g)|(\.\s*c\s*o\s*m)|(c\s*o\s*m\s*\/)|(d\s*o\s*t\s*c\s*o\s*m)|(\.\s*x\s*y\s*z)|(x\s*y\s*z\s*\/)|(d\s*o\s*t\s*x\s*y\s*z)|(\.\s*n\s*z)|(\s+n\s*z\s+)|(\s*n\s*z\s*\/)|(d\s*o\s*t\s*n\s*z)|(\.\s*t\s*v)|(\s*t\s*v\s*\/)|(d\s*o\s*t\s*t\s*v)|(\.\s*o\s*r\s*g)|(\s*o\s*r\s*g\s*\/)|(d\s*o\s*t\s*o\s*r\s*g)|(v\s*m\s*\.\s*t\s*i\s*k\s*t\s*o\s*k)'
        self.invitefilter = r'(?i)(t\s*\.m\s*e)|(t\s*d\s*o\s*t\s*m\s*e)|(t\s*m\s*e\s*\/)|(\/\s*j\s*o\s*i\s*n\s*c\s*h\s*a\s*t\s*\/)(.{16})|(^\/.{16}$)|(^.{16}\/$)'

    def sql(self, query, mode=None):
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        self.cursor.execute(query)
        if mode is None:
            output = self.cursor.fetchall()
        if mode == "Write":
            self.connection.commit()
        self.cursor.close()
        self.connection.close()
        if mode == None:
            return output

    #def Keyboard(self, )

    def initialize_database(self):
        try:
            self.sql("CREATE TABLE chats (id INTEGER, 'type' TEXT, title TEXT, username TEXT, first_name TEXT, last_name TEXT, bio TEXT, description TEXT, invite_link TEXT, filters TEXT, user_index_date INTEGER, chat_auth INTEGER, CONSTRAINT chats_PK PRIMARY KEY (id))", mode="Write")
            self.sql("CREATE TABLE users (id INTEGER, first_name TEXT, last_name TEXT, username TEXT, last_message INTEGER, universal_ban INTEGER, is_bot_owner INTEGER, universal_mute INTEGER, CONSTRAINT users_PK PRIMARY KEY (id))", mode="Write")
            self.sql("CREATE TABLE chat_memberships ('user' INTEGER, chat INTEGER, CONSTRAINT chat_memberships_PK PRIMARY KEY ('user', chat), CONSTRAINT chat_memberships_FK FOREIGN KEY ('user') REFERENCES users(id), CONSTRAINT chat_memberships_FK_1 FOREIGN KEY (chat) REFERENCES chats(id))", mode="Write")
        except Exception as e:
            self.logger.critical(f"Could not create database: {e}")
            quit()

    def instantiate_user(self, chatid, userid):
        try:
            ChatMember = self.get_chat_member(chatid, userid)
            self.sql(f"INSERT OR REPLACE INTO [users] (id, first_name, last_name, username) VALUES ({ChatMember.user.id}, '{ChatMember.user.first_name}', '{ChatMember.user.last_name}', '{ChatMember.user.username}')",mode="Write")
        except Exception as e:
            self.logger.critical(f"Could not instantate user {ChatMember.user.username} from {chatid}: {e}")

    def update_user(self, chatid, userid, message=None):
        # Check if user needs instantiation
        userid_from_db = self.sql(f"SELECT id FROM users WHERE id LIKE {userid}")
        if not userid_from_db:
            self.instantiate_user(chatid, userid)
            return
        # update user info
        try:
            ChatMember = self.get_chat_member(chatid, userid)
            self.sql(f"UPDATE [users] set username='{ChatMember.user.username}', first_name='{ChatMember.user.first_name}', last_name='{ChatMember.user.last_name}' WHERE id = {ChatMember.user.id}", mode="Write")
            # If this is from a message by them, update their last message
            if not message is None and ChatMember.user.id == message.from_user.id:
                self.sql (f"UPDATE [users] set last_message={int(time.time())}",mode="Write")
        except Exception as e:
            self.logger.critical(f"Could not update user index from chat {chatid}: {e}")

    def instantiate_chat(self,chat):
        try:
            self.sql(f"INSERT OR REPLACE INTO [chats] (id, type, title, username, first_name, last_name, bio, description, invite_link, user_index_date) VALUES ({chat.id}, '{chat.type}', '{chat.title}', '{chat.username}', '{chat.first_name}', '{chat.last_name}', '{chat.bio}', '{chat.description}', '{chat.invite_link}', 1)", mode="Write")
            self.update_users(chat.id,force=True)
        except Exception as e:
            self.logger.critical(f"Could not instantiate chat info: {e}")

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
