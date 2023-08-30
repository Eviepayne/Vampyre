# Vampyre Telegram Bot

## Setup
Quick steps to get the bot up and running.

### Configure `config.ini`

Edit the `config.ini` file to set the bot configurations.

```ini
[bot]                            # Do not change this
flog = warning                   # File log level in the /data folder
slog = info                      # Console log level in the terminal
glog = debug                     # Global minimum log level across file and console
app_name = Vampyre               # App name
api_id = 1234567                 # Get this from https://my.telegram.org/apps
api_hash = 11111111111111111111  # Get this from https://my.telegram.org/apps
bot_token = 1234567890:token     # Get this from BotFather
bot_owner = 123456789            # Run the bot once and use /id to get the ID
```

### Ignore Changes in `config.ini` 

To prevent `git` from tracking changes to `config.ini`, run the following command in the repository:

```bash
git update-index --assume-unchanged config.ini
```

This ensures that your `config.ini` changes don't interfere with the repository.

### Set Up Virtual Environment

If you haven't already, install `pip` and `virtualenv`, then run:

```bash
virtualenv .venv
source ./.venv/bin/activate
pip install -r ./requirements.txt
```

### Run the Bot

To start the bot, execute:

```bash
./Vampyre.py
```