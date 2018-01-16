import os, sys, traceback

#__all__ = ["get_settings_path", "get_data_dir", "FOLDER_DATA"]

FOLDER_DATA = 'data'


def get_settings_path(name):
    '''Get a directory to save user preferences.
    Copied from pyglet.resource so we don't have to load that module
    (which recursively indexes . on loading -- wtf?).'''
    if sys.platform in ('cygwin', 'win32'):
        if 'APPDATA' in os.environ:
            return os.path.join(os.environ['APPDATA'], name)
        else:
            return os.path.expanduser('~/%s' % name)
    elif sys.platform == 'darwin':
        return os.path.expanduser('~/Library/Application Support/%s' % name)
    else: # on *nix, we want it to be lowercase and without spaces (~/.brainworkshop/data)
        return os.path.expanduser('~/.%s' % (name.lower().replace(' ', '')))


def get_data_dir():
    try:
        return sys.argv[sys.argv.index('--datadir') + 1]
    except:
        return os.path.join(get_settings_path('Brain Workshop'), FOLDER_DATA)


def quit_with_error(message='', postmessage='', quit=True, trace=True):
    if message:     print >> sys.stderr, message + '\n'
    if trace:
        print >> sys.stderr, _("Full text of error:\n")
        traceback.print_exc()
    if postmessage: print >> sys.stderr, '\n\n' + postmessage
    if quit:        sys.exit(1)
