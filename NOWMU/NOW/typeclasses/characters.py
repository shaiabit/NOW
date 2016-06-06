"""
Characters

Characters are (by default) Objects setup to be puppeted by Players.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
import re
from world.helpers import make_bar
from evennia import DefaultCharacter

class Character(DefaultCharacter):
    """
    The Character defaults to implementing some of its hook methods with the
    following standard functionality:

    at_basetype_setup - always assigns the DefaultCmdSet to this object type
                    (important!)sets locks so character cannot be picked up
                    and its commands only be called by itself, not anyone else.
                    (to change things, use at_object_creation() instead)
    at_after_move - launches the "look" command
    at_post_puppet(player) -  when Player disconnects from the Character, we
                    store the current location, so the "unconnected" character
                    object does not need to stay on grid but can be given a
                    None-location while offline.
    at_pre_puppet - just before Player re-connects, retrieves the character's
                    old location and puts it back on the grid with a "charname
                    has connected" message echoed to the room
    """

    STYLE = '|c'

    def at_before_move(self, destination):
        """
        Called just before moving object - here we check to see if
        it is supporting another object that is currently in the room
        before allowing the move. If it is, we do prevent the move by
        returning False.
        """

        if self.attributes.has('locked'):
            self.msg("\nYou're still sitting.") # stance, prep, obj
            return False # Object is supporting something; do not move it
        elif self.attributes.has('health') and self.db.health <= 0:
            self.msg("You can't move; you're incapacitated!") # Type 'home' to \ TODO:
                # go back home and recover, or wait for a healer to come to you.")
            return False
        if self.db.Combat_TurnHandler:
            self.caller.msg("You can't leave while engaged in combat!")
            return False
        return True

    def at_after_move(self, source_location):
        """
        Trigger look after a move.
        """
        if self.location.access(self, "view"):
            self.msg(text=((self.at_look(self.location),), {"window":"room"}))
            # TODO: Display name for objects in message.
            self.location.msg_contents("%s arrives at %s from %s." % (self, self.location, source_location))
            # self.location.msg_contents("%s arrives at %s from %s." % \
               # self.full_name(viewer) if hasattr(self, "full_name") else self, self.location, \
               # self.location.get_display_name(viewer) if hasattr(self.location, "full_name") else self.location, \
               # source_location.get_display_name(viewer) if hasattr(source_location, "full_name") else source_location)

    def at_post_puppet(self):
        """
        Called just after puppeting has been completed and all
        Player<->Object links have been established.
        """
        self.msg("\nYou assume the role of %s.\n" % self.full_name(self))
        self.msg(self.at_look(self.location))

        def message(obj, from_obj):
            obj.msg("|g%s|n fades into view." % self.get_display_name(obj), from_obj=from_obj)
        self.location.for_contents(message, exclude=[self], from_obj=self)

        def message(obj, from_obj):
            obj.msg("|c%s|n awakens." % self.get_display_name(obj), from_obj=from_obj)
        self.location.for_contents(message, exclude=[self], from_obj=self)

    def at_post_unpuppet(self, player, session=None):
        """
        We store the character when the player goes ooc/logs off,
        when the character is left in a public or semi-public room.
        Otherwise the character object will remain in the room after
        the player logged off ("headless", so to say).
        Args:
            player (Player): The player object that just disconnected
                from this object.
            session (Session): Session controlling the connection that
                just disconnected.
        """
        if not self.sessions.count():
            # only remove this char from grid if no sessions control it anymore.
            if self.location:
                def message(obj, from_obj):
                    obj.msg("|c%s|n sleeps." % self.get_display_name(obj), from_obj=from_obj)
                self.location.for_contents(message, exclude=[self], from_obj=self)
                self.db.prelogout_location = self.location
                self.location = None
                def message(obj, from_obj):
                    obj.msg("|r%s|n fades from view." % self.get_display_name(obj), from_obj=from_obj)
                self.db.prelogout_location.for_contents(message, exclude=[self], from_obj=self)

    def full_name(self, viewer):
        """
        Returns the full styled and clickable-look name
        for the viewer's perspective as a string.
        """

        if viewer and self.access(viewer, "view"):
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

    def get_pronoun(self, regex_match):
        """
        Get pronoun from the pronoun marker in the text. This is used as
        the callable for the re.sub function.
        Args:
            regex_match (MatchObject): the regular expression match.
        Notes:
            - `|s`, `|S`: Subjective form: he, she, it, He, She, It
            - `|o`, `|O`: Objective form: him, her, it, Him, Her, It
            - `|p`, `|P`: Possessive form: his, her, its, His, Her, Its
            - `|a`, `|A`: Absolute Possessive form: his, hers, its, His, Hers, Its
        """

        _GENDER_PRONOUN_MAP = {"male": {"s": "he",
                                        "o": "him",
                                        "p": "his",
                                        "a": "his"},
                             "female": {"s": "she",
                                        "o": "her",
                                        "p": "her",
                                        "a": "hers"},
                            "neutral": {"s": "it",
                                        "o": "it",
                                        "p": "its",
                                        "a": "its"}}

        _RE_GENDER_PRONOUN = re.compile(r'[^\|]+(\|s|S|o|O|p|P|a|A)')

        typ = regex_match.group()[2] # "s", "O" etc
        gender = self.attributes.get("gender", default="neutral")
        gender = gender if gender in ("male", "female", "neutral") else "neutral"
        pronoun = _GENDER_PRONOUN_MAP[gender][typ.lower()]
        return pronoun.capitalize() if typ.isupper() else pronoun

    def get_mass(self):
        mass = self.attributes.get('mass') or 10
        return reduce(lambda x, y: x+y.get_mass(),[mass] + self.contents)

    def get_carry_limit(self):
        return 80 * self.get_attribute_value('health')

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

        string = "\n%s" % self.mxp_name(viewer, '@verb #%s' % self.id)
        string += " (%s) " % self.get_mass()
        if self.attributes.has('health') and self.attributes.has('health_max'): # Add character health bar.
            gradient = ["|[300", "|[300", "|[310", "|[320", "|[330", "|[230", "|[130", "|[030", "|[030"]
            health = make_bar(self.attributes.get('health'), self.attributes.get('health_max'), 20, gradient)
            string += " %s\n" % health
        else:
            string += "\n"
        desc = self.db.desc
        desc_brief = self.db.desc_brief
        if desc:
            string += "%s" % desc
        elif desc_brief:
            string += "%s" % desc_brief
        else:
            string += 'A shimmering illusion shifts from form to form.'
        if exits:
            string += "\n|wExits: " + ", ".join("%s" % e.full_name(viewer) for e in exits)
        if users or things:
            user_list = ", ".join(u.full_name(viewer) for u in users)
            ut_joiner = ', ' if users and things else ''
            item_list = ", ".join(t.full_name(viewer) for t in things)
            string += "\n|wYou see:|n " + user_list + ut_joiner + item_list
        return string


class NPC(Character):
    """
    Uses Character class as a starting point.
    """

    STYLE = '|m'

    def at_post_puppet(self): # TODO: Fix this for multi-puppeters.
        """
        Called just after puppeting has been completed and all
        Player<->Object links have been established.
        """
        self.msg("\nYou assume the role of %s.\n" % self.full_name(self))
        self.msg(self.at_look(self.location))

        # def message(obj, from_obj):
        #    obj.msg("|g%s|n fades into view." % self.get_display_name(obj), from_obj=from_obj)
        # self.location.for_contents(message, exclude=[self], from_obj=self)

        def message(obj, from_obj):
            obj.msg("|c%s|n awakens." % self.get_display_name(obj), from_obj=from_obj)
        self.location.for_contents(message, exclude=[self], from_obj=self)

    def at_post_unpuppet(self, player, session=None):
        """
        We store the character when the player goes ooc/logs off,
        when the character is left in a public or semi-public room.
        Otherwise the character object will remain in the room after
        the player logged off ("headless", so to say).
        Args:
            player (Player): The player object that just disconnected
                from this object.
            session (Session): Session controlling the connection that
                just disconnected.
        """
        if not self.sessions.count():
            # only remove this char from grid if no sessions control it anymore.
            if self.location:
                def message(obj, from_obj):
                    obj.msg("|c%s|n sleeps." % self.get_display_name(obj), from_obj=from_obj)
                self.location.for_contents(message, exclude=[self], from_obj=self)
                self.db.prelogout_location = self.location
                # self.location = None  # TODO: Send NPC home after unpuppeting.
                # def message(obj, from_obj):
                #     obj.msg("|r%s|n fades from view." % self.get_display_name(obj), from_obj=from_obj)
                # self.db.prelogout_location.for_contents(message, exclude=[self], from_obj=self)