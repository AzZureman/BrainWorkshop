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
import utils
import modes as md
import window as wnd
import messages as msg
import resource as res
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
    print (cmd + ' "' + os.path.join(utils.get_data_dir(), param.CONFIGFILE) + '"')
    wnd.window.on_close()
    import subprocess
    subprocess.call((cmd + ' "' + os.path.join(utils.get_data_dir(), param.CONFIGFILE) + '"'), shell=True)
    sys.exit(0)


def dump_pyglet_info():
    from pyglet import info
    sys.stdout = open(os.path.join(utils.get_data_dir(), 'dump.txt'), 'w')
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

 
def check_and_move_user_data():
    if not '--datadir' in sys.argv and \
      (not os.path.exists(utils.get_data_dir()) or len(os.listdir(utils.get_data_dir())) < 1):
        import shutil
        shutil.copytree(utils.get_old_data_dir(), utils.get_data_dir())
        if len(os.listdir(utils.get_old_data_dir())) > 2:
            msg.Message(
"""Starting with version 4.8.2, Brain Workshop stores its user profiles \
(statistics and configuration data) in "%s", rather than the old location, "%s". \
Your configuration data has been copied to the new location. The files in the \
old location have not been deleted. If you want to edit your config.ini, \
make sure you look in "%s".

Press space to continue.""" % (utils.get_data_dir(),  utils.get_old_data_dir(),  utils.get_data_dir()))


def load_last_user(lastuserpath):
    if os.path.isfile(os.path.join(utils.get_data_dir(), lastuserpath)):
        f = file(os.path.join(utils.get_data_dir(), lastuserpath), 'r')
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
        f = file(os.path.join(utils.get_data_dir(), lastuserpath), 'w')
        p = pickle.Pickler(f)
        p.dump({'USER': param.USER})
        # also do date of last session?
    except:
        pass


check_and_move_user_data()
load_last_user('defaults.ini')



        
# Initialize resources (sounds and images)
#
# --- BEGIN RESOURCE INITIALIZATION SECTION ----------------------------------
#

#
# --- END RESOURCE INITIALIZATION SECTION ----------------------------------
#
    
    




    

# What follows are the classes which control all the text and graphics.
#
# --- BEGIN GRAPHICS SECTION ----------------------------------------------
#

        

#
# --- END GRAPHICS SECTION ----------------------------------------------
#


# this function handles initiation of a new session.
def new_session():
    md.mode.tick = -9  # give a 1-second delay before displaying first trial
    md.mode.tick -= 5 * (md.mode.flags[md.mode.mode]['multi'] - 1 )
    if config.cfg.MULTI_MODE == 'image':
        md.mode.tick -= 5 * (md.mode.flags[md.mode.mode]['multi'] - 1 )
        
    md.mode.session_number += 1
    md.mode.trial_number = 0
    md.mode.started = True
    md.mode.paused = False
    circles.update()
    
    md.mode.sound_mode  = random.choice(config.cfg.AUDIO1_SETS)
    md.mode.sound2_mode = random.choice(config.cfg.AUDIO2_SETS)
    
    visuals[0].load_set()
    visuals[0].choose_random_images(8)
    visuals[0].letters  = random.sample(res.sounds[md.mode.sound_mode ].keys(), 8)
    visuals[0].letters2 = random.sample(res.sounds[md.mode.sound2_mode].keys(), 8)
    

    for i in range(1, md.mode.flags[md.mode.mode]['multi']):
        visuals[i].load_set(visuals[0].image_set_index)
        visuals[i].choose_indicated_images(visuals[0].image_indices)
        visuals[i].letters  = visuals[0].letters  # I don't think these are used for anything, but I'm not sure
        visuals[i].letters2 = visuals[0].letters2

    global input_labels
    input_labels.extend(generate_input_labels()) # have to do this after images are loaded
    

    md.mode.soundlist  = [res.sounds[md.mode.sound_mode][l]  for l in visuals[0].letters]
    md.mode.soundlist2 = [res.sounds[md.mode.sound2_mode][l] for l in visuals[0].letters2]
            
    if config.cfg.JAEGGI_MODE:
        compute_bt_sequence()
        
    pyglet.clock.tick(poll=True) # Prevent music/applause skipping
        
    if config.cfg.VARIABLE_NBACK:
        # compute variable n-back sequence using beta distribution
        md.mode.variable_list = []
        for index in range(0, md.mode.num_trials_total - md.mode.back):
            md.mode.variable_list.append(int(random.betavariate(md.mode.back / 2.0, 1) * md.mode.back + 1))
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
        md.mode.session_number -= 1
    if not cancelled:
        stats.sessions_today += 1
    for visual in visuals: visual.hide()
    md.mode.started = False
    md.mode.paused = False
    circles.update()
    field.crosshair_update()
    reset_input()
    if cancelled:
        update_all_labels()
    else:
        update_all_labels(do_analysis = True)
        if config.cfg.PANHANDLE_FREQUENCY:
            statsfile_path = os.path.join(utils.get_data_dir(), config.cfg.STATSFILE)
            statsfile = open(statsfile_path, 'r')
            sessions = len(statsfile.readlines()) # let's just hope people 
            statsfile.close()       # don't manually edit their statsfiles
            if (sessions % config.cfg.PANHANDLE_FREQUENCY) == 0 and not param.CLINICAL_MODE:
                Panhandle(n=sessions)
            
    
            
# this function causes the key labels along the bottom to revert to their
# "non-pressed" state for a new trial or when returning to the main screen.
def reset_input():
    for k in md.mode.inputs.keys():
        md.mode.inputs[k] = False
        md.mode.input_rts[k] = 0.
    arithmeticAnswerLabel.reset_input()
    update_input_labels()

# this handles the computation of a round with exactly 6 position and 6 audio matches
# this function is not currently used -- compute_bt_sequence() is used instead
##def new_compute_bt_sequence(matches=6, modalities=['audio', 'vis']):
##    # not ready for visaudio or audiovis, doesn't get 
##    seq = {}
##    for m in modalities:
##        seq[m] = [False]*md.mode.back + \
##                 random.shuffle([True]*matches + 
##                                [False]*(md.mode.num_trials_total - md.mode.back - matches))
##        for i in range(md.mode.back):
##            seq[m][i] = random.randint(1,8)
##
##        for i in range(md.mode.back, len(seq[m])):
##            if seq[m][i] == True:
##                seq[m][i] = seq[m][i-md.mode.back]
##            elif seq[m][i] == False:  # should be all other cases
##                seq[m][i] = random.randint(1,7)
##                if seq[m][i] >= seq[m][i-md.mode.back]:
##                    seq[m][i] += 1
##    md.mode.bt_sequence = seq.values()


def compute_bt_sequence():
    bt_sequence = []
    bt_sequence.append([])
    bt_sequence.append([])    
    for x in range(0, md.mode.num_trials_total):
        bt_sequence[0].append(0)
        bt_sequence[1].append(0)
    
    for x in range(0, md.mode.back):
        bt_sequence[0][x] = random.randint(1, 8)
        bt_sequence[1][x] = random.randint(1, 8)
        
    position = 0
    audio = 0
    both = 0
    
    # brute force it
    while True:
        position = 0
        for x in range(md.mode.back, md.mode.num_trials_total):
            bt_sequence[0][x] = random.randint(1, 8)
            if bt_sequence[0][x] == bt_sequence[0][x - md.mode.back]:
                position += 1
        if position != 6:
            continue
        while True:
            audio = 0
            for x in range(md.mode.back, md.mode.num_trials_total):
                bt_sequence[1][x] = random.randint(1, 8)
                if bt_sequence[1][x] == bt_sequence[1][x - md.mode.back]:
                    audio += 1
            if audio == 6:
                break
        both = 0
        for x in range(md.mode.back, md.mode.num_trials_total):
            if bt_sequence[0][x] == bt_sequence[0][x - md.mode.back] and bt_sequence[1][x] == bt_sequence[1][x - md.mode.back]:
                both += 1
        if both == 2:
            break
    
    md.mode.bt_sequence = bt_sequence


# responsible for the random generation of each new stimulus (audio, color, position)
def generate_stimulus():
    # first, randomly generate all stimuli
    positions = random.sample(range(1,9), 4)   # sample without replacement
    for s, p in zip(range(1, 5), positions):
        md.mode.current_stim['position' + `s`] = p
        md.mode.current_stim['vis' + `s`] = random.randint(1, 8)

    #md.mode.current_stim['position1'] = random.randint(1, 8)
    md.mode.current_stim['color'] = random.randint(1, 8)
    md.mode.current_stim['vis'] = random.randint(1, 8)
    md.mode.current_stim['audio'] = random.randint(1, 8)
    md.mode.current_stim['audio2'] = random.randint(1, 8)
    
    
    # treat arithmetic specially
    operations = []
    if config.cfg.ARITHMETIC_USE_ADDITION: operations.append('add')
    if config.cfg.ARITHMETIC_USE_SUBTRACTION: operations.append('subtract')
    if config.cfg.ARITHMETIC_USE_MULTIPLICATION: operations.append('multiply')
    if config.cfg.ARITHMETIC_USE_DIVISION: operations.append('divide')
    md.mode.current_operation = random.choice(operations)
    
    if config.cfg.ARITHMETIC_USE_NEGATIVES:
        min_number = 0 - config.cfg.ARITHMETIC_MAX_NUMBER
    else:
        min_number = 0
    max_number = config.cfg.ARITHMETIC_MAX_NUMBER
    
    if md.mode.current_operation == 'divide' and 'arithmetic' in md.mode.modalities[md.mode.mode]:
        if len(stats.session['position1']) >= md.mode.back:
            number_nback = stats.session['numbers'][md.mode.trial_number - md.mode.back - 1]
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
            md.mode.current_stim['number'] = random.choice(possibilities)
        else:
            md.mode.current_stim['number'] = random.randint(min_number, max_number)
            while md.mode.current_stim['number'] == 0:
                md.mode.current_stim['number'] = random.randint(min_number, max_number)
    else:
        md.mode.current_stim['number'] = random.randint(min_number, max_number)
    
    multi = md.mode.flags[md.mode.mode]['multi']
    
    real_back = md.mode.back
    if md.mode.flags[md.mode.mode]['crab'] == 1:
        real_back = 1 + 2*((md.mode.trial_number-1) % md.mode.back)
    else:
        real_back = md.mode.back
    if config.cfg.VARIABLE_NBACK:
        real_back = md.mode.variable_list[md.mode.trial_number - real_back - 1]

    if md.mode.modalities[md.mode.mode] != ['arithmetic'] and md.mode.trial_number > md.mode.back:
        for mod in md.mode.modalities[md.mode.mode]:
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

            elif r2 < config.cfg.CHANCE_OF_INTERFERENCE and md.mode.back > 1:
                back = real_back
                interference = [-1, 1, md.mode.back]
                if back < 3: interference = interference[1:] # for crab mode and 2-back
                random.shuffle(interference)
                for i in interference: # we'll just take the last one that works.
                    if md.mode.trial_number - (real_back+i) - 1 >= 0 and \
                         stats.session[back_data][md.mode.trial_number - (real_back+i) - 1] != \
                         stats.session[back_data][md.mode.trial_number -  real_back    - 1]:
                        back = real_back + i
                if back == real_back: back = None # if none of the above worked
                elif param.DEBUG:
                    print 'Forcing interference for %s' % current
            
            if back:            
                nback_trial = md.mode.trial_number - back - 1
                matching_stim = stats.session[back_data][nback_trial]
                # check for collisions in multi-stim md.mode
                if multi > 1 and mod.startswith('position'): 
                    potential_conflicts = set(range(1, multi+1)) - set([int(mod[-1])])
                    conflict_positions = [positions[i-1] for i in potential_conflicts]
                    if matching_stim in conflict_positions: # swap 'em
                        i = positions.index(matching_stim)
                        if param.DEBUG:
                            print "moving position%i from %i to %i for %s" % (i+1, positions[i], md.mode.current_stim[current], current)
                        md.mode.current_stim['position' + `i+1`] = md.mode.current_stim[current]
                        positions[i] = md.mode.current_stim[current]
                    positions[int(current[-1])-1] = matching_stim
                if param.DEBUG:
                    print "setting %s to %i" % (current, matching_stim)
                md.mode.current_stim[current] = matching_stim

        if multi > 1:
            if random.random() < config.cfg.CHANCE_OF_INTERFERENCE / 3.:
                mod = 'position'
                if 'vis1' in md.mode.modalities[md.mode.mode] and random.random() < .5:
                    mod = 'vis'
                offset = random.choice(range(1, multi))
                for i in range(multi):
                    md.mode.current_stim[mod + `i+1`] = stats.session[mod + `((i+offset)%multi) + 1`][md.mode.trial_number - real_back - 1]
                    if mod == 'position':
                        positions[i] = md.mode.current_stim[mod + `i+1`]

        
    # set static stimuli according to mode.
    # default position is 0 (center)
    # default color is 1 (red) or 2 (black)
    # default vis is 0 (square)
    # audio is never static so it doesn't have a default.
    if not 'color'     in md.mode.modalities[md.mode.mode]: md.mode.current_stim['color'] = config.cfg.VISUAL_COLORS[0]
    if not 'position1' in md.mode.modalities[md.mode.mode]: md.mode.current_stim['position1'] = 0
    if not set(['visvis', 'arithmetic', 'image']).intersection( md.mode.modalities[md.mode.mode] ):
        md.mode.current_stim['vis'] = 0
    if multi > 1 and not 'vis1' in md.mode.modalities[md.mode.mode]:
        for i in range(1, 5):
            if config.cfg.MULTI_MODE == 'color':
                md.mode.current_stim['vis'+`i`] = 0 # use squares
            elif config.cfg.MULTI_MODE == 'image':
                md.mode.current_stim['vis'+`i`] = config.cfg.VISUAL_COLORS[0]
        
    # in jaeggi mode, set using the predetermined sequence.
    if config.cfg.JAEGGI_MODE:
        md.mode.current_stim['position1'] = md.mode.bt_sequence[0][md.mode.trial_number - 1]
        md.mode.current_stim['audio'] = md.mode.bt_sequence[1][md.mode.trial_number - 1]
    
    # initiate the chosen stimuli.
    # md.mode.current_stim['audio'] is a number from 1 to 8.
    if 'arithmetic' in md.mode.modalities[md.mode.mode] and md.mode.trial_number > md.mode.back:
        player = pyglet.media.Player()
        player.queue(res.sounds['operations'][md.mode.current_operation])  # maybe we should try... catch... here
        player.play()                                               # and maybe we should recycle sound players...
    elif 'audio' in md.mode.modalities[md.mode.mode] and not 'audio2' in md.mode.modalities[md.mode.mode]:
        player = pyglet.media.Player()
        player.queue(md.mode.soundlist[md.mode.current_stim['audio']-1])
        player.play()
    elif 'audio2' in md.mode.modalities[md.mode.mode]:
        # dual audio modes - two sound players
        player = pyglet.media.Player()
        player.queue(md.mode.soundlist[md.mode.current_stim['audio']-1])
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
        player2.queue(md.mode.soundlist2[md.mode.current_stim['audio2']-1])
        player2.min_distance = 100.0
        if config.cfg.CHANNEL_AUDIO2 == 'left':
            player2.position = (-99.0, 0.0, 0.0)
        elif config.cfg.CHANNEL_AUDIO2 == 'right':
            player2.position = (99.0, 0.0, 0.0)
        elif config.cfg.CHANNEL_AUDIO2 == 'center':
            #player2.position = (0.0, 0.0, 0.0)
            pass
        player2.play()
        
            
    if config.cfg.VARIABLE_NBACK and md.mode.trial_number > md.mode.back:
        variable = md.mode.variable_list[md.mode.trial_number - 1 - md.mode.back]
    else:
        variable = 0
    if param.DEBUG and multi < 2:
        print "trial=%i, \tpos=%i, \taud=%i, \tcol=%i, \tvis=%i, \tnum=%i,\top=%s, \tvar=%i" % \
                (md.mode.trial_number, md.mode.current_stim['position1'], md.mode.current_stim['audio'],
                 md.mode.current_stim['color'], md.mode.current_stim['vis'], \
                 md.mode.current_stim['number'], md.mode.current_operation, variable)
    if multi == 1:
        visuals[0].spawn(md.mode.current_stim['position1'], md.mode.current_stim['color'],
                         md.mode.current_stim['vis'], md.mode.current_stim['number'],
                         md.mode.current_operation, variable)
    else: # multi > 1
        for i in range(1, multi+1):
            if config.cfg.MULTI_MODE == 'color':
                if param.DEBUG:
                    print "trial=%i, \tpos=%i, \taud=%i, \tcol=%i, \tvis=%i, \tnum=%i,\top=%s, \tvar=%i" % \
                        (md.mode.trial_number, md.mode.current_stim['position' + `i`], md.mode.current_stim['audio'],
                        config.cfg.VISUAL_COLORS[i-1], md.mode.current_stim['vis'+`i`], \
                        md.mode.current_stim['number'], md.mode.current_operation, variable)
                visuals[i-1].spawn(md.mode.current_stim['position'+`i`], config.cfg.VISUAL_COLORS[i-1],
                                   md.mode.current_stim['vis'+`i`], md.mode.current_stim['number'],
                                   md.mode.current_operation, variable)
            else:
                if param.DEBUG:
                    print "trial=%i, \tpos=%i, \taud=%i, \tcol=%i, \tvis=%i, \tnum=%i,\top=%s, \tvar=%i" % \
                        (md.mode.trial_number, md.mode.current_stim['position' + `i`], md.mode.current_stim['audio'],
                        md.mode.current_stim['vis'+`i`], i, \
                        md.mode.current_stim['number'], md.mode.current_operation, variable)
                visuals[i-1].spawn(md.mode.current_stim['position'+`i`], md.mode.current_stim['vis'+`i`],
                                   i,                            md.mode.current_stim['number'],
                                   md.mode.current_operation, variable)


def toggle_manual_mode():
    if md.mode.manual:
        md.mode.manual = False
    else:
        md.mode.manual = True
    
    #if not md.mode.manual:
        #md.mode.enforce_standard_md.mode()
        
    update_all_labels()

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
@wnd.window.event
def on_mouse_press(x, y, button, modifiers):
    Flag = True
    if md.mode.started:
        if len(md.mode.modalities[md.mode.mode])==2:
            for k in md.mode.modalities[md.mode.mode]:
                if k == 'arithmetic':
                    Flag = False
            if Flag:
                if (button == pyglet.window.mouse.LEFT):
                    md.mode.inputs[md.mode.modalities[md.mode.mode][0]] = True
                elif (button == pyglet.window.mouse.RIGHT):
                    md.mode.inputs[md.mode.modalities[md.mode.mode][1]] = True
                update_input_labels()


@wnd.window.event
def on_key_press(symbol, modifiers):    
    if symbol == key.D and (modifiers & key.MOD_CTRL):
        dump_pyglet_info()
        
    elif md.mode.title_screen and not md.mode.draw_graph:
        if symbol == key.ESCAPE or symbol == key.X:
            window.on_close()
            
        elif symbol == key.SPACE:
            md.mode.title_screen = False
            #md.mode.shrink_brain = True
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
            graph.graph = md.mode.mode
            md.mode.draw_graph = True
            
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

    elif md.mode.draw_graph:
        if symbol == key.ESCAPE or symbol == key.G or symbol == key.X:
            md.mode.draw_graph = False
            
        #elif symbol == key.E and (modifiers & key.MOD_CTRL):
            #graph.export_data()

        elif symbol == key.N:
            graph.next_nonempty_mode()
            
        elif symbol == key.M:
            graph.next_style()
                                                    
    elif md.mode.saccadic:
        if symbol in (key.ESCAPE, key.E, key.X, key.SPACE):
            saccadic.stop()
            
    elif not md.mode.started:
        
        if symbol == key.ESCAPE or symbol == key.X:
            if config.cfg.SKIP_TITLE_SCREEN:
                window.on_close()
            else:
                md.mode.title_screen = True
        
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
            graph.graph = md.mode.mode
            md.mode.draw_graph = True

        elif symbol == key.F1 and md.mode.manual:
            if md.mode.back > 1:
                md.mode.back -= 1
                gameModeLabel.flash()
                spaceLabel.update()
                sessionInfoLabel.update()
                
        elif symbol == key.F2 and md.mode.manual:
            md.mode.back += 1
            gameModeLabel.flash()
            spaceLabel.update()
            sessionInfoLabel.update()

        elif symbol == key.F3 and md.mode.num_trials > 5 and md.mode.manual:
            md.mode.num_trials -= 5
            md.mode.num_trials_total = md.mode.num_trials + md.mode.num_trials_factor * \
                md.mode.back ** md.mode.num_trials_exponent
            sessionInfoLabel.flash()

        elif symbol == key.F4 and md.mode.manual:
            md.mode.num_trials += 5
            md.mode.num_trials_total = md.mode.num_trials + md.mode.num_trials_factor * \
                md.mode.back ** md.mode.num_trials_exponent
            sessionInfoLabel.flash()            
            
        elif symbol == key.F5 and md.mode.manual:
            if md.mode.ticks_per_trial < param.TICKS_MAX:
                md.mode.ticks_per_trial += 1
                sessionInfoLabel.flash()
                        
        elif symbol == key.F6 and md.mode.manual:
            if md.mode.ticks_per_trial > param.TICKS_MIN:
                md.mode.ticks_per_trial -= 1
                sessionInfoLabel.flash()
                
        elif symbol == key.C and (modifiers & key.MOD_CTRL):
            stats.clear()
            chartLabel.update()
            averageLabel.update()
            todayLabel.update()
            md.mode.progress = 0
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
            md.mode.progress = 0
            circles.update()

        elif symbol == key.H:
            webbrowser.open_new_tab(param.WEB_TUTORIAL)
                        
        elif symbol == key.D and not param.CLINICAL_MODE:
            webbrowser.open_new_tab(param.WEB_DONATE)

        elif symbol == key.J and 'morse' in config.cfg.AUDIO1_SETS or 'morse' in config.cfg.AUDIO2_SETS:
            webbrowser.open_new_tab(param.WEB_MORSE)
                            
                        
    # these are the keys during a running session.
    elif md.mode.started:
        if (symbol == key.ESCAPE or symbol == key.X) and not param.CLINICAL_MODE:
            end_session(cancelled = True)
            
        elif symbol == key.P and not param.CLINICAL_MODE:
            md.mode.paused = not md.mode.paused
            pausedLabel.update()
            field.crosshair_update()
                
        elif symbol == key.F8 and not param.CLINICAL_MODE:
            md.mode.hide_text = not md.mode.hide_text
            update_all_labels()
                
        elif md.mode.tick != 0 and md.mode.trial_number > 0:
            if 'arithmetic' in md.mode.modalities[md.mode.mode]:
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
                    
            
            for k in md.mode.modalities[md.mode.mode]:
                if not k == 'arithmetic':
                    keycode = config.cfg['KEY_%s' % k.upper()]
                    if symbol == keycode:
                        md.mode.inputs[k] = True
                        md.mode.input_rts[k] = time.time() - md.mode.trial_starttime
                        update_input_labels()
        
        if symbol == config.cfg.KEY_ADVANCE and md.mode.flags[md.mode.mode]['selfpaced']:
            md.mode.tick = md.mode.ticks_per_trial-5

    return pyglet.event.EVENT_HANDLED


# the loop where everything is drawn on the screen.
@wnd.window.event
def on_draw():
    if md.mode.shrink_brain:
        return
    window.clear()
    if md.mode.draw_graph:
        graph.draw()
    elif md.mode.saccadic:
        saccadic.draw()
    elif md.mode.title_screen:
        brain_graphic.draw()
        titleMessageLabel.draw()
        titleKeysLabel.draw()
    else:
        batch.draw()
        if not md.mode.started and not param.CLINICAL_MODE:
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
    if md.mode.started and not md.mode.paused: # only run the timer during a game
        if not md.mode.flags[md.mode.mode]['selfpaced'] or \
                md.mode.tick > md.mode.ticks_per_trial-6 or \
                md.mode.tick < 5:
            md.mode.tick += 1
        if md.mode.tick == 1:
            md.mode.show_missed = False
            if md.mode.trial_number > 0:
                stats.save_input()
            md.mode.trial_number += 1
            md.mode.trial_starttime = time.time()
            trialsRemainingLabel.update()
            if md.mode.trial_number > md.mode.num_trials_total:
                end_session()
            else: generate_stimulus()
            reset_input()
        # Hide square at either the 0.5 second mark or sooner
        positions = len([mod for mod in md.mode.modalities[md.mode.mode] if mod.startswith('position')])
        positions = max(0, positions-1)
        if md.mode.tick == (6+positions) or md.mode.tick >= md.mode.ticks_per_trial - 2:
            for visual in visuals: visual.hide()
        if md.mode.tick == md.mode.ticks_per_trial - 2:  # display feedback for 200 ms
            md.mode.tick = 0
            md.mode.show_missed = True
            update_input_labels()
        if md.mode.tick == md.mode.ticks_per_trial:
            md.mode.tick = 0
pyglet.clock.schedule_interval(update, param.TICK_DURATION)

angle = 0


def pulsate(dt):
    global angle
    if md.mode.started: return
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


# Instantiate the classes




# load last game mode
stats.initialize_session()
stats.parse_statsfile()
if len(stats.full_history) > 0 and not config.cfg.JAEGGI_MODE:
    md.mode.mode = stats.full_history[-1][1]
stats.retrieve_progress()

update_all_labels()

# Initialize brain sprite
brain_icon = pyglet.sprite.Sprite(pyglet.image.load(random.choice(res.resourcepaths['misc']['brain'])))
brain_icon.set_position(field.center_x - brain_icon.width//2,
                           field.center_y - brain_icon.height//2)
if config.cfg.BLACK_BACKGROUND:
    brain_graphic = pyglet.sprite.Sprite(pyglet.image.load(random.choice(res.resourcepaths['misc']['splash-black'])))
else:
    brain_graphic = pyglet.sprite.Sprite(pyglet.image.load(random.choice(res.resourcepaths['misc']['splash'])))
brain_graphic.set_position(field.center_x - brain_graphic.width//2,
                           field.center_y - brain_graphic.height//2 + 40)

def shrink_brain(dt):
    brain_graphic.scale -= dt * 2
    brain_graphic.x = field.center_x - brain_graphic.image.width//2  + 2 + (brain_graphic.image.width - brain_graphic.width) // 2
    brain_graphic.y = field.center_y - brain_graphic.image.height//2 - 1 + (brain_graphic.image.height - brain_graphic.height) // 2
    window.clear()
    brain_graphic.draw()
    if brain_graphic.width < 56:
        md.mode.shrink_brain = False
        pyglet.clock.unschedule(shrink_brain)
        brain_graphic.scale = 1
        brain_graphic.set_position(field.center_x - brain_graphic.width//2,
                           field.center_y - brain_graphic.height//2 + 40)
        

# If we had messages queued during loading (like from moving our data files), display them now
msg.messagequeue.reverse()
for msg in msg.messagequeue:
    msg.Message(msg)

# start the event loops!
if __name__ == '__main__':

    pyglet.app.run()

# nothing below the line "pyglet.app.run()" will be executed until the
# window is closed or ESC is pressed.

