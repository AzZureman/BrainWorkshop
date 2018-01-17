import pyglet, os, math
from pyglet.gl import *
from datetime import *
import config
from utils import *


class Graph:
    def __init__(self, window, mode):
        self.window = window
        self.mode = mode
        self.graph = 2
        self.reset_dictionaries()
        self.reset_percents()
        self.batch = None
        self.styles = ['N+10/3+4/3', 'N', '%', 'N.%', 'N+2*%-1']
        self.style = 0

    def next_style(self):
        self.style = (self.style + 1) % len(self.styles)
        print "style = %s" % self.styles[self.style]  # fixme:  change the labels
        self.parse_stats()

    def reset_dictionaries(self):
        self.dictionaries = dict([(i, {}) for i in self.mode.modalities])

    def reset_percents(self):
        self.percents = dict([(k, dict([(i, []) for i in v])) for k, v in self.mode.modalities.items()])

    def next_nonempty_mode(self):
        self.next_mode()
        mode1 = self.graph
        mode2 = None  # to make sure the loop runs the first iteration
        while self.graph != mode2 and not self.dictionaries[self.graph]:
            self.next_mode()
            mode2 = mode1

    def next_mode(self):
        modes = self.mode.modalities.keys()
        modes.sort()
        i = modes.index(self.graph)
        i = (i + 1) % len(modes)
        self.graph = modes[i]
        self.batch = None

    def parse_stats(self):
        self.batch = None
        self.reset_dictionaries()
        self.reset_percents()
        ind = {'date': 0, 'modename': 1, 'percent': 2, 'mode': 3, 'n': 4, 'ticks': 5,
               'trials': 6, 'manual': 7, 'session': 8, 'position1': 9, 'audio': 10,
               'color': 11, 'visvis': 12, 'audiovis': 13, 'arithmetic': 14,
               'image': 15, 'visaudio': 16, 'audio2': 17, 'position2': 18,
               'position3': 19, 'position4': 20, 'vis1': 21, 'vis2': 22, 'vis3': 23,
               'vis4': 24}

        if os.path.isfile(os.path.join(get_data_dir(), config.cfg.STATSFILE)):
            try:
                statsfile_path = os.path.join(get_data_dir(), config.cfg.STATSFILE)
                statsfile = open(statsfile_path, 'r')
                for line in statsfile:
                    if line == '': continue
                    if line == '\n': continue
                    if line[0] not in '0123456789': continue
                    datestamp = date(int(line[:4]), int(line[5:7]), int(line[8:10]))
                    hour = int(line[11:13])
                    if hour < config.cfg.ROLLOVER_HOUR:
                        datestamp = date.fromordinal(datestamp.toordinal() - 1)
                    if line.find('\t') >= 0:
                        separator = '\t'
                    else:
                        separator = ','
                    newline = line.split(separator)
                    try:
                        if int(newline[7]) != 0:  # only consider standard mode
                            continue
                    except:
                        continue
                    newmode = int(newline[3])
                    newback = int(newline[4])

                    while len(newline) < 24:
                        newline.append('0')  # make it work for image mode, missing visaudio and audio2
                    if len(newline) >= 16:
                        for m in self.mode.modalities[newmode]:
                            self.percents[newmode][m].append(int(newline[ind[m]]))

                    dictionary = self.dictionaries[newmode]
                    if datestamp not in dictionary:
                        dictionary[datestamp] = []
                    dictionary[datestamp].append([newback] + [int(newline[2])] + \
                                                 [self.percents[newmode][n][-1] for n in self.mode.modalities[newmode]])

                statsfile.close()
            except:
                quit_with_error(_('Error parsing stats file\n %s') %
                                os.path.join(get_data_dir(), config.cfg.STATSFILE),
                                _('Please fix, delete or rename the stats file.'))

            def mean(x):
                if len(x):
                    return sum(x) / float(len(x))
                else:
                    return 0.

            def cent(x):
                return map(lambda y: .01 * y, x)

            for dictionary in self.dictionaries.values():
                for datestamp in dictionary.keys():  # this would be so much easier with numpy
                    entries = dictionary[datestamp]
                    if self.styles[self.style] == 'N':
                        scores = [entry[0] for entry in entries]
                    elif self.styles[self.style] == '%':
                        scores = [.01 * entry[1] for entry in entries]
                    elif self.styles[self.style] == 'N.%':
                        scores = [entry[0] + .01 * entry[1] for entry in entries]
                    elif self.styles[self.style] == 'N+2*%-1':
                        scores = [entry[0] - 1 + 2 * .01 * entry[1] for entry in entries]
                    elif self.styles[self.style] == 'N+10/3+4/3':
                        adv, flb = config.get_threshold_advance(), config.get_threshold_fallback()
                        m = 1. / (adv - flb)
                        b = -m * flb
                        scores = [entry[0] + b + m * (entry[1]) for entry in entries]
                    dictionary[datestamp] = (mean(scores), max(scores))

            for game in self.percents:
                for category in self.percents[game]:
                    pcts = self.percents[game][category][-50:]
                    if not pcts:
                        self.percents[game][category].append(0)
                    else:
                        self.percents[game][category].append(sum(pcts) / len(pcts))

                        # def export_data(self):
        # dictionary = {}
        # for x in self.dictionaries: # cycle through game modes
        # chartfile_name = CHARTFILE[x]
        # dictionary = self.dictionaries[x]
        # output = ['Date\t%s N-Back Average\n' % mode.long_mode_names[x]]

        # keyslist = dictionary.keys()
        # keyslist.sort()
        # if len(keyslist) == 0: continue
        # for datestamp in keyslist:
        # if dictionary[datestamp] == (-1, -1):
        # continue
        # output.append(str(datestamp))
        # output.append('\t')
        # output.append(str(dictionary[datestamp]))
        # output.append('\n')

        # try:
        # chartfile_path = os.path.join(get_data_dir(), chartfile_name)
        # chartfile = open(chartfile_path, 'w')
        # chartfile.write(''.join(output))
        # chartfile.close()

        # except:
        # quit_with_error('Error writing chart file:\n%s' %
        # os.path.join(get_data_dir(), chartfile_name))

    def draw(self):
        if not self.batch:
            self.create_batch()
        else:
            self.batch.draw()

    def create_batch(self):
        self.batch = pyglet.graphics.Batch()

        linecolor = (0, 0, 255)
        linecolor2 = (255, 0, 0)
        if config.cfg.BLACK_BACKGROUND:
            axiscolor = (96, 96, 96)
            minorcolor = (64, 64, 64)
        else:
            axiscolor = (160, 160, 160)
            minorcolor = (224, 224, 224)

        x_label_width = 20
        y_marking_interval = 0.25

        height = int(self.window.height * 0.625)
        width = int(self.window.width * 0.625)
        center_x = self.window.width // 2
        center_y = self.window.height // 2 + 20
        left = center_x - width // 2
        right = center_x + width // 2
        top = center_y + height // 2
        bottom = center_y - height // 2
        try:
            dictionary = self.dictionaries[self.graph]
        except:
            print self.graph
        graph_title = self.mode.long_mode_names[self.graph] + _(' N-Back')

        self.batch.add(3, GL_LINE_STRIP,
                       pyglet.graphics.OrderedGroup(order=1), ('v2i', (
                left, top,
                left, bottom,
                right, bottom)), ('c3B', axiscolor * 3))

        pyglet.text.Label(
            _('G: Return to Main Screen\n\nN: Next Game Type'),
            batch=self.batch,
            multiline=True, width=300,
            font_size=9,
            color = config.cfg.COLOR_TEXT,
            x = 10, y = self.window.height - 10,
            anchor_x='left', anchor_y='top')

        pyglet.text.Label(graph_title,
                          batch=self.batch,
                          font_size=18, bold=True, color=config.cfg.COLOR_TEXT,
                          x=center_x, y=top + 60,
                          anchor_x='center', anchor_y='center')

        pyglet.text.Label(_('Date'),
                          batch=self.batch,
                          font_size=12, bold=True, color=config.cfg.COLOR_TEXT,
                          x=center_x, y=bottom - 80,
                          anchor_x='center', anchor_y='center')

        pyglet.text.Label(_('Maximum'), width=1,
                          batch=self.batch,
                          font_size=12, bold=True, color=linecolor2 + (255,),
                          x=left - 60, y=center_y + 50,
                          anchor_x='right', anchor_y='center')

        pyglet.text.Label(_('Average'), width=1,
                          batch=self.batch,
                          font_size=12, bold=True, color=linecolor + (255,),
                          x=left - 60, y=center_y + 25,
                          anchor_x='right', anchor_y='center')

        pyglet.text.Label(_('Score'), width=1,
                          batch=self.batch,
                          font_size=12, bold=True, color=config.cfg.COLOR_TEXT,
                          x=left - 60, y=center_y,
                          anchor_x='right', anchor_y='center')

        dates = dictionary.keys()
        dates.sort()
        if len(dates) < 2:
            pyglet.text.Label(_('Insufficient data: two days needed'),
                              batch=self.batch,
                              font_size=12, bold=True, color=axiscolor + (255,),
                              x=center_x, y=center_y,
                              anchor_x='center', anchor_y='center')
            return

        ymin = 100000.0
        ymax = 0.0
        for entry in dates:
            if dictionary[entry] == (-1, -1):
                continue
            if dictionary[entry][0] < ymin:
                ymin = dictionary[entry][0]
            if dictionary[entry][1] > ymax:
                ymax = dictionary[entry][1]
        if ymin == ymax:
            ymin = 0

        pyglet.clock.tick(poll=True)  # Prevent music skipping 1

        ymin = int(math.floor(ymin * 4)) / 4.
        ymax = int(math.ceil(ymax * 4)) / 4.

        # remove these two lines to revert to the old behaviour
        # ymin = 1.0
        # ymax += 0.25

        # add intermediate days
        z = 0
        while z < len(dates) - 1:
            if dates[z + 1].toordinal() > dates[z].toordinal() + 1:
                newdate = date.fromordinal(dates[z].toordinal() + 1)
                dates.insert(z + 1, newdate)
                dictionary[newdate] = (-1, -1)
            z += 1

        avgpoints = []
        maxpoints = []

        xinterval = width / (float(len(dates) - 1))
        skip_x = int(x_label_width // xinterval)

        for index in range(len(dates)):
            x = int(xinterval * index + left)
            if dictionary[dates[index]][0] != -1:
                avgpoints.extend([x, int((dictionary[dates[index]][0] - ymin) / (ymax - ymin) * height + bottom)])
                maxpoints.extend([x, int((dictionary[dates[index]][1] - ymin) / (ymax - ymin) * height + bottom)])
            datestring = str(dates[index])[2:]
            datestring = datestring.replace('-', '\n')
            if not index % (skip_x + 1):
                pyglet.text.Label(datestring, multiline=True, width=12,
                                  batch=self.batch,
                                  font_size=8, bold=False, color=config.cfg.COLOR_TEXT,
                                  x=x, y=bottom - 15,
                                  anchor_x='center', anchor_y='top')
                self.batch.add(2, GL_LINES,
                               pyglet.graphics.OrderedGroup(order=0), ('v2i', (
                        x, bottom,
                        x, top)), ('c3B', minorcolor * 2))
                self.batch.add(2, GL_LINES,
                               pyglet.graphics.OrderedGroup(order=1), ('v2i', (
                        x, bottom - 10,
                        x, bottom)), ('c3B', axiscolor * 2))

        pyglet.clock.tick(poll=True)  # Prevent music skipping 2

        y_marking = ymin
        while y_marking <= ymax:
            y = int((y_marking - ymin) / (ymax - ymin) * height + bottom)
            pyglet.text.Label(str(round(y_marking, 2)),
                              batch=self.batch,
                              font_size=10, bold=False, color=config.cfg.COLOR_TEXT,
                              x=left - 30, y=y + 1,
                              anchor_x='center', anchor_y='center')
            self.batch.add(2, GL_LINES,
                           pyglet.graphics.OrderedGroup(order=0), ('v2i', (
                    left, y,
                    right, y)), ('c3B', minorcolor * 2))
            self.batch.add(2, GL_LINES,
                           pyglet.graphics.OrderedGroup(order=1), ('v2i', (
                    left - 10, y,
                    left, y)), ('c3B', axiscolor * 2))
            y_marking += y_marking_interval

        self.batch.add(len(avgpoints) // 2, GL_LINE_STRIP,
                       pyglet.graphics.OrderedGroup(order=2), ('v2i',
                                                               avgpoints),
                       ('c3B', linecolor * (len(avgpoints) // 2)))
        self.batch.add(len(maxpoints) // 2, GL_LINE_STRIP,
                       pyglet.graphics.OrderedGroup(order=3), ('v2i',
                                                               maxpoints),
                       ('c3B', linecolor2 * (len(maxpoints) // 2)))

        pyglet.clock.tick(poll=True)  # Prevent music skipping 3

        radius = 1
        o = 4
        for index in range(0, len(avgpoints) // 2):
            x = avgpoints[index * 2]
            avg = avgpoints[index * 2 + 1]
            max = maxpoints[index * 2 + 1]
            # draw average
            self.batch.add(4, GL_POLYGON,
                           pyglet.graphics.OrderedGroup(order=o), ('v2i',
                                                                   (x - radius, avg - radius,
                                                                    x - radius, avg + radius,
                                                                    x + radius, avg + radius,
                                                                    x + radius, avg - radius)),
                           ('c3B', linecolor * 4))
            o += 1
            # draw maximum
            self.batch.add(4, GL_POLYGON,
                           pyglet.graphics.OrderedGroup(order=o), ('v2i',
                                                                   (x - radius, max - radius,
                                                                    x - radius, max + radius,
                                                                    x + radius, max + radius,
                                                                    x + radius, max - radius)),
                           ('c3B', linecolor2 * 4))
            o += 1

        pyglet.clock.tick(poll=True)  # Prevent music skipping 4

        labelstrings = {'position1': _('Position: '), 'position2': _('Position 2: '),
                        'position3': _('Position 3: '), 'position4': _('Position 4: '),
                        'vis1': _('Color/Image 1: '), 'vis2': _('Color/Image 2: '),
                        'vis3': _('Color/Image 3: '), 'vis4': _('Color/Image 4: '),
                        'visvis': _('Vis & nvis: '), 'visaudio': _('Vis & n-sound: '),
                        'audiovis': _('Sound & n-vis: '), 'audio': _('Sound: '),
                        'color': _('Color: '), 'image': _('Image: '),
                        'arithmetic': _('Arithmetic: '), 'audio2': _('Sound2: ')}
        str_list = [_('Last 50 rounds:   ')]
        for m in self.mode.modalities[self.graph]:
            str_list.append(labelstrings[m] + '%i%% ' % self.percents[self.graph][m][-1]
                            + ' ' * (7 - len(self.mode.modalities[self.graph])))

        pyglet.text.Label(''.join(str_list),
                          batch=self.batch,
                          font_size=11, bold=False, color=config.cfg.COLOR_TEXT,
                          x=self.window.width // 2, y=20,
                          anchor_x='center', anchor_y='center')
