import os
import pyglet
import utils
import config
import parameters as param
import messages as msg
import modes as md


res_path = utils.get_res_dir()
if not os.access(res_path, os.F_OK):
    utils.quit_with_error(('Error: the resource folder\n%s') % res_path +
                    (' does not exist or is not readable.  Exiting'), trace=False)

if pyglet.version < '1.1':
    utils.quit_with_error(('Error: pyglet 1.1 or greater is required.\n') +
                    ('You probably have an older version of pyglet installed.\n') +
                    ('Please visit %s') % param.WEB_PYGLET_DOWNLOAD, trace=False)

supportedtypes = {'sounds': ['wav'],
                  'music': ['wav', 'ogg', 'mp3', 'aac', 'mp2', 'ac3', 'm4a'],  # what else?
                  'sprites': ['png', 'jpg', 'bmp']}


def test_avbin():
    try:
        import pyglet
        from pyglet.media import avbin
        if pyglet.version >= '1.2':  # temporary workaround for defect in pyglet svn 2445
            pyglet.media.have_avbin = True

        # On Windows with Data Execution Protection enabled (on by default on Vista),
        # an exception will be raised when use of avbin is attempted:
        #   WindowsError: exception: access violation writing [ADDRESS]
        # The file doesn't need to be in a avbin-specific format,
        # since pyglet will use avbin over riff whenever it's detected.
        # Let's find an audio file and try to load it to see if avbin works.
        opj = os.path.join
        opj = os.path.join

        def look_for_music(path):
            files = [p for p in os.listdir(path) if not p.startswith('.') and not os.path.isdir(opj(path, p))]
            for f in files:
                ext = f.lower()[-3:]
                if ext in ['wav', 'ogg', 'mp3', 'aac', 'mp2', 'ac3', 'm4a'] and not ext in ('wav'):
                    return [opj(path, f)]
            dirs = [opj(path, p) for p in os.listdir(path) if not p.startswith('.') and os.path.isdir(opj(path, p))]
            results = []
            for d in dirs:
                results.extend(look_for_music(d))
                if results: return results
            return results

        music_file = look_for_music(res_path)
        if music_file:
            # The first time we load a file should trigger the exception
            music_file = music_file[0]
            loaded_music = pyglet.media.load(music_file, streaming=False)
            del loaded_music
        else:
            config.cfg.USE_MUSIC = False

    except ImportError:
        config.cfg.USE_MUSIC = False
        if pyglet.version >= '1.2':
            pyglet.media.have_avbin = False
        print ('AVBin not detected. Music disabled.')
        print ('Download AVBin from: http://code.google.com/p/avbin/')

    except:  # WindowsError
        config.cfg.USE_MUSIC = False
        pyglet.media.have_avbin = False
        if hasattr(pyglet.media, '_source_class'):  # pyglet v1.1
            import pyglet.media.riff
            pyglet.media._source_class = pyglet.media.riff.WaveSource
        elif hasattr(pyglet.media, '_source_loader'):  # pyglet v1.2 and development branches
            import pyglet.media.riff
            pyglet.media._source_loader = pyglet.media.RIFFSourceLoader()
        msg.Message("""Warning: Could not load AVbin. Music disabled.

This is usually due to Windows Data Execution Prevention (DEP). Due to a bug in 
AVbin, a library used for decoding sound files, music is not available when \
DEP is enabled. To enable music, disable DEP for Brain Workshop. To simply get \
rid of this message, set USE_MUSIC = False in your config.ini file.

To disable DEP:

1. Open Control Panel -> System
2. Select Advanced System Settings
3. Click on Performance -> Settings
4. Click on the Data Execution Prevention tab
5. Either select the "Turn on DEP for essential Windows programs and services \
only" option, or add an exception for Brain Workshop.

Press any key to continue without music support.
""")


test_avbin()
if pyglet.media.have_avbin:
    supportedtypes['sounds'] = supportedtypes['music']
elif config.cfg.USE_MUSIC:
    supportedtypes['music'] = supportedtypes['sounds']
else:
    del supportedtypes['music']

supportedtypes['misc'] = supportedtypes['sounds'] + supportedtypes['sprites']

resourcepaths = {}
for restype in supportedtypes.keys():
    res_sets = {}
    for folder in os.listdir(os.path.join(res_path, restype)):
        contents = []
        if os.path.isdir(os.path.join(res_path, restype, folder)):
            contents = [os.path.join(res_path, restype, folder, obj)
                        for obj in os.listdir(os.path.join(res_path, restype, folder))
                        if obj[-3:] in supportedtypes[restype]]
            contents.sort()
        if contents: res_sets[folder] = contents
    if res_sets: resourcepaths[restype] = res_sets

sounds = {}
for k in resourcepaths['sounds'].keys():
    sounds[k] = {}
    for f in resourcepaths['sounds'][k]:
        sounds[k][os.path.basename(f).split('.')[0]] = pyglet.media.load(f, streaming=False)

sound = sounds['letters']  # is this obsolete yet?

if config.cfg.USE_APPLAUSE:
    applausesounds = [pyglet.media.load(soundfile, streaming=False)
                      for soundfile in resourcepaths['misc']['applause']]

applauseplayer = pyglet.media.Player()
musicplayer = pyglet.media.Player()


def sound_stop():
    global applauseplayer
    global musicplayer
    musicplayer.volume = 0
    applauseplayer.volume = 0


def fade_out(dt):
    global applauseplayer
    global musicplayer

    if musicplayer.volume > 0:
        if musicplayer.volume <= 0.1:
            musicplayer.volume -= 0.02
        else:
            musicplayer.volume -= 0.1
        if musicplayer.volume <= 0.02:
            musicplayer.volume = 0
    if applauseplayer.volume > 0:
        if applauseplayer.volume <= 0.1:
            applauseplayer.volume -= 0.02
        else:
            applauseplayer.volume -= 0.1
        if applauseplayer.volume <= 0.02:
            applauseplayer.volume = 0

    if (applauseplayer.volume == 0 and musicplayer.volume == 0) or md.mode.trial_number == 3:
        pyglet.clock.unschedule(fade_out)