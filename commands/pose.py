# -*- coding: UTF-8 -*-
from commands.command import MuxCommand
from world.helpers import escape_braces


class CmdPose(MuxCommand):
    """
    Describe and/or attempt to trigger an action on an object.
    The pose text will automatically begin with your name.
    pose, emote, :, ;
    Usage:
      pose <pose text>
      pose's <pose text>
      pp <pose text> = <verb> <noun>
    Options:
    /o or /ooc  (Out-of-character to the room or channel.)
    /m or /magnet  (Show which characters remove name/pose space.)
    /do    (Pose and set room-pose/doing message.)
    Example:
      > pose is standing by the tree, smiling.
      Rulan is standing by the tree, smiling.
    """
    # > ppose strains to lift the anvil. = get anvil
    # > Werewolf strains to lift the anvil.
    # ==> Werewolf takes the anvil.
    # (optional success message if anvil is liftable.)
    key = 'pose'
    aliases = ['p:', 'pp', 'ppose', ':', ';', 'rp', 'do', 'doing']
    locks = 'cmd:all()'
    player_caller = True

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
        power = True if self.cmdstring == 'ppose' or self.cmdstring == 'pp' or self.cmdstring == 'p:' else False
        pose = ('' if magnet else '|_') + (self.lhs if power and self.rhs else args)
        if 'do' in cmd or 'rp' in cmd:
            target = char
            if not args and 'reset' not in opt:
                pose = char.attributes.get('pose')
                if pose:
                    char.msg("Current pose reads: '%s'" % char.get_display_name(char, pose=True))
                    default_pose = target.db.pose_default or None
                    if default_pose:
                        char.msg('Default pose is \'%s%s\'' % (char.get_display_name(char), pose))
                    else:
                        char.msg('Default pose not set.')
                else:
                    char.msg('No pose has been set.|/Usage: rp <pose-text> OR pose obj = <pose-text>')
                return
            if target and '=' in self.args:  # affect something else other than self. TODO: not currently parsed.
                target = char.search(target)
                if not target:
                    return
                if not target.access(char, 'edit'):
                    char.msg('You have no permission to edit %s.' % target.get_display_name(char))
                    return
            else:
                target = char
            if not target.attributes.has('pose'):  # Check to see if any pose message is available, set Default if so
                char.db.pose = ''  # TODO: Replace use of .db.pose with db.message['pose']
                char.db.pose_default = '|_is here.'  # TODO: depreciate .db.pose_default, use db.message['pose default']
            target_name = target.sdesc.get() if hasattr(target, '_sdesc') else target.key
            # set the pose
            if 'reset' in opt:
                pose = target.db.pose_default
                target.db.pose = pose
            elif 'default' in opt:
                target.db.pose_default = pose
                char.msg("Default pose is now: '%s%s'" % (char.get_display_name(char), pose))
                return
            else:
                if len(target_name) + len(pose) > 60:
                    char.msg('Your pose is too long.')
                    return
                target.db.pose = pose
                if self.args:
                    player.execute_cmd(';%s' % pose)
            char.msg("Pose now set to: '%s'" % char.get_display_name(char, pose=True))
        else:  # Action pose, not static Room Pose.
            if 'magnet' in opt or 'm' in opt:
                char.msg("Pose magnet glyphs are %s." % non_space_chars)
            if not (here and char):
                if args:
                    player.execute_cmd('pub :%s' % pose)
                else:
                    player.msg('Usage: pose <message>   to pose to public channel.')
                return
            if args:
                if char.location.tags.get('rp', category='flags') and 'o' not in self.switches:
                    pass  # char.execute_cmd('emote /me%s' % pose)  # Emoting is posing in RP flagged areas.
                elif power and self.rhs and 'o' not in self.switches:
                    char.ndb.power_pose = pose
                    player.execute_cmd(self.rhs)
                else:
                    prepend_ooc = '[OOC] ' if 'o' in self.switches or 'ooc' in self.switches else ''
                    here.msg_contents('%s{char}%s' % (prepend_ooc, escape_braces(pose)),
                                      from_obj=char, mapping=dict(char=char))
            else:
                if char.location.tags.get('rp', category='flags'):
                    player.execute_cmd('help emote')
                else:
                    player.execute_cmd('help pose')
