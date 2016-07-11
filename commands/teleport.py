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

        caller = self.character
        player = self.player
        args = self.args
        lhs, rhs = self.lhs, self.rhs
        switches = self.switches

        if caller.ndb.currently_moving:
            caller.msg("You can not teleport while moving. (|rstop|n, then try again.)")
            return

        # setting switches
        tel_quietly = 'quiet' in switches or 'silent' in switches
        to_none = 'vanish' in switches

        if to_none:  # teleporting to Nothingness
            if not args:
                target = caller
                caller.msg("|*Teleported to None-location.|n")
                if caller.location and not tel_quietly:
                    caller.location.msg_contents("|r%s|n vanishes." % caller, exclude=caller)
            else:
                target = caller.search(lhs, global_search=True)
                if not target:
                    caller.msg("Did not find object to teleport.")
                    return
                if not player.check_permstring('Mages') or not target.access(player, 'control'):
                    caller.msg("You must have |wMages|n or higher access to send something into nothingness.")
                    return
                caller.msg("Teleported %s%s|n -> None-location." % (target.STYLE, target))
                if target.location and not tel_quietly:
                    if caller.location == target.location and caller != target:
                        target.location.msg_contents("%s%s|n sends %s%s|n into nothingness."
                                                     % (caller.STYLE, caller, target.STYLE, target))
                    else:
                        target.location.msg_contents("|r%s|n vanishes into nothingness." % (target))
            target.location = None
            return
        if not args:
            caller.msg("Usage: teleport[/switches] [<obj> =] <target_loc>||home")
            return
        if rhs:
            target = caller.search(lhs, global_search=True)
            destination = caller.search(rhs, global_search=True)
        else:
            target = caller
            destination = caller.search(lhs, global_search=True)
        if not target:
            caller.msg("Did not find object to teleport.")
            return
        if not destination:
            caller.msg("Destination not found.")
            return
        if target == destination:
            caller.msg("You can not teleport an object inside of itself!")
            return
        print("%s is trying to go to %s" % (target.key, destination.location))
        if target == destination.location:
            caller.msg("You can not teleport an object inside something it holds!")
            return
        if target.location and target.location == destination:
            caller.msg("%s is already at %s." % (target, destination))
            return
        use_destination = True
        if 'intoexit' in self.switches:
            use_destination = False
        if target == caller:
            caller.msg('Personal teleporting costs 1 coin.')
        if target.move_to(destination, quiet=tel_quietly, emit_to_obj=caller, use_destination=use_destination):
            if target == caller:
                caller.msg("Teleported to %s%s|n." % (destination.STYLE, destination))
            else:
                caller.msg("Teleported %s%s|n -> %s%s|n." % (target.STYLE, target,
                                                             destination.STYLE, destination))
