from evennia import default_cmds


class CmdTeleport(default_cmds.MuxCommand):
    """
    Change object's location - IC component-aware.
    If no object is given, you are teleported to the target location.
    Usage:
      tel/switch [<object> =] <target location>
    Switches:
    /quiet     don't echo leave/arrive messages to the source/target
               locations for the move.
    /intoexit  if target is an exit, teleport INTO
               the exit object instead of to its destination
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
    player_caller = True

    def func(self):
        """Performs the teleport, accounting for in-world conditions."""

        char = self.character
        player = self.player
        args = self.args
        lhs, rhs = self.lhs, self.rhs
        switches = self.switches

        if char.ndb.currently_moving:
            player.msg("You can not teleport while moving. (|rstop|n, then try again.)")
            return

        # setting switches
        tel_quietly = 'quiet' in switches or 'silent' in switches
        to_none = 'vanish' in switches

        if to_none:  # teleporting to Nothingness
            if not args:
                target = char
                player.msg("|*Teleported to Nothingness.|n")
                if char.location and not tel_quietly:
                    char.location.msg_contents("|r%s|n vanishes." % char, exclude=char)
            else:
                target = char.search(lhs, global_search=True)
                if not target:
                    player.msg("Did not find object to teleport.")
                    return
                if not player.check_permstring('Mages') or not target.access(player, 'control'):
                    player.msg("You must have |wMages|n or higher access to send something into |222Nothingness|n.")
                    return
                player.msg("Teleported %s -> None-location." % (target.get_display_name(player)))
                if target.location and not tel_quietly:
                    if char.location == target.location and char != target:
                        target.location.msg_contents("%s%s|n sends %s%s|n into |222Nothingness|n."
                                                     % (char.STYLE, char, target.STYLE, target))
                    else:
                        target.location.msg_contents("|r%s|n vanishes into |222Nothingness|n." % target)
            target.location = None
            return
        if not args:
            player.msg("Usage: teleport[/switches] [<obj> =] <target_loc>||home")
            return
        if rhs:
            target = char.search(lhs, global_search=True)
            destination = char.search(rhs, global_search=True)
        else:
            target = char
            destination = char.search(lhs, global_search=True)
        if not target:
            player.msg("Did not find object to teleport.")
            return
        if not destination:
            player.msg("Destination not found.")
            return
        if target == destination:
            player.msg("You can not teleport an object inside of itself!")
            return
        print("%s is trying to go to %s" % (target.key, destination.location))
        if target == destination.location:
            player.msg("You can not teleport an object inside something it holds!")
            return
        if target.location and target.location == destination:
            player.msg("%s is already at %s." % (target.get_display_name(player), destination.get_display_name(player)))
            return
        use_destination = True
        if 'intoexit' in self.switches:
            use_destination = False
        if target == char:
            player.msg('Personal teleporting costs 1 coin.')
        if target.move_to(destination, quiet=tel_quietly, emit_to_obj=char, use_destination=use_destination):
            if target == char:
                player.msg("Teleported to %s." % destination.get_display_name(player))
            else:
                player.msg("Teleported %s -> %s." % (target.get_display_name(player),
                                                     destination.get_display_name(player)))
