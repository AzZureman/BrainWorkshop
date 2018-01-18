import random
import pyglet
import cPickle as pickle
import os
import datetime
from datetime import date
import time
from time import strftime
import utils
import config
import parameters as param
import resource as res
import modes as md
import graphics as g


# this class stores the raw statistics and history information.
# the information is analyzed by the AnalysisLabel class.
class Stats:
    def __init__(self):
        # set up data variables
        self.initialize_session()
        self.history = []
        self.full_history = []  # not just today
        self.sessions_today = 0
        self.time_today = 0
        self.time_thours = 0
        self.sessions_thours = 0

    def parse_statsfile(self):
        self.clear()
        if os.path.isfile(os.path.join(utils.get_data_dir(), config.cfg.STATSFILE)):
            try:
                # last_session = []
                # last_session_number = 0
                last_mode = 0
                last_back = 0
                statsfile_path = os.path.join(utils.get_data_dir(), config.cfg.STATSFILE)
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
                    if datestamp == today or (datestamp == yesterday and (
                            hour > thour or (hour == thour and (mins > tmin or (mins == tmin and sec > tsec))))):
                        is_thours = True
                    if '\t' in line:
                        separator = '\t'
                    else:
                        separator = ','
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
                        self.sessions_thours += 1
                        self.time_thours += sesstime
                    if is_today:
                        self.sessions_today += 1
                        self.time_today += sesstime
                        self.history.append([newsession_number, newmode, newback, newpercent, newmanual])
                    # if not newmanual and (is_today or config.cfg.RESET_LEVEL):
                    #    last_session = self.full_history[-1]
                statsfile.close()
                self.retrieve_progress()

            except:
                utils.quit_with_error(('Error parsing stats file\n%s') %
                                      os.path.join(utils.get_data_dir(), config.cfg.STATSFILE),
                                      ('\nPlease fix, delete or rename the stats file.'),
                                      quit=False)

    def retrieve_progress(self):
        if config.cfg.RESET_LEVEL:
            sessions = [s for s in self.history if s[1] == md.mode.mode]
        else:
            sessions = [s for s in self.full_history if s[1] == md.mode.mode]
        md.mode.enforce_standard_mode()
        if sessions:
            ls = sessions[-1]
            md.mode.back = ls[2]
            if ls[3] >= config.get_threshold_advance():
                md.mode.back += 1
            md.mode.session_number = ls[0]
            md.mode.progress = 0
            for s in sessions:
                if s[2] == md.mode.back and s[3] < config.get_threshold_fallback():
                    md.mode.progress += 1
                elif s[2] != md.mode.back:
                    md.mode.progress = 0
            if md.mode.progress >= config.cfg.THRESHOLD_FALLBACK_SESSIONS:
                md.mode.progress = 0
                md.mode.back -= 1
                if md.mode.back < 1:
                    md.mode.back = 1
        else:  # no sessions today for this user and this mode
            md.mode.back = md.default_nback_mode(md.mode.mode)
        md.mode.num_trials_total = md.mode.num_trials + md.mode.num_trials_factor * md.mode.back ** md.mode.num_trials_exponent

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

        self.session['position1_rt'] = []  # reaction times
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
        # self.session['arithmetic_rt'] = []

    def save_input(self):
        for k, v in md.mode.current_stim.items():
            if k == 'number':
                self.session['numbers'].append(v)
            else:
                self.session[k].append(v)
            if k == 'vis':  # goes to both self.session['vis'] and ['image']
                self.session['image'].append(v)
        for k, v in md.mode.inputs.items():
            self.session[k + '_input'].append(v)
        for k, v in md.mode.input_rts.items():
            self.session[k + '_rt'].append(v)

        self.session['operation'].append(md.mode.current_operation)
        self.session['arithmetic_input'].append(g.arithmeticAnswerLabel.parse_answer())

    def log_saccadic(self, start_time, elapsed_time, counter):
        if param.ATTEMPT_TO_SAVE_STATS and config.cfg.SACCADIC_LOGGING:
            try:
                statsfile_path = os.path.join(utils.get_data_dir(), config.cfg.STATSFILE)
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
        self.history.append([md.mode.session_number, md.mode.mode, md.mode.back, percent, md.mode.manual])

        if param.ATTEMPT_TO_SAVE_STATS:
            try:
                sep = param.STATS_SEPARATOR
                statsfile_path = os.path.join(utils.get_data_dir(), config.cfg.STATSFILE)
                statsfile = open(statsfile_path, 'a')
                outlist = [strftime("%Y-%m-%d %H:%M:%S"),
                           md.mode.short_name(),
                           str(percent),
                           str(md.mode.mode),
                           str(md.mode.back),
                           str(md.mode.ticks_per_trial),
                           str(md.mode.num_trials_total),
                           str(int(md.mode.manual)),
                           str(md.mode.session_number),
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
                           str(md.mode.ticks_per_trial * param.TICK_DURATION * md.mode.num_trials_total),
                           str(0),
                           ]
                statsfile.write(sep.join(outlist))  # adds sep between each element
                statsfile.write('\n')  # but we don't want a sep before '\n'
                statsfile.close()
                if param.CLINICAL_MODE:
                    picklefile = open(os.path.join(utils.get_data_dir(), param.STATS_BINARY), 'ab')
                    pickle.dump([strftime("%Y-%m-%d %H:%M:%S"), md.mode.short_name(),
                                 percent, md.mode.mode, md.mode.back, md.mode.ticks_per_trial,
                                 md.mode.num_trials_total, int(md.mode.manual),
                                 md.mode.session_number, category_percents['position1'],
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
                config.cfg.SAVE_SESSIONS = True  # FIXME: put this where it belongs
                config.cfg.SESSION_STATS = param.USER + '-sessions.dat'  # FIXME: default user; configurability
                if config.cfg.SAVE_SESSIONS:
                    picklefile = open(os.path.join(utils.get_data_dir(), config.cfg.SESSION_STATS), 'ab')
                    session = {}  # it's not a dotdict because we want to pickle it
                    session['summary'] = outlist  # that's what goes into stats.txt
                    session['cfg'] = config.cfg.__dict__
                    session['timestamp'] = strftime("%Y-%m-%d %H:%M:%S")
                    session['mode'] = md.mode.mode
                    session['n'] = md.mode.back
                    session['manual'] = md.mode.manual
                    session['trial_duration'] = md.mode.ticks_per_trial * param.TICK_DURATION
                    session['trials'] = md.mode.num_trials_total
                    session['session'] = self.session
                    pickle.dump(session, picklefile)
                    picklefile.close()
            except:
                utils.quit_with_error(('Error writing to stats file\n%s') %
                                      os.path.join(utils.get_data_dir(), config.cfg.STATSFILE),
                                      ('\nPlease check file and directory permissions.'))

        perfect = False
        awesome = False
        great = False
        good = False
        advance = False
        fallback = False

        if not md.mode.manual:
            if percent >= config.get_threshold_advance():
                md.mode.back += 1
                md.mode.num_trials_total = md.mode.num_trials + md.mode.num_trials_factor * md.mode.back ** md.mode.num_trials_exponent
                md.mode.progress = 0
                g.circles.update()
                if config.cfg.USE_APPLAUSE:
                    # applauseplayer = pyglet.media.ManagedSoundPlayer()
                    applauseplayer.queue(random.choice(res.applausesounds))
                    applauseplayer.volume = config.cfg.APPLAUSE_VOLUME
                    applauseplayer.play()
                advance = True
            elif md.mode.back > 1 and percent < config.get_threshold_fallback():
                if config.cfg.JAEGGI_MODE:
                    md.mode.back -= 1
                    fallback = True
                else:
                    if md.mode.progress == config.cfg.THRESHOLD_FALLBACK_SESSIONS - 1:
                        md.mode.back -= 1
                        md.mode.num_trials_total = md.mode.num_trials + md.mode.num_trials_factor * \
                            md.mode.back ** md.mode.num_trials_exponent
                        fallback = True
                        md.mode.progress = 0
                        g.circles.update()
                    else:
                        md.mode.progress += 1
                        g.circles.update()

            if percent == 100:
                perfect = True
            elif percent >= config.get_threshold_advance():
                awesome = True
            elif percent >= (config.get_threshold_advance() + config.get_threshold_fallback()) // 2:
                great = True
            elif percent >= config.get_threshold_fallback():
                good = True
                g.congratsLabel.update(True, advance, fallback, awesome, great, good, perfect)

        if md.mode.manual and not config.cfg.USE_MUSIC_MANUAL:
            return

        if config.cfg.USE_MUSIC:
            musicplayer = pyglet.media.Player()
            if percent >= config.get_threshold_advance() and res.resourcepaths['music']['advance']:
                musicplayer.queue(
                    pyglet.media.load(random.choice(res.resourcepaths['music']['advance']), streaming=True))
            elif percent >= (config.get_threshold_advance() + config.get_threshold_fallback()) // 2 and \
                    res.resourcepaths['music']['great']:
                musicplayer.queue(pyglet.media.load(random.choice(res.resourcepaths['music']['great']), streaming=True))
            elif percent >= config.get_threshold_fallback() and res.resourcepaths['music']['good']:
                musicplayer.queue(pyglet.media.load(random.choice(res.resourcepaths['music']['good']), streaming=True))
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


stats = Stats()
