"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""
from evennia import DefaultExit

class Exit(DefaultExit):
    """
    Exits are connectors between rooms. Exits are normal Objects except
    they defines the `destination` property. It also does work in the
    following methods:

     basetype_setup() - sets default exit locks (to change, use `at_object_creation` instead).
     at_cmdset_get(**kwargs) - this is called when the cmdset is accessed and should
                              rebuild the Exit cmdset along with a command matching the name
                              of the Exit object. Conventionally, a kwarg `force_init`
                              should force a rebuild of the cmdset, this is triggered
                              by the `@alias` command when aliases are changed.
     at_failed_traverse() - gives a default error message ("You cannot
                            go there") if exit traversal fails and an
                            attribute `err_traverse` is not defined.

    Relevant hooks to overload (compared to other types of Objects):
        at_traverse(traveller, target_loc) - called to do the actual traversal and calling of the other hooks.
                                            If overloading this, consider using super() to use the default
                                            movement implementation (and hook-calling).
        at_after_traverse(traveller, source_loc) - called by at_traverse just after traversing.
        at_failed_traverse(traveller) - called by at_traverse if traversal failed for some reason. Will
                                        not be called if the attribute `err_traverse` is
                                        defined, in which case that will simply be echoed.
    """
    def at_desc(self, looker=None):
        """
        This is called whenever someone looks at an exit.

        viewer (Object): The object requesting the description.

        """
        if not looker.location == self:
            looker.msg("You gaze into the distance.")


    def full_name(self, viewer):
        """
        Returns the full styled and clickable-look name
        for the viewer's perspective as a string.
        """

        if viewer and (self != viewer) and self.access(viewer, "view"):
            return "|g{lc%s{lt%s{le|n" % (self.name, self.get_display_name(viewer))
        else:
            return ''


    def return_appearance(self, viewer):
        """
        This formats a description. It is the hook a 'look' command
        should call.

        Args:
            viewer (Object): Object doing the looking.
        """
        if not viewer:
            return
        # get and identify all objects
        visible = (con for con in self.contents if con != viewer and
                                                    con.access(viewer, "view"))
        exits, users, things = [], [], []
        for con in visible:
            if con.destination:
                exits.append(con)
            elif con.has_player:
                users.append(con)
            else:
                things.append(key)
        # get description, build string
        string = "|g{lc%s{lt%s{le|n -- " % (self.name, self.get_display_name(viewer))
        desc = self.db.desc
        desc_brief = self.db.desc_brief
        if desc and viewer.location == self:
            string += "%s" % desc
        elif desc_brief:
            string += "%s" % desc_brief
        else:
            string += "leads to |y%s|n" % self.destination.get_display_name(viewer)
        if exits:
            string += "\n|wExits: " + ", ".join("%s" % e.full_name(viewer) for e in exits)
        if users or things:
            user_list = ", ".join(u.full_name(viewer) for u in users)
            ut_joiner = ', ' if users and things else ''
            item_list = ", ".join(t.full_name(viewer) for t in things)
            string += "\n|wYou see:|n " + user_list + ut_joiner + item_list
        return string