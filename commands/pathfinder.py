from evennia import default_cmds
from evennia import CmdSet

class CmdSetBot(CmdSet):
    """This method adds commands to the grid room command set."""
    key = 'bot'
    priority = 101  # Same as Exit objects

    def at_cmdset_creation(self):
        self.add(CmdPathfind())


class CmdPathfind(default_cmds.MuxCommand):
    key = "find"
    locks = "cmd:all()"

    maxdepth = 10

    def func(self):
        """confirms the target and initiates the search"""
        # save the target object onto the command
        # this will use Evennia's default multimatch handling if more than one object matches
        loc = self.caller.location
        if loc is None:
            return
        self.target = self.caller.search(self.args, global_search=True)
        this = self.obj.get_display_name(self.caller)
        if self.caller is not self.obj:
            loc.msg_contents("{who} asks {it} to find something.", mapping=dict(who=self.caller, it=self.obj))
        loc.msg_contents("%s's ears swivel, scanning for \"%s\"." % (this, self.args))
        if not self.target:
            loc.msg_contents("%s can't find \"%s\"." % (this, self.args))
            return
        target = self.target.get_display_name(self.caller)
        # initialize a list to store rooms we've visited
        self.visited = []
        # Start search at depth=0
        if not self._searcher(self.caller.location, 0):  # give 'not found' message
            loc.msg_contents("%s can't find %s in range." % (this, target))

    def _searcher(self, room, depth):
        """Searches surrounding rooms recursively for an object"""
        loc = self.caller.location
        this = self.obj.get_display_name(self.caller)
        target = self.target.get_display_name(self.caller)
        # first, record searching here
        self.visited.append(room)
        # End search either when the item is found...
        if self.target in room.contents or self.target is room:
            if depth == 0:
                here = loc.get_display_name(self.caller)
                loc.msg_contents("{} finds {} right here in {}!".format(this, target, here))
            else:
                way = self.direction.get_display_name(self.caller, mxp=self.direction.key)
                plural = 's' if depth != 1 else ''
                loc.msg_contents("{} detects {} {} step{} away. Go {}".format(this, target, depth, plural, way))
            return True
        # or searched to `maxdepth` distance
        if depth > self.maxdepth:
            return False
        # Target not in the current room, scan through the exits and check them,
        # skipping rooms we've already visited
        exits = [exit for exit in room.exits if exit.destination not in self.visited]
        for next in exits:
            if depth == 0:  # we only want to return the exit out of the current room
                self.direction = next
            if self._searcher(next.destination, depth + 1):  # if we found the object, stop searching
                return True
        # Check all the exits, no result
        return False
