# This is a test of showing more easily-understood lock permissions rather than
# Evennia's internally used lock permissions, found in:
# NOW\old-evennia\evennia\locks\lockfuncs.py

# +---------+-----------+-----------+----------------------------+-------------+
# | sub     | channel   | my        | locks                      | description |
# |         |           | aliases   |                            |             |
# +~~~~~~~~~+~~~~~~~~~~~+~~~~~~~~~~~+~~~~~~~~~~~~~~~~~~~~~~~~~~~~+~~~~~~~~~~~~~+
# | Yes     | Public(pu |           | control:perm(Wizards);list | Public      |
# |         | b)        |           | en:all();send:all()        | discussion  |
# |         |           |           | control:id(2);listen:perm_ |             |
# | Yes     | dev       |           | above(Guests);send:perm_ab | Development |
# |         |           |           | ove(Guests)                |  chat       |
# +---------+-----------+-----------+----------------------------+-------------+

# Amber yaps. I would put locks in with "sub" and make a control/joined/listen/send?
# Yes/No section.

# Rulan: not sure what she means by that; this is a guess:
#        Just throwing out ideas; nothing is set in stone
# Tria:  Six letters might work if you want to use words or optionally you could
#        use a key at the bottom and just use CJLS

# +----------+-------------+---------+----------------------+
# | Channel  | Description | Aliases | Joined Control Send  |
# +~~~~~~~~~~+~~~~~~~~~~~~~+~~~~~~~~~+~~~~~~~~~~~~~~~~~~~~~~+
# | Public   | Public      |         | Yes    Yes      Yes  |
# | (pub)    | discussion  |         |                      |
# +~~~~~~~~~~+~~~~~~~~~~~~~+~~~~~~~~~+~~~~~~~~~~~~~~~~~~~~~~+ # add this separator
# | dev      | Development |         | Yes    No       No   |
# |          |  chat       |         |                      |
# +----------+-------------+---------+----------------------+

# Rulan: looks pretty reasonable although "joined" is duplicated
# Amber: Use green Unicode check mark or red X if terminal supports it; otherwise
#           green Yes/red No
# Amber: I ordered the table as Channel, description, aliases and then the 3 bools:
#         Control joined send

import sys
import re

# from http://stackoverflow.com/questions/12595051/python-check-if-string-matches-pattern

regex = '([A-Z|a-z]\d+)+'
prog = re.compile(regex)

while True:
    print
    print 'Type something to match "%s" against.' % regex
    print '"q" exits this program.'
    line = sys.stdin.readline()
# fixed: trim off trailing \n from raw input:
    line = line.rstrip("\n")
    if line == "q":
        print "Quitting."
        break
    if prog.match(line):
        print '"%s" matched' % line
    else:
        print '"%s" did not match' % line

# I'm not sure why the same code as above doesn't work here:

lock_names = "control:perm(Wizards);listen:all();send:all();blah"

num = 0

for lock in lock_names.split(";"):
    num += 1
    print "#%d: %s" % (num, lock),
    if re.match(lock, "listen:all\(\)", 1):  # is "listen:all()" found within the lock?
        print "Listen"  # yes
    elif re.match(lock, "send:all\(\)", 1):  # is "send:all()" found within the lock?
        print "Send"    # yes
    else:
        print "Neither"
