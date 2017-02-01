# -*- coding: UTF-8 -*-
from commands.command import MuxCommand


class CmdWhisper(MuxCommand):
    """
    Whisper to one or more nearby targets.
    Syntax:
      whisper [target name, or names =[=] ][message]
    Usage:
       whisper A, B, C = text of message
    1) whisper text of message
    2) whisper A, B, C =
    3) whisper ==
    4) whisper =
    5) whisper
    *1 Omitting the target(s) and equal sign will whisper
       to the last whispered if message text is given.
    *2 Supplying target(s), an equal sign, but no message
      will set the target(s) for future whispers.
    *3 Supplying two equal signs without target(s) or
       message will set your next whisper to reply to
       the last whispered group.
    *4 Supplying only an equal sign without target(s) or
       message text will set your next whisper to the one
       who last whispered to you.
    *5 If no parameters are given, whisper will display
       the names of those whom you last whispered.
    * In some environments, message degradation may occur,
      similar to a mumble with only partial readability.
    Planned Options:
    /o or /ooc  - Out-of-character whispering.
    /t or /tel  - Telepathic whispering, if you and your
                  target(s) have enough combined telepathy.
    """
    key = 'whisper'
    aliases = ['wh', '""', "''", 'say to']
    locks = 'cmd:all()'

    def func(self):
        """Run the whisper command"""
        char = self.character
        who = self.lhs.strip()
        opt = self.switches
        message = self.args.strip() if not self.rhs else self.rhs.strip()  # If no equals sign, use args for message
        last = self.character.ndb.last_whispered or []
        all_present = [each.key for each in self.character.location.contents] +\
                      [each.key for each in self.character.contents]
        result, new_last = self.whisper(who, message, last, all_present)
        for each in new_last:
            target = char.search(each, quiet=True)
            if target and len(target) == 1:
                target[0].private(char, 'whisper', message)
        char.msg(result)
        char.ndb.last_whispered = new_last
        if 'ver' in opt:
            char.msg('Whisper version 14, Tuesday 31 Jan 2017')

    @staticmethod
    def whisper(who, message, last, all_present):
        """
        Whisper to one or more nearby targets.
        Syntax:
               whisper A, B, C = text of whisper
               <command> <who> =[=] <message> (last, all_present)
          where:
          who is a comma-delimited string of text from the left-hand
               side of the = sign, of who should receive this whisper.
               If left empty, the last whisperers list is used.
          message is the text from the right-hand side of the = sign,
               the message to be whispered.
          last is a comma-delimited string (like who) of who last
               received a whisper from me, used when who is empty.
          all_present is a list of which objects are near you, in range.
        """

        # is_present, is_awake, is_unlocked, is_available.

        def is_available(object):  # Test if object is present in room
            return True

        def is_unlocked(object):  # Test if object is present in room
            return True

        def is_present(object):  # Test if object is present in room
            return True if object in all_present else False

        def is_awake(object):  # To be altered after testing phase.
            return True  # Tests if character is awake.

        def convert_who_list(who_string):
            """
            This converts a comma-delimited string, returning
            a list with duplicates and whitespace removed.
            """
            return list(set([each_who.strip() for each_who in who_string.split(',')]))

        who_present, who_success, failed_whisper = [], [], []
        whisper_list = convert_who_list(who) if who else last
        whisper_success = False

        for each in whisper_list:
            if is_available(each):
                if is_unlocked(each):
                    if is_present(each):
                        if is_awake(each):
                            who_success.append(each)
                            whisper_success = True
                        else:
                            who_success.append(each)
                            whisper_success = True
                            failed_whisper.append(each + " (is asleep)")
                    else:
                        failed_whisper.append(each + " (is not present)")
                else:
                    failed_whisper.append(each + " (is uninterested)")
            else:
                failed_whisper.append(each + " (is not available/unreachable)")

        if whisper_success:
            result_message = 'You whispered "' + message + '" to ' + ', '.join(who_success) + '.'
        else:
            result_message = 'The names provided were unable to be whispered to.'
        if len(failed_whisper) > 0:
            result_message += '\n  Your whisper was not heard by ' + ', '.join(failed_whisper) + '.'
        return result_message, who_success  # String displayed to self showing whisper results.
