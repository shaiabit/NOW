# -*- coding: UTF-8 -*-
from commands.command import MuxCommand


class CmdTeleport(MuxCommand):
    """
    Change object's location - IC component-aware.
    If no object is given, you are teleported to the target location.
    Usage:
      tel/switch [<object> =] <target location>
    Options:
    /quiet     don't echo leave/arrive messages to the source/target
               locations for the move.
    /into      if target is an exit, teleport INTO
               the exit object instead of to its destination
    /to        if target is not a room, teleport to its location.
    /vanish    if set, teleport the object into Nothingness. If this
               option is used, <target location> is ignored.
               Note that the only way to retrieve an object from
               Nothingness is by direct #dbref reference.
    Examples:
      tel Limbo
      tel/quiet box=fog
      tel/vanish box
    """
    key = 'teleport'
    aliases = ['tport', 'tel']
    locks = 'cmd:perm(teleport) or perm(Builders)'
    help_category = 'Travel'

    def func(self):
        """Performs the teleport, accounting for in-world conditions."""

        char = self.character
        cmd = self.cmdstring
        player = self.player
        args = self.args
        lhs, rhs = self.lhs, self.rhs
        opt = self.switches

        if char and char.ndb.currently_moving:
            player.msg("You can not teleport while moving. (|rstop|n, then try again.)")
            return

        # setting command options
        tel_quietly = 'quiet' in opt or 'silent' in opt
        to_none = 'vanish' in opt

        search_as = player.db._playable_characters[0]
        if not search_as:
            search_as = player.db._last_puppet
        if not search_as:
            player.msg("|yMust be |c@ic|y to use |g%s|w." % cmd)
            return

        if to_none:  # teleporting to Nothingness
            if not args and char:
                target = char
                player.msg("|*Teleported to Nothingness.|n")
                if char and char.location and not tel_quietly:
                    char.location.msg_contents("|r%s|n vanishes." % char, exclude=char)
            else:
                target = search_as.search(lhs, global_search=True)
                if not target:
                    player.msg("Did not find object to teleport.")
                    return
                if not player.check_permstring('Mages') or not target.access(player, 'control'):
                    player.msg("You must have |wMages|n or higher access to send something into |222Nothingness|n.")
                    return
                player.msg("Teleported %s -> None-location." % (target.get_display_name(player)))
                if target.location and not tel_quietly:
                    if char and char.location == target.location and char != target:
                        target.location.msg_contents("%s%s|n sends %s%s|n into |222Nothingness|n."
                                                     % (char.STYLE, char, target.STYLE, target))
                    else:
                        target.location.msg_contents("|r%s|n vanishes into |222Nothingness|n." % target)
            target.location = None
            return
        if not args:
            player.msg("Usage: teleport[/options] [<obj> =] <target_loc>||home")
            return
        if rhs:
            target = search_as.search(lhs, global_search=True)
            loc = search_as.search(rhs, global_search=True)
        else:
            target = char
            loc = search_as.search(lhs, global_search=True)
        if not target:
            player.msg("Did not find object to teleport.")
            return
        if not loc:
            player.msg("Destination not found.")
            return
        if target == loc:
            player.msg("You can not teleport an object inside of itself!")
            return
        print("%s is trying to go to %s" % (target.key, loc.key))
        if target == loc.location:
            player.msg("You can not teleport an object inside something it holds!")
            return
        if target.location and target.location == loc:
            player.msg("%s is already at %s." % (target.get_display_name(player), loc.get_display_name(player)))
            return
        use_loc = True
        if 'into' in opt:
            use_loc = False
        if 'to' in opt and loc.location:
            loc = loc.location
        if target == char:
            player.msg('Personal teleporting costs 1 coin.')
        else:
            target.ndb.mover = char or player
        if target.move_to(loc, quiet=tel_quietly, emit_to_obj=char, use_destination=use_loc):
            if char and target == char:
                player.msg("Teleported to %s." % loc.get_display_name(player))
            else:
                player.msg("Teleported %s to %s." % (target.get_display_name(player), loc.get_display_name(player)))
                target.nattributes.remove('mover')
            if target.location and target.db.prelogout_location and not target.has_player:
                target.db.prelogout_location = target.location  # Have Character awaken here.
        else:
            if target.location != loc:
                player.msg("|rFailed to teleport %s to %s." % (target.get_display_name(player),
                                                               loc.get_display_name(player)))
