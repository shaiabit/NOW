from evennia import default_cmds


class CmdWhoinfo(default_cmds.MuxCommand):
    "Parent class for pre-login who and info commands."
    locks = "cmd:all()"
    auto_help = True

class CmdWhoUs(CmdWhoinfo):
    key = "who"
    aliases = ["w"]

    def func(self):
        "returns the message"
        self.caller.msg("[%s] You cannot see us through the fog." % self.key)   
