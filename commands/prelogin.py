from evennia import default_cmds
from evennia.players.models import PlayerDB


class CmdWhoinfo(default_cmds.MuxCommand):
    """Parent class for pre-login who and info commands."""
    locks = "cmd:all()"
    auto_help = True


class CmdWhoUs(CmdWhoinfo):
    key = "who"
    aliases = ["w"]

    def func(self):
        """returns the message"""
        current_users = PlayerDB.objects.get_connected_players()
        self.caller.msg("[%s] Through the fog you see %s:" % (self.key, len(current_users)))
        self.caller.msg("|/".join("%s(%s)" % (char.puppet.key, char.id) for char in current_users))
