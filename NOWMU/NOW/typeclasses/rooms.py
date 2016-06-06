"""
Room

Rooms are simple containers that has no location of their own.

"""

import random
from evennia import DefaultRoom
from evennia import TICKER_HANDLER
from evennia.comms.models import ChannelDB, Msg
from evennia.comms.channelhandler import CHANNELHANDLER

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
        Returns the full styled non-clickable name
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

        for obj in self.contents_get(exclude=new_arrival):
            if hasattr(obj, "at_new_arrival"):
                obj.at_new_arrival(new_arrival)


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
        exits, ways, users, things = [], [], [], []

        way_dir = {'ne': 'northeast', 'n': 'north', 'nw': 'northwest', 'e': 'east',
                   'se': 'southeast', 's': 'south', 'sw': 'southwest', 'w': 'west'}

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
        if self.attributes.has('exits'):
            ways = self.db.exits
        if exits or ways:
            string += "\n|wVisible exits|n: " + ", ".join("%s" % e.mxp_name(viewer, '@verb #%s' % e.id) if hasattr(e, "mxp_name") else e.get_display_name(viewer) for e in exits)
            if ways and not ways == {}:
                ew_joiner = ', ' if exits and ways else ''
                string += ew_joiner + ", ".join("|lc%s|lt|540%s|n|le" % (w, way_dir[w]) for w in ways.keys())
        else:
            string += "\n|wVisible exits|n: |lcback|lt|gBack|n|le to %s." % viewer.db.last_room.name
        if users or things:
            user_list = ", ".join(u.mxp_name(viewer, '@verb #%s' % u.id) for u in users)
            ut_joiner = ', ' if users and things else ''
            item_list = ", ".join(t.mxp_name(viewer, '@verb #%s' % t.id) if hasattr(t, "mxp_name") else t.get_display_name(viewer) for t in things)
            string += "\n|wHere you find:|n " + user_list + ut_joiner + item_list
        return string

#[...] class TutorialRoom(DefaultRoom):

    def at_object_creation(self):
        "Called when room is first created"
        self.db.tutorial_info = "This is a tutorial room. It allows you to use the 'tutorial' command."
        # self.cmdset.add_default(TutorialRoomCmdSet) # 
        
    def at_object_receive(self, new_arrival, source_location):
        """
        When an object enters a room we tell other objects in the room
        about it by trying to call a hook on them. The Mob object
        uses this to cheaply get notified of enemies without having
        to constantly scan for them.

        Args:
            new_arrival (Object): the object that just entered this room.
            source_location (Object): the previous location of new_arrival.

        """
        if new_arrival.has_player: # and not new_arrival.is_superuser: # this is a character
            outdoor = self.tags.get('outdoor', category='flags')
            if outdoor:
                tickers = TICKER_HANDLER.all_display()
                counter = 0
                for tick in tickers:
                    if tick[0] == self and tick[1] == 'update_weather':
                        notice = ''
                        counter += 1
                        show = '20%% chance every %s seconds in ' % tick[3]
                        show += "%s%s" % (tick[0] or "[None]", tick[0] and " (#%s)" % (tick[0].id if hasattr(tick[0], "id") else "") or "")
                        if counter > 1:
                            notice = '|rExtra Ticker|n - |yadditional|n '
                            # Too many weather tickers going, maybe remove extra?
                        channel = ChannelDB.objects.channel_search('MudInfo')
                        if channel[0]:
                            channel[0].msg('* %s\'s %s experience * %s%s' % (new_arrival.key, tick[4], notice, show), keep_log=False)
                if counter == 0:  # No weather ticker - add one.
                    interval = random.randint(50, 70)
                    TICKER_HANDLER.add(interval=interval, callback=self.update_weather, idstring='Weather')

            for obj in self.contents_get(exclude=new_arrival):
                if hasattr(obj, "at_new_arrival"):
                    obj.at_new_arrival(new_arrival)

    def return_detail(self, detailkey):
        """
        This looks for an Attribute "obj_details" and possibly
        returns the value of it.

        Args:
            detailkey (str): The detail being looked at. This is
                case-insensitive.

        """
        details = self.db.details
        if details:
            return details.get(detailkey.lower(), None)


    def set_detail(self, detailkey, description):
        """
        This sets a new detail, using an Attribute "details".

        Args:
            detailkey (str): The detail identifier to add (for
                aliases you need to add multiple keys to the
                same description). Case-insensitive.
            description (str): The text to return when looking
                at the given detailkey.

        """
        if self.db.details:
            self.db.details[detailkey.lower()] = description
        else:
            self.db.details = {detailkey.lower(): description}

# [...] class WeatherRoom(TutorialRoom):

    def update_weather(self, *args, **kwargs):
        """
        Called by the tickerhandler at regular intervals. Even so, we
        only update 20% of the time, picking a random weather message
        when we do. The tickerhandler requires that this hook accepts
        any arguments and keyword arguments (hence the *args, **kwargs
        even though we don't actually use them in this example)
        """

        WEATHER_STRINGS = (
        "The rain coming down from the iron-grey sky intensifies.",
        "A gush of wind throws the rain right in your face. Despite your cloak you shiver.",
        "The rainfall eases a bit and the sky momentarily brightens.",
        "For a moment it looks like the rain is slowing, then it begins anew with renewed force.",
        "The rain pummels you with large, heavy drops. You hear the rumble of thunder in the distance.",
        "The wind is picking up, howling around you, throwing water droplets in your face. It's cold.",
        "Bright fingers of lightning flash over the sky, moments later followed by a deafening rumble.",
        "It rains so hard you can hardly see your hand in front of you. You'll soon be drenched to the bone.",
        "Lightning strikes in several thundering bolts, striking the trees in the forest to your west.",
        "You hear the distant howl of what sounds like some sort of dog or wolf.",
        "Large clouds rush across the sky, throwing their load of rain over the world.")

        if random.random() < 0.2:
            # only update 20 % of the time
            self.msg_contents("|w%s|n" % random.choice(WEATHER_STRINGS))
            # TODO: Weather channel? Send weather messages to a channel.   


class RealmEntry(Room):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See examples/object.py for a list of
    properties and methods available on all Objects.
    """

    STYLE = '|242'

    def at_object_creation(self):
        """
        Called when the room is first created.
        """
        super(Room, self).at_object_creation()
        self.db.tutorial_info = "The first room of the realm. " \
                                "This assigns the needed attributes to "\
                                "the character."

    def at_object_receive(self, character, source_location):
        """
        Assign properties on characters
        """

        # setup character for the tutorial
        health = self.db.char_health or 20

        if character.has_player:
            character.db.health = health
            character.db.health_max = health

        if character.is_superuser:
            SUPERUSER_WARNING = "|/WARNING: You are playing as a superuser ({name}). Use the {quell} command to|/" \
                    "play without superuser privileges (many functions and puzzles ignore the|/" \
                    "presence of a superuser, making this mode useful for exploring things behind|/" \
                    "the scenes later).|/"
            string = "-"*78 + SUPERUSER_WARNING + "-"*78
            character.msg("|r%s|n" % string.format(name=character.key, quell="|w@quell|r"))

