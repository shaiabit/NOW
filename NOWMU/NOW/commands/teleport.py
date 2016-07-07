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
    /tonone    if set, teleport the object to a None-location. If this
               switch is set, <target location> is ignored.
               Note that the only way to retrieve an object from a
               None location is by direct #dbref reference.
    Examples:
      tel Limbo
      tel/quiet box=fog
      tel/tonone box
    """
    key = 'teleport'
    aliases = ['tport', 'tel']
    locks = 'cmd:perm(teleport) or perm(Builders)'
    help_category = 'Travel'

    def func(self):
        """Performs the teleport, accounting for in-world conditions."""

        caller = self.caller
        args = self.args
        lhs, rhs = self.lhs, self.rhs
        switches = self.switches

        if caller.ndb.currently_moving:
            caller.msg("You can not teleport while moving. (|rstop|n, then try again.)")
            return

        # setting switches
        tel_quietly = 'quiet' in switches or 'silent' in switches
        to_none = 'tonone' in switches

        if to_none:  # teleporting to None
            if not args:
                obj_to_teleport = caller
                caller.msg("|*Teleported to None-location.|n")
                if caller.location and not tel_quietly:
                    caller.location.msg_contents("|r%s|n vanishes." % caller, exclude=caller)
            else:
                obj_to_teleport = caller.search(lhs, global_search=True)
                if not obj_to_teleport:
                    caller.msg("Did not find object to teleport.")
                    return
                caller.msg("Teleported %s -> None-location." % obj_to_teleport)
                if obj_to_teleport.location and not tel_quietly:
                    obj_to_teleport.location.msg_contents("%s teleported %s into nothingness."
                                                          % (caller, obj_to_teleport),
                                                          exclude=caller)
            obj_to_teleport.location = None
            return
        if not args and not to_none:  # not teleporting to None location
            caller.msg("Usage: teleport[/switches] [<obj> =] <target_loc>||home")
            return
        if rhs:
            obj_to_teleport = caller.search(lhs, global_search=True)
            destination = caller.search(rhs, global_search=True)
        else:
            obj_to_teleport = caller
            destination = caller.search(lhs, global_search=True)
        if not obj_to_teleport:
            caller.msg("Did not find object to teleport.")
            return
        if not destination:
            caller.msg("Destination not found.")
            return
        if obj_to_teleport == destination:
            caller.msg("You can not teleport an object inside of itself!")
            return
        print("%s is trying to go to %s" % (obj_to_teleport.key, destination.location))
        if obj_to_teleport == destination.location:
            caller.msg("You can not teleport an object inside something it holds!")
            return
        if obj_to_teleport.location and obj_to_teleport.location == destination:
            caller.msg("%s is already at %s." % (obj_to_teleport, destination))
            return
        use_destination = True
        if 'intoexit' in self.switches:
            use_destination = False

        # try the teleport
        if obj_to_teleport == caller:
            caller.msg('Personal teleporting costs 1 coin.')
        if obj_to_teleport.move_to(destination, quiet=tel_quietly, emit_to_obj=caller,
                                   use_destination=use_destination):
            if obj_to_teleport == caller:
                caller.msg("Teleported to %s." % destination)
            else:
                caller.msg("Teleported %s -> %s." % (obj_to_teleport, destination))
