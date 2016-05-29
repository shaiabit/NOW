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

    STYLE = '|y'

    def full_name(self, viewer):
        """
        Returns the full styled and clickable-look name
        for the viewer's perspective as a string.
        """

        if viewer and (self != viewer) and self.access(viewer, "view"):
            return "%s%s|n" % (self.STYLE, self.get_display_name(viewer))
        else:
            return ''


    def mxp_name(self, viewer, command):
        """
        Returns the full styled and clickable-look name
        for the viewer's perspective as a string.
        """

        if viewer and self.access(viewer, "view"):
            return "|lc%s|lt%s%s|n|le" % (command, self.STYLE, self.full_name(viewer))
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
        command = '%s #%s' % ('@verb', self.id)
        string = "\n%s\n" % self.mxp_name(viewer, command)
        desc = self.db.desc
        desc_brief = self.db.desc_brief
        if desc:
            string += "%s" % desc
        elif desc_brief:
            string += "%s" % desc_brief
        else:
            string += 'Nothing more than smoke and mirrors appears around you.'
        if exits:
            string += "\n|wVisible exits|n: " + ", ".join("%s" % e.mxp_name(viewer, '@verb #%s' % e.id) for e in exits)
        if users or things:
            user_list = ", ".join(u.mxp_name(viewer, u.mxp_name(viewer, '@verb #%s' % u.id)) for u in users)
            ut_joiner = ', ' if users and things else ''
            item_list = ", ".join(t.mxp_name(viewer, '@verb #%s' % t.id) for t in things)
            string += "\n|wHere you find:|n " + user_list + ut_joiner + item_list
        return string