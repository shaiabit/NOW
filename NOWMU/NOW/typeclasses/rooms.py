"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia import DefaultRoom


class Room(DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See examples/object.py for a list of
    properties and methods available on all Objects.
    """

    def full_name(self, viewer):
        """
        Returns the full styled and clickable-look name
        for the viewer's perspective as a string.
        """

        if viewer and (self != viewer) and self.access(viewer, "view"):
            return "|y|lclook %s|lt%s|le|n" % (self.name, self.get_display_name(viewer))
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
                things.append(con)
        # get description, build string
        string = self.full_name(viewer) + "\n"
        desc = self.db.desc
        desc_brief = self.db.desc_brief
        if desc:
            string += "%s" % desc
        elif desc_brief:
            string += "%s" % desc_brief
        else:
            string += 'Nothing more than smoke and mirrors appears around you.'
        if exits:
            string += "\n|wExits: " + ", ".join("%s" % e.full_name(viewer) for e in exits)
        if users or things:
            user_list = ", ".join(u.full_name(viewer) for u in users)
            ut_joiner = ', ' if users and things else ''
            item_list = ", ".join(t.full_name(viewer) for t in things)
            string += "\n|wYou see:|n " + user_list + ut_joiner + item_list
        return string