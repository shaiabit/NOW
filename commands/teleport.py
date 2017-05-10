# -*- coding: UTF-8 -*-
from commands.command import MuxCommand
import time  # Check time since last activity


class CmdTeleport(MuxCommand):
    """
    Change object's location - IC component-aware.
    if target has a location, the teleport will be to its location by default.
    If no object is given, you are teleported.

    Usage:
      tel/switch [<object> =|to] <target's location>
    Options:
    /quiet     don't echo leave/arrive messages to the source/target
               locations for the move.
    /into      if target is an exit, teleport INTO the object
               instead of to its location or destination.    
    /vanish    if set, teleport the object into Nothingness. If this
               option is used, <target location> is ignored.
               Note that the only way to retrieve an object from
               Nothingness is by direct #dbref reference.
    Examples:
      tel Limbo
      tel Rulan to me
      tel/quiet box=fog
      tel/into book to shelf
      tel/vanish box
    """
    key = 'teleport'
    aliases = ['tport', 'tel']
    locks = 'cmd:perm(teleport) or perm(Builders)'
    help_category = 'Travel'
    parse_using = ' to '

    @staticmethod
    def stop_check(target):
        """
        Forbidden items do not teleport.
        
        Marked by tags, they are either left behind (teleport:remain),
         or they prevent their holder to teleport (teleport:forbid).
        
        """
        def tag_check(obj):
            if obj.tags.get('teleport', category='forbid'):
                return False
            if obj.tags.get('teleport', category='remain'):
                return None
            return True

        # Test target and target's contents:
        items, result = [target] + target.contents, []
        for each in items:
            check = tag_check(each)
            if not check:
                result.append((each, check))
        return True if not result else result

    def func(self):
        """Performs the teleport, accounting for in-world conditions."""

        char = self.character
        cmd = self.cmdstring
        player = self.player
        args = self.args
        lhs, rhs = self.lhs, self.rhs
        if lhs.startswith('to ') and not rhs:  # Additional parse step when left of "to" is left empty.
            lhs, rhs = 'me', lhs[3:].strip()
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
                target = search_as.search(lhs, global_search=True, exact=False)
                if not target:
                    player.msg("Did not find object to teleport.")
                    return
                if not (player.check_permstring('Mages') or target.access(player, 'control')):
                    player.msg("You must have |wMages|n or higher access to send something into |222Nothingness|n.")
                    return
                player.msg("Teleported %s -> None-location." % (target.get_display_name(char)))
                if target.location and not tel_quietly:
                    if char and char.location == target.location and char != target:
                        target.location.msg_contents("%s%s|n sends %s%s|n into |222Nothingness|n."
                                                     % (char.STYLE, char, target.STYLE, target))
                    else:
                        target.location.msg_contents("|r%s|n vanishes into |222Nothingness|n." % target)
            target.location = None
            return
        if not args:
            player.msg("Usage: teleport[/options] [<obj> =|to] <target>")
            return
        if rhs:
            target = search_as.search(lhs, global_search=True, exact=False)
            loc = search_as.search(rhs, global_search=True, exact=False)
        else:
            target = char
            loc = search_as.search(lhs, global_search=True, exact=False)
        if not target:
            player.msg("Did not find object to teleport.")
            return
        if not loc:
            player.msg("Destination not found.")
            return
        be_with = loc
        use_loc = True
        if 'into' in opt:
            use_loc = False
        elif loc.location:
            loc = loc.location
        if target == loc:
            player.msg("You can not teleport an object inside of itself!")
            return
        if target == loc.location:
            player.msg("You can not teleport an object inside something it holds!")
            return
        if target.location and target.location == loc:
            with_clause = ' with %s' % be_with.get_display_name(char) if be_with is not loc else '' 
            player.msg("%s is already at %s%s." % (target.get_display_name(char),
                                                   loc.get_display_name(char), with_clause))
            return
        print("%s is about to go to %s" % (target.key, loc.key))
        target.ndb._teleport_time = time.time()
        scan = self.stop_check(target)
        if scan is not True:
            print("Teleport contraband detected: " + ', '.join([repr(each) for each in scan]))
        if target == char:
            player.msg('Personal teleporting costs 1 coin.')
            target.nattributes.remove('exit_used')  # Remove reference to using exit when not using exit to leave
        else:
            target.ndb.mover = char or player
        if target.move_to(loc, quiet=tel_quietly, emit_to_obj=char, use_destination=use_loc):
            print("%s finally arrives at %s (Delay: %s seconds)" %
                  (target.key, loc.key, str(time.time() - target.ndb._teleport_time)))
            if char and target == char:
                player.msg("Teleported to %s." % loc.get_display_name(char))
            else:
                player.msg("Teleported %s to %s." % (target.get_display_name(char), loc.get_display_name(char)))
                target.nattributes.remove('mover')
            if target.location and target.db.prelogout_location and not target.has_player:
                target.db.prelogout_location = target.location  # Have Character awaken here.
        else:
            if target.location != loc:
                player.msg("|rFailed to teleport %s to %s." % (target.get_display_name(char),
                                                               loc.get_display_name(char)))
