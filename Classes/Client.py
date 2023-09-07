import sqlite3, os, logging, time, json
from pyrogram import Client as PyrogramClient
from pyrogram import errors, enums
from Classes.HandlerManager import HandlerManager

class Client(PyrogramClient):

    def __init__(self, bot_owner, flog, slog, glog, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_name = f"{self.name}.db"
        self.db_path = os.path.join("data", self.db_name)
        self.bot_owner = bot_owner
        self.handler_manager = HandlerManager()

       # Root Logging
        self.logger = logging.getLogger('Vampyre')
        if glog == "debug":
            self.logger.setLevel(logging.DEBUG)
        elif glog == "info":
            self.logger.setLevel(logging.INFO)
        elif glog == "warning":
            self.logger.setLevel(logging.WARNING)
        elif glog == "error":
            self.logger.setLevel(logging.ERROR)
        elif glog == "critical":
            self.logger.setLevel(logging.CRITICAL)

       # Stdout Logger
        self.stdout_handler = logging.StreamHandler()
        self.logger.addHandler(self.stdout_handler)
        self.stdout_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        if slog == "debug":
            self.stdout_handler.setLevel(logging.DEBUG)
        elif slog == "info":
            self.stdout_handler.setLevel(logging.INFO)
        elif slog == "warning":
            self.stdout_handler.setLevel(logging.WARNING)
        elif slog == "error":
            self.stdout_handler.setLevel(logging.ERROR)
        elif slog == "critical":
            self.stdout_handler.setLevel(logging.CRITICAL)

       # File logs
        self.file_handler = logging.FileHandler(os.path.join("data", "Vampyre.log"))
        self.logger.addHandler(self.file_handler)
        self.file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        if flog == "debug":
            self.file_handler.setLevel(logging.DEBUG)
        elif flog == "info":
            self.file_handler.setLevel(logging.INFO)
        elif flog == "warning":
            self.file_handler.setLevel(logging.WARNING)
        elif flog == "error":
            self.file_handler.setLevel(logging.ERROR)
        elif flog == "critical":
            self.file_handler.setLevel(logging.CRITICAL)

       # DefaultFilters
        self.LinkFilter = r'(?i)(h\s*t\s*t\s*p)|(h\s*\w\s*\w\s*p\:)|(h\s*\w\s*\w\s*p\s*s\:)|(\:\s*\/\s*\/)|(w\s*w\s*w\s*\.)|(w\s*w\s*w\s*d\s*o\s*t)|(\.\s*g\s*g)|(g\s*g\s*\/)|(d\s*o\s*t\s*g\s*g)|(\.\s*c\s*o\s*m)|(c\s*o\s*m\s*\/)|(d\s*o\s*t\s*c\s*o\s*m)|(\.\s*x\s*y\s*z)|(x\s*y\s*z\s*\/)|(d\s*o\s*t\s*x\s*y\s*z)|(\.\s*n\s*z)|(\s+n\s*z\s+)|(\s*n\s*z\s*\/)|(d\s*o\s*t\s*n\s*z)|(\.\s*t\s*v)|(\s*t\s*v\s*\/)|(d\s*o\s*t\s*t\s*v)|(\.\s*o\s*r\s*g)|(\s*o\s*r\s*g\s*\/)|(d\s*o\s*t\s*o\s*r\s*g)|(v\s*m\s*\.\s*t\s*i\s*k\s*t\s*o\s*k)'
        self.InviteFilter = r'(?i)(t\s*\.m\s*e)|(t\s*d\s*o\s*t\s*m\s*e)|(t\s*m\s*e\s*\/)|(\/\s*j\s*o\s*i\s*n\s*c\s*h\s*a\s*t\s*\/)(.{16})|(^\/.{16}$)|(^.{16}\/$)'
        self.defaultfilters =[
        ("Link Filter",self.LinkFilter,{"delete":0,"notify":0,},1),
        ("Invite Filter",self.InviteFilter,{"delete":0,"notify":0,},1)
        ]

  # Access database ===============================================
    def sql(self, query, params=None, mode=None):
        
        if params is None:
            params = []
        
        if mode is None:
            mode = "Read"
        else:
            mode = "Write"

        for i, param in enumerate(params):
            self.logger.debug(f"Parameter {i+1} is of type {type(param)}")

        self.logger.debug(f"Connecting to DB in {mode} mode")
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()

        self.logger.debug(f"Executing Query: {query}")
        self.cursor.execute(query, params)

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

  # Create operations ============================================
    def initialize_database(self):
        self.logger.debug("Creating Database")
        try:
            self.logger.debug("Creating chats table")
            self.sql("CREATE TABLE chats (id INTEGER, 'type' TEXT, title TEXT, username TEXT, first_name TEXT, last_name TEXT, bio TEXT, description TEXT, invite_link TEXT, filters TEXT, user_index_date INTEGER DEFAULT (1), chat_auth INTEGER, CONSTRAINT chats_PK PRIMARY KEY (id))", mode="Write")
            self.logger.debug("Creating users table")
            self.sql("CREATE TABLE users (id INTEGER, first_name TEXT, last_name TEXT, username TEXT, universal_ban INTEGER, is_bot_owner INTEGER, universal_mute INTEGER, CONSTRAINT users_PK PRIMARY KEY (id))", mode="Write")
            self.logger.debug("Creating chat memberships table")
            self.sql("CREATE TABLE chat_memberships ('user' INTEGER, chat INTEGER, ban_reason TEXT DEFAULT ('Not Banned'), last_message INTEGER, status TEXT, CONSTRAINT chat_memberships_PK PRIMARY KEY ('user', chat), CONSTRAINT chat_memberships_FK FOREIGN KEY ('user') REFERENCES users(id), CONSTRAINT chat_memberships_FK_1 FOREIGN KEY (chat) REFERENCES chats(id))", mode="Write")
        except Exception as e:
            self.logger.critical(f"Could not create database: {e}")
            quit()

    def instantiate_user(self, userid):
        self.logger.info(f"instantiate_user | userid: {userid}")
        try:
            self.logger.info("Instantiating user in database")
            user = self.get_users(userid)
            self.sql(f"INSERT OR REPLACE INTO [users] (id, first_name, last_name, username) VALUES (?, ?, ?, ?)", params=[user.id, user.first_name, user.last_name, user.username], mode="Write")
            self.logger.info("Success")
            return True
        except Exception as e:
            self.logger.critical(f"Could not instantiate user: {e}")
            return False

    def instantiate_chat(self, chatid): # TODO - When new filters are introduced, instantiate new filters
        """creates chat record and updates users index for the chat

            Args:
                chatid (int): chatid

            Returns:
                bool: True - If chat record was created with user's index
            """
        self.logger.info(f"instantiate_chat | chatid: {chatid}")
        try:
            self.logger.info("creating chat record")
            chat = self.get_chat(chatid)
            self.sql(f"INSERT OR REPLACE INTO [chats] (id, type, title, username, first_name, last_name, bio, description, invite_link, user_index_date, filters) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)", params=[chat.id, str(chat.type), chat.title, chat.username, chat.first_name, chat.last_name, chat.bio, chat.description, chat.invite_link, json.dumps(self.defaultfilters)], mode="Write")
            self.logger.info("Success")
            self.update_users(chatid, force=True)
            self.handler_manager.unload_filters(self)
            self.handler_manager.load_filters(self)
            return True
        except Exception as e:
            self.logger.critical(f"Could not instantiate chat info: {e}")

    def instantiate_chat_membership(self, chatid, userid):
        self.logger.info(f"instantiate_chat_membership | chatid: {chatid} | userid: {userid}")
        try:
            self.logger.info("Instantiating membership")
            self.sql("INSERT INTO [chat_memberships] (user, chat) VALUES (?, ?)", [userid, chatid], mode="Write")
            self.logger.debug("Done instantiation")
            return True
        except Exception as e:
            self.logger.critical(f"Failed to instantiate chat membership. Reason: {e}")
            return False

  # Read from database ===========================================
    def does_user_exist(self, userid):
        self.logger.info(f"does_user_exist | userid: {userid}")
        if not self.sql("SELECT id FROM users WHERE id LIKE ?", [userid]):
            self.logger.info("User doesn't exist")
            return self.instantiate_user(userid)
        else:
            self.logger.info("User does exist")
            return True

    def does_chat_exist(self, chatid):
        self.logger.info(f"does_chat_exist | userid: {chatid}")
        if not self.sql("SELECT id FROM chats WHERE id LIKE ?", [chatid]):
            self.logger.info("chat doesn't exist")
            return self.instantiate_chat(chatid)
        else:
            self.logger.info("chat does exist")
            return True

    def does_chat_membership_exist(self, chatid, userid):
        self.logger.info(f"does_chat_membership_exist | chatid: {chatid} | userid: {userid}")
        if not self.does_user_exist(userid):
            raise Exception("Chat_membership can't exist because user doesn't exist, and can't be made")
            return
        if not self.does_chat_exist(chatid):
            raise Exception("Chat_membership can't exist because chat doesn't exist, and can't be made")
            return
        if not self.sql("SELECT * FROM chat_memberships WHERE user LIKE ? AND chat LIKE ?", [userid, chatid]):
            self.logger.debug("Record doesn't exist")
            return self.instantiate_chat_membership(chatid, userid)
        else:
            self.logger.info("chat_membership does exist")
            return True

    def get_user_admin_list(self, userid):
        """returns a list of tuples containing chatids

        Args:
            userid (int): userid

        Returns:
            list: list of chatids
        """
        if not self.does_user_exist:
            return
        try:
            listraw = self.sql("SELECT chat in [chat_memberships] WHERE user LIKE ? AND status 'administrator'", [userid])
            return listraw
        except Exception as e:
            self.logger.critical(f"Failed to retrieve list of chats {userid} is admin in")

    def get_chats(self):
        """Gets a list of chats in the database

            Returns:
                list: Array of uuids for chats
            """
        search = self.sql("SELECT id FROM chats WHERE id LIKE '-%'")
        chats = []
        for chat in search:
            chats.append(chat[0])
        return chats

    def get_ban_reason(self, chatid, userid):
        self.does_user_exist(userid)
        try:
            query = self.sql("SELECT ban_reason from [chat_memberships] WHERE user LIKE ? and chat LIKE ?", [userid, chatid])
            return query[0][0]
        except Exception as e:
            self.logger.critical(f"Failed to update ban reason: {userid}:user | {chatid}:chat")

    def get_uban_status(self, userid):
        self.does_user_exist(userid)
        try:
            query = self.sql("SELECT universal_ban from [users] WHERE id LIKE ?", [userid])
            return query[0][0]
        except Exception as e:
            self.logger.critical(f"Could not get universal ban status: {e}")

    def get_uban_users(self):
        try:
            users = self.sql("SELECT id from [users] WHERE universal_ban=?", [1])
            return users
        except Exception as e:
            self.logger.critical("Could not return users who are banned universally")

    def get_filters(self, chatid):
        try:
            query = self.sql("SELECT filters FROM [chats] WHERE id = ?", [chatid])
            filters = json.loads(query[0][0])
            self.logger.debug(filters)
            return filters
        except Exception as e:
            self.send_message(chatid, f"Failed to read chat filters: {e}")

  # Update operations ============================================

    def update_chat(self,chatid):
        """Updates chat information in db

        Args:
            chatid (int): chatid

        Returns:
            bool: True - If chat was updated
        """
        self.logger.info(f"update_chat | chatid: {chatid}")
        self.logger.info("Making sure chat exists in db")
        if self.does_chat_exist(chatid):
            chat = self.get_chat(chatid)
            try:
                self.sql("UPDATE [chats] set type=?, title=?, username=?, first_name=?, last_name=?, bio=?, description=?, invite_link=? WHERE id = ?", [str(chat.type), chat.title, chat.username, chat.first_name, chat.last_name, chat.bio, chat.description, chat.invite_link, chat.id], mode="Write")
                return True
            except Exception as e:
                self.logger.critical(f"Could not update chat info: {e}")
                return
        self.logger.critical("Chat failed to be updated")
    
    def update_user(self, chatid, userid, message=None):
        """Updates a single user

        Args:
            chatid (int): chatid
            userid (int): userid
            message (message, optional): message. Defaults to None.
        """
        # Log things
        self.logger.info(f"update_user | chatid: {chatid} | userid: {userid}")
        if message:
            self.logger.info("Message is present")
        
        self.logger.info("Making sure user exists in db")
        if self.does_user_exist(userid):
            try:
                self.logger.info("Updating user info")
                ChatMember = self.get_chat_member(chatid, userid)
                self.sql("UPDATE [users] set username=?, first_name=?, last_name=? WHERE id = ?", [ChatMember.user.username, ChatMember.user.first_name, ChatMember.user.last_name, ChatMember.user.id], mode="Write")
                
                # If this is from a message by them, update their last message
                if message is not None and ChatMember.user.id == message.from_user.id:
                    self.logger.info("Updating last_message time")
                    self.update_lastmessage(chatid, userid, int(time.time()))
            except Exception as e:
                self.logger.critical(f"Could not update user from chat {chatid}: {e}")
    
    def update_users(self, chatid, force=False):
        """_summary_

        Args:
            chatid (_type_): _description_
            force (bool, optional): _description_. Defaults to False.
        """
        self.logger.info(f"update_users | chatid: {chatid} | Force: {force}")
        self.logger.info("Getting last date")
        last_date = self.sql(f"SELECT user_index_date FROM chats WHERE id LIKE {chatid}")
        self.logger.debug(last_date)
        if int(time.time() - last_date[0][0] > 3600 or force):
            self.logger.info("Updating user index")
            try:
                ChatMembers = self.get_chat_members(chatid)
                for ChatMember in ChatMembers:
                    self.update_user(chatid, ChatMember.user.id)
                self.sql("UPDATE [chats] SET user_index_date=?", [int(time.time())], mode="Write")
                return
            except Exception as e:
                self.logger.critical(f"Could not update user index from chat {chatid}: {e}")
                return
        self.logger.info("Too Soon to update")

    def add_universal_ban(self, userid):
        if self.does_user_exist(userid):
            try:
                self.sql("UPDATE [users] set universal_ban=? WHERE id LIKE ?", [1, userid], mode="Write")
            except Exception as e:
                self.logger.critical(f"Could not store universal ban, user will be able to join new chats where not banned")  

    def update_status(self, chatid, userid):
        if self.does_chat_membership_exist(chatid, userid):
            try:
                chatmember = self.get_chat_member(chatid, userid)
                self.sql("UPDATE [chat_memberships] set status=? WHERE user LIKE ? and chat LIKE ?", [f"{chatmember.user.status}", userid, chatid], mode="Write")
            except Exception as e:
                self.logger.critical(f"Failed to update ban reason: {userid}:user | {chatid}:chat\n{e}")

    def update_ban_reason(self, chatid, userid, reason):
        if self.does_chat_membership_exist(chatid, userid):
            try:
                self.sql("UPDATE [chat_memberships] set ban_reason=? WHERE user LIKE ? and chat LIKE ?", [reason, userid, chatid], mode="Write")
            except Exception as e:
                self.logger.critical(f"Failed to update ban reason: {userid}:user | {chatid}:chat\n{e}")

    def update_lastmessage(self, chatid, userid, time):
        if self.does_chat_membership_exist(chatid, userid):
            try:
                self.sql("UPDATE [chat_memberships] set last_message=?", [time], mode="Write")
            except Exception as e:
                self.logger.critical(f"Failed to update last_message time: {userid}:user | {chatid}:chat")
    
    def update_filters(self, chatid, filters):
        try:
            chat_filter_raw = self.sql("SELECT filters FROM chats WHERE id LIKE ?", [chatid])
        except Exception as e:
            self.send_message(chatid, f"Failed to Get the chat filters: {e}")
        chat_filters = json.loads(chat_filter_raw[0][0])
        for f in filters:
            chat_filters.append(f)
        try:
            self.sql("UPDATE [chats] set filters=? WHERE id = ?", [json.dumps(chat_filters), chatid])
        except Exception as e:
            self.send_message(chatid, f"Failed to update chat filters: {e}")
    
    def instantiate_filters(self,chatid): # TODO - parse existing filters, overwrite default filters
        try:
            self.sql("UPDATE [chats] set filters=? WHERE id = ?", [json.dumps(self.defaultfilters), chatid])
        except Exception as e:
            self.send_message(chatid, f"Failed to instantiate chat filters: {e}")

  # Delete operations ============================================
    def delete_user(self, userid): # TODO - There is currently no need to delete a user
        pass 

    def delete_chat(self, chatid): # TODO - Delete chat
        pass

    def delete_filter(self, chatid, filter): # TODO - remove a filter
        pass