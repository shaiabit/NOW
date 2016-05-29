from evennia import default_cmds

class CmdExit(default_cmds.MuxCommand):
    "Parent class for all exit-directions."        
    locks = "cmd:all()"
    auto_help = False

    def func(self):
        "returns the error"
        self.caller.msg("You cannot move %s." % self.key)   

class CmdExitNorth(CmdExit):
    key = "north"
    aliases = ["n"]

class CmdExitEast(CmdExit):
    key = "east"
    aliases = ["e"]

class CmdExitSouth(CmdExit):
    key = "south"
    aliases = ["s"]

class CmdExitWest(CmdExit):
    key = "west"
    aliases = ["w"]