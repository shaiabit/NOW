# -*- coding: UTF-8 -*-
from evennia import default_cmds
from evennia.utils import ansi


class CmdSay(default_cmds.MuxCommand):
    """
    Speak as your character.
    Usage:
      say <message>
    Switches:
    /o or /ooc  - Out-of-character to the room.
    /v or /verb - set default say verb.
    """
    key = 'say'
    aliases = ['"', "'"]
    locks = 'cmd:all()'
    player_caller = True

    def func(self):
        """Run the say command"""
        char = self.character
        here = char.location
        player = self.player
        args = self.args.strip()
        switches = self.switches
        if not here:
            player.execute_cmd("pub %s" % args)
            return
        if not args:
            char.execute_cmd("help say")
            return
        if 'v' in switches or 'verb' in switches:
            char.attributes.add('say-verb', args)
            emit_string = '%s%s|n warms up vocally with "%s|n"' % (char.STYLE, char.key, args)
            here.msg_contents(emit_string)
            return
        if 'q' in switches or 'quote' in switches:
            if len(args) > 2:
                char.quote = args  # Not yet implemented.
                return
        speech = here.at_say(char, args)  # Notify NPCs and listeners.
        if 'o' in switches or 'ooc' in switches:
            emit_string = '[OOC]|n %s%s|n says, "%s"' % (char.STYLE, char, speech)
        else:
            verb = char.attributes.get('say-verb') if char.attributes.has('say-verb') else 'says'
            emit_string = '%s%s|n %s, "%s|n"' % (char.STYLE, char.key, verb, speech)
        here.msg_contents(emit_string)


class CmdOoc(default_cmds.MuxCommand):
    """
    Send an out-of-character message to your current location.
    Usage:
      ooc <message>
      ooc :<message>
      ooc "<message>.
    """
    key = 'ooc'
    aliases = ['_']
    locks = 'cmd:all()'

    def func(self):
        """Run the ooc command"""
        caller = self.caller
        args = self.args.strip()
        if not args:
            caller.execute_cmd('help ooc')
            return
        elif args[0] == '"' or args[0] == "'":
            caller.execute_cmd('say/o ' + caller.location.at_say(caller, args[1:]))
        elif args[0] == ':' or args[0] == ';':
            caller.execute_cmd('pose/o %s' % args[1:])
        else:
            caller.location.msg_contents('[OOC %s] %s' % (caller.get_display_name(self.session), args))


class CmdSpoof(default_cmds.MuxCommand):
    """
    Send a spoofed message to your current location.
    Usage:
      spoof <message>
    Switches:
    /self <message only to you>
    """
    key = 'spoof'
    aliases = ['~', '`', 'sp']
    locks = 'cmd:all()'

    def func(self):
        """Run the spoof command"""
        caller = self.caller
        if not self.args:
            caller.execute_cmd('help spoof')
            return
        if 'self' in self.switches:
            caller.msg(self.args)
            return
        else:  # Strip any markup to secure the spoof.
            spoof = ansi.strip_ansi(self.args)
        # calling the speech hook on the location.
        # An NPC would know who spoofed.
        spoof = caller.location.at_say(caller, spoof)
        caller.location.msg_contents(spoof, options={'raw': True})


class CmdPose(default_cmds.MuxCommand):
    """
    Describe and/or attempt to trigger an action on an object.
    The pose text will automatically begin with your name.
    pose, try, :, ;
    Usage:
      pose <pose text>
      pose's <pose text>
      pose <verb> <noun>::<pose text>
      try <verb> <noun>
    Switches:
    /o or /ooc - Out-of-character to the room.
    Example:
      > pose is standing by the tree, smiling.
      Rulan is standing by the tree, smiling.

      > pose get anvil::puts his back into it.
      Rulan tries to get the anvil. He puts his back into it.
      (optional success message if anvil is liftable.)

      > try unlock door
      Rulan tries to unlock the door.
      (optional success message if door is unlocked.)
    """
    key = 'pose'
    aliases = [':', ';', 'emote', 'try']
    locks = 'cmd:all()'
    player_caller = True

    def parse(self):
        """
        Parse the cases where the emote starts with specific characters,
        such as 's, at which we don't want to separate the character's
        name and the emote with a space.

        Also parse for a verb and optional noun, which if blank is assumed
        to be the character, in a power pose of the form:
        verb noun::pose
        verb::pose

        verb noun::
        verb::

        or using the try command, just
        verb noun
        verb
        """
        super(CmdPose, self).parse()
        args = unicode(self.args).strip()
        char = self.character
        here = char.location
        player = self.player
        if not here:
            player.execute_cmd("pub :%s" % args)
            return
        if not self.args:
            char.execute_cmd("help pose")
            return
        self.verb = None
        self.obj = None
        self.msg = ''
        non_space_chars = ["®", "©", "°", "·", "~", "@", "-", "'", "’", ",", ";", ":", ".", "?", "!", "…"]

        if 'magnet' in self.switches or 'm' in self.switches:
            char.msg("Pose magnet glyphs are %s." % non_space_chars)
        if self.cmdstring == 'try':
            args += '::'
        if len(args.split('::')) > 1:
            verb_noun, pose = args.split('::', 1)
            if 0 < len(verb_noun.split()):
                args = pose
                self.verb = verb_noun.split()[0]
                noun = ' '.join(verb_noun.split()[1:])
                if noun == '':
                    # if self.verb is any of the current exits or aliases of the exits:
                    exit_list = here.exits
                    if self.verb in exit_list:  # TODO: Test if the verb is an exit name
                        noun = self.verb
                        self.verb = 'go'
                    else:
                        self.obj = char
                        noun = 'me'
                else:
                    self.obj = char.search(noun, location=[char, here])
        if args and not args[0] in non_space_chars:
            if not self.cmdstring == ";":
                args = " %s" % args.strip()
        self.args = args

    def func(self):
        """Hook function"""
        cmd = self.cmdstring
        args = unicode(self.args)
        char = self.character
        here = char.location
        if not here:
            return
        self.text = ''
        if self.args:
            if 'o' in self.switches or 'ooc' in self.switches:
                self.text = "[OOC] %s%s|n%s" % (char.STYLE, char.key, args)
            else:
                self.text = "%s%s|n%s" % (char.STYLE, char.key, args)
            if self.obj and self.verb:
                pass
            else:
                here.msg_contents(self.text)
        elif cmd != 'try':
            return

    def at_post_cmd(self):
        """Verb response here."""
        super(CmdPose, self).at_post_cmd()
        if not self.character.location:
            return
        if self.obj:
            obj = self.obj
            verb = self.verb
            safe_verb = verb
            char = self.character
            player = self.player
            here = char.location
            pose = self.text
            if verb == 'go':
                verb = 'traverse'
                safe_verb = 'traverse'
            if not obj.access(char, verb):  # Try original verb first.
                safe_verb = 'v-' + verb  # If that does not work, then...
            if obj.access(char, safe_verb):  # try the safe verb form.
                if verb == 'drop':
                    obj.drop(pose, char)
                elif verb == 'get':
                    obj.get(pose, char)
                elif verb == 'traverse':
                    char.execute_cmd(obj.key)
                elif verb == 'sit':
                    obj.surface_put(pose, char, 'on')
                elif verb == 'leave':
                    obj.surface_off(pose, char)
                elif verb == 'read':
                    obj.read(pose, char)
                elif verb == 'drink':
                    obj.drink(char)
                elif verb == 'eat':
                    obj.eat(char)
                elif verb == 'follow':
                    obj.follow(char)
                elif verb == 'view':
                    char.execute_cmd('%s #%s' % ('l', obj.id))
                elif verb == 'puppet':
                    player.execute_cmd('@ic ' + obj.key)
                elif verb == 'examine':
                    player.execute_cmd('examine ' + obj.key)
                else:
                    if self.text != '':
                        # self.text += " |g|S|n is able to %s %s%s|n." % (verb, obj.STYLE, obj.key)
                        # TODO: When pronoun substitution works.
                        self.text = "|g%s|n is able to %s %s%s|n." % (char.key, verb, obj.STYLE, obj.key)
                        # TODO: Otherwise, do this.
                    else:
                        self.text = "|g%s|n is able to %s %s%s|n." % (char.key, verb, obj.STYLE, obj.key)
                    here.msg_contents(self.text)
                    # TODO: Show actual message response below. TODO - show get_display_name once session is available.
                    here.msg_contents("%s%s|n response message to %s%s|n %s goes here." %
                                      (obj.STYLE, obj.key, char.STYLE, char.key, verb))
            else:
                if self.obj.locks.get(verb):  # Test to see if a lock string exists.
                    if self.text != '':
                        self.text += " |r|S|n fails to %s %s%s|n." % (verb, obj.STYLE, obj.key)
                    else:
                        self.text = "|r%s|n fails to %s %s%s|n." % (char.key, verb, obj.STYLE, obj.key)
                    here.msg_contents(self.text)  # , exclude=char)
                    # char.msg("You failed to %s %s." % (verb, obj.name))
                else:
                    char.msg("It is not possible to %s %s%s|n." % (verb, obj.STYLE, obj.key))
