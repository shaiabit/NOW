# -*- coding: utf-8 -*-
from evennia import DefaultObject
from evennia.utils import inherits_from
from evennia.utils.utils import lazy_property
from typeclasses.traits import TraitHandler
from functools import reduce
import time  # Check time since last visit


class Tangible(DefaultObject):
    """
    Methods universal to all tangible in-world objects are
    included here.

    Includes all DefaultObject methods and contains methods
    used in Rooms, Characters, Objects, and Exits, which
    are categorized as "Tangible"
    """
    STYLE = '|Y'

    @lazy_property
    def traits(self):
        return TraitHandler(self)

    def at_object_receive(self, new_arrival, source_location):
        """
        When an object enters another.

        Args:
            new_arrival (Object): the object that just entered this room.
            source_location (Object): the previous location of new_arrival.
        """
        # Add object to "hosted" attribute dictionary on self, keyed by object.
        # Value is (timestamp, source_location, visit_count)
        now = int(time.time())
        last_entry = (self.db.hosted and self.db.hosted.get(new_arrival)) or (now, source_location, 0)
        visit_count = (last_entry[2] + 1)
        new_arrival.ndb.last_visit = (last_entry[0], source_location)
        if self.db.hosted:
            self.db.hosted[new_arrival] = (now, source_location, visit_count)
        else:
            self.db.hosted = {new_arrival: (now, source_location, visit_count)}

    def get_display_name(self, viewer, **kwargs):
        """
        Displays the name of the object in a viewer-aware manner.

        Args:
            self (Object, Character, Exit or Room):
            viewer (TypedObject): The Tangible object, account, or session
                that needs the name of this Tangible object.
        Kwargs:
            pose Return pose appended to name if True
            color Return includes color style markup prefix if True
            mxp Return includes mxp command markup prefix if provided
            db_id Return includes database id to privileged viewers if True
            plain Return does not include database id or color
        Returns:
            name (str): A string of the sdesc containing the name of the object,
            if this is defined.
                including the DBREF if viewer is privileged to control this.
        """
        name = self.key
        if not viewer:
            viewer = viewer.get_puppet_or_account
        if inherits_from(viewer, "evennia.accounts.accounts.DefaultAccount"):
            viewer = viewer.get_puppet(viewer.sessions.all()[0])  # viewer is an Account, convert to tangible
        if not (viewer and viewer.has_account):
            return '{}{}|n'.format(self.STYLE, name)
        color, pose = [kwargs.get('color', True), kwargs.get('pose', False)]  # Read kwargs, set defaults.
        mxp, db_id = [kwargs.get('mxp', False), kwargs.get('db_id', True)]
        if kwargs.get('plain', False):  # "plain" means "without color, without db_id"
            color, db_id = [False, False]
        display_name = ("%s%s|n" % (self.STYLE, name)) if color else name
        if mxp:
            display_name = "|lc%s|lt%s|le" % (mxp, display_name)
        if not viewer.account.attributes.has('_quell') and self.access(viewer, access_type='control') and db_id:
            display_name += '|w(#%s)|n' % self.id
        if pose and self.db.messages and (self.db.messages.get('pose') or self.db.messages.get('pose_default')):
            display_pose = self.db.messages.get('pose') if self.db.messages.get('pose', None)\
                else self.db.messages.get('pose_default')
            display_name += ('|n' if color else '') + display_pose
        return display_name

    def get_mass(self):
        mass = self.traits.mass.actual if self.traits.mass else 0
        if mass <= 0 and self.tags.get('weightless', category='flags'):
            return mass  # Ignore mass of contents if this tangible is weight-free or inert.
        return reduce(lambda x, y: x+y.get_mass() if hasattr(y, 'get_mass') else 0, [mass] + self.contents)

    def get_limit(self):
        # TODO: Apply health as a small factor.
        mass = self.traits.mass.actual if self.traits.mass else 10
        swr = self.traits.swr.actual if self.traits.swr else 1.0
        return swr * mass - (self.get_mass() - mass)

    def private(self, source, category, text):
        """
        Displays a private message to self from source of a certain category
        Args:
            self (Object, Character, Exit or Room to receive message)
            source (Object, Character, Exit or Room)
            category (string) type of private message.
            text (string) text of private message.
              self will see "You privately " prepended to message.
        """
        print('%s-(%s)-> %s "%s"' % (source.key if source else 'NOW', category, self.key, text))
        message = '%sYou|n privately ' % self.STYLE
        if category == 'whisper':
            message += 'hear %s whisper "|w%s|n".' % (source.get_display_name(self), text)
        elif source is None:
            message = text
        else:
            message += text
        self.msg(message)

    def return_glance(self, viewer, bool=False, oob=False):
        """
        Displays the name or sdesc of the object with its room pose in a viewer-aware manner.
        If self is in Nothingness, shows inventory contents instead of room contents.

        Args:
            self (Object, Character, or Room):
            viewer (TypedObject): The object or account that is looking
                at/getting information for this object.
            bool (bool): Return True instead of a string list.
            oob (bool): Include viewer as if out of body.

        Returns:
            name (str): A string of the name or sdesc containing the name of the objects
            contained within and their poses in the room. If 'self' is a room, the room
            is omitted from the output. Calls 'get_display_name' - output depends on viewer.
        """
        users, things = [], []
        if self.location:
            visible = (con for con in [self] + self.contents if con.access(viewer, 'view'))
        else:
            visible = (con for con in self.contents if (con != viewer or oob) and con.access(viewer, 'view'))
        for con in visible:
            if con.has_account:
                users.append(con)
            elif con.destination:
                continue
            else:
                things.append(con)
        if users or things:
            user_list = ", ".join(u.get_display_name(viewer, mxp='sense %s' % u.get_display_name(
                viewer, plain=True), pose=True) for u in users)
            ut_joiner = ', ' if users and things else ''
            item_list = ", ".join(t.get_display_name(viewer, mxp='sense %s' % t.get_display_name(
                viewer, plain=True), pose=True) for t in things)
            if bool:
                return True
            glance_result = ((user_list + ut_joiner + item_list).replace('\n', '').replace('.,', ';'))
            end_character = '' if glance_result[-1:] in ('.', '!', '?', ';', ':') else '.'
            return glance_result + end_character
        if bool:
            return False
        # See your own pose if OOB mode, else there's nothing here except you.
        return viewer.get_display_name(viewer, pose=True) if oob else '%sYou|n see no items here.' % viewer.STYLE

    def return_detail(self, detail_key, detail_sense):
        """
        This looks for an Attribute "obj_details" and possibly
        returns the value of it.

        Args:
            detail_key (str): The detail being looked at. This is case-insensitive.
        """
        # return self.db.details.get(self.db.senses.get(detail_sense.lower()), None) if self.db.details else None
        pass

    def set_detail(self, detail_key, description):
        """
        This sets a new detail, using an Attribute "details".

        Args:
            detail_key (str): The detail identifier to add (for
                aliases you need to add multiple keys to the
                same description). Case-insensitive.
            description (str): The text to return when looking
                at the given detail_key.
        """
        # if self.db.details:
        #     self.db.details[detail_key.lower()] = description
        # else:
        #     self.db.details = {detail_key.lower(): description}
        pass
