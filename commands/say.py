# -*- coding: UTF-8 -*-
from commands.command import MuxCommand
from evennia.utils import ansi


class CmdSay(MuxCommand):
    """
    Speak as your character.
    Usage:
      say <message>
    Switches:
    /o or /ooc  - Out-of-character to the room.
    /v or /verb - set default say verb.
    """
    key = 'say'
    aliases = ['"', "'", '""', "''", 'lsay']
    locks = 'cmd:all()'

    def func(self):
        """Run the say command"""
        char = self.character
        here = char.location if char else None
        player = self.player
        cmd = self.cmdstring
        opt = self.switches
        args = self.args.strip()
        if not (here and char):
            player.execute_cmd("pub %s" % args)
            return
        if not args:
            player.execute_cmd("help say")
            return
        if 'v' in opt or 'verb' in opt:
            char.attributes.add('say-verb', args)
            emit_string = '%s%s|n warms up vocally with "%s|n"' % (char.STYLE, char.key, args)
            here.msg_contents(emit_string)
            return
        if 'q' in opt or 'quote' in opt:
            if len(args) > 2:
                char.quote = args  # Not yet implemented.
                return
        if 'l' in opt or 'local' in opt or cmd == 'lsay' or cmd == "''" or cmd == '""':
            seat = here  # seat is where character is sitting.
            speech = seat.at_say(char, args)  # Notify NPCs and listeners.
            verb = char.attributes.get('say-verb') if char.attributes.has('say-verb') else 'says'
            emit_string = '%s%s|n %s, "%s|n"' % (char.STYLE, char.key, verb, speech)
            sitters = []
            for sitter in sitters:
                if 'o' in opt or 'ooc' in opt:
                    emit_string = '[OOC]|n %s%s|n says, "%s"' % (char.STYLE, char, speech)
                else:
                    sitter.msg(emit_string)
        else:
            speech = here.at_say(char, args)  # Notify NPCs and listeners.
            verb = char.attributes.get('say-verb') if char.attributes.has('say-verb') else 'says'
            if 'o' in opt or 'ooc' in opt:
                emit_string = '[OOC]|n %s%s|n says, "%s"' % (char.STYLE, char, speech)
            else:
                emit_string = '%s%s|n %s, "%s|n"' % (char.STYLE, char.key, verb, speech)
            here.msg_contents(emit_string)


class CmdOoc(MuxCommand):
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
        char = self.character
        player = self.player
        here = char.location
        args = self.args.strip()
        if not args:
            player.execute_cmd('help ooc')
            return
        elif args[0] == '"' or args[0] == "'":
            player.execute_cmd('say/o ' + here.at_say(char, args[1:]))
        elif args[0] == ':' or args[0] == ';':
            player.execute_cmd('pose/o %s' % args[1:])
        else:
            here.msg_contents('[OOC %s] %s' % (char.get_display_name(self.session), args))


class CmdSpoof(MuxCommand):
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
        char = self.character
        here = char.location
        args = self.args.strip()
        if not args:
            char.execute_cmd('help spoof')
            return
        if 'self' in self.switches:
            char.msg(self.args)
            return
        else:  # Strip any markup to secure the spoof.
            spoof = ansi.strip_ansi(args)
        # calling the speech hook on the location.
        # An NPC would know who spoofed.
        spoof = here.at_say(char, spoof)
        here.msg_contents(spoof, options={'raw': True})
