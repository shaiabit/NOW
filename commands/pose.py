# -*- coding: UTF-8 -*-
from commands.command import MuxCommand


class CmdPose(MuxCommand):
    """
    Describe and/or attempt to trigger an action on an object.
    The pose text will automatically begin with your name.
    pose, emote, :, ;
    Usage:
      pose <pose text>
      pose's <pose text>
      pose <pose text> = <verb> <noun>
    Options:
    /o or /ooc  (Out-of-character to the room or channel.)
    /m or /magnet  (Show which characters remove name/pose space.)
    Example:
      > pose is standing by the tree, smiling.
      Rulan is standing by the tree, smiling.

      > pose strains to lift the anvil. = get anvil
      Werewolf strains to lift the anvil. Werewolf takes the anvil.
      (optional success message if anvil is liftable.)
    """
    key = 'pose'
    aliases = [':', ';', 'emote']
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
        pose = self.lhs if self.rhs else args
        if not (here and char):
            if args:
                player.execute_cmd('pub :%s%s' % ('' if magnet else '|_', pose))
            else:
                player.msg('Usage: pose <message>   to pose to public channel.')
            return
        if 'magnet' in opt or 'm' in opt:
            char.msg("Pose magnet glyphs are %s." % non_space_chars)
        if args:
            emote = '[OOC] ' if 'o' in self.switches or 'ooc' in self.switches else ''
            emote += "%s%s|n%s%s" % (char.STYLE, char.key, '' if magnet else '|_', pose)
            if self.rhs:
                char.ndb.power_pose = emote
                player.execute_cmd(self.rhs)
            else:
                here.msg_contents(emote)
        else:
            player.execute_cmd('help pose')
