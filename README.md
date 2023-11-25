# Destiny Discord Bots

> Fair warning: these bots aren't really Destiny-focused. If you're looking for anything to interface with Destiny or Bungie APIs, you won't find that here. These are just some bots I made for a Destiny-oriented server for me and my friends.

## Description

This project consists of several Python scripts that interact with the Discord API using the Disnake library. The scripts perform various tasks such as managing roles and handling temporary voice channels.

I wrote these scripts primarily for a Destiny-focused gaming server for me and my friends, but they should be applicable to other things as well with some small modifications - I particularly like the temporary VC bot, it allows the server to scale dynamically quite nicely. For a large server it would probably need some optimizations (potentially a database instead of a little json file, as well as some error-checking to remove orphaned VCs if the bot gets rate-limited or something), but for a relatively small or quiet server it works great as is.

## Installation

To install the required dependencies, run the following command:

```sh
pip install -r ./requirements.txt
```

## Usage

The project consists of several scripts that can be run independently. Here's how to use each one:

### Ping Bot

The Ping Bot pings a specific user when they go offline. To use it, run the following command:

```bash
python3 ./ping.py
```

### Roles Bot

The Roles Bot manages roles in a Discord server. To use it, run the following command:

```bash
python3 ./roles.py
```

### Temporary Voice Channels Bot

The Temporary Voice Channels Bot manages temporary voice channels in a Discord server. To use it, run the following command:

```bash
python3 ./temp_vc.py
```

## Environment Variables

The scripts use environment variables for configuration. You can set these variables in a `.env` file. Here's an example:

```
TEMP_CHANNELS_DISCORD_TOKEN=YOUR_TOKEN_HERE
ROLES_DISCORD_TOKEN=YOUR_TOKEN_HERE
PING_TARGET=USER_ID_HERE
TEST_GUILD=YOUR_GUILD_ID_HERE
```
