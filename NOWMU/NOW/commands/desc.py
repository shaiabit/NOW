from evennia import default_cmds
# from evennia.utils.evmenu import get_input # Might not be needed.
from evennia.utils.eveditor import EvEditor

def _desc_load(caller):
    return caller.db.evmenu_target.db.desc or ''

def _desc_save(caller, buf):
    """
    Save line buffer to the desc prop. This should
    return True if successful and also report its status to the user.
    """
    caller.db.evmenu_target.db.desc = buf
    caller.msg('Saved.')
    return True

def _desc_quit(caller):
    caller.attributes.remove('evmenu_target')
    caller.msg("Exited editor.")

class CmdDesc(default_cmds.MuxCommand):
    """
    Describe yourself!
    Usage:
      desc [description]
    Switches:
    /edit  - Use a line-based editor similar to vi for more advanced editing.
    /brief - Add a brief description, 65 characters or less.

    Add a description to your character, visible to characters who look at you.
    """
    key = 'desc'
    locks = 'cmd:all()'
    arg_regex = r'^/|\s|$'

    def edit_handler(self):
        if self.args:
            self.msg("|yYou may specify a description, or use the edit switch, "
                     "but not both.|n")
            return
        else:
            obj = self.caller

        def load(obj):
            return obj.db.evmenu_target.db.desc or ''

        def save(obj, buf):
            """
            Save line buffer to the desc prop. This should return True
            if successful and also report its status to the user.
            """
            obj.db.evmenu_target.db.desc = buf
            obj.msg('Saved.')
            return True

        def quit(obj):
            obj.attributes.remove('evmenu_target')
            obj.msg('Exited editor.')

        self.caller.db.evmenu_target = obj  # launch the editor
        EvEditor(obj, loadfunc=load, savefunc=save, quitfunc=quit, key='desc', persistent=True)
        return

    def func(self):
        """Add the description."""
        if 'edit' in self.switches:
            self.edit_handler()
            return
        if not self.args:
            if 'brief' in self.switches:
                self.caller.msg("You must supply a brief description (65 characters or less) to describe yourself.")
                return

            def desc_callback(caller, prompt, user_input):
                """"Response to input given after description is set"""
                msg = "%s's appearance begins to change." % self.full_name(caller.sessions)
                caller.location.msg_contents(msg)
                caller.db.desc = user_input.strip()

            get_input(caller, "Type your description now, and then |g[enter]|n: ", desc_callback)
            return
        if 'brief' in self.switches:
            self.caller.db.desc_brief = self.args[0:65].strip()
            self.caller.msg("Your brief description has been saved: %s" % self.caller.db.desc_brief)
            return
        self.caller.db.desc = self.args.strip()
        self.caller.msg('You successfully set your description.')
