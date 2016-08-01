# -*- coding: UTF-8 -*-
from commands.command import MuxCommand


class CmdPose(MuxCommand):
    """
    Describe and/or attempt to trigger an action on an object.
    The pose text will automatically begin with your name.
    pose, try, :, ;
    Usage:
      pose <pose text>
      pose's <pose text>
      pose <pose text> = <verb> <noun>
      try <verb> <noun>
    Options:
    /o or /ooc  (Out-of-character to the room or channel.)
    /m or /magnet  (Show which characters remove name/pose space.)
    Example:
      > pose is standing by the tree, smiling.
      Rulan is standing by the tree, smiling.

      > pose puts his back into it. = get anvil
      Rulan tries to get the anvil. He puts his back into it.
      (optional success message if anvil is liftable.)

      > try unlock door
      Rulan tries to unlock the door.
      (optional success message if door is unlocked.)
    """
    key = 'pose'
    aliases = [':', ';', 'emote', 'try']
    locks = 'cmd:all()'

    def func(self):
        """Basic pose"""
        cmd = self.cmdstring
        opt = self.switches
        args = unicode(self.args).strip()
        char = self.character
        player = self.player
        here = char.location if char else None
        non_space_chars = ['®', '©', '°', '·', '~', '@', '-', "'", '’', ',', ';', ':', '.', '?', '!', '…']
        magnet = True if args and args[0] in non_space_chars or cmd == ";" else False
        if cmd != 'try':
            if not (here and char):
                if args:
                    player.execute_cmd('pub :%s%s' % ('' if magnet else ' ', args))
                else:
                    player.msg('Usage: pose <message>   to pose to public channel.')
                return
            if 'magnet' in opt or 'm' in opt:
                char.msg("Pose magnet glyphs are %s." % non_space_chars)
            if args:
                emote = '[OOC] ' if 'o' in self.switches or 'ooc' in self.switches else ''
                emote += "%s%s|n%s%s" % (char.STYLE, char.key, '' if magnet else ' ', args)
                here.msg_contents(emote)
            else:
                player.execute_cmd('help pose')
        else:
            player.msg('"Try" is |rdisabled|n. (|wCurrently being renovated!|n)')
