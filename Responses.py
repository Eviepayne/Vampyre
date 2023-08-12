HELP_DIALOG = """
Legend:
[optional args]
![mandatory args]
[option1 | option2 | option3]

Commands:
/help, /h, /start:
Will give you this Help dialog

/getid [@user]:
Will return your ID or another user's ID if they're mentioned.

/getchid:
Will return the chat ID

/bait:
Will tell you if you're in the pedohunter list pedohunter

/istrusted [@user]:
Will return if the specified user is trusted.
If no arguments are given, it will give your own trusted status.

# Admin only commands ============================================

/ban, /b ![@user | userID] [type anything here as a reason]:
Will ban someone, you can optionally make a reason.
    Example: /ban @stupiduser this is a reason
    Example: /ban 236134137

/clean, /p, /purge:
! requires that you replied to the message you want to delete to
This will delete all the messages from yours to the replied message.

/trust ![@user]:
Will add users to the trusted list. A trusted user can bypass all enabled filters.

/untrust ![@user]:
Will remove users from the trusted list.

# What this bot does =============================================

Link filter:
Will always delete links. Admins/trusted excepted. If a link get's through please report to @VladTheImplier

Snap hack beg filter:
These guys are annoying. Will do it's best to remove messages from people begging.

Pedo Filter:
Far from perfect, but will attempt to remove people it suspects are pedophiles.
A bot that is better than this one for this would be @antipedo2_bot

Invite Filter:
Will automatically remove telegram invites.

Forward filter:
A popular way to bypass advertizing filters is for people to forward from the channel account using the anonymous admin feature.
This stops that from happening.

Command Cleaner:
Will automatically remove commands from other bots, because they leave a mess/spam.

service message cleaner:
Removes all toast messages.
    join messages
    leave messages
    Pin notifications
    Changes to chat

This bot was made by https://github.com/Eviepayne
"""