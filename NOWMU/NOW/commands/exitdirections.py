from evennia import default_cmds

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
    auto_help = False

    def func(self):
        "Command for all simple exit directions."

        you = self.caller
        loc = you.location

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
                    ways[self.aliases[0]] = you.search(self.args)
                    if ways[self.aliases[0]]:
                        if loc.access(you, 'edit'):
                            if ways[self.aliases[0]].access(you, 'control'):
                                loc.db.exits = ways
                                you.msg("|gAdded|n exit %s to %s leading to %s." % (self.key, loc, ways[self.aliases[0]]))
                            else:
                                you.msg("You do not control the destination, so can not add an exit to it.")
                        else:
                            you.msg("You have no permission to edit here.")
                elif 'del' in self.switches:
                    you.msg("Exit %s does not exist here." % self.key)
                else:
                    you.msg("You cannot travel %s." % self.key)
        else:  # No simple exits from this location.
            ways = {}
            if 'add' in self.switches:
                ways[self.aliases[0]] = you.search(self.args)
                if ways[self.aliases[0]]:
                    if loc.access(you, 'edit'):
                        if ways[self.aliases[0]].access(you, 'control'):
                            loc.db.exits = ways
                            you.msg("|gAdded|n exit %s to %s leading to %s." % (self.key, loc, ways[self.aliases[0]]))
                        else:
                            you.msg("You do not control the destination, so can not add an exit to it.")
                    else:
                        you.msg("You have no permission to edit here.")
            elif 'del' in self.switches:
                you.msg("No simple exit %s to delete." % self.key)
            else:
                you.msg("You cannot travel %s." % self.key)

class CmdExitNorth(CmdExit):
    key = "north"
    aliases = ["n"]

class CmdExitNortheast(CmdExit):
    key = "northeast"
    aliases = ["ne"]

class CmdExitNorthwest(CmdExit):
    key = "northwest"
    aliases = ["nw"]

class CmdExitEast(CmdExit):
    key = "east"
    aliases = ["e"]

class CmdExitSouth(CmdExit):
    key = "south"
    aliases = ["s"]

class CmdExitSoutheast(CmdExit):
    key = "southeast"
    aliases = ["se"]

class CmdExitSouthwest(CmdExit):
    key = "southwest"
    aliases = ["sw"]

class CmdExitWest(CmdExit):
    key = "west"
    aliases = ["w"]
