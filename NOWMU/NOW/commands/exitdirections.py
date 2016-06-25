from evennia import default_cmds
from evennia.utils import search
from evennia.utils import create
from django.conf import settings
from django.db.models import Q
from evennia.objects.models import ObjectDB
from evennia.utils.utils import inherits_from, class_from_module

class CmdExit(default_cmds.MuxCommand):
    """
    Simple destinations are stored on the room in its 'exits' attribute in a dictionary.
    All simple exits on the room use the same attribute, compared to object-based exits,
    which create a new database object.  Simple exits use much less database space.
    Actual exit objects superceed simple exits in every way.

    <direction>/add [name] -- adds simple exit to destination in the given direction.
    <direction>/del        -- removes simple exit in given direction.
    <direction>/tun <name> -- adds simple exit from destination in opposite direction.
    <direction>/new [name] -- creates a new room of given name as destination.
    <direction>/go         -- after any above operations, move to destination.
    <direction>/show       -- shows room exit information and back exit from <direction>.

    Switches combine in some combinations e.g. west/del/tun/go would remove the exits
    into and out of the room in the given direction, then take you to the destination room.

    This command never deletes rooms, but can create them in a simple fashion when needed.
    """
    locks = 'cmd:all()'
    arg_regex = r"^/|\s|$"
    help_category = 'Travel'
    auto_help = True
    player_caller = True

    def func(self):
        """Command for all simple exit directions."""
        you = self.character
        loc = you.location
        player = self.player

        def new_room(room_name):
            """
            print("-----")
            print("New Room creation details.")
            print("Name: %s" % room['name'])
            print("Alises: %s" % room['aliases'])
            print("Type: %s" % typeclass)
            print("Lock: %s" % lockstring)
            print("=====")
            """
            if not player.check_permstring('Builders'):
                you.msg("You must have |wBuilders|n or higher access to create a new room.")
                return None

            typeclass = settings.BASE_ROOM_TYPECLASS
            room = {'name': room_name.strip(), 'aliases': ''}  # No alias parsing. TODO?
            lockstring = "control:id(%s) or perm(Immortals); delete:id(%s)" \
                         " or perm(Wizards); edit:id(%s) or perm(Wizards)"
            lockstring = lockstring % (self.caller.dbref, self.caller.dbref, self.caller.dbref)

            new_room = create.create_object(typeclass, room['name'],
                                            aliases=room['aliases'],
                                            report_to=you)
            new_room.locks.add(lockstring)

            alias_string = ''  # No parsing for aliases here yet, so new rooms never have aliases.
            if new_room.aliases.all():
                alias_string = " (%s)" % ", ".join(new_room.aliases.all())
            self.caller.msg("Created room %s(%s)%s of type %s." % (new_room,
                new_room.dbref, alias_string, typeclass))
            return new_room or None

        def find_by_name(search):
            search = search.strip()
            keyquery = Q(db_key__istartswith=search)
            aliasquery = Q(db_tags__db_key__istartswith=search,
                           db_tags__db_tagtype__iexact='alias')

            results = ObjectDB.objects.filter(keyquery | aliasquery).distinct()
            nresults = results.count()

            if nresults:  # convert multiple results to typeclasses.
                results = [result for result in results]
                ROOM_TYPECLASS = settings.BASE_ROOM_TYPECLASS # Narrow results to only rooms.
                results = [obj for obj in results if inherits_from(obj, ROOM_TYPECLASS)]
            return results

        def add(you, loc, ways):
            """"Command for adding an exit - checks location and permissions."""
            results = find_by_name(self.args)
            if not results:
                result = None
            else:
                result = results[0]  # Arbitrarily select the first result of usually only one.
            ways[self.aliases[0]] = result
            you.msg("|ySearch found|n (%s)" % result.get_display_name(you) if result else None)
            if not result:
                return None
            if ways[self.aliases[0]]:
                if loc.access(you, 'edit'):
                    if ways[self.aliases[0]].access(you, 'control'):
                        loc.db.exits = ways
                        you.msg("|gAdded|n exit: %s from %s to %s." % (self.key, loc, ways[self.aliases[0]]))
                    else:
                        you.msg("You do not control the destination, so can not connect an exit to it.")
                else:
                    you.msg("You have no permission to edit here.")
                return ways[self.aliases[0]]
            return None 

        def back_dir(dir):
            return {'n': 's', 's': 'n', 'e': 'w', 'w': 'e', 'nw': 'se', 'se': 'nw', 'ne': 'sw', 'sw': 'ne'}[dir]

        def long_dir(dir):
            return {'n': 'north', 's': 'south', 'e': 'east', 'w': 'west', 'nw': 'northwest', 'se': 'southeast',
                    'ne': 'northeast', 'sw': 'southwest'}[dir]

        def tun(you, loc, dest, dir):
            """Command for tunneling an exit back - checks existing exits, location and permissions."""
            # Check dest for dict with entry back_dir(dir), 
            tways = dest.db.exits if dest.db.exits else {}
            tway = tways.get(back_dir(self.aliases[0]))
            if tway:  # Is the direction in the room's exit dictionary?
                return None
            else:
                tways[back_dir(self.aliases[0])] = loc
                if dest.access(you, 'control'):
                    dest.db.exits = tways
                    you.msg("|gAdded|n exit: %s from %s to %s." % (long_dir(back_dir(self.aliases[0])), dest, loc))
                else:
                    you.msg("You do not control the destination, so can not connect an exit to it.")
        dest = None  # Hopeful destination for exits and moving to.
        if 'add' in self.switches and 'del' in self.switches:  # Can't do both!
            you.msg("|g%s|r/add/del|n: Switches are mutually exclusive - Can't do both!" % self.cmdstring)
            return  # No further action, not even check for /go.
        if you.location.attributes.has('exits'):  # Does an 'exits' attribute exist?
            ways = loc.db.exits
            # Reference direction by short version of the direction name: self.aliases[0]
            way = ways.get(self.aliases[0])
            if way:  # Direction in the room's exit dictionary should know room.
                dest = way
                if 'del' in self.switches:
                    dest = way
                    tway = back_dir(self.aliases[0])
                    tways = dest.db.exits
                    if loc.access(you, 'edit'):
                        del(ways[self.aliases[0]])
                        loc.db.exits = ways
                        you.msg("|rRemoved|n exit %s from %s." % (self.key, loc))
                    if 'tun' in self.switches and tways:
                        if dest.access(you, 'edit'):
                            del(tways[tway])
                            dest.db.exits = tways
                            you.msg("|rRemoved|n exit %s from %s." % (long_dir(tway), dest))
                        else:
                            you.msg("You have no permission to edit here.")
                elif 'add' in self.switches:
                    if loc.access(you, 'edit'):
                        you.msg("Exit %s to %s leading to %s already exists here." % (self.key, loc, dest))
                    else:
                        you.msg("You have no permission to edit here.")
                if 'tun' in self.switches and 'del' not in self.switches:
                    dir = self.aliases[0]
                    tun(you, loc, dest, dir)  # Add is done, now see if tun can be done.
                if 'new' in self.switches:
                    you.msg("Can't make a new room, already going to %s." % dest)
                if 'go' in self.switches:
                    you.move_to(dest)
                if not self.switches:
                    you.move_to(dest)
            else:  # No direction in the room's exit dictionary goes that way.
                if 'new' in self.switches:
                    dest = new_room(self.args)
                if 'add' in self.switches:
                    add(you, loc, ways)
                elif 'del' in self.switches:
                    you.msg("Exit %s does not exist here." % self.key)
                if 'tun' in self.switches:
                    dir = self.aliases[0]
                    dest = ways.get(dir)
                    if dest:
                        tun(you, loc, dest, dir)  # Add is done, now see if tun can be done.
                    else:
                        if self.args:
                            you.msg("|ySearching|n for \"%s\" to the %s." % (self.args, self.key))
                            dest = find_by_name(self.args)
                            if dest:
                                dest = dest[0]
                                you.msg("|gFound|n \"%s\" to the %s." % (dest, self.key))
                                tun(you, loc, dest, dir)  # Add not done, but see if tun can be done.
                            else:
                                you.msg(
                                    "|rDestination room not found|n \"{0:s}\" to the {1:s} when searching by: {2:s}."
                                    .format(dest, self.key, self.args))
                        else:
                            you.msg("|yYou must supply a name or alias of the target room.|n")
                if 'go' in self.switches:
                    if 'add' in self.switches: 
                        you.move_to(ways[dir])
                    else:
                        if 'tun' in self.switches and dest:
                            you.move_to(dest)
                if not self.switches:
                    you.msg("You cannot travel %s." % self.key)
        else:  # No simple exits from this location.
            ways = {}
            way = None
            dest = way
            if 'new' in self.switches:
                dest = new_room(self.args)
            if 'add' in self.switches:
                dest = add(you, loc, ways)
            elif 'del' in self.switches:
                if 'tun' in self.switches:
                    # TODO: If 'tun' option is also used - 
                    # there is no easy way to find it to delete it.
                    pass
                else:
                    you.msg("No simple exit %s to delete." % self.key)
            if 'tun' in self.switches and 'del' not in self.switches:
                if 'add' in self.switches:
                    dir = self.aliases[0]
                    dest = ways[dir]
                    tun(you, loc, dest, dir)  # Add is done, now see if tun can be done.
                else:
                    # TODO: Test - does this only work with 'add' option?
                    # It requires a destination, if not.
                    pass
            if 'go' in self.switches and way:
                you.move_to(dest)
            if not self.switches:
                you.msg("You cannot travel %s." % self.key)
        if 'show' in self.switches:
            if not player.check_permstring('Helpstaff'):
                self.caller.msg("You must have |gHelpstaff|n or higher access to use this.")
                return None
            if you.location.attributes.has('exits'):  # Does an 'exits' attribute exist?
                ways = loc.db.exits
                dir = self.aliases[0]
                dest = ways[dir]
                you.msg("Simple exits exist in %s: %s" % (you.location.full_name(you), ways))
                tways = dest.db.exits
                if tways:
                    tway = tways.get(back_dir(self.aliases[0]))
                    you.msg("Simple exit exists in %s going %s back to %s." % 
                        (dest.full_name(you), long_dir(back_dir(self.aliases[0])), you.location.full_name(you)))
            else:
                you.msg("No simple exits exist in %s." % you.location.full_name(you))


class CmdExitNorth(CmdExit):
    __doc__ = CmdExit.__doc__
    key = "north"
    aliases = ["n"]


class CmdExitNortheast(CmdExit):
    __doc__ = CmdExit.__doc__
    key = "northeast"
    aliases = ["ne"]


class CmdExitNorthwest(CmdExit):
    __doc__ = CmdExit.__doc__
    key = "northwest"
    aliases = ["nw"]


class CmdExitEast(CmdExit):
    __doc__ = CmdExit.__doc__
    key = "east"
    aliases = ["e"]


class CmdExitSouth(CmdExit):
    __doc__ = CmdExit.__doc__
    key = "south"
    aliases = ["s"]


class CmdExitSoutheast(CmdExit):
    __doc__ = CmdExit.__doc__
    key = "southeast"
    aliases = ["se"]


class CmdExitSouthwest(CmdExit):
    __doc__ = CmdExit.__doc__
    key = "southwest"
    aliases = ["sw"]


class CmdExitWest(CmdExit):
    __doc__ = CmdExit.__doc__
    key = "west"
    aliases = ["w"]
