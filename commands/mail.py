from evennia import default_cmds, CmdSet
from past.builtins import cmp
from django.conf import settings
from evennia.comms.models import ChannelDB, Msg
from evennia.players.models import PlayerDB
from evennia.players import bots
from evennia.comms.channelhandler import CHANNELHANDLER
from evennia.utils import create, utils, evtable
from evennia.utils.utils import make_iter, class_from_module

COMMAND_DEFAULT_CLASS = class_from_module(settings.COMMAND_DEFAULT_CLASS)

# limit symbol import for API
__all__ = ("CmdAddCom", "CmdDelCom", "CmdAllCom",
           "CmdChannels", "CmdCdestroy", "CmdCBoot", "CmdCemit",
           "CmdCWho", "CmdChannelCreate", "CmdClock", "CmdCdesc",
           "CmdPage", "CmdIRC2Chan", "CmdRSS2Chan")
_DEFAULT_WIDTH = settings.CLIENT_DEFAULT_WIDTH


class MailCmdSet(CmdSet):
    key = 'mailbox'

    def at_cmdset_creation(self):
        """Add command to the set - this set will be attached to the mailbox object (item or room)."""
        self.add(CmdMail())


class CmdMail(default_cmds.MuxCommand):
    """
    send a private message to another player
    Usage:
      mail[/switches] [<player>,<player>,... = <message>]
      mail <number>
    Switch:
      last - shows who you last messaged
      list - show your last <number> of tells/pages (default)
    Send a message to target user (if online). If no
    argument is given, you will get a list of your latest messages.
    """

    key = 'mail'
    locks = 'cmd:not pperm(mail_banned) and at_home()'
    help_category = 'Communication'

    # this is used by the COMMAND_DEFAULT_CLASS parent
    player_caller = True

    def func(self):
        """Implement function using the Msg methods"""
        # Since player_caller is set above, this will be a Player.
        char = self.character

        # get the messages we've sent (not to channels)
        sent_messages = Msg.objects.get_messages_by_sender(char, exclude_channel_messages=True)
        # get last messages we've got
        recd_messages = Msg.objects.get_messages_by_receiver(char)

        if 'last' in self.switches:
            if sent_messages:
                recv = ",".join(obj.key for obj in sent_messages[-1].receivers)
                self.msg("You last mailed |c%s|n:%s" % (recv, sent_messages[-1].message))
                return
            else:
                self.msg("You haven't mailed anyone yet.")
                return

        if not self.args or not self.rhs:
            mail = sent_messages + recd_messages
            mail.sort(lambda x, y: cmp(x.date_sent, y.date_sent))

            number = 5
            if self.args:
                try:
                    number = int(self.args)
                except ValueError:
                    self.msg("Usage: mail [<character> = msg]")
                    return

            if len(mail) > number:
                mail_last = mail[-number:]
            else:
                mail_last = mail
            template = "|w%s|n |w%s|n to |w%s|n: %s"
            mail_last = "\n ".join(template %
                                   (utils.datetime_format(mail.date_sent), ",".join(obj.key for obj in mail.senders),
                                    "|n,|w ".join([obj.key for obj in mail.receivers]),
                                    mail.message) for mail in mail_last)

            if mail_last:
                string = "Your latest messages:\n %s" % mail_last
            else:
                string = "You haven't mailed anyone yet."
            self.msg(string)
            return
        # Send mode: Build a list of targets.
        if not self.lhs:
            # If there are no targets, then set the targets to the last person mailed.
            if sent_messages:
                receivers = sent_messages[-1].receivers
            else:
                self.msg("Who do you want to mail?")
                return
        else:
            receivers = self.lhslist
        rec_objs = []
        for receiver in set(receivers):
            if isinstance(receiver, basestring):
                c_obj = char.search(receiver)
            elif hasattr(receiver, 'character'):
                c_obj = receiver
            else:
                self.msg("Who do you want to mail?")
                return
            if c_obj:
                rec_objs.append(c_obj)
        if not rec_objs:
            self.msg("No one found to mail.")
            return

        header = '|mMessage|n from %s%s:|n ' % (char.STYLE, char.key)
        message = self.rhs.strip()

        # if message begins with a :, we assume it is a 'page-pose'
        if message.startswith(':'):
            message = "%s%s|n %s" % (char.STYLE, char.key, message.strip(':'))

        # TODO: persist message only if character is not online currently.
        create.create_message(char, message, receivers=rec_objs)

        # tell the character about the message.
        received = []
        r_strings = []
        for c_obj in rec_objs:
            if not c_obj.access(char, 'tell'):
                r_strings.append("You are not allowed to mail %s." % c_obj)
                continue
            c_obj.msg("%s %s" % (header, message))
            if hasattr(c_obj, 'sessions') and not c_obj.sessions.count():
                received.append("%s%s|n" % (c_obj.STYLE, c_obj.key))
                r_strings.append("%s is offline."
                                 % received[-1])
            else:
                received.append("%s%s|n" % (c_obj.STYLE, c_obj.key))
        if r_strings:
            self.msg("\n".join(r_strings))
        self.msg("You mailed %s: '%s'." % (', '.join(received), message))
