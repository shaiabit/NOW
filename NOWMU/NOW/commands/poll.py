from evennia import CmdSet
from evennia import default_cmds
from evennia.utils.evmenu import get_input


class PollCmdSet(CmdSet):
    key = 'polling'

    def at_cmdset_creation(self):
        """Add command to the set - this set will be attached to the polling object (item or room)."""
        self.add(CmdPoll())
        self.add(CmdSuggest())


class CmdPoll(default_cmds.MuxCommand):
    """
    Poll player or characters with questions.
    Usage:
      poll   (Yet to be determined)
      survey (Yet to be determined)
      vote   (Yet to be determined)
      quiz   (Yet to be determined)
      test   (Yet to be determined)
      trivia (Yet to be determined)
    """
    key = 'poll'
    aliases = ['survey', 'vote', 'quiz', 'test', 'trivia']  # Support different types of question-asking.
    locks = 'cmd:all()'
    arg_regex = r'\s|$'
    player_caller = True

# list_of_polls = [{'name': 'A sample poll', 'questions': [['Do you?', 'yes', 'no', 'maybe'], 'Would you?',  ...
    # ['Can you?', ['yes', 'no', 'sometimes', 'always']]]}]

    def func(self):
        """Poll player or characters with questions."""
        char = self.character
        here = char.location or 'the Void'
        player = self.player
        cmd = self.cmdstring
        where = self.obj

        def look_ready(to):
            """Message/pose to the room: "looks ready to <insert message>. (adds ending period) """
            here.msg_contents("%s looks ready to %s." % (char.get_display_name(player), to))

        if 'poll' in cmd:
            look_ready("take a %s poll" % where.get_display_name(player))
            player.msg("No polls available from %s." % where.get_display_name(player))
        elif 'survey' in cmd:
            look_ready("take a survey on %s" % where.get_display_name(player))
            player.msg("No surveys are available from %s." % where.get_display_name(player))
        elif 'vote' in cmd:
            look_ready("vote with %s" % where.get_display_name(player))
            player.msg("No voting issues are available from %s." % where.get_display_name(player))
        elif 'quiz' in cmd:
            look_ready("take a %s quiz" % where.get_display_name(player))
            player.msg("No quizes are available from %s." % where.get_display_name(player))
        elif 'test' in cmd:
            look_ready("take a %s test" % where.get_display_name(player))
            player.msg("No tests are available from %s." % where.get_display_name(player))
        elif 'trivia' in cmd:
            look_ready("answer %s trivia" % where.get_display_name(player))
            player.msg("No trivia is available from %s." % where.get_display_name(player))
        pass


class CmdSuggest(default_cmds.MuxCommand):
    """
    Poll player or characters with questions.
    Usage:
      suggest [optional topic or brief suggestion (Up to 60 characters)]
          (then prompted for optional long suggestion up to 300 characters)
    """
    key = 'suggest'
    locks = 'cmd:all()'
    arg_regex = r'\s|$'
    player_caller = True

    def func(self):
        """Allow player or character to submit short and/or long suggestions."""
        char = self.character
        here = char.location or 'the Void'
        player = self.player
        args = self.args.strip()
        where = self.obj

        def suggest_callback(caller, prompt, user_input):
            """"Response to input given after suggestion submitted"""
            if len(user_input.strip()) < 1:
                here.msg_contents("%s%s|n discards the full suggestion intended for %s%s|n." %
                                  (char.STYLE, char.key, where.STYLE, where.key))
                player.msg("Long suggestion discarded. Only the topic or short suggestion was given to %s." %
                           where.get_display_name(player))
                return  # Abort the suggestion.
            here.msg_contents("%s%s|n pops a suggestion into %s%s|n." %
                              (char.STYLE, char.key, where.STYLE, where.key))
            # List structure to allow multiple suggestions to be saved. (By player and character name)
            answer = [player.get_display_name(player), char.get_display_name(player), user_input[0:355].strip()]
            if where.db.suggestions:
                suggestions = list(where.db.suggestions)
                where.db.suggestions = suggestions + answer
            else:
                where.db.suggestions = answer

        topic = args[0:80].strip()
        if topic:
            topic_answer = [player.get_display_name(player), char.get_display_name(player), topic]
            if where.db.suggestions:
                suggestions1 = list(where.db.suggestions)
                where.db.suggestions = suggestions1 + topic_answer
            else:
                where.db.suggestions = topic_answer
            msg = '%s%s|n begins writing a suggestion for %s%s|n regarding "|w%s|n".' %\
                  (char.STYLE, char.key, where.STYLE, where.key, topic)
        else:
            msg = "%s%s|n begins writing a suggestion for %s%s|n regarding no specific topic." % \
                  (char.STYLE, char.key, where.STYLE, where.key)
        here.msg_contents(msg)
        get_input(char, "|wSuggestion?|n (Type your suggestion now (300 characters or less),"
                        " and then |g[enter]|n) ", suggest_callback)
