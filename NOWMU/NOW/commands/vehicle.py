from evennia import CmdSet
from evennia import default_cmds


class VehicleCmdSet(CmdSet):
    def at_cmdset_creation(self):
        """Add command to the set - this set will be attached to the vehicle object (item or room)."""
        self.add(CmdBoard())
        self.add(CmdDisembark())
        self.add(CmdDrive())


class CmdVehicleDefault(default_cmds.MuxCommand):
    """Add command to the set - this set will be attached to the vehicle object (item or room)."""
    key = 'vehicle'
    locks = 'cmd:all()'
    help_category = 'Travel'
    player_caller = True

    def send_msg(self, message):
        """Send message internal and external to vehicle"""
        char = self.character
        where = self.obj
        outside = where.location
        where.msg_contents(message, exclude=char)
        outside.msg_contents(message)


class CmdBoard(CmdVehicleDefault):
    """
    Board the vehicle.
    Usage:
      board
    """
    key = 'board'
    aliases = ['enter']

    def func(self):
        """ """
        # cmd = self.cmdstring
        # args = self.args.strip()
        char = self.character
        # here = char.location
        where = self.obj
        player = self.player
        entry_message = where.db.messages['entry']
        char.msg('%s%s|n %s' % (char.STYLE, char.key, entry_message))
        player.msg("You board %s." % where.get_display_name(player))
        char.move_to(where)
        self.send_msg('%s%s|n %s' % (char.STYLE, char.key, entry_message))


class CmdDisembark(CmdVehicleDefault):
    """
    Disembark the vehicle.
    Usage:
      disembark
    """
    key = 'disembark'
    aliases = ['exit', 'leave']

    def func(self):
        """ """
        cmd = self.cmdstring
        # args = self.args.strip()
        char = self.character
        # here = char.location
        where = self.obj
        outside = where.location
        player = self.player

        player.msg("%s commands: %s" % (char.get_display_name(player), cmd))
        player.msg("You disembark %s." % where.get_display_name(player))
        char.move_to(outside)


class CmdDrive(CmdVehicleDefault):
    """
    Operate the vehicle
    Usage:
      drive
      fly
    """
    key = 'drive'
    aliases = ['fly', 'sail', 'go', 'move']

    def func(self):
        """ """
        # cmd = self.cmdstring
        args = self.args.strip()
        char = self.character
        # player = self.player
        where = self.obj
        # here = char.location
        self.send_msg("%s%s|n commands in-operable %s%s|n vehicle to %s." %
                      (char.STYLE, char.key, where.STYLE, where.key, args))
        self.send_msg("%s%s|n does nothing." % (where.STYLE, where.key))
