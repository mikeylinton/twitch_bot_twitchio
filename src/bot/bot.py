import os
from twitchio.ext import commands
from twitchio.ext.commands.errors import TwitchCommandError
from oauth.oauth import get_token
from bot.commands import attach_commands_from_file_to_bot, Command

# ENV vars
TWITCH_CHANNEL_LIST = "TWITCH_CHANNEL_LIST"
TWITCH_CLIENT_ID = "TWITCH_CLIENT_ID"
TWITCH_CLIENT_SECRET = "TWITCH_CLIENT_SECRET"


class Bot(commands.Bot):
    def __init__(self):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        super().__init__(
            token=get_token(),
            prefix="?",
            initial_channels=os.environ[TWITCH_CHANNEL_LIST].split(","),
        )

    async def event_ready(self):
        # We are logged in and ready to chat and use commands...
        print(f"Logged in as | {self.nick}")
        print(f"User id is | {self.user_id}")
        attach_commands_from_file_to_bot(self)

    # Built-in commands

    @commands.command()
    async def addcommand(self, ctx: commands.Context):
        ret = ctx.message.content.split()
        cmd_name = ret[1]
        cmd_str = " ".join(ret[2::])
        try:
            self.add_command(Command(cmd_name, cmd_str))
            await ctx.send(f"Command {self._prefix}{cmd_name} added!")
        except TwitchCommandError:
            await ctx.send(f"Command {self._prefix}{cmd_name} already exists!")
