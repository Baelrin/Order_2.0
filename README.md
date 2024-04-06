# Order_2.0

Order_2.0 is a Discord bot designed to manage roles and send messages based on user join time. It's built with Python using the discord.py library, which allows for easy interaction with the Discord API.

## Features

- **Role Management**: Automatically changes user roles based on their join time.
- **Message Sending**: Sends congratulatory messages to users when their roles are changed.
- **Admin Role Check**: Ensures that only users with the admin role can execute certain commands.
- **Join Time Threshold**: Allows for customization of the join time threshold for role changes.

## Setup

1. **Environment Variables**: Create a `.env` file in the root directory of the project. Add your Discord bot token and any other necessary environment variables.

2. **Configuration**: Create a `config.json` file in the root directory. This file should contain the following keys:

   - `ADMIN_ROLE_ID`: The ID of the admin role.
   - `OLD_ROLE_ID`: The ID of the old role to be removed.
   - `NEW_ROLE_ID`: The ID of the new role to be added.
   - `CHANNEL_ID`: The ID of the channel where messages will be sent.
   - `JOIN_TIME_THRESHOLD`: The join time threshold in seconds for role changes.
   - `TIMEZONE`: The timezone for join time calculations.
   - `PREFIX`: The prefix for bot commands.
   - `LOG_FILE`: The path to the log file.

3. **Dependencies**: Install the required Python packages by running `pip install -r requirements.txt`.

4. **Running the Bot**: Execute `python master.py` to start the bot.

## Commands

- `C [threshold]`: Changes the roles of users who have been in the server longer than the specified threshold and sends them a congratulatory message.
- `c [threshold]`: Same as `C`, but with a lowercase prefix.

## Contributing

Contributions are welcome. Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.
