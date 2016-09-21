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
            contents = here.contents
            for obj in contents:
                obj.msg('%s warms up vocally with "%s|n"' % (char.get_display_name(obj), args))
            return
        if 'q' in opt or 'quote' in opt:
            if len(args) > 2:
                char.quote = args  # Not yet implemented.
                return
        else:
            speech = here.at_say(char, args)  # Notify NPCs and listeners.
            verb = char.attributes.get('say-verb') if char.attributes.has('say-verb') else 'says'
            if 'o' in opt or 'ooc' in opt:
                contents = here.contents
                for obj in contents:
                    obj.msg('[OOC]|n %s %s, "|w%s|n"' % (char.get_display_name(obj), 'says', speech))
            else:
                contents = here.contents
                for obj in contents:
                    obj.msg('%s %s, "|w%s|n"' % (char.get_display_name(obj), verb, speech))


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
            contents = here.contents
            for obj in contents:
                obj.msg('[OOC %s] %s' % (char.get_display_name(obj), args))


class CmdSpoof(MuxCommand):
    """
    Send a spoofed message to your current location.
    Usage:
      spoof <message>
    Switches:
    /center <msg> [ = position ]  Center msg at position
    /right <msg> [ = position ]   Align right at position
    /indent <msg> [ = position ]  Begin msg starting at position
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
        if 'indent' in opt:
            indent = 20
            if self.rhs:
                args = self.lhs.strip()
                indent = re.sub("[^0123456789]", '', self.rhs) or 20
                indent = int(indent)
            if 'self' in opt:
                char.msg(' ' * indent + args.rstrip())
            else:
                here.msg_contents(' ' * indent + args.rstrip())
        elif 'right' in opt or 'center' in opt or 'news' in opt:
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
                    outside, inside = [72, 20]
            else:
                outside, inside = [72, min(int(self.rhs or 72), 20)]
            block = 'r' if 'right' in opt else 'f'
            block = 'c' if 'center' in opt else block
            for text in justify(args, width=outside, align=block, indent=inside).split('\n'):
                if 'self' in opt:
                    char.msg(text.rstrip())
                else:
                    here.msg_contents(text.rstrip())
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
                    char.msg(args.rstrip())
                else:
                    here.msg_contents(marked.rstrip())
