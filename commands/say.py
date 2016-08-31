# -*- coding: UTF-8 -*-
import re
from commands.command import MuxCommand
from evennia.utils import ansi
from evennia.utils.utils import pad, justify


class CmdSay(MuxCommand):
    """
    Speak as your character.
    Usage:
      say <message>
    Options:
    /o or /ooc  - Out-of-character to the room.
    /v or /verb - set default say verb.
    """
    key = 'say'
    aliases = ['"', "'"]
    locks = 'cmd:all()'

    def func(self):
        """Run the say command"""
        char = self.character
        here = char.location if char else None
        player = self.player
        opt = self.switches
        args = self.args.strip()
        if not (here and char):
            if args:
                player.execute_cmd('pub %s' % args)
            else:
                player.msg('Usage: say <message>   to speak on public channel.')
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
    /center <msg> [ = position ]  Center msg at position
    /right <msg> [ = position ]   Alighn right at position
    /news <message> [ = <width> [indent] ]
    /strip <message sent to room with markup stripped>
    /self <message only to you with full markup>
    """
    key = 'spoof'
    aliases = ['~', '`', 'sp']
    locks = 'cmd:all()'

    def func(self):
        """Run the spoof command"""
        char = self.character
        here = char.location
        opt = self.switches
        args = self.args.strip()
        if not args:
            char.execute_cmd('help spoof')
            return
        if 'right' in opt:
            right = 20
            if self.rhs:
                args = self.lhs.strip()
                right = re.sub("[^0123456789]", '', self.rhs) or 20
                right = int(right)
            if 'self' in opt:
                char.msg(args.rstrip().rjust(right, ' '))
            else:
                here.msg_contents(args.rstrip().rjust(right, ' '))
        elif 'center' in opt:
            center = 72
            if self.rhs:
                args = self.lhs.strip()
                center = re.sub("[^0123456789]", '', self.rhs) or 72
                center = int(center)
            if 'self' in opt:
                char.msg(pad(args, width=center).rstrip())
            else:
                here.msg_contents(pad(args, width=center).rstrip())
        elif 'news' in opt:
            if self.rhs is not None:  # Equals sign exists.
                parameters = '' if not self.rhs else self.rhs.split()
                args = self.lhs.strip()
                if len(parameters) > 1:
                    if len(parameters) == 2:
                        outside, inside = self.rhs.split()
                    else:
                        outside, inside = [parameters[0], parameters[1]]
                    outside = re.sub("[^0123456789]", '', outside) or 0
                    inside = re.sub("[^0123456789]", '', inside) or 0
                    outside, inside = [int(max(outside, inside)), int(min(outside, inside))]
                else:
                    outside, inside = [72, 52]
            else:
                outside, inside = [72, min(int(self.rhs or 72), 72)]
            for text in justify(args, width=inside).split('\n'):
                if 'self' in opt:
                    char.msg(pad(text, width=outside).rstrip())
                else:
                    here.msg_contents(pad(text, width=outside).rstrip())
        else:
            stripped = ansi.strip_ansi(args)
            marked = self.args.replace('|', '||')
            here.at_say(char, stripped)  # calling the speech hook on the location.
            if 'strip' in opt:  # Optionally strip any markup or escape it,
                if 'self' in opt:
                    char.msg(stripped.rstrip(), options={'raw': True})
                else:
                    here.msg_contents(stripped.rstrip(), options={'raw': True})
            else:
                if 'self' in opt:
                    char.msg(marked.rstrip())
                else:
                    here.msg_contents(marked.rstrip())
