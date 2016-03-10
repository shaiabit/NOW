# Welcome to Novel Online World!

This directory is the directory that contains all NOW assets,
set up to mirror the operating NOW server.

If you are cloning NOW, tou can delete this readme file, or just
re-arrange things in this game-directory to suit your own sense of
organisation (the only exception is the directory structure of the
server/ directory, which Evennia expects). If you change the structure
you must however also edit/add to your settings file to tell Evennia
where to look for things.

Your game's main configuration file is found in
`server/conf/settings.py` (but you don't need to change it to get
started). If you just created this directory, `cd` to this directory
then initialize a new database using

    evennia migrate

To start the server, `cd` to this directory and run

    evennia -i start

This will start the server so that it logs output to the console. Make
sure to create a superuser when asked. By default you can now connect
to your new game using a MUD client on localhost:4000.  You can also
log into the web client by pointing a browser to
http://localhost:8000.

# Getting started

It's highly recommended that you look up Evennia's extensive
documentation found here: https://github.com/evennia/evennia/wiki.

Plenty of beginner's tutorials can be found here:
http://github.com/evennia/evennia/wiki/Tutorials.

After installed, to start it, log in then:

    source pyenv/bin/activate
    cd NOW
    evennia start

You will see console output, but can disconnect with Control-D or exit
evennia stays running in daemon mode.
