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
    /do or do, rp, doing  (Pose and set room-pose/doing message.)
      Additional options for do, rp, doing command version of pose:
      /reset   (Reset the current room pose to use default setting)
      /default (Set the default room pose for all rooms, all times)
      /quiet or silent (Update doing, but do not pose) 
    
    Example:
      > pose is standing by the tree, smiling.
      Rulan is standing by the tree, smiling.
    """
    # > ppose strains to lift the anvil. = get anvil
    # > Werewolf strains to lift the anvil.
    # ==> Werewolf takes the anvil.
    # (optional success message if anvil can be lifted.)
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
                has_pose = char.db.messages and char.db.messages.get('pose')
                if has_pose:
                    char.msg("Current pose reads: '%s'" % char.get_display_name(char, pose=True))
                    default_pose = target.db.messages and target.db.messages.get('pose_default') or None
                    if default_pose:
                        char.msg('Default pose is \'%s%s\'' % (char.get_display_name(char), default_pose))
                    else:
                        char.msg('Default pose not set.')
                else:
                    char.msg('No pose has been set.|/Usage: rp <pose-text> OR pose obj = <pose-text>')
                return
            if target and '=' in self.args:  # affect something else other than self.
                target = char.search(target)
                if not target:
                    return
                if not target.access(char, 'edit'):
                    char.msg('You have no permission to edit %s.' % target.get_display_name(char))
                    return
                pass  # TODO: Apply setting to target.
            else:
                target = char
            if not char.db.messages:
                char.db.messages = {}
            char.db.messages['pose'] = pose
            char.db.messages['pose_default'] = '|_is here.'  # set Default if so
            target_name = target.sdesc.get() if hasattr(target, '_sdesc') else target.key
            # reset the pose to default
            if 'reset' in opt:
                pose = target.db.messages and target.db.messages.get('pose_default', '')
                if not target.db.messages:
                    target.db.messages = {}
                target.db.messages['pose'] = pose
            elif 'default' in opt:
                if not target.db.messages:
                    target.db.messages = {}
                target.db.messages['pose_default'] = pose
                char.msg("Default pose is now: '%s%s'" % (char.get_display_name(char), pose))
                return
            else:
                if len(target_name) + len(pose) > 60:
                    char.msg('Your pose is too long.')
                    return
                if not target.db.messages:
                    target.db.messages = {}
                target.db.messages['pose'] = pose
                if self.args and not ('silent' in opt or 'quiet' in opt):
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
                    ooc = 'o' in self.switches or 'ooc' in self.switches
                    prepend_ooc = '[OOC] ' if ooc else ''
                    here.msg_contents(('%s{char}%s' % (prepend_ooc, escape_braces(pose)),
                                       {'type': 'pose', 'ooc': ooc}),
                                      from_obj=char, mapping=dict(char=char))
            else:
                if char.location.tags.get('rp', category='flags'):
                    player.execute_cmd('help emote')
                else:
                    player.execute_cmd('help pose')
