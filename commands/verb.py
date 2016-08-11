# -*- coding: UTF-8 -*-
from commands.command import MuxCommand


class CmdTry(MuxCommand):
    """
    Verbs you can do as your character.
    Usage:
      try <verb> [noun]
    """
    key = 'try'
    # aliases = verb_list()  # Scan room for things that can be tried.
    locks = 'cmd:all()'

    def func(self):
        """Run the say command"""
        if self.args:
            pass
        else:
            self.player.msg('Verbs to try: |g%r|n.' % '|w, |g'.join(self.verb_list()))

    def verb_list(self):
        collection = []
        for obj in [self.character.location] + self.character.location.contents + self.character.contents:
            verbs = obj.locks
            for verb in ("%s" % verbs).split(';'):
                element = verb.split(':')[0]
                name = element[2:] if element[:2] == 'v-' else element
                if obj.access(self.character, element):  # obj lock checked against character
                    collection.append(name)
        return list(set(collection))
