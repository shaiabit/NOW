from evennia import CmdSet
from evennia import default_cmds


class VehicleCmdSet(CmdSet):
    key = 'vehicle'

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
        """Send message internal and external to vehicle and optionally move vehicle."""
        char = self.character
        where = self.obj
        outside = where.location
        where.msg_contents(message, exclude=char)
        outside.msg_contents(message, exclude=char)


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
        here = char.location
        outside = where.location
        player = self.player
        if 'vehicle' in cmd:
            player.msg('|wCommand list for %s%s|n:|/|C%s' % (where.STYLE, where.key, '|n, |C'.join(self.aliases)))
        if 'board' in cmd or 'enter' in cmd:
            if here == where:
                player.msg("You are already aboard %s." % where.get_display_name(player))
                return
            entry_message = None
            if 'entry' in where.db.messages:
                entry_message = where.db.messages['entry']
            if entry_message:
                char.msg('%s%s|n %s' % (char.STYLE, char.key, entry_message))
            player.msg("You board %s." % where.get_display_name(player))
            if entry_message:
                where.msg_contents('%s%s|n %s' % (char.STYLE, char.key, entry_message), exclude=char)
            char.move_to(where)
            if entry_message:
                outside.msg_contents('%s%s|n %s' % (char.STYLE, char.key, entry_message))
        if 'disembark' in cmd or 'exit' in cmd or 'leave' in cmd:
            if here != where:
                player.msg("You are not aboard %s." % where.get_display_name(player))
                return
            exit_message = None
            if 'exit' in where.db.messages:
                exit_message = where.db.messages['exit']
            player.msg("You disembark %s." % where.get_display_name(player))
            if exit_message:
                self.send_msg('%s%s|n %s' % (char.STYLE, char.key, exit_message))
            char.move_to(outside)
            if exit_message:
                char.msg('%s%s|n %s' % (char.STYLE, char.key, exit_message))
        if 'operate' in cmd:
            self.send_msg("%s%s|n commands in-operable %s%s|n vehicle to %s." %
                          (char.STYLE, char.key, where.STYLE, where.key, args))
            player.msg("%s%s|n commands in-operable %s%s|n vehicle to %s." %
                       (char.STYLE, char.key, where.STYLE, where.key, args))
            self.send_msg("%s%s|n does nothing." % (where.STYLE, where.key))
            player.msg("%s%s|n does nothing." % (where.STYLE, where.key))
