from evennia import default_cmds
from evennia.utils import search
from django.conf import settings
from django.db.models import Q
from evennia.objects.models import ObjectDB
from evennia.utils.utils import inherits_from, class_from_module

class CmdExit(default_cmds.MuxCommand):
    """
    Parent class for all simple exit-directions. 
    Actual exit objects superceed these in every way.

    Simple destinations are stored on the room in its 'exits' attribute in a dictionary.
    All simple exits uses the same one attribute, compared to object-based exits, which
    create a new database object.  Simple exits use much less database space by comparison.

    Use of "ex here/exits" to view them is prefered, as the default "@set here/exits"
    will not show the destinations.

    <direction>/add [destination] -- adds simple exit to destination in the given direction.
    <direction>/del  -- removes simple exit in given direction. 
    """
    locks = "cmd:all()"
    arg_regex = r"^/|\s|$"
    auto_help = True
    help_category = "Travel"

    def func(self):
        "Command for all simple exit directions."

        player_caller = True
        you = self.caller
        loc = you.location

        def add(you, loc, ways):
            "Command for adding an exit - checks location and permissions."

            searchstring=self.args
            keyquery = Q(db_key__istartswith=searchstring)
            aliasquery = Q(db_tags__db_key__istartswith=searchstring,
                           db_tags__db_tagtype__iexact="alias")


            results = ObjectDB.objects.filter(keyquery | aliasquery).distinct()
            nresults = results.count()

            if nresults: # convert multiple results to typeclasses.
                results = [result for result in results]
                ROOM_TYPECLASS = settings.BASE_ROOM_TYPECLASS # Narrow reuslts to only rooms.
                results = [obj for obj in results if inherits_from(obj, ROOM_TYPECLASS)]
            
            if not results:
                result = None
            else:
                result = results[0] # Aribritrarily select the first result of usually only one.

            ways[self.aliases[0]] = result
            you.msg("|ySearch found|n (%s)" % None if result == None else result.get_display_name(you))
            if result == None:
                return
            if ways[self.aliases[0]]:
                if loc.access(you, 'edit'):
                    if ways[self.aliases[0]].access(you, 'control'):
                        loc.db.exits = ways
                        you.msg("|gAdded|n exit %s to %s leading to %s." % (self.key, loc, ways[self.aliases[0]]))
                    else:
                        you.msg("You do not control the destination, so can not connect an exit to it.")
                else:
                    you.msg("You have no permission to edit here.")

        if self.caller.location.attributes.has('exits'):  # Does an 'exits' attribute exist?
            ways = loc.db.exits
            # Only test for the short version of the direction name: self.aliases[0]
            way = ways.get(self.aliases[0])
            if way:  # Is the direction in the room's exit dictionary?
                if 'del' in self.switches:
                    if loc.access(you, 'edit'):
                        del(ways[self.aliases[0]])
                        loc.db.exits = ways
                        you.msg("|rRemoved|n exit %s from %s." % (self.key, loc))
                    else:
                        you.msg("You have no permission to edit here.")
                elif 'add' in self.switches:
                    if loc.access(you, 'edit'):
                        you.msg("Exit %s to %s leading to %s already exists here." % (self.key, loc, ways[self.aliases[0]]))
                    else:
                        you.msg("You have no permission to edit here.")
                else:
                    you.move_to(way)
            else:
                if 'add' in self.switches:
                    add(you, loc, ways)
                elif 'del' in self.switches:
                    you.msg("Exit %s does not exist here." % self.key)
                else:
                    you.msg("You cannot travel %s." % self.key)
        else:  # No simple exits from this location.
            ways = {}
            if 'add' in self.switches:
                add(you, loc, ways)
            elif 'del' in self.switches:
                you.msg("No simple exit %s to delete." % self.key)
            else:
                you.msg("You cannot travel %s." % self.key)


class CmdExitNorth(CmdExit):
    """
    north  or n                   -- move north
    north  or n/add [destination] -- adds simple exit north to destination.
    north  or n/del               -- removes simple exit north from current room. 
    """
    key = "north"
    aliases = ["n"]

class CmdExitNortheast(CmdExit):
    """
    northeast  or ne                   -- move northeast
    northeast  or ne/add [destination] -- adds simple exit northeast to destination.
    northeast  or ne/del               -- removes simple exit northeast from current room. 
    """
    key = "northeast"
    aliases = ["ne"]


class CmdExitNorthwest(CmdExit):
    """
    northwest  or nw                   -- move northwest
    northwest  or nw/add [destination] -- adds simple exit northwest to destination.
    northwest  or nw/del               -- removes simple exit northwest from current room. 
    """
    key = "northwest"
    aliases = ["nw"]


class CmdExitEast(CmdExit):
    """
    east  or e                   -- move east
    east  or e/add [destination] -- adds simple exit east to destination.
    east  or e/del               -- removes simple exit east from current room. 
    """
    key = "east"
    aliases = ["e"]


class CmdExitSouth(CmdExit):
    """
    south  or s                   -- move south
    south  or s/add [destination] -- adds simple exit south to destination.
    south  or s/del               -- removes simple exit south from current room. 
    """
    key = "south"
    aliases = ["s"]


class CmdExitSoutheast(CmdExit):
    """
    sortheast  or se                   -- move southeast
    sortheast  or se/add [destination] -- adds simple exit southeast to destination.
    sortheast  or se/del               -- removes simple exit southeast from current room. 
    """
    key = "southeast"
    aliases = ["se"]


class CmdExitSouthwest(CmdExit):
    """
    southwest  or sw                   -- move southwest
    southwest  or sw/add [destination] -- adds simple exit southwest to destination.
    southwest  or sw/del               -- removes simple exit southwest from current room. 
    """
    key = "southwest"
    aliases = ["sw"]


class CmdExitWest(CmdExit):
    """
    west  or w                   -- move west
    west  or w/add [destination] -- adds simple exit west to destination.
    west  or w/del               -- removes simple exit west from current room. 
    """
    key = "west"
    aliases = ["w"]
