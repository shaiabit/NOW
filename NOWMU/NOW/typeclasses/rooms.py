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
            key = con.get_display_name(viewer)
            if con.destination:
                exits.append(con.name)
            elif con.has_player:
                users.append("|c%s|n" % key)
            else:
                things.append(key)
        # get description, build string
        string = "|y%s|n\n" % self.get_display_name(viewer)
        desc = self.db.desc
        desc_brief = self.db.desc_brief
        if desc:
            string += "%s" % desc
        elif desc_brief:
            string += "%s" % desc_brief
        else:
            string += 'Nothing more than smoke and mirrors appears around you.'
        if exits:
            string += "\n|wExits: " + ", ".join("|g{lc%s{lt%s{le|n" % (e, e) for e in exits)
        if users or things:
            ut_joiner = ', ' if users and things else ''
            string += "\n|wYou see:|n " + ", ".join(users) + ut_joiner + '|M' + "|n, |M".join(things)
        return string