from evennia import default_cmds
from evennia.utils import search, utils


class CmdFlag(default_cmds.MuxCommand):
    """
    Add flag to object.
    Usage:
      flag   shows flags on the current room.
      flag <object>  shows flags on that object.
      flag <object> = <flag>  sets flag on object.
    Switches:
    /search
    /list  Shows a list of flags used.
    """
    key = 'flag'
    locks = 'cmd:all()'
    arg_regex = r'^/|\s|$'
    help_category = 'System'
    player_caller = True
    FLAGS = {'road': 'cars can drive into here, can take taxi from here',
             'offroad': 'Same as "road" - but unpaved, slower speed',
             'outside': 'weather occurs here, land and ascend to/from sky',
             'weather': 'weather occurs here.Weather messages are custom per room.',
             'shelter': 'weather observable here',
             'water': 'there is water here, but also air',
             'underwater': 'there is water, no way to surface for air',
             'air': 'flight into here is allowed by fliers',
             'cloud': 'denser air type, might allow alternate travel',
             'public': 'anyone allowed here',
             'disk': 'a stepdisk room, can jump to any other stepdisk from here.',
             'haunt': 'a room that allows dark characters.',
             'diet': 'room has food available. You can not starve here.',
             'stealth': 'room does not announce when someone enters or leaves.'}

#     myscript.tags.add("weather", category="climate")

    def func(self):
        """ """
        char = self.character
        here = char.location
        player = self.player
        cmd = self.cmdstring
        args = self.args.strip()
        lhs, rhs = [self.lhs, self.rhs]
        switches = self.switches
        switches_list = [u'list', u'info', u'search']

        if not switches:
            obj = here
            if not lhs:
                if not here:
                    player.msg("No flag can be put on this location. Trying flags on %s%s|n/" % (char.STYLE, char.key))
                    obj = char
            else:
                obj = char.search(lhs, location=[char, char.location]) if args else here
            flags_obj = obj.tags.all(category='flags')
            flags_obj_count = len(flags_obj)
            if flags_obj:  # returns a list of flags
                player.msg('Flags in effect on %s: (%s) = |c%s' %
                           (obj.get_display_name(player), flags_obj_count, "|n, |c".join(a for a in flags_obj)))
        elif not all(x in switches_list for x in switches):
            player.msg("Not a valid switch for %s. Use only these: |g/%s" % (cmd, "|n, |g/".join(switches_list)))
            return
        if 'list' in switches:
            player.msg('Displaying list of ' + ('|ymatching' if args else '|gall') + '|n flags:')
            if args:  # Show list of matching flags
                match_list = [x for x in self.FLAGS if x in args]
                player.msg('|c%s' % "|n, |c".join(match_list))
            else:
                player.msg('|c%s' % "|n, |c".join(a for a in self.FLAGS))
        if 'info' in switches:
            player.msg('Displaying info for ' + ('|ymatching' if args else '|gall') + '|n flags:')
            player.msg('|c%s' % "|n, |c".join(a for a in self.FLAGS))
        if 'search' in switches:
            obj = search.search_tag(args, category='flags')
            object_count = len(obj)
            if object_count > 0:
                match_string = ", ".join(o.get_display_name(player) for o in obj)
                string = "Found |w%i|n object%s with flag '|g%s|n':\n %s" %\
                         (object_count, "s" if object_count > 1 else '', args, match_string)
                player.msg(string)
            else:
                player.msg('Found no objects flagged: "|g%s"' % args)
