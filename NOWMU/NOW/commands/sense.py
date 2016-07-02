from evennia import default_cmds
from django.conf import settings
from evennia import utils

# error return function, needed by Extended Look command
_AT_SEARCH_RESULT = utils.variable_from_module(*settings.SEARCH_AT_RESULT.rsplit('.', 1))


class CmdSense(default_cmds.MuxCommand):
    """
    Handle sensing objects in different ways. WIP: Expanding to handle other senses.
    Sense yourself, your location or objects in your vicinity.
    Usage:
      <sense verb>[/switch] <object>['s aspect[ = [detail]]
      <sense verb>[/switch] *<player>['s aspect[ = [detail]]

      Add detail following the equal sign after the object's aspect.
      Nothing following the equals sign (=) will remove the detail.

      The command 'sense' is strictly informative, while the more specific alternative
      versions are interactive and may trigger a notification, response, or cause effects.
    """
    key = 'sense'
    aliases = ['l', 'look', 'taste', 'touch', 'smell', 'listen']
    locks = 'cmd:all()'
    arg_regex = r'\s|$'
    player_caller = True

    def func(self):
        """Handle sensing objects in different ways. WIP: Expanding to handle other senses."""
        char = self.character
        player = self.player
        args = self.args.strip()
        cmd = self.cmdstring

        if self.rhs is not None:  # Equals sign exists.
            if not self.rhs:  # Nothing on the right side
                char.msg('Functionality to delete aspects and details is not yet implemented.' % self.switches)
            else:
                char.msg('Functionality to add aspects and details is not yet implemented.' % self.switches)
            return
        if cmd != 'l' and 'look' not in cmd:
            if 'sense' in cmd:
                if char and char.location:
                    obj = char.search(args.strip(), candidates=[char.location] + char.location.contents +
                                      char.contents) if args else char
                    verb_msg = ''
                    if obj and obj.db.senses:
                        string = '%s can be sensed in the following ways: ' % obj.get_display_name(player)
                        string += ", ".join('|lc%s #%s|lt|g%s|n|le' % (element, obj.id, element)
                                            for element in obj.db.senses.keys())
                        char.msg(string)
                        string = ''  # list aspects.
                        for element in obj.db.senses.keys():
                            for aspect in obj.db.senses[element].keys():
                                string += "|lc%s %s's %s|lt|g%s|n|le " % (element, obj.key, aspect, aspect)\
                                    if aspect else ''
                        if len(string) > 0:
                            char.msg(obj.get_display_name(player) + ' has the following aspects that can be sensed: ' +
                                     string)
                    else:
                        if obj:
                            verb_msg = "%s responds to: " % obj.get_display_name(player)
                        else:
                            obj = char
                            verb_msg = "%sYou|n respond to: " % char.STYLE
                    verbs = obj.locks
                    collector = ''
                    show_red = True if obj.access(char, 'examine') else False
                    for verb in ("%s" % verbs).split(';'):
                        element = verb.split(':')[0]
                        if element == 'call':
                            continue
                        name = element[2:] if element[:2] == 'v-' else element
                        if obj.access(char, element):  # obj lock checked against actor
                            collector += "|lctry %s #%s|lt|g%s|n|le " % (name, obj.id, name)
                        elif show_red:
                            collector += "|r%s|n " % name
                    char.msg(verb_msg + "%s" % collector)
            elif 'taste' in cmd or 'touch' in cmd or 'smell' in cmd or 'listen' in cmd:  # Specific sense (not look)
                obj, aspect = [args, None] if "'s " not in args else args.rsplit("'s ", 1)
                obj = char.search(obj, candidates=[char.location] + char.location.contents + char.contents)\
                    if args else char
                if not obj:
                    return
                # Object to sense might have been found. Check the senses dictionary.
                if obj.db.senses and cmd in obj.db.senses:
                    senses_of = obj.db.senses[cmd]  # senses_of is the sense dictionary for current sense.
                    if aspect in senses_of:
                        details_of = obj.db.details
                        if details_of and senses_of[aspect] in details_of:
                            entry = details_of[senses_of[aspect]]
                            char.msg('%sYou|n sense %s from %s.' % (char.STYLE, entry, obj.get_display_name(player)))
                        else:
                            if aspect:
                                char.msg("%sYou|n try to sense %s's %s, but can not."
                                         % (char.STYLE, obj.get_display_name(player), aspect))
                            else:
                                char.msg("%sYou|n try to sense %s, but can not."
                                         % (char.STYLE, obj.get_display_name(player)))
                    else:
                        if aspect:
                            char.msg("%sYou|n try to sense %s's %s, but can not."
                                     % (char.STYLE, obj.get_display_name(player), aspect))
                        else:
                            char.msg("%sYou|n try to sense %s, but can not."
                                     % (char.STYLE, obj.get_display_name(player)))
                else:
                    char.msg('%sYou|n try to sense %s, but can not.' % (char.STYLE, obj.get_display_name(player)))
                # First case: look for an object in room, inventory, room contents, their contents,
                # and their contents contents with tagged restrictions, then if no match is found
                # in their name or alias, look at the senses tables in each of these objects: The
                # Senses attribute is a dictionary of senses that point to the details dictionary
                # entries. Senses dictionary allows for aliases in the details and pointing
                # specific senses to specific entries.
                #
                # If not looking for a specific object or entry, list objects and aspects of the particular
                # sense. Start with that first, and start with the char's own self and inventory.
                # when the /self;me and /inv;inventory switch is used?
            return
        if args:
            obj = char.search(args, candidates=char.location.contents + char.contents, use_nicks=True, quiet=True)
            if not obj:
                # no object found. Check if there is a matching detail around the location.
                # TODO: Restrict search for details by possessive parse:  [object]'s [aspect]
                candidates = [char.location] + char.location.contents + char.contents
                for location in candidates:
                    # TODO: Continue if look location is not visible to looker.
                    if location and hasattr(location, "return_detail") and callable(location.return_detail):
                        detail = location.return_detail(args)
                        if detail:
                            char.msg(detail)  # Show found detail.
                            return  # TODO: Add /all switch to override return here to view all details.
                # no detail found. Trigger delayed error messages
                _AT_SEARCH_RESULT(obj, char, args, quiet=False)
                return
            else:
                obj = utils.make_iter(obj)[0]  # Use the first match in the list.
        else:
            obj = char.location
            if not obj:
                char.msg("There is nothing to sense here.")
                return
        if not hasattr(obj, 'return_appearance'):
            # this is likely due to a player calling the command.
            obj = obj.character
        if not obj.access(char, 'view'):
            char.msg("You are unable to sense '%s'." % args)
            return
        # get object's appearance
        char.msg(obj.return_appearance(char))
        # the object's at_desc() method.
        obj.at_desc(looker=char)
