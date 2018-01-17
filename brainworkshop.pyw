#!/usr/bin/env python
# ------------------------------------------------------------------------------
# Brain Workshop: a Dual N-Back game in Python
#
# Tutorial, installation instructions & links to the dual n-back community
# are available at the Brain Workshop web site:
#
#       http://brainworkshop.net/
#
# Also see Readme.txt.
#
# Copyright (C) 2009-2011: Paul Hoskinson (plhosk@gmail.com) 
#
# The code is GPL licensed (http://www.gnu.org/copyleft/gpl.html)
# ------------------------------------------------------------------------------

import random, os, sys, socket, urllib2, webbrowser, time, math, traceback, datetime
import cPickle as pickle
from decimal import Decimal
from time import strftime
from datetime import date
import config
import parameters as param
from utils import *
from mode import *
from graphics import *

import gettext
gettext.install('messages', localedir='res/i18n', unicode=True)


def edit_config_ini():
    if sys.platform == 'win32':
        cmd = 'notepad'
    elif sys.platform == 'darwin':
        cmd = 'open'
    else:
        cmd = 'xdg-open'
    print (cmd + ' "' + os.path.join(get_data_dir(), param.CONFIGFILE) + '"')
    window.on_close()
    import subprocess
    subprocess.call((cmd + ' "' + os.path.join(get_data_dir(), param.CONFIGFILE) + '"'), shell=True)
    sys.exit(0)


def quit_with_error(message='', postmessage='', quit=True, trace=True):
    if message:     print >> sys.stderr, message + '\n'
    if trace:       
        print >> sys.stderr, ("Full text of error:\n")
        traceback.print_exc()
    if postmessage: print >> sys.stderr, '\n\n' + postmessage
    if quit:        sys.exit(1)


def dump_pyglet_info():
    from pyglet import info
    sys.stdout = open(os.path.join(get_data_dir(), 'dump.txt'), 'w')
    info.dump()
    sys.stdout.close()
    sys.exit()
    
# parse config file & command line options
if '--debug' in sys.argv:
    param.DEBUG = True
if '--vsync' in sys.argv or sys.platform == 'darwin':
    param.VSYNC = True
if '--dump' in sys.argv:
    dump_pyglet_info()
try: param.CONFIGFILE = sys.argv[sys.argv.index('--configfile') + 1]
except: pass

messagequeue = [] # add messages generated during loading here
class Message:
    def __init__(self, msg):
        if not 'window' in globals():
            print msg                # dump it to console just in case
            messagequeue.append(msg) # but we'll display this later
            return
        self.batch = pyglet.graphics.Batch()
        self.label = pyglet.text.Label(msg, 
                            font_name='Times New Roman',
                            color=config.cfg.COLOR_TEXT,
                            batch=self.batch,
                            multiline=True,
                            width=(4*window.width)/5,
                            font_size=14,
                            x=window.width//2, y=window.height//2,
                            anchor_x='center', anchor_y='center')
        window.push_handlers(self.on_key_press, self.on_draw)
        self.on_draw()

    def on_key_press(self, sym, mod):
        if sym:
            self.close()
        return pyglet.event.EVENT_HANDLED
            
    def close(self):
        return window.remove_handlers(self.on_key_press, self.on_draw)    
    
    def on_draw(self):
        window.clear()
        self.batch.draw()
        return pyglet.event.EVENT_HANDLED
 
def check_and_move_user_data():
    if not '--datadir' in sys.argv and \
      (not os.path.exists(get_data_dir()) or len(os.listdir(get_data_dir())) < 1):
        import shutil
        shutil.copytree(get_old_data_dir(), get_data_dir())
        if len(os.listdir(get_old_data_dir())) > 2:
            Message(
"""Starting with version 4.8.2, Brain Workshop stores its user profiles \
(statistics and configuration data) in "%s", rather than the old location, "%s". \
Your configuration data has been copied to the new location. The files in the \
old location have not been deleted. If you want to edit your config.ini, \
make sure you look in "%s".

Press space to continue.""" % (get_data_dir(),  get_old_data_dir(),  get_data_dir()))

def load_last_user(lastuserpath):
    if os.path.isfile(os.path.join(get_data_dir(), lastuserpath)):
        f = file(os.path.join(get_data_dir(), lastuserpath), 'r')
        p = pickle.Unpickler(f)
        options = p.load()
        del p
        f.close()
        if not options['USER'].lower() == 'default':
            param.USER = options['USER']
            param.CONFIGFILE = param.USER + '-config.ini'
            param.STATS_BINARY = param.USER + '-logfile.dat'

def save_last_user(lastuserpath):
    try:
        f = file(os.path.join(get_data_dir(), lastuserpath), 'w')
        p = pickle.Pickler(f)
        p.dump({'USER': param.USER})
        # also do date of last session?
    except:
        pass

check_and_move_user_data()
load_last_user('defaults.ini')


# this function checks if a new update for Brain Workshop is available.
update_available = False
update_version = 0
def update_check():
    global update_available
    global update_version
    socket.setdefaulttimeout(param.TIMEOUT_SILENT)
    req = urllib2.Request(param.WEB_VERSION_CHECK)
    try:
        response = urllib2.urlopen(req)
        version = response.readline().strip()
    except:
        return
    if version > param.VERSION: # simply comparing strings works just fine
        update_available = True
        update_version = version

if config.cfg.VERSION_CHECK_ON_STARTUP and not param.CLINICAL_MODE:
    update_check()
try:
    # workaround for pyglet.gl.ContextException error on certain video cards.
    os.environ["PYGLET_SHADOW_WINDOW"]="0"
    # import pyglet
    import pyglet
    from pyglet.gl import *
    if param.NOVBO: pyglet.options['graphics_vbo'] = False
    from pyglet.window import key
except:
    quit_with_error(('Error: unable to load pyglet.  If you already installed pyglet, please ensure ctypes is installed.  Please visit %s') % param.WEB_PYGLET_DOWNLOAD)
try:
    pyglet.options['audio'] = ('directsound', 'openal', 'alsa', )
    # use in pyglet 1.2: pyglet.options['audio'] = ('directsound', 'pulse', 'openal', )
    import pyglet.media
except:
    quit_with_error(('No suitable audio driver could be loaded.'))
        
# Initialize resources (sounds and images)
#
# --- BEGIN RESOURCE INITIALIZATION SECTION ----------------------------------
#

res_path = get_res_dir()
if not os.access(res_path, os.F_OK):
    quit_with_error(('Error: the resource folder\n%s') % res_path +
                    (' does not exist or is not readable.  Exiting'), trace=False)

if pyglet.version < '1.1':
    quit_with_error(('Error: pyglet 1.1 or greater is required.\n') +
                    ('You probably have an older version of pyglet installed.\n') +
                    ('Please visit %s') % param.WEB_PYGLET_DOWNLOAD, trace=False)

supportedtypes = {'sounds' :['wav'],
                  'music'  :['wav', 'ogg', 'mp3', 'aac', 'mp2', 'ac3', 'm4a'], # what else?
                  'sprites':['png', 'jpg', 'bmp']}

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
            dirs  = [opj(path, p) for p in os.listdir(path) if not p.startswith('.') and os.path.isdir(opj(path, p))]
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

    except: # WindowsError
        config.cfg.USE_MUSIC = False
        pyglet.media.have_avbin = False 
        if hasattr(pyglet.media, '_source_class'): # pyglet v1.1
            import pyglet.media.riff
            pyglet.media._source_class = pyglet.media.riff.WaveSource
        elif hasattr(pyglet.media, '_source_loader'): # pyglet v1.2 and development branches
            import pyglet.media.riff
            pyglet.media._source_loader = pyglet.media.RIFFSourceLoader()
        Message("""Warning: Could not load AVbin. Music disabled.

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
if pyglet.media.have_avbin: supportedtypes['sounds'] = supportedtypes['music']
elif config.cfg.USE_MUSIC:         supportedtypes['music'] = supportedtypes['sounds']
else:                       del supportedtypes['music']

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

sound = sounds['letters'] # is this obsolete yet?
    
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
        else: musicplayer.volume -= 0.1
        if musicplayer.volume <= 0.02:
            musicplayer.volume = 0
    if applauseplayer.volume > 0:
        if applauseplayer.volume <= 0.1:
            applauseplayer.volume -= 0.02
        else: applauseplayer.volume -= 0.1
        if applauseplayer.volume <= 0.02:
            applauseplayer.volume = 0

    if (applauseplayer.volume == 0 and musicplayer.volume == 0) or mode.trial_number == 3:
        pyglet.clock.unschedule(fade_out)
        
        
#
# --- END RESOURCE INITIALIZATION SECTION ----------------------------------
#
    
    
# The colors of the squares in Triple N-Back mode are defined here.
# Color 1 is used in Dual N-Back mode.
def get_color(color):
    if color in (4, 7) and config.cfg.BLACK_BACKGROUND:
        return config.cfg['COLOR_%i_BLK' % color]
    return config.cfg['COLOR_%i' % color]


#Create the game window
caption = []
if param.CLINICAL_MODE:
    caption.append('BW-Clinical ')
else:
    caption.append('Brain Workshop by AzZu ')
caption.append(param.VERSION)
if param.USER != 'default':
    caption.append(' - ')
    caption.append(param.USER)
if config.cfg.WINDOW_FULLSCREEN:
    style = pyglet.window.Window.WINDOW_STYLE_BORDERLESS
else:
    style = pyglet.window.Window.WINDOW_STYLE_DEFAULT


class MyWindow(pyglet.window.Window):
    def on_key_press(self, symbol, modifiers):
        pass
    def on_key_release(self, symbol, modifiers):
        pass

window = MyWindow(config.cfg.WINDOW_WIDTH, config.cfg.WINDOW_HEIGHT, caption=''.join(caption), style=style, vsync=param.VSYNC)
#if DEBUG: 
#    window.push_handlers(pyglet.window.event.WindowEventLogger())
if sys.platform == 'darwin' and config.cfg.WINDOW_FULLSCREEN:
    window.set_exclusive_keyboard()
if sys.platform == 'linux2':
    window.set_icon(pyglet.image.load(resourcepaths['misc']['brain'][0]))

# set the background color of the window
if config.cfg.BLACK_BACKGROUND:
    glClearColor(0, 0, 0, 1)
else:
    glClearColor(1, 1, 1, 1)
if config.cfg.WINDOW_FULLSCREEN:
    window.maximize()
    window.set_mouse_visible(False)
    

# What follows are the classes which control all the text and graphics.
#
# --- BEGIN GRAPHICS SECTION ----------------------------------------------
#

class TextInputScreen:
    titlesize = 18
    textsize = 16
    
    def __init__(self, title='', text='', callback=None, catch=''):
        self.titletext = title
        self.text = text
        self.starttext = text
        self.bgcolor = (255 * int(not config.cfg.BLACK_BACKGROUND), )*3
        self.textcolor = (255 * int(config.cfg.BLACK_BACKGROUND), )*3 + (255, )
        self.batch = pyglet.graphics.Batch()
        self.title = pyglet.text.Label(title, font_size=self.titlesize,
            bold=True, color=self.textcolor, batch=self.batch,
            x=window.width/2, y=(window.height*9)/10,
            anchor_x='center', anchor_y='center')
        self.document = pyglet.text.document.UnformattedDocument()
        self.document.set_style(0, len(self.document.text), {'color': self.textcolor})
        self.layout = pyglet.text.layout.IncrementalTextLayout(self.document,
            (window.width/2 - 20 - len(title)*6), (window.height*10)/11, batch=self.batch)
        self.layout.x = (window.width)/2 + 15 + len(title)*6
        if not callback: callback = lambda x: x
        self.callback = callback
        self.caret = pyglet.text.caret.Caret(self.layout)
        window.push_handlers(self.caret)
        window.push_handlers(self.on_key_press, self.on_draw)
        self.document.text = text
        # workaround for a bug:  the keypress that spawns TextInputScreen doesn't
        # get handled until after the caret handler has been pushed, which seems
        # to result in the keypress being interpreted as a text input, so we 
        # catch that later
        self.catch = catch
    
    def on_draw(self):
        # the bugfix hack, which currently does not work
        if self.catch and self.document.text == self.catch + self.starttext: 
            self.document.text = self.starttext 
            self.catch = ''
            self.caret.select_paragraph(600,0)

        window.clear()
        self.batch.draw()
        return pyglet.event.EVENT_HANDLED
    
    def on_key_press(self, k, mod):
        if k in (key.ESCAPE, key.RETURN, key.ENTER):
            if k is key.ESCAPE:
                self.text = self.starttext
            else:
                self.text = self.document.text
            window.pop_handlers()
            window.pop_handlers()
        self.callback(self.text.strip())
        return pyglet.event.EVENT_HANDLED
      

class Cycler:
    def __init__(self, values, default=0):
        self.values = values
        if type(default) is not int or default > len(values):
            default = values.index(default)
        self.i = default
    def choose(self, val):
        if val in self.values:
            self.i = self.values.index(val)
    def nxt(self): # not named "next" to prevent using a Cycler as an iterator, which would hang
        self.i = (self.i + 1) % len(self.values)
        return self.value()
    def value(self):
        return self.values[self.i]
    def __str__(self):
        return str(self.value())
    
class PercentCycler(Cycler):
    def __str__(self):
        v = self.value()
        if type(v) == float and (v < .1 or v > .9) and not v in (0., 1.):
            return "%2.2f%%" % (v*100.)
        else:
            return "%2.1f%%"   % (v*100.)

class Menu:
    """
    Menu.__init__(self, options, values={}, actions={}, names={}, title='',  choose_once=False, 
                  default=0):
        
    A generic menu class.  The argument options is edited in-place.  Instancing
    the Menu displays the menu.  Menu will install its own event handlers for
    on_key_press, on_text, on_text_motion and on_draw, all of which 
    do not pass events to later handlers on the stack.  When the user presses 
    esc,  Menu pops its handlers off the stack. If the argument actions is used,
    it should be a dict with keys being options with specific actions, and values
    being a python callable which returns the new value for that option.
    
    """
    titlesize = 18
    choicesize = 12
    footnotesize = 10
    fontlist = ['Courier New', # try fixed width fonts first
                'Monospace', 'Terminal', 'fixed', 'Fixed', 'Times New Roman', 
                'Helvetica', 'Arial']
            
    
    def __init__(self, options, values=None, actions={}, names={}, title='', 
                 footnote = ('Esc: cancel     Space: modify option     Enter: apply'),
                 choose_once=False, default=0):
        self.bgcolor = (255 * int(not config.cfg.BLACK_BACKGROUND), )*3
        self.textcolor = (255 * int(config.cfg.BLACK_BACKGROUND), )*3 + (255,)
        self.markercolors = (0,0,255,0,255,0,255,0,0)#(255 * int(config.cfg.BLACK_BACKGROUND), )*3*3
        self.pagesize = min(len(options), (window.height*6/10) / (self.choicesize*3/2))
        if type(options) == dict:
            vals = options
            self.options = options.keys()
        else:
            vals = dict([[op, None] for op in options])
            self.options = options
        self.values = values or vals # use values if there's anything in it
        self.actions = actions
        for op in self.options:
            if not op in names.keys():
                names[op] = op
        self.names = names
        self.choose_once = choose_once
        self.disppos = 0 # which item in options is the first on the screen                          
        self.selpos = default # may be offscreen?
        self.batch = pyglet.graphics.Batch()
        self.title = pyglet.text.Label(title, font_size=self.titlesize,
            bold=True, color=self.textcolor, batch=self.batch,
            x=window.width/2, y=(window.height*9)/10,
            anchor_x='center', anchor_y='center')
        self.footnote = pyglet.text.Label(footnote, font_size=self.footnotesize,
            bold=True, color=self.textcolor, batch=self.batch,
            x=window.width/2, y=(window.height*2)/10,
            anchor_x='center', anchor_y='center')
        
        self.labels = [pyglet.text.Label('', font_size=self.choicesize,
            bold=True, color=self.textcolor, batch=self.batch,
            x=window.width/8, y=(window.height*8)/10 - i*(self.choicesize*3/2),
            anchor_x='left', anchor_y='center', font_name=self.fontlist) 
                       for i in range(self.pagesize)]
        
        self.marker = self.batch.add(3, GL_POLYGON, None, ('v2i', (0,)*6,),
            ('c3B', self.markercolors))
            
        self.update_labels()

        window.push_handlers(self.on_key_press, self.on_text, 
                             self.on_text_motion, self.on_draw)
        
    def textify(self, x):
        if type(x) == bool:
            return x and ('Yes') or ('No')
        return str(x)

    def update_labels(self):
        for l in self.labels: l.text = 'Hello, bug!'
        
        markerpos = self.selpos - self.disppos                
        i = 0
        di = self.disppos
        if not di == 0: # displacement of i
            self.labels[i].text = '...'
            i += 1
        ending = int(di + self.pagesize < len(self.options))
        while i < self.pagesize-ending and i+self.disppos < len(self.options):
            k = self.options[i+di]
            if k == 'Blank line':
                self.labels[i].text = ''
            elif k in self.values.keys() and not self.values[k] == None: 
                v = self.values[k]
                self.labels[i].text = '%s:%7s' % (self.names[k].ljust(52), self.textify(v))
            else:
                self.labels[i].text = self.names[k]
            i += 1
        if ending:
            self.labels[i].text = '...'
        w, h, cs = window.width, window.height, self.choicesize
        self.marker.vertices = [w/10, (h*8)/10 - markerpos*(cs*3/2) + cs/2,
                                w/9,  (h*8)/10 - markerpos*(cs*3/2),
                                w/10, (h*8)/10 - markerpos*(cs*3/2) - cs/2]
        
    def move_selection(self, steps, relative=True):
        # FIXME:  pageup/pagedown can occasionally cause "Hello bug!" to be displayed
        if relative:
            self.selpos += steps
        else:
            self.selpos = steps
        self.selpos = min(len(self.options)-1, max(0, self.selpos))
        if self.disppos >= self.selpos and not self.disppos == 0:
            self.disppos = max(0, self.selpos-1)
        if self.disppos <= self.selpos - self.pagesize +1\
          and not self.disppos == len(self.options) - self.pagesize:
            self.disppos = max(0, min(len(self.options), self.selpos+1) - self.pagesize + 1)
            
        if not self.selpos in (0, len(self.options)-1) and self.options[self.selpos] == 'Blank line':
            self.move_selection(int(steps > 0)*2-1)
        self.update_labels()
        
    def on_key_press(self, sym, mod):
        if sym == key.ESCAPE:
            self.close()
        elif sym in (key.RETURN, key.ENTER):
            self.save()
            self.close()
        elif sym == key.SPACE:
            self.select()
        return pyglet.event.EVENT_HANDLED
    
    def select(self):
        k = self.options[self.selpos]
        i = self.selpos
        if k == "Blank line":
            pass
        elif k in self.actions.keys():
            self.values[k] = self.actions[k](k)
        elif type(self.values[k]) == bool:
            self.values[k] = not self.values[k]  # todo: other data types
        elif isinstance(self.values[k], Cycler):
            self.values[k].nxt()
        elif self.values[k] == None:
            self.choose(k, i)
            self.close()
        if self.choose_once:
            self.close()        
        self.update_labels()
        
    def choose(self, k, i): # override this method in subclasses
        print "Thank you for beta-testing our software."
        
    def close(self):
        return window.remove_handlers(self.on_key_press, self.on_text, 
                                      self.on_text_motion, self.on_draw)
        
    def save(self):
        "Override me in subclasses."
        return
    
    def on_text_motion(self, evt):
        if evt == key.MOTION_UP:            self.move_selection(steps=-1)
        if evt == key.MOTION_DOWN:          self.move_selection(steps=1)
        if evt == key.MOTION_PREVIOUS_PAGE: self.move_selection(steps=-self.pagesize)
        if evt == key.MOTION_NEXT_PAGE:     self.move_selection(steps=self.pagesize)
        return pyglet.event.EVENT_HANDLED
    
    def on_text(self, evt):
        return pyglet.event.EVENT_HANDLED # todo: entering values after select()
    
    def on_draw(self):
        window.clear()
        self.batch.draw()
        return pyglet.event.EVENT_HANDLED
    
class MainMenu(Menu):
    def __init__(self):
        def NotImplemented():
            raise NotImplementedError
        ops = [('game', ('Choose Game Mode'), GameSelect),
               ('sounds', ('Choose Sounds'), SoundSelect),
               ('images', ('Choose Images'), ImageSelect),
               ('user', ('Choose User'), UserScreen),
               ('graph', ('Daily Progress Graph'), NotImplemented),
               ('help', ('Help / Tutorial'), NotImplemented),
               ('donate', ('Donate'), NotImplemented)
               ('forum', ('Go to Forum / Mailing List'), NotImplemented)]
        options =       [  op[0]         for op in ops]
        names   = dict( [ (op[0], op[1]) for op in ops])
        actions = dict( [ (op[0], op[2]) for op in ops])
        
class UserScreen(Menu):
    def __init__(self):
    
        self.users = users = [("New user"), 'Blank line'] + get_users()
        Menu.__init__(self, options=users, 
                      #actions=dict([(user, choose_user) for user in users]),
                      title=("Please select your user profile"),
                      choose_once=True,
                      default=users.index(param.USER))
    
    def save(self):
        self.select() # Enter should choose a user too
        Menu.save(self)
        
    def choose(self, k, i):
        newuser = self.users[i]
        if newuser == ("New user"):
            textInput = TextInputScreen(("Enter new user name:"), param.USER, callback=set_user, catch=' ')
        else:
            set_user(newuser)
            
class LanguageScreen(Menu):
    def __init__(self):
        self.languages = languages = [fn for fn in os.listdir(os.path.join('res', 'i18n')) if fn.lower().endswith('mo')]
        try:
            default = languages.index(config.cfg.LANGUAGE + '.mo')
        except:
            default = 0
        Menu.__init__(self, options=languages,
                      title=("Please select your preferred language"),
                      choose_once=True,
                      default=default)
    def save(self):
        self.select() 
        Menu.save(self)
        
    def choose(self, k, i):
        newlang = self.languages[i]
        # set the new language here

class OptionsScreen(Menu):
    def __init__(self):
        """
        Sorta works.  Not yet useful, though.
        """        
        options = config.cfg.keys()
        options.sort()
        Menu.__init__(self, options=options, values=config.cfg, title=('Configuration'))


class GameSelect(Menu):
    def __init__(self):
        modalities = ['position1', 'color', 'image', 'audio', 'audio2', 'arithmetic']
        options = modalities[:]
        names = dict([(m, ("Use %s") % m) for m in modalities])
        names['position1'] = ("Use position")
        options.append("Blank line")
        options.append('combination')
        options.append("Blank line")
        options.append('variable')
        options.append('crab')      
        options.append("Blank line")
        options.append('multi')
        options.append('multimode')
        options.append('Blank line')
        options.append('selfpaced')
        options.append("Blank line")
        options.append('interference')
        names['combination'] = ('Combination N-back mode')
        names['variable'] = ('Use variable N-Back levels')
        names['crab'] = ('Crab-back mode (reverse order of sets of N stimuli)')
        names['multi'] = ('Simultaneous visual stimuli')
        names['multimode'] = ('Simultaneous stimuli differentiated by')
        names['selfpaced'] = ('Self-paced mode')
        names['interference'] = ('Interference (tricky stimulus generation)')
        vals = dict([[op, None] for op in options])
        curmodes = mode.modalities[mode.mode]
        interference_options = [i / 8. for i in range(0, 9)]
        if not config.cfg.DEFAULT_CHANCE_OF_INTERFERENCE in interference_options:
            interference_options.append(config.cfg.DEFAULT_CHANCE_OF_INTERFERENCE)
        interference_options.sort()
        if config.cfg.CHANCE_OF_INTERFERENCE in interference_options:
            interference_default = interference_options.index(config.cfg.CHANCE_OF_INTERFERENCE)
        else:
            interference_default = 3
        vals['interference'] = PercentCycler(values=interference_options, default=interference_default)
        vals['combination'] = 'visvis' in curmodes
        vals['variable'] = bool(config.cfg.VARIABLE_NBACK)
        vals['crab'] = bool(mode.flags[mode.mode]['crab'])
        vals['multi'] = Cycler(values=[1,2,3,4], default=mode.flags[mode.mode]['multi']-1)
        vals['multimode'] = Cycler(values=['color', 'image'], default=config.cfg.MULTI_MODE)
        vals['selfpaced'] = bool(mode.flags[mode.mode]['selfpaced'])
        for m in modalities:
            vals[m] = m in curmodes
        Menu.__init__(self, options, vals, names=names, title=('Choose your game mode'))
        self.modelabel = pyglet.text.Label('', font_size=self.titlesize,
            bold=False, color=(0,0,0,255), batch=self.batch,
            x=window.width/2, y=(window.height*1)/10,
            anchor_x='center', anchor_y='center')
        self.update_labels()
        self.newmode = mode.mode # self.newmode will be False if an invalid mode is chosen

    def update_labels(self):
        self.calc_mode()
        try:
            if self.newmode:
                self.modelabel.text = mode.long_mode_names[self.newmode] + \
                    (self.values['variable'] and ' V.' or '') + ' N-Back'
            else:
                self.modelabel.text = "An invalid mode has been selected."
        except AttributeError:
            pass
        Menu.update_labels(self)
        
    def calc_mode(self):
        modes = [k for (k, v) in self.values.items() if v and not isinstance(v, Cycler)]
        crab = 'crab' in modes
        if 'variable' in modes:  modes.remove('variable')
        if 'combination' in modes:
            modes.remove('combination')
            modes.extend(['visvis', 'visaudio', 'audiovis']) # audio should already be there
        base = 0
        base += 256 * (self.values['multi'].value()-1)
        if 'crab' in modes: 
            modes.remove('crab')
            base += 128
        if 'selfpaced' in modes:
            modes.remove('selfpaced')
            base += 1024
            
        candidates = set([k for k,v in mode.modalities.items() if not 
                         [True for m in modes if not m in v] and not
                         [True for m in v if not m in modes]])
        candidates = candidates & set(range(0, 128))
        if len(candidates) == 1: 
            candidate = list(candidates)[0] + base
            if candidate in mode.modalities:
                self.newmode = candidate
            else: self.newmode = False
        else:
            if param.DEBUG: print candidates, base
            self.newmode = False 

    def close(self):
        Menu.close(self)
        if not mode.manual:
            mode.enforce_standard_mode()
            stats.retrieve_progress()
        update_all_labels()
        circles.update()

    def save(self):
        self.calc_mode()
        config.cfg.VARIABLE_NBACK = self.values['variable']
        config.cfg.MULTI_MODE = self.values['multimode'].value()
        config.cfg.CHANCE_OF_INTERFERENCE = self.values['interference'].value()
        if self.newmode:
            mode.mode = self.newmode
        
        
    def select(self):
        choice = self.options[self.selpos]
        if choice == 'combination':
            self.values['arithmetic'] = False
            self.values['image'] = False
            self.values['audio2'] = False
            self.values['audio'] = True
            self.values['multi'].i = 0 # no multi mode
        elif choice == 'arithmetic':
            self.values['image'] = False
            self.values['audio'] = False
            self.values['audio2'] = False
            self.values['combination'] = False
            self.values['multi'].i = 0 
        elif choice == 'audio':
            self.values['arithmetic'] = False
            if self.values['audio']: 
                self.values['combination'] = False
                self.values['audio2'] = False
        elif choice == 'audio2':
            self.values['audio'] = True
            self.values['combination'] = False
            self.values['arithmetic'] = False
        elif choice == 'image':
            self.values['combination'] = False
            self.values['arithmetic'] = False
            if self.values['multi'].value() > 1 and not self.values['image']:
                self.values['color'] = False
                self.values['multimode'].choose('color')
        elif choice == 'color':
            if self.values['multi'].value() > 1 and not self.values['color']:
                self.values['image'] = False
                self.values['multimode'].choose('image')
        elif choice == 'multi':
            self.values['arithmetic'] = False
            self.values['combination'] = False
            self.values[self.values['multimode'].value()] = False
        elif choice == 'multimode' and self.values['multi'].value() > 1:
            mm = self.values['multimode'].value() # what we're changing from
            notmm = (mm == 'image') and 'color' or 'image' # changing to
            self.values[mm] = self.values[notmm]
            self.values[notmm] = False

                            
        Menu.select(self)
        modes = [k for k,v in self.values.items() if v]
        if not [v for k,v in self.values.items() 
                  if v and not k in ('crab', 'combination', 'variable')] \
           or len(modes) == 1 and modes[0] in ['image', 'color']:
            self.values['position1'] = True
            self.update_labels()
        self.calc_mode()
        
class ImageSelect(Menu):
    def __init__(self):
        imagesets = resourcepaths['sprites']
        self.new_sets = {}
        for image in imagesets:
            self.new_sets[image] = image in config.cfg.IMAGE_SETS
        options = self.new_sets.keys()
        options.sort()
        vals = self.new_sets
        Menu.__init__(self, options, vals, title=('Choose images to use for the Image n-back tasks.'))

    def close(self):
        while config.cfg.IMAGE_SETS:
            config.cfg.IMAGE_SETS.remove(config.cfg.IMAGE_SETS[0])
        for k,v in self.new_sets.items():
            if v: config.cfg.IMAGE_SETS.append(k)
        Menu.close(self)
        update_all_labels()

    def select(self):
        Menu.select(self)
        if not [val for val in self.values.values() if (val and not isinstance(val, Cycler))]:
            i = 0
            if self.selpos == 0:
                i = random.randint(1, len(self.options)-1)
            self.values[self.options[i]] = True
            self.update_labels()
            
class SoundSelect(Menu):            
    def __init__(self):
        audiosets = resourcepaths['sounds'] # we don't want to delete 'operations' from resourcepaths['sounds']
        self.new_sets = {}
        for audio in audiosets:
            if not audio == 'operations':
                self.new_sets['1'+audio] = audio in config.cfg.AUDIO1_SETS
                self.new_sets['2'+audio] = audio in config.cfg.AUDIO2_SETS
        for audio in audiosets:
            if not audio == 'operations':
                self.new_sets['2'+audio] = audio in config.cfg.AUDIO2_SETS
        options = self.new_sets.keys()
        options.sort()
        options.insert(len(self.new_sets)/2, "Blank line") # Menu.update_labels and .select will ignore this
        options.append("Blank line")
        options.extend(['config.cfg.CHANNEL_AUDIO1', 'config.cfg.CHANNEL_AUDIO2'])
        lcr = ['left', 'right', 'center']
        vals = self.new_sets
        vals['config.cfg.CHANNEL_AUDIO1'] = Cycler(lcr, default=lcr.index(config.cfg.CHANNEL_AUDIO1))
        vals['config.cfg.CHANNEL_AUDIO2'] = Cycler(lcr, default=lcr.index(config.cfg.CHANNEL_AUDIO2))
        names = {}
        for op in options:
            if op.startswith('1') or op.startswith('2'):
                names[op] = ("Use sound set '%s' for channel %s") % (op[1:], op[0])
            elif 'CHANNEL_AUDIO' in op:
                names[op] = 'Channel %i is' % (op[-1]=='2' and 2 or 1)
        Menu.__init__(self, options, vals, {}, names, title=('Choose sound sets to Sound n-back tasks.'))
        
    def close(self):
        config.cfg.AUDIO1_SETS = []
        config.cfg.AUDIO2_SETS = []
        for k,v in self.new_sets.items():
            if   k.startswith('1') and v: config.cfg.AUDIO1_SETS.append(k[1:])
            elif k.startswith('2') and v: config.cfg.AUDIO2_SETS.append(k[1:])
        config.cfg.CHANNEL_AUDIO1  = self.values['config.cfg.CHANNEL_AUDIO1'].value()
        config.cfg.CHANNEL_AUDIO2 = self.values['config.cfg.CHANNEL_AUDIO2'].value()
        Menu.close(self)
        update_all_labels()
        
    def select(self):
        Menu.select(self)
        for c in ('1', '2'):
            if not [v for k,v in self.values.items() if (k.startswith(c) and v and not isinstance(v, Cycler))]:
                options = resourcepaths['sounds'].keys()
                options.remove('operations')
                i = 0
                if self.selpos == 0:
                    i = random.randint(1, len(options)-1)
                elif self.selpos==len(options)+1:
                    i = random.randint(len(options)+2, 2*len(options))
                elif self.selpos > len(options)+1:
                    i = len(options)+1
                self.values[self.options[i]] = True
            self.update_labels()

# this class controls the field.
# the field is the grid on which the squares appear
class Field:
    def __init__(self):
        if config.cfg.FIELD_EXPAND:
            self.size = int(window.height * 0.85)
        else: self.size = int(window.height * 0.625)
        if config.cfg.BLACK_BACKGROUND:
            self.color = (64, 64, 64)
        else: 
            self.color = (192, 192, 192)
        self.color4 = self.color * 4
        self.color8 = self.color * 8
        self.center_x = window.width // 2
        if config.cfg.FIELD_EXPAND:
            self.center_y = window.height // 2
        else: self.center_y = window.height // 2 + 20
        self.x1 = self.center_x - self.size/2
        self.x2 = self.center_x + self.size/2
        self.x3 = self.center_x - self.size/6
        self.x4 = self.center_x + self.size/6
        self.y1 = self.center_y - self.size/2
        self.y2 = self.center_y + self.size/2
        self.y3 = self.center_y - self.size/6
        self.y4 = self.center_y + self.size/6
        
        # add the inside lines
        if config.cfg.GRIDLINES:
            self.v_lines = batch.add(8, GL_LINES, None, ('v2i', (
                self.x1, self.y3,
                self.x2, self.y3,
                self.x1, self.y4,
                self.x2, self.y4,
                self.x3, self.y1,
                self.x3, self.y2,
                self.x4, self.y1,
                self.x4, self.y2)),
                      ('c3B', self.color8))
                
        self.crosshair_visible = False
        # initialize crosshair
        self.crosshair_update()
                
    # draw the target cross in the center
    def crosshair_update(self):
        if not config.cfg.CROSSHAIRS:
            return
        if (not mode.paused) and 'position1' in mode.modalities[mode.mode] and not config.cfg.VARIABLE_NBACK:
            if self.crosshair_visible: return
            else:
                self.v_crosshair = batch.add(4, GL_LINES, None, ('v2i', (
                    self.center_x - 8, self.center_y,
                    self.center_x + 8, self.center_y,
                    self.center_x, self.center_y - 8,
                    self.center_x, self.center_y + 8)), ('c3B', self.color4))
                self.crosshair_visible = True
        else:
            if self.crosshair_visible:
                self.v_crosshair.delete()
                self.crosshair_visible = False
            else: return


# this class controls the visual cues (colored squares).
class Visual:
    def __init__(self):
        self.visible = False
        self.label = pyglet.text.Label(
            '',
            font_size=field.size//6, bold=True,
            anchor_x='center', anchor_y='center', batch=batch)
        self.variable_label = pyglet.text.Label(
            '',
            font_size=field.size//6, bold=True,
            anchor_x='center', anchor_y='center', batch=batch)

        self.spr_square = [pyglet.sprite.Sprite(pyglet.image.load(path))
                              for path in resourcepaths['misc']['colored-squares']]
        self.spr_square_size = self.spr_square[0].width
    
        if config.cfg.ANIMATE_SQUARES:
            self.size_factor = 0.9375
        elif config.cfg.OLD_STYLE_SQUARES:
            self.size_factor = 0.9375
        else:
            self.size_factor = 1.0
        self.size = int(field.size / 3 * self.size_factor)
        
        # load an image set
        self.load_set()
        
    def load_set(self, index=None):
        if type(index) == int:
            index = config.cfg.IMAGE_SETS[index]
        if index == None:
            index = random.choice(config.cfg.IMAGE_SETS)
        if hasattr(self, 'image_set_index') and index == self.image_set_index: 
            return
        self.image_set_index = index
        self.image_set = [pyglet.sprite.Sprite(pyglet.image.load(path))
                            for path in resourcepaths['sprites'][index]]
        self.image_set_size = self.image_set[0].width
        
    def choose_random_images(self, number):
        self.image_indices = random.sample(range(len(self.image_set)), number)
        self.images = random.sample(self.image_set, number)
    
    def choose_indicated_images(self, indices):
        self.image_indices = indices
        self.images = [self.image_set[i] for i in indices]
        
    def spawn(self, position=0, color=1, vis=0, number=-1, operation='none', variable = 0):

        self.position = position
        self.color = get_color(color)
        self.vis = vis
        
        self.center_x = field.center_x + (field.size / 3)*((position+1)%3 - 1) + (field.size / 3 - self.size)/2
        self.center_y = field.center_y + (field.size / 3)*((position/3+1)%3 - 1) + (field.size / 3 - self.size)/2
        
        if self.vis == 0:
            if config.cfg.OLD_STYLE_SQUARES:
                lx = self.center_x - self.size // 2 + 2
                rx = self.center_x + self.size // 2 - 2
                by = self.center_y - self.size // 2 + 2
                ty = self.center_y + self.size // 2 - 2
                cr = self.size // 5
                
                if config.cfg.OLD_STYLE_SHARP_CORNERS:
                    self.square = batch.add(4, GL_POLYGON, None, ('v2i', (
                        lx, by,
                        rx, by,
                        rx, ty,
                        lx, ty,)),
                        ('c4B', self.color * 4))
                else:
                    #rounded corners: bottom-left, bottom-right, top-right, top-left
                    x = ([lx + int(cr*(1-math.cos(math.radians(i)))) for i in range(0, 91, 10)] +
                         [rx - int(cr*(1-math.sin(math.radians(i)))) for i in range(0, 91, 10)] +
                         [rx - int(cr*(1-math.sin(math.radians(i)))) for i in range(90, -1, -10)] +
                         [lx + int(cr*(1-math.cos(math.radians(i)))) for i in range(90, -1, -10)])
                        
                    y = ([by + int(cr*(1-math.sin(math.radians(i)))) for i in range(0, 91, 10) + range(90, -1, -10)] +
                         [ty - int(cr*(1-math.sin(math.radians(i)))) for i in range(0, 91, 10) + range(90, -1, -10)])
                    xy = []
                    for a,b in zip(x,y): xy.extend((a, b))
                    
                    self.square = batch.add(40, GL_POLYGON, None, 
                                            ('v2i', xy), ('c4B', self.color * 40))
                
            else:
                # use sprite squares   
                self.square = self.spr_square[color-1]
                self.square.opacity = 255
                self.square.x = self.center_x - field.size // 6
                self.square.y = self.center_y - field.size // 6
                self.square.scale = 1.0 * self.size / self.spr_square_size
                self.square_size_scaled = self.square.width
                self.square.batch = batch
                
                # initiate square animation
                self.age = 0.0
                pyglet.clock.schedule_interval(self.animate_square, 1/60.)
        
        elif 'arithmetic' in mode.modalities[mode.mode]: # display a number
            self.label.text = str(number)
            self.label.x = self.center_x
            self.label.y = self.center_y + 4
            self.label.color = self.color
        elif 'visvis' in mode.modalities[mode.mode]: # display a letter
            self.label.text = self.letters[vis - 1].upper()
            self.label.x = self.center_x
            self.label.y = self.center_y + 4
            self.label.color = self.color
        elif 'image' in mode.modalities[mode.mode] \
              or 'vis1' in mode.modalities[mode.mode] \
              or (mode.flags[mode.mode]['multi'] > 1 and config.cfg.MULTI_MODE == 'image'): # display a pictogram
            self.square = self.images[vis-1]
            self.square.opacity = 255
            self.square.color = self.color[:3]
            self.square.x = self.center_x - field.size // 6
            self.square.y = self.center_y - field.size // 6
            self.square.scale = 1.0 * self.size / self.image_set_size
            self.square_size_scaled = self.square.width
            self.square.batch = batch
            
            # initiate square animation
            self.age = 0.0
            #self.animate_square(0)
            pyglet.clock.schedule_interval(self.animate_square, 1/60.)
            
        if variable > 0:
            # display variable n-back level
            self.variable_label.text = str(variable)

            if not 'position1' in mode.modalities[mode.mode]:
                self.variable_label.x = field.center_x
                self.variable_label.y = field.center_y - field.size//3 + 4
            else:
                self.variable_label.x = field.center_x
                self.variable_label.y = field.center_y + 4

            self.variable_label.color = self.color
        
        self.visible = True
        
    def animate_square(self, dt):
        self.age += dt
        if mode.paused: return
        if not config.cfg.ANIMATE_SQUARES: return
        
        # factors which affect animation
        scale_addition = dt / 8
        fade_begin_time = 0.4
        fade_end_time = 0.5
        fade_end_transparency = 1.0  # 1 = fully transparent, 0.5 = half transparent
    
        self.square.scale += scale_addition
        dx = (self.square.width - self.square_size_scaled) // 2
        self.square.x = self.center_x - field.size // 6 - dx
        self.square.y = self.center_y - field.size // 6 - dx
        
        if self.age > fade_begin_time:
            factor = (1.0 - fade_end_transparency * (self.age - fade_begin_time) / (fade_end_time - fade_begin_time))
            if factor > 1.0: factor = 1.0
            if factor < 0.0: factor = 0.0
            self.square.opacity = int(255 * factor)
    
    def hide(self):
        if self.visible:
            self.label.text = ''
            self.variable_label.text = ''
            if 'image' in mode.modalities[mode.mode] \
                  or 'vis1' in mode.modalities[mode.mode] \
                  or (mode.flags[mode.mode]['multi'] > 1 and config.cfg.MULTI_MODE == 'image'): # hide pictogram
                self.square.batch = None
                pyglet.clock.unschedule(self.animate_square)
            elif self.vis == 0:
                if config.cfg.OLD_STYLE_SQUARES:
                    self.square.delete()
                else:
                    self.square.batch = None
                    pyglet.clock.unschedule(self.animate_square)
            self.visible = False
            
# Circles is the 3-strikes indicator in the top left corner of the screen.
class Circles:
    def __init__(self):
        self.y = window.height - 20
        self.start_x = 30
        self.radius = 8
        self.distance = 20
        if config.cfg.BLACK_BACKGROUND:
            self.not_activated = [64, 64, 64, 255]
        else:
            self.not_activated = [192, 192, 192, 255]
        self.activated = [64, 64, 255, 255]
        if config.cfg.BLACK_BACKGROUND:
            self.invisible = [0, 0, 0, 0]
        else:
            self.invisible = [255, 255, 255, 0]
        
        self.circle = []
        for index in range(0, config.cfg.THRESHOLD_FALLBACK_SESSIONS - 1):
            self.circle.append(batch.add(4, GL_QUADS, None, ('v2i', (
                self.start_x + self.distance * index - self.radius,
                self.y + self.radius,
                self.start_x + self.distance * index + self.radius,
                self.y + self.radius,
                self.start_x + self.distance * index + self.radius,
                self.y - self.radius,
                self.start_x + self.distance * index - self.radius,
                self.y - self.radius)),
                ('c4B', self.not_activated * 4)))
            
        self.update()
            
    def update(self):
        if mode.manual or mode.started or config.cfg.JAEGGI_MODE:
            for i in range(0, config.cfg.THRESHOLD_FALLBACK_SESSIONS - 1):
                self.circle[i].colors = (self.invisible * 4)
        else:
            for i in range(0, config.cfg.THRESHOLD_FALLBACK_SESSIONS - 1):
                self.circle[i].colors = (self.not_activated * 4)
            for i in range(0, mode.progress):
                self.circle[i].colors = (self.activated * 4)
            
        
# this is the update notification
class UpdateLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            multiline = True, width = field.size//3 - 4, align='middle',
            font_size=11, bold=True,
            color=(0, 128, 0, 255),
            x=window.width//2, y=field.center_x + field.size // 6,
            anchor_x='center', anchor_y='center', batch=batch)
        self.update()
    def update(self):
        if not mode.started and update_available:
            str_list = []
            str_list.append(('An update is available ('))
            str_list.append(str(update_version))
            str_list.append(('). Press W to open web site'))
            self.label.text = ''.join(str_list)
        else: self.label.text = ''
        
# this is the black text above the field
class GameModeLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            font_size=16,
            color=config.cfg.COLOR_TEXT,
            x=window.width//2, y=window.height - 20,
            anchor_x='center', anchor_y='center', batch=batch)
        self.update()
    def update(self):
        if mode.started and mode.hide_text:
            self.label.text = ''
        else:
            str_list = []
            if config.cfg.JAEGGI_MODE and not param.CLINICAL_MODE:
                str_list.append(('Jaeggi mode: '))
            if mode.manual:
                str_list.append(('Manual mode: '))
            str_list.append(mode.long_mode_names[mode.mode] + ' ')
            if config.cfg.VARIABLE_NBACK:
                str_list.append(('V. '))
            str_list.append(str(mode.back))
            str_list.append(('-Back'))
            self.label.text = ''.join(str_list)

    def flash(self):
        pyglet.clock.unschedule(gameModeLabel.unflash)
        self.label.color = (255,0 , 255, 255)
        self.update()
        pyglet.clock.schedule_once(gameModeLabel.unflash, 0.5)
    def unflash(self, dt):
        self.label.color = config.cfg.COLOR_TEXT
        self.update()

class JaeggiWarningLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            font_size=12, bold = True,
            color=(255, 0, 255, 255),
            x=window.width//2, y=field.center_x + field.size // 3 + 8,
            anchor_x='center', anchor_y='center', batch=batch)

    def show(self):
        pyglet.clock.unschedule(jaeggiWarningLabel.hide)
        self.label.text = ('Please disable Jaeggi Mode to access additional modes.')
        pyglet.clock.schedule_once(jaeggiWarningLabel.hide, 3.0)
    def hide(self, dt):
        self.label.text = ''

# this is the keyboard reference list along the left side
class KeysListLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            multiline = True, width = 300, bold = False,
            font_size=9,
            color=config.cfg.COLOR_TEXT,
            x = 10,
            anchor_x='left', anchor_y='top', batch=batch)
        self.update()
    def update(self):
        str_list = []
        if mode.started:
            self.label.y = window.height - 10
            if not mode.hide_text:
                str_list.append(('P: Pause / Unpause\n'))
                str_list.append('\n')
                str_list.append(('F8: Hide / Reveal Text\n'))
                str_list.append('\n')                
                str_list.append(('ESC: Cancel Session\n'))
        elif param.CLINICAL_MODE:
            self.label.y = window.height - 10
            str_list.append(('ESC: Exit'))
        else:
            if mode.manual or config.cfg.JAEGGI_MODE:
                self.label.y = window.height - 10
            else:
                self.label.y = window.height - 40
            if 'morse' in config.cfg.AUDIO1_SETS or 'morse' in config.cfg.AUDIO2_SETS:
                str_list.append(('J: Morse Code Reference\n'))
                str_list.append('\n')
            str_list.append(('H: Help / Tutorial\n'))
            str_list.append('\n')
            if mode.manual:
                str_list.append(('F1: Decrease N-Back\n'))
                str_list.append(('F2: Increase N-Back\n'))
                str_list.append('\n')
                str_list.append(('F3: Decrease Trials\n'))
                str_list.append(('F4: Increase Trials\n'))
                str_list.append('\n')
            if mode.manual:
                str_list.append(('F5: Decrease Speed\n'))
                str_list.append(('F6: Increase Speed\n'))
                str_list.append('\n')
            str_list.append(('C: Choose Game Type\n'))
            str_list.append(('S: Select Sounds\n'))
            str_list.append(('I: Select Images\n'))
            if mode.manual:
                str_list.append(('M: Standard Mode\n'))
            else:
                str_list.append(('M: Manual Mode\n'))
            str_list.append(('D: Donate\n'))
            str_list.append('\n')
            str_list.append(('G: Daily Progress Graph\n'))
            str_list.append('\n')
            str_list.append(('W: Brain Workshop Web Site\n'))
            if config.cfg.WINDOW_FULLSCREEN:
                str_list.append(('E: Saccadic Eye Exercise\n'))
            str_list.append('\n')
            str_list.append(('ESC: Exit\n'))
            
        self.label.text = ''.join(str_list)

class TitleMessageLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            ('Brain Workshop'),
            #multiline = True, width = window.width // 2,
            font_size = 32, bold = True, color = config.cfg.COLOR_TEXT,
            x = window.width // 2, y = window.height - 35,
            anchor_x = 'center', anchor_y = 'center')
        self.label2 = pyglet.text.Label(
            ('Version ') + str(param.VERSION),
            font_size = 14, bold = False, color = config.cfg.COLOR_TEXT,
            x = window.width // 2, y = window.height - 75,
            anchor_x = 'center', anchor_y = 'center')
        
    def draw(self):
        self.label.draw()
        self.label2.draw()

class TitleKeysLabel:
    def __init__(self):
        str_list = []
        if not (config.cfg.JAEGGI_MODE or param.CLINICAL_MODE):
            str_list.append(('C: Choose Game Mode\n'))
            str_list.append(('S: Choose Sounds\n'))
            str_list.append(('I: Choose Images\n'))
        if not param.CLINICAL_MODE:
            str_list.append(('U: Choose User\n'))
            str_list.append(('G: Daily Progress Graph\n'))
        str_list.append(('H: Help / Tutorial\n'))
        if not param.CLINICAL_MODE:
            str_list.append(('D: Donate\n'))
            str_list.append(('F: Go to Forum / Mailing List\n'))
            str_list.append(('O: Edit configuration file'))
        
        self.keys = pyglet.text.Label(
            ''.join(str_list),
            multiline = True, width = 260,
            font_size = 12, bold = True, color = config.cfg.COLOR_TEXT,
            x = window.width // 2, y = 230,
            anchor_x = 'center', anchor_y = 'top')
        
        self.space = pyglet.text.Label(
            ('Press SPACE to enter the Workshop'),
            font_size = 20, bold = True, color = (32, 32, 255, 255),
            x = window.width // 2, y = 35,
            anchor_x = 'center', anchor_y = 'center')
    def draw(self):
        self.space.draw()
        self.keys.draw()

        
# this is the word "brain" above the brain logo.
class LogoUpperLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            'Brain', # I think we shouldn't translate the program name.  Yes?
            font_size=11, bold = True,
            color=config.cfg.COLOR_TEXT,
            x=field.center_x, y=field.center_y + 30,
            anchor_x='center', anchor_y='center')
    def draw(self):
        self.label.draw()

# this is the word "workshop" below the brain logo.
class LogoLowerLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            'Workshop',
            font_size=11, bold = True,
            color=config.cfg.COLOR_TEXT,
            x=field.center_x, y=field.center_y - 27,
            anchor_x='center', anchor_y='center')
    def draw(self):
        self.label.draw()

# this is the word "Paused" which appears when the game is paused.
class PausedLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            font_size=14,
            color=(64, 64, 255, 255),
            x=field.center_x, y=field.center_y,
            anchor_x='center', anchor_y='center', batch=batch)
        self.update()
    def update(self):
        if mode.paused:
            self.label.text = 'Paused'
        else:
            self.label.text = ''

# this is the congratulations message which appears when advancing N-back levels.
class CongratsLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            font_size=14,
            color=(255, 32, 32, 255),
            x=field.center_x, y=window.height - 47,
            anchor_x='center', anchor_y='center', batch=batch)
        self.update()
    def update(self, show=False, advance=False, fallback=False, awesome=False, great=False, good=False, perfect = False):
        str_list = []
        if show and not param.CLINICAL_MODE and config.cfg.USE_SESSION_FEEDBACK:
            if perfect: str_list.append(('Perfect score! '))
            elif awesome: str_list.append(('Awesome score! '))
            elif great: str_list.append(('Great score! '))
            elif good: str_list.append(('Not bad! '))
            else: str_list.append(('Keep trying. You\'re getting there! '))
        if advance:
            str_list.append(('N-Back increased'))
        elif fallback:
            str_list.append(('N-Back decreased'))
        self.label.text = ''.join(str_list)
        
class FeedbackLabel:
    def __init__(self, modality, pos=0, total=1):
        """
        Generic text label for giving user feedback during N-back sessions.  All
        of the feedback labels should be instances of this class.
        
        pos should be which label number this one is displayed as (order: left-to-right).
        total should be the total number of feedback labels for this mode.
        """
        self.modality = modality
        self.letter = key.symbol_string(config.cfg['KEY_%s' % modality.upper()])
        if self.letter == 'SEMICOLON': 
            self.letter = ';'      
        modalityname = modality
        if modalityname.endswith('vis'):
            modalityname = modalityname[:-3] + ' & n-vis'
        elif modalityname.endswith('audio') and not modalityname == 'audio':
            modalityname = modalityname[:-5] + ' & n-audio'
        if mode.flags[mode.mode]['multi'] == 1 and modalityname == 'position1':
            modalityname = 'position'
            
	if total == 2 and not config.cfg.JAEGGI_MODE and config.cfg.ENABLE_MOUSE:
	    if pos == 0:
		self.mousetext = "Left-click or"
	    if pos == 1:
		self.mousetext = "Right-click or"
	else:
	    self.mousetext = ""

        self.text = "%s %s: %s" % ((self.mousetext), self.letter, (modalityname)) # FIXME: will this break pyglettext?

        if total < 4:
            self.text += (' match')
            font_size = 16
        elif total < 5: font_size = 14
        elif total < 6: font_size = 13
        else:           font_size = 11 
                
        self.label = pyglet.text.Label(
            text=self.text,
            x=-200, y=30, # we'll fix this position later, after we see how big the label is
            anchor_x='left', anchor_y='center', batch=batch, font_size=font_size)
        #w = self.label.width  # this doesn't work; how are you supposed to find the width of a label texture?
        w = (len(self.text) * font_size*4)/5
        dis = (window.width-100) / float(total-.99)
        x = 30 + int( pos*dis - w*pos/(total-.5) )

        # draw an icon next to the label for multi-stim mode
        if mode.flags[mode.mode]['multi'] > 1 and self.modality[-1].isdigit():
            self.id = int(modality[-1])
            if config.cfg.MULTI_MODE == 'color':
                self.icon = pyglet.sprite.Sprite(visuals[self.id-1].spr_square[config.cfg.VISUAL_COLORS[self.id-1]-1].image)
                self.icon.scale = .125 * visuals[self.id-1].size / visuals[self.id-1].image_set_size
                self.icon.y = 22    
                self.icon.x = x - 15
                x += 15

            else: # 'image'
                self.icon = pyglet.sprite.Sprite(visuals[self.id-1].images[self.id-1].image)
                self.icon.color = get_color(1)[:3]
                self.icon.scale = .25 * visuals[self.id-1].size / visuals[self.id-1].image_set_size
                self.icon.y = 15
                self.icon.x = x - 25
                x += 25

            self.icon.opacity = 255
            self.icon.batch = batch

        self.label.x = x
        
        self.update()
        
    def draw(self):
        pass # don't draw twice; this was just for debugging
        #self.label.draw()
        
    def update(self):
        if mode.started and not mode.hide_text and self.modality in mode.modalities[mode.mode]: # still necessary?
            self.label.text = self.text
        else:
            self.label.text = ''
        if config.cfg.SHOW_FEEDBACK and mode.inputs[self.modality]:
            result = check_match(self.modality)
            #self.label.bold = True
            if result == 'correct':
                self.label.color = config.cfg.COLOR_LABEL_CORRECT
            elif result == 'unknown':
                self.label.color = config.cfg.COLOR_LABEL_OOPS
            elif result == 'incorrect':
                self.label.color = config.cfg.COLOR_LABEL_INCORRECT
        elif config.cfg.SHOW_FEEDBACK and (not mode.inputs['audiovis']) and mode.show_missed:
            result = check_match(self.modality, check_missed=True)
            if result == 'missed':
                self.label.color = config.cfg.COLOR_LABEL_OOPS
                #self.label.bold = True
        else:
            self.label.color = config.cfg.COLOR_TEXT
            self.label.bold = False

    def delete(self):
        self.label.delete()
        if mode.flags[mode.mode]['multi'] > 1 and self.modality[-1].isdigit():
            self.icon.batch = None
        

def generate_input_labels():
    labels = []
    modalities = mode.modalities[mode.mode]
    pos = 0
    total = len(modalities)
    for m in modalities:
        if m != 'arithmetic':

            labels.append(FeedbackLabel(m, pos, total))
        pos += 1
    return labels

class ArithmeticAnswerLabel:
    def __init__(self):
        self.answer = []
        self.negative = False
        self.decimal = False
        self.label = pyglet.text.Label(
            '',
            x=window.width/2 - 40, y=30,
            anchor_x='left', anchor_y='center', batch=batch)
        self.update()
    def update(self):
        if not 'arithmetic' in mode.modalities[mode.mode] or not mode.started:
            self.label.text = ''
            return
        if mode.started and mode.hide_text:
            self.label.text = ''
            return
        
        self.label.font_size = 16
        str_list = []
        str_list.append(('Answer: '))
        str_list.append(str(self.parse_answer()))
        self.label.text = ''.join(str_list)
        
        if config.cfg.SHOW_FEEDBACK and mode.show_missed:
            result = check_match('arithmetic')
            if result == ('correct'):
                self.label.color = config.cfg.COLOR_LABEL_CORRECT
                self.label.bold = True
            if result == ('incorrect'):
                self.label.color = config.cfg.COLOR_LABEL_INCORRECT
                self.label.bold = True
        else:
            self.label.color = config.cfg.COLOR_TEXT
            self.label.bold = False
        
    def parse_answer(self):
        chars = ''.join(self.answer)
        if chars == '' or chars == '.':
            result = Decimal('0')
        else:
            result = Decimal(chars)
        if self.negative:
            result = Decimal('0') - result
        return result
            
    def input(self, input):
        if input == '-':
            if self.negative:
                self.negative = False
            else: self.negative = True
        elif input == '.':
            if not self.decimal:
                self.decimal = True
                self.answer.append(input)
        else:
            self.answer.append(input)
        self.update()
    
    def reset_input(self):
        self.answer = []
        self.negative = False
        self.decimal = False
        self.update()
                

# this is the text that shows the seconds per trial and the number of trials.
class SessionInfoLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            multiline = True, width = 128,
            font_size=11,
            color=config.cfg.COLOR_TEXT,
            x=20, y=field.center_y - 145,
            anchor_x='left', anchor_y='top', batch=batch)
        self.update()
    def update(self):
        if mode.started or param.CLINICAL_MODE:
            self.label.text = ''
        else:
            self.label.text = ('Session:\n%1.2f sec/trial\n%i+%i trials\n%i seconds') % \
                              (mode.ticks_per_trial / 10.0, mode.num_trials, \
                               mode.num_trials_total - mode.num_trials, 
                               int((mode.ticks_per_trial / 10.0) * \
                               (mode.num_trials_total)))
    def flash(self):
        pyglet.clock.unschedule(sessionInfoLabel.unflash)
        self.label.bold = True
        self.update()
        pyglet.clock.schedule_once(sessionInfoLabel.unflash, 1.0)
    def unflash(self, dt):
        self.label.bold = False
        self.update()
# this is the text that shows the seconds per trial and the number of trials.

class ThresholdLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            multiline = True, width = 155,
            font_size=11,
            color=config.cfg.COLOR_TEXT,
            x=window.width - 20, y=field.center_y - 145,
            anchor_x='right', anchor_y='top', batch=batch)
        self.update()
    def update(self):
        if mode.started or mode.manual or param.CLINICAL_MODE:
            self.label.text = ''
        else:
            self.label.text = (u'Thresholds:\nRaise level: \u2265 %i%%\nLower level: < %i%%') % \
            (config.get_threshold_advance(), config.get_threshold_fallback())   # '\u2265' = '>='
        
# this controls the "press space to begin session #" text.
class SpaceLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            font_size=16,
            bold=True,
            color=(32, 32, 255, 255),
            x=window.width//2, y=62,
            anchor_x='center', anchor_y='center', batch=batch)
        self.update()
    def update(self):
        if mode.started:
            self.label.text = ''
        else: 
            str_list = []
            str_list.append(('Press SPACE to begin session #'))
            str_list.append(str(mode.session_number + 1))
            str_list.append(': ')
            str_list.append(mode.long_mode_names[mode.mode] + ' ')
                
            if config.cfg.VARIABLE_NBACK:
                str_list.append(('V. '))
            str_list.append(str(mode.back))
            str_list.append(('-Back'))
            self.label.text = ''.join(str_list)
        
def check_match(input_type, check_missed = False):
    current = 0
    back_data = ''
    operation = 0
    # FIXME:  I'm not going to think about whether crab_back will work with 
    # config.cfg.VARIABLE_NBACK yet, since I don't actually understand how the latter works
    
    if mode.flags[mode.mode]['crab'] == 1:
        back = 1 + 2*((mode.trial_number-1) % mode.back)
    else:
        back = mode.back
    
    if config.cfg.VARIABLE_NBACK:
        nback_trial = mode.trial_number - mode.variable_list[mode.trial_number - back - 1] - 1
    else:
        nback_trial = mode.trial_number - back - 1
        
    if len(stats.session['position1']) < mode.back:
        return 'unknown'
    
    if   input_type in ('visvis', 'visaudio', 'image'):
        current = mode.current_stim['vis']
    elif input_type in ('audiovis', ):
        current = mode.current_stim['audio']
    if   input_type in ('visvis', 'audiovis', 'image'):
        back_data = 'vis'
    elif input_type in ('visaudio', ):
        back_data = 'audio'
    elif input_type is 'arithmetic':
        current = mode.current_stim['number']
        back_data = stats.session['numbers'][nback_trial]
        operation = mode.current_operation
    else:
        current = mode.current_stim[input_type]
        back_data = input_type
            
    if input_type == 'arithmetic':
        if operation == 'add':
            correct_answer = back_data + current
        elif operation == 'subtract':
            correct_answer = back_data - current
        elif operation == 'multiply':
            correct_answer = back_data * current
        elif operation == 'divide':
            correct_answer = Decimal(back_data) / Decimal(current)
        if correct_answer == arithmeticAnswerLabel.parse_answer():
            return 'correct'
        
    elif current == stats.session[back_data][nback_trial]:
        if check_missed:
            return 'missed'
        else:
            return 'correct'
    return 'incorrect'

                
# this controls the statistics which display upon completion of a session.
class AnalysisLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            font_size=14,
            color=config.cfg.COLOR_TEXT,
            x=window.width//2, y=92,
            anchor_x='center', anchor_y='center', batch=batch)
        self.update()
        
    def update(self, skip=False):
        if mode.started or mode.session_number == 0 or skip:
            self.label.text = ''
            return

        poss_mods = ['position1', 'position2', 'position3', 'position4', 
                     'vis1', 'vis2', 'vis3', 'vis4',  'color', 'visvis', 
                     'visaudio', 'audiovis', 'image', 'audio', 
                     'audio2', 'arithmetic'] # arithmetic must be last so it's easy to exclude
        
        rights = dict([(mod, 0) for mod in poss_mods])
        wrongs = dict([(mod, 0) for mod in poss_mods])
        category_percents = dict([(mod, 0) for mod in poss_mods])

        mods = mode.modalities[mode.mode]
        data = stats.session

        for mod in mods:
            for x in range(mode.back, len(data['position1'])):

                if mode.flags[mode.mode]['crab'] == 1:
                    back = 1 + 2*(x % mode.back)
                else:
                    back = mode.back
                if config.cfg.VARIABLE_NBACK:
                    back = mode.variable_list[x - back]
                                
                # data is a dictionary of lists.
                if mod in ['position1', 'position2', 'position3', 'position4', 
                           'vis1', 'vis2', 'vis3', 'vis4', 'audio', 'audio2', 'color', 'image']:
                    rights[mod] += int((data[mod][x] == data[mod][x-back]) and data[mod+'_input'][x])
                    wrongs[mod] += int((data[mod][x] == data[mod][x-back])  ^  data[mod+'_input'][x]) # ^ is XOR
                    if config.cfg.JAEGGI_SCORING:
                        rights[mod] += int(data[mod][x] != data[mod][x-back]  and not data[mod+'_input'][x])
                
                if mod in ['visvis', 'visaudio', 'audiovis']:
                    modnow = mod.startswith('vis') and 'vis' or 'audio' # these are the python<2.5 compatible versions
                    modthn = mod.endswith('vis')   and 'vis' or 'audio' # of 'vis' if mod.startswith('vis') else 'audio'
                    rights[mod] += int((data[modnow][x] == data[modthn][x-back]) and data[mod+'_input'][x])
                    wrongs[mod] += int((data[modnow][x] == data[modthn][x-back])  ^  data[mod+'_input'][x]) 
                    if config.cfg.JAEGGI_SCORING:
                        rights[mod] += int(data[modnow][x] != data[modthn][x-back]  and not data[mod+'_input'][x])
                    
                if mod in ['arithmetic']:
                    ops = {'add':'+', 'subtract':'-', 'multiply':'*', 'divide':'/'}
                    answer = eval("Decimal(data['numbers'][x-back]) %s Decimal(data['numbers'][x])" % ops[data['operation'][x]])
                    rights[mod] += int(answer == Decimal(data[mod+'_input'][x])) # data[...][x] is only Decimal if op == /
                    wrongs[mod] += int(answer != Decimal(data[mod+'_input'][x])) 
        
        str_list = []
        if not param.CLINICAL_MODE:
            str_list += [('Correct-Errors:   ')]
            sep = '   '
            keys = dict([(mod, config.cfg['KEY_%s' % mod.upper()]) for mod in poss_mods[:-1]]) # exclude 'arithmetic'
            
            for mod in poss_mods[:-1]: # exclude 'arithmetic'
                if mod in mods:
                    keytext = key.symbol_string(keys[mod])
                    if keytext == 'SEMICOLON': keytext = ';'
                    str_list += ["%s:%i-%i%s" % (keytext, rights[mod], wrongs[mod], sep)]
    
            if 'arithmetic' in mods:
                str_list += ["%s:%i-%i%s" % (("Arithmetic"), rights['arithmetic'], wrongs['arithmetic'], sep)]
             
        def calc_percent(r, w):
            if r+w: return int(r*100 / float(r+w))
            else:   return 0
            
        right = sum([rights[mod] for mod in mods])
        wrong = sum([wrongs[mod] for mod in mods])
        
        for mod in mods:
            category_percents[mod] = calc_percent(rights[mod], wrongs[mod])

        if config.cfg.JAEGGI_SCORING:
            percent = min([category_percents[m] for m in mode.modalities[mode.mode]])
            #percent = min(category_percents['position1'], category_percents['audio']) # config.cfg.JAEGGI_MODE forces mode.mode==2
            if not param.CLINICAL_MODE:
                str_list += [('Lowest score: %i%%') % percent]
        else:
            percent = calc_percent(right, wrong)
            str_list += [('Score: %i%%') % percent]
        
        self.label.text = ''.join(str_list)

        stats.submit_session(percent, category_percents)
                    
# this controls the title of the session history chart.
class ChartTitleLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            font_size = 10,
            bold = True,
            color = config.cfg.COLOR_TEXT,
            x = window.width - 10,
            y = window.height - 85,
            anchor_x = 'right',
            anchor_y = 'top',
            batch = batch)
        self.update()
    def update(self):
        if mode.started:
            self.label.text = ''
        else:
            self.label.text = ('Today\'s Last 20:')

# this controls the session history chart.
class ChartLabel:
    def __init__(self):
        self.start_x = window.width - 140
        self.start_y = window.height - 105
        self.line_spacing = 15
        self.column_spacing_12 = 30
        self.column_spacing_23 = 70
        self.font_size = 10
        self.color_normal = (128, 128, 128, 255)
        self.color_advance = (0, 160, 0, 255)
        self.color_fallback = (160, 0, 0, 255)
        self.column1 = []
        self.column2 = []
        self.column3 = []
        for zap in range(0, 20):
            self.column1.append(pyglet.text.Label(
                '', font_size = self.font_size,
                x = self.start_x, y = self.start_y - zap * self.line_spacing,
                anchor_x = 'left', anchor_y = 'top', batch=batch))
            self.column2.append(pyglet.text.Label(
                '', font_size = self.font_size,
                x = self.start_x + self.column_spacing_12, y = self.start_y - zap * self.line_spacing,
                anchor_x = 'left', anchor_y = 'top', batch=batch))
            self.column3.append(pyglet.text.Label(
                '', font_size = self.font_size,
                x = self.start_x + self.column_spacing_12 + self.column_spacing_23, y = self.start_y - zap * self.line_spacing,
                anchor_x = 'left', anchor_y = 'top', batch=batch))
        stats.parse_statsfile()
        self.update()
        
    def update(self):
        for x in range(0, 20):
            self.column1[x].text = ''
            self.column2[x].text = ''
            self.column3[x].text = ''
        if mode.started: return
        index = 0
        for x in range(len(stats.history) - 20, len(stats.history)):
            if x < 0: continue
            manual = stats.history[x][4]
            color = self.color_normal
            if not manual and stats.history[x][3] >= config.get_threshold_advance():
                color = self.color_advance
            elif not manual and stats.history[x][3] < config.get_threshold_fallback():
                color = self.color_fallback
            self.column1[index].color = color
            self.column2[index].color = color
            self.column3[index].color = color
            if manual:
                self.column1[index].text = 'M'
            elif stats.history[x][0] > -1:
                self.column1[index].text = '#%i' % stats.history[x][0]
            self.column2[index].text = mode.short_name(mode=stats.history[x][1], back=stats.history[x][2])
            self.column3[index].text = '%i%%' % stats.history[x][3]
            index += 1
            
# this controls the title of the session history chart.
class AverageLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            font_size=10, bold=False,
            color=config.cfg.COLOR_TEXT,
            x=window.width - 10, y=window.height-55,
            anchor_x='right', anchor_y='top', batch=batch)
        self.update()
    def update(self):
        if mode.started or param.CLINICAL_MODE:
            self.label.text = ''
        else:
            sessions = [sess for sess in stats.history if sess[1] == mode.mode][-20:]
            if sessions:
                average = sum([sess[2] for sess in sessions]) / float(len(sessions))
            else:
                average = 0.
            self.label.text = ("%sNB average: %1.2f") % (mode.short_mode_names[mode.mode], average)


class TodayLabel:
    def __init__(self):
        self.labelTitle = pyglet.text.Label(
            '',
	    font_size = 9,
	    color = config.cfg.COLOR_TEXT,
            x=window.width, y=window.height-5,
            anchor_x='right', anchor_y='top',width=280, multiline=True, batch=batch)
        self.update()
    def update(self):
        if mode.started:
            self.labelTitle.text = ''
        else:
            total_trials = sum([mode.num_trials + mode.num_trials_factor * \
             his[2] ** mode.num_trials_exponent for his in stats.history])
            total_time = mode.ticks_per_trial * param.TICK_DURATION * total_trials
            
            self.labelTitle.text = ("%i min %i sec done today in %i sessions\
			    %i min %i sec done in last 24 hours in %i sessions" % (stats.time_today//60, stats.time_today%60, stats.sessions_today, stats.time_thours//60, stats.time_thours%60, stats.sessions_thours))

class TrialsRemainingLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            font_size=12, bold = True,
            color=config.cfg.COLOR_TEXT,
            x=window.width - 10, y=window.height-5,
            anchor_x='right', anchor_y='top', batch=batch)
        self.update()
    def update(self):
        if (not mode.started) or mode.hide_text:
            self.label.text = ''
        else:
            self.label.text = ('%i remaining') % (mode.num_trials_total - mode.trial_number)
           
class Saccadic:
    def __init__(self):
        self.position = 'left'
        self.counter = 0
        self.radius = 10
        self.color = (0, 0, 255, 255)
    
    def tick(self, dt):
        self.counter += 1
        if self.counter == config.cfg.SACCADIC_REPETITIONS:
            self.stop()
        elif self.position == 'left':
            self.position = 'right'
        else: self.position = 'left'
        
    def start(self):
        self.start_time = time.time()
        self.position = 'left'
        mode.saccadic = True
        self.counter = 0
        pyglet.clock.schedule_interval(saccadic.tick, config.cfg.SACCADIC_DELAY)

    def stop(self):
        elapsed_time = time.time() - self.start_time
        stats.log_saccadic(self.start_time, elapsed_time, self.counter) 
        
        pyglet.clock.unschedule(saccadic.tick)
        mode.saccadic = False
        
    def draw(self):
        y = window.height / 2
        if saccadic.position == 'left':
            x = self.radius
        elif saccadic.position == 'right':
            x = window.width - self.radius
        pyglet.graphics.draw(4, GL_POLYGON, ('v2i', (
            x - self.radius, y - self.radius,  # lower-left
            x + self.radius, y - self.radius,  # lower-right
            x + self.radius, y + self.radius,  # upper-right
            x - self.radius, y + self.radius,  # upper-left
            
            )), ('c4B', self.color * 4))

#                    self.square = batch.add(40, GL_POLYGON, None, 
#                                            ('v2i', xy), ('c4B', self.color * 40))
       

class Panhandle:
    def __init__(self, n=-1):
        paragraphs = [ 
("""
You have completed %i sessions with Brain Workshop.  Your perseverance suggests \
that you are finding some benefit from using the program.  If you have been \
benefiting from Brain Workshop, don't you think Brain Workshop should \
benefit from you?
""") % n, 
("""
Brain Workshop is and always will be 100% free.  Up until now, Brain Workshop \
as a project has succeeded because a very small number of people have each \
donated a huge amount of time to it.  It would be much better if the project \
were supported by small donations from a large number of people.  Do your \
part.  Donate.
"""),
("""
As of March 2010, Brain Workshop has been downloaded over 75,000 times in 20 \
months.  If each downloader donated an average of $1, we could afford to pay \
decent full- or part-time salaries (as appropriate) to all of our developers, \
and we would be able to buy advertising to help people learn about Brain \
Workshop.  With $2 per downloader, or with more downloaders, we could afford \
to fund controlled experiments and clinical trials on Brain Workshop and \
cognitive training.  Help us make that vision a reality.  Donate.
"""),  
("""
The authors think it important that access to cognitive training \
technologies be available to everyone as freely as possible.  Like other \
forms of education, cognitive training should not be a luxury of the rich, \
since that would tend to exacerbate class disparity and conflict.  Charging \
money for cognitive training does exactly that.  The commercial competitors \
of Brain Workshop have two orders of magnitude more users than does Brain \
Workshop because they have far more resources for research, development, and \
marketing.  Help us bridge that gap and improve social equality of \
opportunity.  Donate.
"""),
("""
Brain Workshop has many known bugs and missing features.  The developers \
would like to fix these issues, but they also have to work in order to be \
able to pay for rent and food.  If you think the developers' time is better \
spent programming than serving coffee, then do something about it.  Donate.
"""),
("""
Press SPACE to continue, or press D to donate now.
""")]    # feel free to add more paragraphs or to change the chances for the 
        # paragraphs you like and dislike, etc.
        chances = [-1, 10, 10, 10, 10, 0] # if < 0, 100% chance of being included.  Otherwise, relative weight.
                                         # if == 0, appended to end and not counted
                                         # for target_len.
        assert len(chances) == len(paragraphs)
        target_len = 3
        text = []
        options = []
        for i in range(len(chances)):
            if chances[i] < 0:
                text.append(i)
            else:
                options.extend([i]*chances[i])
        while len(text) < target_len and len(options) > 0:
            choice = random.choice(options)
            while choice in options:
                options.remove(choice)
            text.append(choice)
        for i in range(len(chances)):
            if chances[i] == 0:
                text.append(i)
        self.text = ''.join([paragraphs[i] for i in text])
        
        self.batch = pyglet.graphics.Batch()
        self.label = pyglet.text.Label(self.text, 
                            font_name='Times New Roman',
                            color=config.cfg.COLOR_TEXT,
                            batch=self.batch,
                            multiline=True,
                            width=(4*window.width)/5,
                            font_size=14,
                            x=window.width//2, y=window.height//2,
                            anchor_x='center', anchor_y='center')
        window.push_handlers(self.on_key_press, self.on_draw)
        self.on_draw()

    def on_key_press(self, sym, mod):
        if sym in (key.ESCAPE, key.SPACE):
            self.close()
        elif sym in (key.RETURN, key.ENTER, key.D):
            self.select()
        return pyglet.event.EVENT_HANDLED
    
    def select(self):
        webbrowser.open_new_tab(param.WEB_DONATE)
        self.close()
        
    def close(self):
        return window.remove_handlers(self.on_key_press, self.on_draw)    
    
    def on_draw(self):
        window.clear()
        self.batch.draw()
        return pyglet.event.EVENT_HANDLED

#
# --- END GRAPHICS SECTION ----------------------------------------------
#

# this class stores the raw statistics and history information.
# the information is analyzed by the AnalysisLabel class.
class Stats:
    def __init__(self):
        # set up data variables
        self.initialize_session()
        self.history = []
        self.full_history = [] # not just today
        self.sessions_today = 0
        self.time_today = 0
        self.time_thours = 0
        self.sessions_thours = 0
        
    def parse_statsfile(self):
        self.clear()
        if os.path.isfile(os.path.join(get_data_dir(), config.cfg.STATSFILE)):
            try:
                #last_session = []
                #last_session_number = 0
                last_mode = 0
                last_back = 0
                statsfile_path = os.path.join(get_data_dir(), config.cfg.STATSFILE)
                statsfile = open(statsfile_path, 'r')
                is_today = False
                is_thours = False
                today = date.today()
                yesterday = date.fromordinal(today.toordinal() - 1)
                tomorrow = date.fromordinal(today.toordinal() + 1)
                for line in statsfile:
                    if line == '': continue
                    if line == '\n': continue
                    if line[0] not in '0123456789': continue
                    datestamp = date(int(line[:4]), int(line[5:7]), int(line[8:10]))
                    hour = int(line[11:13])
                    mins = int(line[14:16])
                    sec = int(line[17:19])
                    thour = datetime.datetime.today().hour
                    tmin = datetime.datetime.today().minute
                    tsec = datetime.datetime.today().second
                    if int(strftime('%H')) < config.cfg.ROLLOVER_HOUR:
                        if datestamp == today or (datestamp == yesterday and hour >= config.cfg.ROLLOVER_HOUR):
                            is_today = True
                    elif datestamp == today and hour >= config.cfg.ROLLOVER_HOUR:
                        is_today = True
                    if datestamp == today or (datestamp == yesterday and (hour > thour or (hour == thour and (mins > tmin or (mins == tmin and sec > tsec))))):
                        is_thours = True
                    if '\t' in line:
                        separator = '\t'
                    else: separator = ','
                    newline = line.split(separator)
                    newmode = int(newline[3])
                    newback = int(newline[4])
                    newpercent = int(newline[2])
                    newmanual = bool(int(newline[7]))
                    newsession_number = int(newline[8])
                    try:
                        sesstime = int(round(float(newline[25])))
                    except:
                        # this session wasn't performed with this version of BW, and is therefore
                        # old, and therefore the session time doesn't matter
                        sesstime = 0
                    if newmanual:
                        newsession_number = 0
                    self.full_history.append([newsession_number, newmode, newback, newpercent, newmanual])
                    if is_thours:
                        stats.sessions_thours += 1
                        stats.time_thours += sesstime
                    if is_today:
                        stats.sessions_today += 1
                        self.time_today += sesstime
                        self.history.append([newsession_number, newmode, newback, newpercent, newmanual])
                    #if not newmanual and (is_today or config.cfg.RESET_LEVEL):
                    #    last_session = self.full_history[-1]
                statsfile.close()
                self.retrieve_progress()
                
            except:
                quit_with_error(('Error parsing stats file\n%s') %
                                os.path.join(get_data_dir(), config.cfg.STATSFILE),
                                ('\nPlease fix, delete or rename the stats file.'),
                                quit=False)
    
    def retrieve_progress(self):
        if config.cfg.RESET_LEVEL:
            sessions = [s for s in self.history if s[1] == mode.mode]
        else:
            sessions = [s for s in self.full_history if s[1] == mode.mode]
        mode.enforce_standard_mode()
        if sessions:
            ls = sessions[-1]
            mode.back = ls[2]
            if ls[3] >= config.get_threshold_advance():
                mode.back += 1
            mode.session_number = ls[0]
            mode.progress = 0
            for s in sessions:
                if s[2] == mode.back and s[3] < config.get_threshold_fallback():
                    mode.progress += 1
                elif s[2] != mode.back:
                    mode.progress = 0
            if mode.progress >= config.cfg.THRESHOLD_FALLBACK_SESSIONS:
                mode.progress = 0
                mode.back -= 1
                if mode.back < 1:
                    mode.back = 1
        else: # no sessions today for this user and this mode
            mode.back = default_nback_mode(mode.mode)
        mode.num_trials_total = mode.num_trials + mode.num_trials_factor * mode.back ** mode.num_trials_exponent

    def initialize_session(self):
        self.session = {}
        self.session['position1'] = []
        self.session['position2'] = []
        self.session['position3'] = []
        self.session['position4'] = []
        self.session['vis1'] = []
        self.session['vis2'] = []
        self.session['vis3'] = []
        self.session['vis4'] = []
        self.session['color'] = []
        self.session['image'] = []
        self.session['audio'] = []
        self.session['audio2'] = []
        self.session['vis'] = []
        self.session['numbers'] = []
        self.session['operation'] = []
        
        self.session['position1_input'] = []
        self.session['position2_input'] = []
        self.session['position3_input'] = []
        self.session['position4_input'] = []
        self.session['vis1_input'] = []
        self.session['vis2_input'] = []
        self.session['vis3_input'] = []
        self.session['vis4_input'] = []
        self.session['visvis_input'] = []
        self.session['visaudio_input'] = []
        self.session['color_input'] = []
        self.session['audiovis_input'] = []
        self.session['image_input'] = []
        self.session['audio_input'] = []
        self.session['audio2_input'] = []
        self.session['arithmetic_input'] = []

        self.session['position1_rt'] = [] # reaction times
        self.session['position2_rt'] = [] 
        self.session['position3_rt'] = [] 
        self.session['position4_rt'] = [] 
        self.session['vis1_rt'] = []
        self.session['vis2_rt'] = []
        self.session['vis3_rt'] = []
        self.session['vis4_rt'] = []
        self.session['visvis_rt'] = []
        self.session['visaudio_rt'] = []
        self.session['color_rt'] = []
        self.session['audiovis_rt'] = []
        self.session['image_rt'] = []
        self.session['audio_rt'] = []
        self.session['audio2_rt'] = []
        #self.session['arithmetic_rt'] = []

    def save_input(self):
        for k, v in mode.current_stim.items():
            if k == 'number':
                self.session['numbers'].append(v)
            else:
                self.session[k].append(v)
            if k == 'vis': # goes to both self.session['vis'] and ['image']
                self.session['image'].append(v)
        for k, v in mode.inputs.items():
            self.session[k + '_input'].append(v)
        for k, v in mode.input_rts.items():
            self.session[k + '_rt'].append(v)

        self.session['operation'].append(mode.current_operation)
        self.session['arithmetic_input'].append(arithmeticAnswerLabel.parse_answer())
            

    def log_saccadic(self, start_time, elapsed_time, counter):
        if param.ATTEMPT_TO_SAVE_STATS and config.cfg.SACCADIC_LOGGING:
            try:
                statsfile_path = os.path.join(get_data_dir(), config.cfg.STATSFILE)
                statsfile = open(statsfile_path, 'a')
                statsfile.write("# Saccadic session at %s for %i seconds and %i saccades\n" % 
                                (strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
                                 int(elapsed_time), 
                                 counter))
                statsfile.close()
            except:
                pass
    
    def submit_session(self, percent, category_percents):
        global musicplayer
        global applauseplayer
        self.history.append([mode.session_number, mode.mode, mode.back, percent, mode.manual])
        
        if param.ATTEMPT_TO_SAVE_STATS:
            try:
                sep = param.STATS_SEPARATOR
                statsfile_path = os.path.join(get_data_dir(), config.cfg.STATSFILE)
                statsfile = open(statsfile_path, 'a')
                outlist = [strftime("%Y-%m-%d %H:%M:%S"),
                           mode.short_name(),
                           str(percent),
                           str(mode.mode),
                           str(mode.back),
                           str(mode.ticks_per_trial),
                           str(mode.num_trials_total),
                           str(int(mode.manual)),
                           str(mode.session_number),
                           str(category_percents['position1']),
                           str(category_percents['audio']),
                           str(category_percents['color']),
                           str(category_percents['visvis']),
                           str(category_percents['audiovis']),
                           str(category_percents['arithmetic']),
                           str(category_percents['image']),
                           str(category_percents['visaudio']),
                           str(category_percents['audio2']),
                           str(category_percents['position2']),
                           str(category_percents['position3']),
                           str(category_percents['position4']),
                           str(category_percents['vis1']),
                           str(category_percents['vis2']),
                           str(category_percents['vis3']),
                           str(category_percents['vis4']),
                           str(mode.ticks_per_trial * param.TICK_DURATION * mode.num_trials_total),
                           str(0),
                           ]
                statsfile.write(sep.join(outlist)) # adds sep between each element
                statsfile.write('\n')  # but we don't want a sep before '\n'
                statsfile.close()
                if param.CLINICAL_MODE:
                    picklefile = open(os.path.join(get_data_dir(), param.STATS_BINARY), 'ab')
                    pickle.dump([strftime("%Y-%m-%d %H:%M:%S"), mode.short_name(), 
                                 percent, mode.mode, mode.back, mode.ticks_per_trial,
                                 mode.num_trials_total, int(mode.manual),
                                 mode.session_number, category_percents['position1'],
                                 category_percents['audio'], category_percents['color'],
                                 category_percents['visvis'], category_percents['audiovis'],
                                 category_percents['arithmetic'], category_percents['image'],
                                 category_percents['visaudio'], category_percents['audio2'], 
                                 category_percents['position2'], category_percents['position3'],
                                 category_percents['position4'], 
                                 category_percents['vis1'], category_percents['vis2'], 
                                 category_percents['vis3'], category_percents['vis4']],
                                picklefile, protocol=2)
                    picklefile.close()
                config.cfg.SAVE_SESSIONS = True # FIXME: put this where it belongs
                config.cfg.SESSION_STATS = param.USER + '-sessions.dat' # FIXME: default user; configurability
                if config.cfg.SAVE_SESSIONS:
                    picklefile = open(os.path.join(get_data_dir(), config.cfg.SESSION_STATS), 'ab')
                    session = {} # it's not a dotdict because we want to pickle it
                    session['summary'] = outlist # that's what goes into stats.txt
                    session['cfg'] = config.cfg.__dict__
                    session['timestamp'] = strftime("%Y-%m-%d %H:%M:%S")
                    session['mode'] = mode.mode
                    session['n'] = mode.back
                    session['manual'] = mode.manual
                    session['trial_duration'] = mode.ticks_per_trial * param.TICK_DURATION
                    session['trials'] = mode.num_trials_total
                    session['session'] = self.session
                    pickle.dump(session, picklefile)
                    picklefile.close()
            except:
                quit_with_error(('Error writing to stats file\n%s') %
                                os.path.join(get_data_dir(), config.cfg.STATSFILE),
                                ('\nPlease check file and directory permissions.'))

        perfect = False        
        awesome = False
        great = False
        good = False
        advance = False
        fallback = False
        
        if not mode.manual:
            if percent >= config.get_threshold_advance():
                mode.back += 1
                mode.num_trials_total = mode.num_trials + mode.num_trials_factor * mode.back ** mode.num_trials_exponent
                mode.progress = 0
                circles.update()
                if config.cfg.USE_APPLAUSE:
                    #applauseplayer = pyglet.media.ManagedSoundPlayer()
                    applauseplayer.queue(random.choice(applausesounds))
                    applauseplayer.volume = config.cfg.APPLAUSE_VOLUME
                    applauseplayer.play()
                advance = True
            elif mode.back > 1 and percent < config.get_threshold_fallback():
                if config.cfg.JAEGGI_MODE:
                    mode.back -= 1
                    fallback = True
                else:
                    if mode.progress == config.cfg.THRESHOLD_FALLBACK_SESSIONS - 1:
                        mode.back -= 1
                        mode.num_trials_total = mode.num_trials + mode.num_trials_factor * mode.back ** mode.num_trials_exponent
                        fallback = True
                        mode.progress = 0
                        circles.update()
                    else:
                        mode.progress += 1
                        circles.update()
    
            if percent == 100: perfect = True
            elif percent >= config.get_threshold_advance(): awesome = True
            elif percent >= (config.get_threshold_advance() + config.get_threshold_fallback()) // 2: great = True
            elif percent >= config.get_threshold_fallback(): good = True
            congratsLabel.update(True, advance, fallback, awesome, great, good, perfect)
        
        if mode.manual and not config.cfg.USE_MUSIC_MANUAL:
            return
        
        if config.cfg.USE_MUSIC:
            musicplayer = pyglet.media.ManagedSoundPlayer()
            if percent >= config.get_threshold_advance() and resourcepaths['music']['advance']:
                musicplayer.queue(pyglet.media.load(random.choice(resourcepaths['music']['advance']), streaming = True))
            elif percent >= (config.get_threshold_advance() + config.get_threshold_fallback()) // 2 and resourcepaths['music']['great']:
                musicplayer.queue(pyglet.media.load(random.choice(resourcepaths['music']['great']), streaming = True))
            elif percent >= config.get_threshold_fallback() and resourcepaths['music']['good']:
                musicplayer.queue(pyglet.media.load(random.choice(resourcepaths['music']['good']), streaming = True))
            else: 
                return
            musicplayer.volume = config.cfg.MUSIC_VOLUME
            musicplayer.play()
        
    def clear(self):
        self.history = []
        self.sessions_today = 0
        self.time_today = 0
        self.sessions_thours = 0
        self.time_thours = 0
        
def update_all_labels(do_analysis=False):
    updateLabel.update()
    congratsLabel.update()
    if do_analysis:
        analysisLabel.update()
    else:
        analysisLabel.update(skip=True)
            
    pyglet.clock.tick(poll=True) # Prevent music/applause skipping 1

    gameModeLabel.update()
    keysListLabel.update()
    pausedLabel.update()
    sessionInfoLabel.update()
    thresholdLabel.update()
    spaceLabel.update()
    chartTitleLabel.update()
    chartLabel.update()
    
    pyglet.clock.tick(poll=True) # Prevent music/applause skipping 2
    
    averageLabel.update()
    todayLabel.update()
    trialsRemainingLabel.update()
   
    update_input_labels()
    
def update_input_labels():
    arithmeticAnswerLabel.update()
    for label in input_labels:
        label.update()

# this function handles initiation of a new session.
def new_session():
    mode.tick = -9  # give a 1-second delay before displaying first trial
    mode.tick -= 5 * (mode.flags[mode.mode]['multi'] - 1 )
    if config.cfg.MULTI_MODE == 'image':
        mode.tick -= 5 * (mode.flags[mode.mode]['multi'] - 1 )
        
    mode.session_number += 1
    mode.trial_number = 0
    mode.started = True
    mode.paused = False
    circles.update()
    
    mode.sound_mode  = random.choice(config.cfg.AUDIO1_SETS)
    mode.sound2_mode = random.choice(config.cfg.AUDIO2_SETS)
    
    visuals[0].load_set()
    visuals[0].choose_random_images(8)
    visuals[0].letters  = random.sample(sounds[mode.sound_mode ].keys(), 8)
    visuals[0].letters2 = random.sample(sounds[mode.sound2_mode].keys(), 8)    
    

    for i in range(1, mode.flags[mode.mode]['multi']):
        visuals[i].load_set(visuals[0].image_set_index)
        visuals[i].choose_indicated_images(visuals[0].image_indices)
        visuals[i].letters  = visuals[0].letters  # I don't think these are used for anything, but I'm not sure
        visuals[i].letters2 = visuals[0].letters2

    global input_labels
    input_labels.extend(generate_input_labels()) # have to do this after images are loaded
    

    mode.soundlist  = [sounds[mode.sound_mode][l]  for l in visuals[0].letters]
    mode.soundlist2 = [sounds[mode.sound2_mode][l] for l in visuals[0].letters2]
            
    if config.cfg.JAEGGI_MODE:
        compute_bt_sequence()
        
    pyglet.clock.tick(poll=True) # Prevent music/applause skipping
        
    if config.cfg.VARIABLE_NBACK:
        # compute variable n-back sequence using beta distribution
        mode.variable_list = []
        for index in range(0, mode.num_trials_total - mode.back):
            mode.variable_list.append(int(random.betavariate(mode.back / 2.0, 1) * mode.back + 1))
    field.crosshair_update()
    reset_input()
    stats.initialize_session()
    update_all_labels()
    pyglet.clock.schedule_interval(fade_out, 0.05)

# this function handles the finish or cancellation of a session.
def end_session(cancelled=False):
    for label in input_labels: 
        label.delete()
    while input_labels:
        input_labels.remove(input_labels[0])
    if cancelled:
        mode.session_number -= 1
    if not cancelled:
        stats.sessions_today += 1
    for visual in visuals: visual.hide()
    mode.started = False
    mode.paused = False
    circles.update()
    field.crosshair_update()
    reset_input()
    if cancelled:
        update_all_labels()
    else:
        update_all_labels(do_analysis = True)
        if config.cfg.PANHANDLE_FREQUENCY:
            statsfile_path = os.path.join(get_data_dir(), config.cfg.STATSFILE)
            statsfile = open(statsfile_path, 'r')
            sessions = len(statsfile.readlines()) # let's just hope people 
            statsfile.close()       # don't manually edit their statsfiles
            if (sessions % config.cfg.PANHANDLE_FREQUENCY) == 0 and not param.CLINICAL_MODE:
                Panhandle(n=sessions)
            
    
            
# this function causes the key labels along the bottom to revert to their
# "non-pressed" state for a new trial or when returning to the main screen.
def reset_input():
    for k in mode.inputs.keys():
        mode.inputs[k] = False
        mode.input_rts[k] = 0.
    arithmeticAnswerLabel.reset_input()
    update_input_labels()

# this handles the computation of a round with exactly 6 position and 6 audio matches
# this function is not currently used -- compute_bt_sequence() is used instead
##def new_compute_bt_sequence(matches=6, modalities=['audio', 'vis']):
##    # not ready for visaudio or audiovis, doesn't get 
##    seq = {}
##    for m in modalities:
##        seq[m] = [False]*mode.back + \
##                 random.shuffle([True]*matches + 
##                                [False]*(mode.num_trials_total - mode.back - matches))
##        for i in range(mode.back):
##            seq[m][i] = random.randint(1,8)
##
##        for i in range(mode.back, len(seq[m])):
##            if seq[m][i] == True:
##                seq[m][i] = seq[m][i-mode.back]
##            elif seq[m][i] == False:  # should be all other cases
##                seq[m][i] = random.randint(1,7)
##                if seq[m][i] >= seq[m][i-mode.back]:
##                    seq[m][i] += 1
##    mode.bt_sequence = seq.values()

def compute_bt_sequence():
    bt_sequence = []
    bt_sequence.append([])
    bt_sequence.append([])    
    for x in range(0, mode.num_trials_total):
        bt_sequence[0].append(0)
        bt_sequence[1].append(0)
    
    for x in range(0, mode.back):
        bt_sequence[0][x] = random.randint(1, 8)
        bt_sequence[1][x] = random.randint(1, 8)
        
    position = 0
    audio = 0
    both = 0
    
    # brute force it
    while True:
        position = 0
        for x in range(mode.back, mode.num_trials_total):
            bt_sequence[0][x] = random.randint(1, 8)
            if bt_sequence[0][x] == bt_sequence[0][x - mode.back]:
                position += 1
        if position != 6:
            continue
        while True:
            audio = 0
            for x in range(mode.back, mode.num_trials_total):
                bt_sequence[1][x] = random.randint(1, 8)
                if bt_sequence[1][x] == bt_sequence[1][x - mode.back]:
                    audio += 1
            if audio == 6:
                break
        both = 0
        for x in range(mode.back, mode.num_trials_total):
            if bt_sequence[0][x] == bt_sequence[0][x - mode.back] and bt_sequence[1][x] == bt_sequence[1][x - mode.back]:
                both += 1
        if both == 2:
            break
    
    mode.bt_sequence = bt_sequence
    
# responsible for the random generation of each new stimulus (audio, color, position)
def generate_stimulus():
    # first, randomly generate all stimuli
    positions = random.sample(range(1,9), 4)   # sample without replacement
    for s, p in zip(range(1, 5), positions):
        mode.current_stim['position' + `s`] = p
        mode.current_stim['vis' + `s`] = random.randint(1, 8)

    #mode.current_stim['position1'] = random.randint(1, 8)
    mode.current_stim['color'] = random.randint(1, 8)
    mode.current_stim['vis'] = random.randint(1, 8)
    mode.current_stim['audio'] = random.randint(1, 8)
    mode.current_stim['audio2'] = random.randint(1, 8)
    
    
    # treat arithmetic specially
    operations = []
    if config.cfg.ARITHMETIC_USE_ADDITION: operations.append('add')
    if config.cfg.ARITHMETIC_USE_SUBTRACTION: operations.append('subtract')
    if config.cfg.ARITHMETIC_USE_MULTIPLICATION: operations.append('multiply')
    if config.cfg.ARITHMETIC_USE_DIVISION: operations.append('divide')
    mode.current_operation = random.choice(operations)
    
    if config.cfg.ARITHMETIC_USE_NEGATIVES:
        min_number = 0 - config.cfg.ARITHMETIC_MAX_NUMBER
    else:
        min_number = 0
    max_number = config.cfg.ARITHMETIC_MAX_NUMBER
    
    if mode.current_operation == 'divide' and 'arithmetic' in mode.modalities[mode.mode]:
        if len(stats.session['position1']) >= mode.back:
            number_nback = stats.session['numbers'][mode.trial_number - mode.back - 1]
            possibilities = []
            for x in range(min_number, max_number + 1):
                if x == 0:
                    continue
                if number_nback % x == 0:
                    possibilities.append(x)
                    continue
                frac = Decimal(abs(number_nback)) / Decimal(abs(x))
                if (frac % 1) in map(Decimal, config.cfg.ARITHMETIC_ACCEPTABLE_DECIMALS):
                    possibilities.append(x)
            mode.current_stim['number'] = random.choice(possibilities)
        else:
            mode.current_stim['number'] = random.randint(min_number, max_number)
            while mode.current_stim['number'] == 0:
                mode.current_stim['number'] = random.randint(min_number, max_number)
    else:
        mode.current_stim['number'] = random.randint(min_number, max_number)
    
    multi = mode.flags[mode.mode]['multi']
    
    real_back = mode.back
    if mode.flags[mode.mode]['crab'] == 1:
        real_back = 1 + 2*((mode.trial_number-1) % mode.back)
    else:
        real_back = mode.back
    if config.cfg.VARIABLE_NBACK:
        real_back = mode.variable_list[mode.trial_number - real_back - 1]

    if mode.modalities[mode.mode] != ['arithmetic'] and mode.trial_number > mode.back:
        for mod in mode.modalities[mode.mode]:
            if   mod in ('visvis', 'visaudio', 'image'):
                current = 'vis'
            elif mod in ('audiovis', ):
                current = 'audio'
            elif mod == 'arithmetic':
                continue
            else:
                current = mod
            if   mod in ('visvis', 'audiovis', 'image'):
                back_data = 'vis'
            elif mod in ('visaudio', ):
                back_data = 'audio'
            else:
                back_data = mod

            back = None
            r1, r2 = random.random(), random.random()
            if multi > 1: 
                r2 = 3./2. * r2 # 33% chance of multi-stim reversal

            if  (r1 < config.cfg.CHANCE_OF_GUARANTEED_MATCH):
                back = real_back

            elif r2 < config.cfg.CHANCE_OF_INTERFERENCE and mode.back > 1:
                back = real_back
                interference = [-1, 1, mode.back]
                if back < 3: interference = interference[1:] # for crab mode and 2-back
                random.shuffle(interference)
                for i in interference: # we'll just take the last one that works.
                    if mode.trial_number - (real_back+i) - 1 >= 0 and \
                         stats.session[back_data][mode.trial_number - (real_back+i) - 1] != \
                         stats.session[back_data][mode.trial_number -  real_back    - 1]:
                        back = real_back + i
                if back == real_back: back = None # if none of the above worked
                elif param.DEBUG:
                    print 'Forcing interference for %s' % current
            
            if back:            
                nback_trial = mode.trial_number - back - 1
                matching_stim = stats.session[back_data][nback_trial]
                # check for collisions in multi-stim mode
                if multi > 1 and mod.startswith('position'): 
                    potential_conflicts = set(range(1, multi+1)) - set([int(mod[-1])])
                    conflict_positions = [positions[i-1] for i in potential_conflicts]
                    if matching_stim in conflict_positions: # swap 'em
                        i = positions.index(matching_stim)
                        if param.DEBUG:
                            print "moving position%i from %i to %i for %s" % (i+1, positions[i], mode.current_stim[current], current)
                        mode.current_stim['position' + `i+1`] = mode.current_stim[current]
                        positions[i] = mode.current_stim[current]
                    positions[int(current[-1])-1] = matching_stim
                if param.DEBUG:
                    print "setting %s to %i" % (current, matching_stim)
                mode.current_stim[current] = matching_stim

        if multi > 1:
            if random.random() < config.cfg.CHANCE_OF_INTERFERENCE / 3.:
                mod = 'position'
                if 'vis1' in mode.modalities[mode.mode] and random.random() < .5:
                    mod = 'vis'
                offset = random.choice(range(1, multi))
                for i in range(multi):
                    mode.current_stim[mod + `i+1`] = stats.session[mod + `((i+offset)%multi) + 1`][mode.trial_number - real_back - 1]
                    if mod == 'position':
                        positions[i] = mode.current_stim[mod + `i+1`]

        
    # set static stimuli according to mode.
    # default position is 0 (center)
    # default color is 1 (red) or 2 (black)
    # default vis is 0 (square)
    # audio is never static so it doesn't have a default.
    if not 'color'     in mode.modalities[mode.mode]: mode.current_stim['color'] = config.cfg.VISUAL_COLORS[0]
    if not 'position1' in mode.modalities[mode.mode]: mode.current_stim['position1'] = 0
    if not set(['visvis', 'arithmetic', 'image']).intersection( mode.modalities[mode.mode] ):
        mode.current_stim['vis'] = 0
    if multi > 1 and not 'vis1' in mode.modalities[mode.mode]:
        for i in range(1, 5):
            if config.cfg.MULTI_MODE == 'color':
                mode.current_stim['vis'+`i`] = 0 # use squares
            elif config.cfg.MULTI_MODE == 'image':
                mode.current_stim['vis'+`i`] = config.cfg.VISUAL_COLORS[0]
        
    # in jaeggi mode, set using the predetermined sequence.
    if config.cfg.JAEGGI_MODE:
        mode.current_stim['position1'] = mode.bt_sequence[0][mode.trial_number - 1]
        mode.current_stim['audio'] = mode.bt_sequence[1][mode.trial_number - 1]
    
    # initiate the chosen stimuli.
    # mode.current_stim['audio'] is a number from 1 to 8.
    if 'arithmetic' in mode.modalities[mode.mode] and mode.trial_number > mode.back:
        player = pyglet.media.Player()
        player.queue(sounds['operations'][mode.current_operation])  # maybe we should try... catch... here
        player.play()                                               # and maybe we should recycle sound players...
    elif 'audio' in mode.modalities[mode.mode] and not 'audio2' in mode.modalities[mode.mode]:
        player = pyglet.media.Player()
        player.queue(mode.soundlist[mode.current_stim['audio']-1])
        player.play()
    elif 'audio2' in mode.modalities[mode.mode]:
        # dual audio modes - two sound players
        player = pyglet.media.Player()
        player.queue(mode.soundlist[mode.current_stim['audio']-1])
        player.min_distance = 100.0
        if config.cfg.CHANNEL_AUDIO1 == 'left':
            player.position = (-99.0, 0.0, 0.0)
        elif config.cfg.CHANNEL_AUDIO1 == 'right':
            player.position = (99.0, 0.0, 0.0)
        elif config.cfg.CHANNEL_AUDIO1 == 'center':
            #player.position = (0.0, 0.0, 0.0)
            pass
        player.play()
        
        player2 = pyglet.media.Player()
        player2.queue(mode.soundlist2[mode.current_stim['audio2']-1])
        player2.min_distance = 100.0
        if config.cfg.CHANNEL_AUDIO2 == 'left':
            player2.position = (-99.0, 0.0, 0.0)
        elif config.cfg.CHANNEL_AUDIO2 == 'right':
            player2.position = (99.0, 0.0, 0.0)
        elif config.cfg.CHANNEL_AUDIO2 == 'center':
            #player2.position = (0.0, 0.0, 0.0)
            pass
        player2.play()
        
            
    if config.cfg.VARIABLE_NBACK and mode.trial_number > mode.back:
        variable = mode.variable_list[mode.trial_number - 1 - mode.back]
    else:
        variable = 0
    if param.DEBUG and multi < 2:
        print "trial=%i, \tpos=%i, \taud=%i, \tcol=%i, \tvis=%i, \tnum=%i,\top=%s, \tvar=%i" % \
                (mode.trial_number, mode.current_stim['position1'], mode.current_stim['audio'], 
                 mode.current_stim['color'], mode.current_stim['vis'], \
                 mode.current_stim['number'], mode.current_operation, variable)
    if multi == 1:
        visuals[0].spawn(mode.current_stim['position1'], mode.current_stim['color'], 
                         mode.current_stim['vis'], mode.current_stim['number'], 
                         mode.current_operation, variable)
    else: # multi > 1
        for i in range(1, multi+1):
            if config.cfg.MULTI_MODE == 'color':
                if param.DEBUG:
                    print "trial=%i, \tpos=%i, \taud=%i, \tcol=%i, \tvis=%i, \tnum=%i,\top=%s, \tvar=%i" % \
                        (mode.trial_number, mode.current_stim['position' + `i`], mode.current_stim['audio'], 
                        config.cfg.VISUAL_COLORS[i-1], mode.current_stim['vis'+`i`], \
                        mode.current_stim['number'], mode.current_operation, variable)
                visuals[i-1].spawn(mode.current_stim['position'+`i`], config.cfg.VISUAL_COLORS[i-1],
                                   mode.current_stim['vis'+`i`], mode.current_stim['number'], 
                                   mode.current_operation, variable)
            else:
                if param.DEBUG:
                    print "trial=%i, \tpos=%i, \taud=%i, \tcol=%i, \tvis=%i, \tnum=%i,\top=%s, \tvar=%i" % \
                        (mode.trial_number, mode.current_stim['position' + `i`], mode.current_stim['audio'], 
                        mode.current_stim['vis'+`i`], i, \
                        mode.current_stim['number'], mode.current_operation, variable)
                visuals[i-1].spawn(mode.current_stim['position'+`i`], mode.current_stim['vis'+`i`], 
                                   i,                            mode.current_stim['number'], 
                                   mode.current_operation, variable)
                
def toggle_manual_mode():
    if mode.manual:
        mode.manual = False
    else:
        mode.manual = True
    
    #if not mode.manual:
        #mode.enforce_standard_mode()
        
    update_all_labels()

def set_user(newuser):
    param.USER = newuser
    if param.USER.lower() == 'default':
        param.CONFIGFILE = 'config.ini'
    else:
        param.CONFIGFILE = param.USER + '-config.ini'
    config.rewrite_configfile(param.CONFIGFILE, overwrite=False)
    config.cfg = config.parse_config(param.CONFIGFILE)
    stats.initialize_session()
    stats.parse_statsfile()
    if len(stats.full_history) > 0 and not config.cfg.JAEGGI_MODE:
        mode.mode = stats.full_history[-1][1]
    stats.retrieve_progress()
    # text labels also need to be remade; until that's done, this remains commented out
    #if config.cfg.BLACK_BACKGROUND:
    #    glClearColor(0, 0, 0, 1)
    #else:
    #    glClearColor(1, 1, 1, 1)
    window.set_fullscreen(config.cfg.WINDOW_FULLSCREEN) # window size needs to be changed
    update_all_labels()
    save_last_user('defaults.ini')


def get_users():
    users = ['default'] + [fn.split('-')[0] for fn in os.listdir(get_data_dir()) if '-stats.txt' in fn]
    if 'Readme' in users: users.remove('Readme')
    return users

# there are 4 event loops:
#   on_mouse_press: allows the user to use the mouse (LMB and RMB) instead of keys
#   on_key_press:   listens to the keyboard and acts when certain keys are pressed
#   on_draw:        draws everything to the screen something like 60 times per second
#   update(dt):     the session timer loop which controls the game during the sessions.
#                   Runs once every quarter-second.
#
# --- BEGIN EVENT LOOP SECTION ----------------------------------------------
#

# this is where the keyboard keys are defined.
@window.event
def on_mouse_press(x, y, button, modifiers):
    Flag = True
    if mode.started:
        if len(mode.modalities[mode.mode])==2:
            for k in mode.modalities[mode.mode]:
                if k == 'arithmetic':
                    Flag = False
            if Flag:
                if (button == pyglet.window.mouse.LEFT):
                    mode.inputs[mode.modalities[mode.mode][0]] = True
                elif (button == pyglet.window.mouse.RIGHT):
                    mode.inputs[mode.modalities[mode.mode][1]] = True
                update_input_labels()

@window.event
def on_key_press(symbol, modifiers):    
    if symbol == key.D and (modifiers & key.MOD_CTRL):
        dump_pyglet_info()
        
    elif mode.title_screen and not mode.draw_graph:
        if symbol == key.ESCAPE or symbol == key.X:
            window.on_close()
            
        elif symbol == key.SPACE:
            mode.title_screen = False
            #mode.shrink_brain = True
            #pyglet.clock.schedule_interval(shrink_brain, 1/60.)
            
        elif symbol == key.C and not config.cfg.JAEGGI_MODE:
            GameSelect()
                                    
        elif symbol == key.I and not config.cfg.JAEGGI_MODE:
            ImageSelect()

        elif symbol == key.H:
            webbrowser.open_new_tab(param.WEB_TUTORIAL)
                
        elif symbol == key.D and not param.CLINICAL_MODE:
            webbrowser.open_new_tab(param.WEB_DONATE)
            
        elif symbol == key.V and param.DEBUG:
            OptionsScreen()

        elif symbol == key.G:
#            sound_stop()
            graph.parse_stats()
            graph.graph = mode.mode
            mode.draw_graph = True
            
        elif symbol == key.U: 
            UserScreen()
            
        elif symbol == key.L:
            LanguageScreen()
                
        elif symbol == key.S and not config.cfg.JAEGGI_MODE:
            SoundSelect()
            
        elif symbol == key.F:
            webbrowser.open_new_tab(param.WEB_FORUM)
        
        elif symbol == key.O:
            edit_config_ini()

    elif mode.draw_graph:
        if symbol == key.ESCAPE or symbol == key.G or symbol == key.X:
            mode.draw_graph = False
            
        #elif symbol == key.E and (modifiers & key.MOD_CTRL):
            #graph.export_data()

        elif symbol == key.N:
            graph.next_nonempty_mode()
            
        elif symbol == key.M:
            graph.next_style()
                                                    
    elif mode.saccadic:
        if symbol in (key.ESCAPE, key.E, key.X, key.SPACE):
            saccadic.stop()
            
    elif not mode.started:
        
        if symbol == key.ESCAPE or symbol == key.X:
            if config.cfg.SKIP_TITLE_SCREEN:
                window.on_close()
            else:
                mode.title_screen = True
        
        elif symbol == key.SPACE:
            new_session()
                        
        elif param.CLINICAL_MODE:
            pass
            #if symbol == key.H:
                #webbrowser.open_new_tab(CLINICAL_TUTORIAL)
        # No elifs below this line at this indentation will be 
        # executed in CLINICAL_MODE
        
        elif symbol == key.E and config.cfg.WINDOW_FULLSCREEN:
            saccadic.start()
        
        elif symbol == key.G:
#            sound_stop()
            graph.parse_stats()
            graph.graph = mode.mode
            mode.draw_graph = True

        elif symbol == key.F1 and mode.manual:
            if mode.back > 1:
                mode.back -= 1
                gameModeLabel.flash()
                spaceLabel.update()
                sessionInfoLabel.update()
                
        elif symbol == key.F2 and mode.manual:
            mode.back += 1
            gameModeLabel.flash()
            spaceLabel.update()
            sessionInfoLabel.update()

        elif symbol == key.F3 and mode.num_trials > 5 and mode.manual:
            mode.num_trials -= 5
            mode.num_trials_total = mode.num_trials + mode.num_trials_factor * \
                mode.back ** mode.num_trials_exponent
            sessionInfoLabel.flash()

        elif symbol == key.F4 and mode.manual:
            mode.num_trials += 5
            mode.num_trials_total = mode.num_trials + mode.num_trials_factor * \
                mode.back ** mode.num_trials_exponent
            sessionInfoLabel.flash()            
            
        elif symbol == key.F5 and mode.manual:
            if mode.ticks_per_trial < param.TICKS_MAX:
                mode.ticks_per_trial += 1
                sessionInfoLabel.flash()
                        
        elif symbol == key.F6 and mode.manual:
            if mode.ticks_per_trial > param.TICKS_MIN:
                mode.ticks_per_trial -= 1
                sessionInfoLabel.flash()
                
        elif symbol == key.C and (modifiers & key.MOD_CTRL):
            stats.clear()
            chartLabel.update()
            averageLabel.update()
            todayLabel.update()
            mode.progress = 0
            circles.update()

        elif symbol == key.C:
            if config.cfg.JAEGGI_MODE:
                jaeggiWarningLabel.show()
                return
            GameSelect()
        
        elif symbol == key.U: 
            UserScreen()
            
        elif symbol == key.I:
            if config.cfg.JAEGGI_MODE:
                jaeggiWarningLabel.show()
                return
            ImageSelect()

        elif symbol == key.S:
            if config.cfg.JAEGGI_MODE:
                jaeggiWarningLabel.show()
                return
            SoundSelect()
            
        elif symbol == key.W:
            webbrowser.open_new_tab(param.WEB_SITE)
            if update_available:
                window.on_close()
            
        elif symbol == key.M:
            toggle_manual_mode()
            update_all_labels()
            mode.progress = 0
            circles.update()

        elif symbol == key.H:
            webbrowser.open_new_tab(param.WEB_TUTORIAL)
                        
        elif symbol == key.D and not param.CLINICAL_MODE:
            webbrowser.open_new_tab(param.WEB_DONATE)

        elif symbol == key.J and 'morse' in config.cfg.AUDIO1_SETS or 'morse' in config.cfg.AUDIO2_SETS:
            webbrowser.open_new_tab(param.WEB_MORSE)
                            
                        
    # these are the keys during a running session.
    elif mode.started:            
        if (symbol == key.ESCAPE or symbol == key.X) and not param.CLINICAL_MODE:
            end_session(cancelled = True)
            
        elif symbol == key.P and not param.CLINICAL_MODE:
            mode.paused = not mode.paused
            pausedLabel.update()
            field.crosshair_update()
                
        elif symbol == key.F8 and not param.CLINICAL_MODE:
            mode.hide_text = not mode.hide_text
            update_all_labels()
                
        elif mode.tick != 0 and mode.trial_number > 0:
            if 'arithmetic' in mode.modalities[mode.mode]:
                if symbol == key.BACKSPACE or symbol == key.DELETE:
                    arithmeticAnswerLabel.reset_input()
                elif symbol == key.MINUS or symbol == key.NUM_SUBTRACT:
                    arithmeticAnswerLabel.input('-')
                elif symbol == key.PERIOD or symbol == key.NUM_DECIMAL:
                    arithmeticAnswerLabel.input('.')
                elif symbol == key._0 or symbol == key.NUM_0:
                    arithmeticAnswerLabel.input('0')
                elif symbol == key._1 or symbol == key.NUM_1:
                    arithmeticAnswerLabel.input('1')
                elif symbol == key._2 or symbol == key.NUM_2:
                    arithmeticAnswerLabel.input('2')
                elif symbol == key._3 or symbol == key.NUM_3:
                    arithmeticAnswerLabel.input('3')
                elif symbol == key._4 or symbol == key.NUM_4:
                    arithmeticAnswerLabel.input('4')
                elif symbol == key._5 or symbol == key.NUM_5:
                    arithmeticAnswerLabel.input('5')
                elif symbol == key._6 or symbol == key.NUM_6:
                    arithmeticAnswerLabel.input('6')
                elif symbol == key._7 or symbol == key.NUM_7:
                    arithmeticAnswerLabel.input('7')
                elif symbol == key._8 or symbol == key.NUM_8:
                    arithmeticAnswerLabel.input('8')
                elif symbol == key._9 or symbol == key.NUM_9:
                    arithmeticAnswerLabel.input('9')
                    
            
            for k in mode.modalities[mode.mode]:
                if not k == 'arithmetic':
                    keycode = config.cfg['KEY_%s' % k.upper()]
                    if symbol == keycode:
                        mode.inputs[k] = True
                        mode.input_rts[k] = time.time() - mode.trial_starttime
                        update_input_labels()
        
        if symbol == config.cfg.KEY_ADVANCE and mode.flags[mode.mode]['selfpaced']:
            mode.tick = mode.ticks_per_trial-5

    return pyglet.event.EVENT_HANDLED
# the loop where everything is drawn on the screen.
@window.event
def on_draw():
    if mode.shrink_brain:
        return
    window.clear()
    if mode.draw_graph:
        graph.draw()
    elif mode.saccadic:
        saccadic.draw()
    elif mode.title_screen:
        brain_graphic.draw()
        titleMessageLabel.draw()
        titleKeysLabel.draw()
    else:
        batch.draw()
        if not mode.started and not param.CLINICAL_MODE:
            brain_icon.draw()
            logoUpperLabel.draw()
            logoLowerLabel.draw()
    for label in input_labels: 
        label.draw()

# the event timer loop. Runs every 1/10 second. This loop controls the session
# game logic.
# During each trial the tick goes from 1 to ticks_per_trial-1 then back to 0.
# tick = 1: Input from the last trial is saved. Input is reset.
#             A new square appears and the sound cue plays. 
# tick = 6: the square disappears.
# tick = ticks_per_trial - 1: tick is reset to 0.
# tick = 1: etc.
def update(dt):
    if mode.started and not mode.paused: # only run the timer during a game
        if not mode.flags[mode.mode]['selfpaced'] or \
                mode.tick > mode.ticks_per_trial-6 or \
                mode.tick < 5:
            mode.tick += 1
        if mode.tick == 1:
            mode.show_missed = False
            if mode.trial_number > 0:
                stats.save_input()
            mode.trial_number += 1
            mode.trial_starttime = time.time()
            trialsRemainingLabel.update()
            if mode.trial_number > mode.num_trials_total:
                end_session()
            else: generate_stimulus()
            reset_input()
        # Hide square at either the 0.5 second mark or sooner
        positions = len([mod for mod in mode.modalities[mode.mode] if mod.startswith('position')])
        positions = max(0, positions-1)
        if mode.tick == (6+positions) or mode.tick >= mode.ticks_per_trial - 2:
            for visual in visuals: visual.hide()
        if mode.tick == mode.ticks_per_trial - 2:  # display feedback for 200 ms
            mode.tick = 0
            mode.show_missed = True
            update_input_labels()
        if mode.tick == mode.ticks_per_trial:
            mode.tick = 0
pyglet.clock.schedule_interval(update, param.TICK_DURATION)

angle = 0
def pulsate(dt):
    global angle
    if mode.started: return
    if not window.visible: return
    angle += 15
    if angle == 360:
        angle = 0
    r = 0
    g = 0
    b = 191 + min(64, int(80 * math.cos(math.radians(angle))))
    spaceLabel.label.color = (r, g, b, 255)
#pyglet.clock.schedule_interval(pulsate, 1/20.)
        
#
# --- END EVENT LOOP SECTION ----------------------------------------------
#


batch = pyglet.graphics.Batch()

try: 
    test_polygon = batch.add(4, GL_QUADS, None, ('v2i', (
        100, 100,
        100, 200,
        200, 200,
        200, 100)),
              ('c3B', (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)))
    test_polygon.delete()
except:
    quit_with_error('Error creating test polygon. Full text of error:\n')

# Instantiate the classes
mode = Mode()
field = Field()
visuals = [Visual() for i in range(4)]
stats = Stats()
graph = Graph(window, mode)
circles = Circles()
saccadic = Saccadic()

updateLabel = UpdateLabel()
gameModeLabel = GameModeLabel()
jaeggiWarningLabel = JaeggiWarningLabel()
keysListLabel = KeysListLabel()
logoUpperLabel = LogoUpperLabel()
logoLowerLabel = LogoLowerLabel()
titleMessageLabel = TitleMessageLabel()
titleKeysLabel = TitleKeysLabel()
pausedLabel = PausedLabel()
congratsLabel = CongratsLabel()
sessionInfoLabel = SessionInfoLabel()
thresholdLabel = ThresholdLabel()
spaceLabel = SpaceLabel()
analysisLabel = AnalysisLabel()
chartTitleLabel = ChartTitleLabel()
chartLabel = ChartLabel()
averageLabel = AverageLabel()
todayLabel = TodayLabel()
trialsRemainingLabel = TrialsRemainingLabel()

arithmeticAnswerLabel = ArithmeticAnswerLabel()
input_labels = []


# load last game mode
stats.initialize_session()
stats.parse_statsfile()
if len(stats.full_history) > 0 and not config.cfg.JAEGGI_MODE:
    mode.mode = stats.full_history[-1][1]
stats.retrieve_progress()

update_all_labels()

# Initialize brain sprite
brain_icon = pyglet.sprite.Sprite(pyglet.image.load(random.choice(resourcepaths['misc']['brain'])))
brain_icon.set_position(field.center_x - brain_icon.width//2,
                           field.center_y - brain_icon.height//2)
if config.cfg.BLACK_BACKGROUND:
    brain_graphic = pyglet.sprite.Sprite(pyglet.image.load(random.choice(resourcepaths['misc']['splash-black'])))
else:
    brain_graphic = pyglet.sprite.Sprite(pyglet.image.load(random.choice(resourcepaths['misc']['splash'])))
brain_graphic.set_position(field.center_x - brain_graphic.width//2,
                           field.center_y - brain_graphic.height//2 + 40)

def shrink_brain(dt):
    brain_graphic.scale -= dt * 2
    brain_graphic.x = field.center_x - brain_graphic.image.width//2  + 2 + (brain_graphic.image.width - brain_graphic.width) // 2
    brain_graphic.y = field.center_y - brain_graphic.image.height//2 - 1 + (brain_graphic.image.height - brain_graphic.height) // 2
    window.clear()
    brain_graphic.draw()
    if brain_graphic.width < 56:
        mode.shrink_brain = False
        pyglet.clock.unschedule(shrink_brain)
        brain_graphic.scale = 1
        brain_graphic.set_position(field.center_x - brain_graphic.width//2,
                           field.center_y - brain_graphic.height//2 + 40)
        

# If we had messages queued during loading (like from moving our data files), display them now
messagequeue.reverse()
for msg in messagequeue:
    Message(msg)

# start the event loops!
if __name__ == '__main__':

    pyglet.app.run()

# nothing below the line "pyglet.app.run()" will be executed until the
# window is closed or ESC is pressed.

