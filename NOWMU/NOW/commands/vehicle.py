from evennia import CmdSet
from evennia import default_cmds


class VehicleCmdSet(CmdSet):
    def at_cmdset_creation(self):
        """Add command to the set - this set will be attached to the vehicle object (item or room)."""
        self.add(CmdVehicle())


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


class CmdVehicle(CmdVehicleDefault):
    """
    Operate various aspects of the vehicle as configured.
    Usage:
      vehicle  display other commands available.
    """
    aliases = ['board', 'enter', 'disembark', 'exit', 'leave', 'operate']

    def func(self):
        """ """
        cmd = self.cmdstring
        args = self.args.strip()
        char = self.character
        where = self.obj
        # here = char.location
        outside = where.location
        player = self.player
        if 'vehicle' in cmd:
            player.msg('|wCommand list for %s%s|n:|/|C%s' % (where.STYLE, where.key, '|n, |C'.join(self.aliases)))
        if 'board' in cmd or 'enter' in cmd:
            entry_message = where.db.messages['entry']
            char.msg('%s%s|n %s' % (char.STYLE, char.key, entry_message))
            player.msg("You board %s." % where.get_display_name(player))
            char.move_to(where)
            self.send_msg('%s%s|n %s' % (char.STYLE, char.key, entry_message))
        if 'disembark' in cmd or 'exit' in cmd or 'leave' in cmd:
            exit_message = where.db.messages['exit']
            char.msg('%s%s|n %s' % (char.STYLE, char.key, exit_message))
            player.msg("You disembark %s." % where.get_display_name(player))
            self.send_msg('%s%s|n %s' % (char.STYLE, char.key, exit_message))
            char.move_to(outside)
        if 'operate' in cmd:
            self.send_msg("%s%s|n commands in-operable %s%s|n vehicle to %s." %
                          (char.STYLE, char.key, where.STYLE, where.key, args))
            self.send_msg("%s%s|n does nothing." % (where.STYLE, where.key))
