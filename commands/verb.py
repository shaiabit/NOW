# -*- coding: UTF-8 -*-
from commands.command import MuxCommand
from evennia import syscmdkeys, Command
from evennia.utils.utils import string_suggestions


class CmdTry(MuxCommand):
    """
    Actions a character can do to things nearby.
    Usage:
      ppose <pose> = <verb> [noun]
      try <verb> [noun]
      <verb> [noun]
    """
    key = syscmdkeys.CMD_NOMATCH
    aliases = 'try'
    auto_help = False
    locks = 'cmd:all()'
    arg_regex = r'\s|$'
    player_caller = True

    def func(self):
        """
        Run the try command
        TODO: Parse <verb>, <verb> <article> <noun>, <verb> <preposition> <noun>, <verb> <preposition> <article> <noun>.
        """
        player = self.player
        char = self.character
        args = self.args
        if args[3:] == 'try':
            args = args[:4]
        here = char.location if char else None
        verb_list = self.verb_list()
        verb, noun = args.split(' ', 1) if ' ' in args else [args, '']
        obj = None
        if args:
            if verb not in verb_list:  # No valid verb used
                if char.ndb.power_pose:  # Detect invalid power pose.
                    here.msg_contents('%s = %s' % (char.ndb.power_pose, args))  # Display as normal pose.
                    char.nattributes.remove('power_pose')  # Flush power pose
                else:
                    player.msg(self.suggest_command())
                return
            else:
                good_targets = self.objects_allowing_verb(verb)
                if noun:  # Look for an object that matches noun.
                    obj = char.search(noun, quiet=True, candidates=[here] + here.contents + char.contents)
                    obj = obj[0] if obj else None
                if not obj:
                    obj = good_targets[0] if len(good_targets) == 1 else None
                player.msg('(%s/%s (%s))' % (verb, noun, obj))
                if obj and obj in good_targets:
                    if char.ndb.power_pose and here:
                        contents = here.contents
                        for viewer in contents:
                            viewer.msg('|w* %s%s' % (char.get_display_name(viewer), char.ndb.power_pose))
                        char.nattributes.remove('power_pose')
                    else:
                        contents = here.contents
                        for viewer in contents:
                            viewer.msg('|w* %s tries to %s %s|n.'
                                       % (char.get_display_name(viewer), verb, obj.get_display_name(viewer)))
                    self.trigger_response(verb, obj)
                else:
                    if good_targets:
                        if obj:
                            player.msg('You can only %s %s|n.' % (verb, self.style_object_list(good_targets, char)))
                        else:
                            player.msg('You can %s %s|n.' % (verb, self.style_object_list(good_targets, char)))
                    else:
                        player.msg('You can not %s %s|n.' % (verb, obj.get_display_name(player)))
        else:
            player.msg('|wVerbs to try|n: |g%s|n.' % '|w, |g'.join(verb_list))

    @staticmethod
    def trigger_response(verb, obj):
        """
        Triggers object method (check for method on object - check against forbidden list.)
        Triggers command alias (tabled)
        Triggers message (look for message)
        """
        if obj.db.messages and verb in obj.db.messages and obj.location:
            contents = obj.location.contents
            for viewer in contents:
                viewer.msg('%s %s' % (obj.get_display_name(viewer), obj.db.messages[verb]))
        elif obj.location:
            contents = obj.location.contents
            for viewer in contents:
                viewer.msg('%s responds to %s.' % (obj.get_display_name(viewer), verb))

    def verb_list(self):
        """Scan location for objects that have verbs, and collect the verbs in a list."""
        collection = []
        for obj in [self.character.location] + self.character.location.contents + self.character.contents:
            verbs = obj.locks
            for verb in ("%s" % verbs).split(';'):
                element = verb.split(':')[0]
                name = element[2:] if element[:2] == 'v-' else element
                if obj.access(self.character, element):  # obj lock checked against character
                    collection.append(name)
        return list(set(collection))

    def objects_allowing_verb(self, search_verb):
        """Scan location for objects that have a specific verb, and collect the objects in a list."""
        collection = []
        for obj in [self.character.location] + self.character.location.contents + self.character.contents:
            verbs = obj.locks
            for verb in ("%s" % verbs).split(';'):
                element = verb.split(':')[0]
                name = element[2:] if element[:2] == 'v-' else element
                if name == search_verb and obj.access(self.character, element):  # search_verb on object is accessible.
                    collection.append(obj)
        return list(set(collection))

    @staticmethod
    def style_object_list(objects, viewer):
        """Turn a list of objects into a stylized string for display."""
        collection = []
        for obj in objects:
            collection.append(obj.get_display_name(viewer))
        return ', '.join(collection)

    def suggest_command(self):
        """Create default "command not available" error message."""
        raw = self.raw_string
        char = self.character
        message = "|wCommand |n'|y%s|n' |wis not available." % raw
        suggestions = string_suggestions(raw, self.cmdset.get_all_cmd_keys_and_aliases(char), cutoff=0.72, maxnum=3)
        if suggestions:
            if len(suggestions) == 1:
                message += ' Maybe you meant |n"|g%s|n" |w?' % suggestions[0]
            else:
                message += ' Maybe you meant %s' % '|w, '.join('|n"|g%s|n"' % each for each in suggestions[:-1])
                message += ' |wor |n"|g%s|n" |w?' % suggestions[-1:][0]
        else:
            message += ' Type |n"|ghelp|n"|w for help.'
        return message
