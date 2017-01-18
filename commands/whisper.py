# -*- coding: UTF-8 -*-
from commands.command import MuxCommand


class CmdWhisper(MuxCommand):
    """
    Whisper to a nearby character.
    Usage:
      whisper [character, or characters = ]<message>
    Options:
    /o or /ooc  - Out-of-character whispering.
    """
    key = 'whisper'
    aliases = ['wh', '""', "''", 'say to']
    locks = 'cmd:all()'

    def func(self):
        """Run the whisper command"""
        char = self.character
        who = self.lhs.strip()
        message = self.rhs.strip() if self.rhs else ''
        last = self.character.ndb.last_whispered
        all_present = [each.key for each in self.character.location.contents]
        result, new_last = self.whisper(who, message, last, all_present)
        char.msg(result)
        char.ndb.last_whispered = new_last

    @staticmethod
    def whisper(who, message, last, all_present):
        """
        Whisper to one or more nearby targets.
        Syntax:
               whisper A, B, C = text of whisper
          where:
          self is me, the object that will whisper.
          who is a comma-delimited string of text from the left-hand
               side of the = sign, of who should receive this whisper.
               If left empty, the last whisperers list is used.
          message is the text from the right-hand side of the = sign,
               the message to be whispered.
          last is a list of who last received a whisper from me,
                used when who is empty.
          all_present is a list of which objects are near you, in range.
        """

        def is_present(object):  # Test if object is present in room
            return True if object in all_present else False

        def is_awake(object):  # To be altered after testing phase.
            return True  # if object  == 'A' else False  # Simulates character A being awake.

        def convert_who_list(who_string):
            """
            This converts a comma-delimited string, returning
            a list with duplicates and whitespace removed.
            """
            converted_who = [each_who.strip() for each_who in who_string.split(',')]
            return list(set(converted_who))

        who_present, who_success, failed_whisper = [], [], []
        whisper_list = convert_who_list(who if who else last)
        whisper_success = False
        for each in whisper_list:
            if is_present(each):
                who_present.append(each)
            else:
                failed_whisper.append(each + " (not in room)")
        for each in who_present:
            if is_awake(each):
                who_success.append(each)
                whisper_success = True
            else:
                failed_whisper.append(each + " (not awake)")
        if whisper_success:
            result_message = 'You whispered ' + message + ' to ' + ', '.join(who_success) + '.'
        else:
            result_message = 'The names provided were unable to be whispered to.'
        if len(failed_whisper) > 0:
            result_message += '\n  You failed to whisper to ' + ', '.join(failed_whisper) + '.'
        return result_message, who_success  # String displayed to self showing whisper results.
