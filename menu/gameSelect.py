import pyglet
import config
import modes as md
import menu
import parameters as param
import stats as st
import window as wnd
import graphics as g


class GameSelect(menu.Menu):
    def __init__(self):
        modalities = ['position1', 'color', 'image', 'audio', 'audio2', 'arithmetic']
        options = modalities[:]
        names = dict([(m, "Use %s" % m) for m in modalities])
        names['position1'] = "Use position"
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
        names['combination'] = 'Combination N-back mode'
        names['variable'] = 'Use variable N-Back levels'
        names['crab'] = 'Crab-back mode (reverse order of sets of N stimuli)'
        names['multi'] = 'Simultaneous visual stimuli'
        names['multimode'] = 'Simultaneous stimuli differentiated by'
        names['selfpaced'] = 'Self-paced mode'
        names['interference'] = 'Interference (tricky stimulus generation)'
        vals = dict([[op, None] for op in options])
        curmodes = md.mode.modalities[md.mode.mode]
        interference_options = [i / 8. for i in range(0, 9)]
        if config.cfg.DEFAULT_CHANCE_OF_INTERFERENCE not in interference_options:
            interference_options.append(config.cfg.DEFAULT_CHANCE_OF_INTERFERENCE)
        interference_options.sort()
        if config.cfg.CHANCE_OF_INTERFERENCE in interference_options:
            interference_default = interference_options.index(config.cfg.CHANCE_OF_INTERFERENCE)
        else:
            interference_default = 3
        vals['interference'] = g.PercentCycler(values=interference_options, default=interference_default)
        vals['combination'] = 'visvis' in curmodes
        vals['variable'] = bool(config.cfg.VARIABLE_NBACK)
        vals['crab'] = bool(md.mode.flags[md.mode.mode]['crab'])
        vals['multi'] = g.Cycler(values=[1, 2, 3, 4], default=md.mode.flags[md.mode.mode]['multi'] - 1)
        vals['multimode'] = g.Cycler(values=['color', 'image'], default=config.cfg.MULTI_MODE)
        vals['selfpaced'] = bool(md.mode.flags[md.mode.mode]['selfpaced'])
        for m in modalities:
            vals[m] = m in curmodes
        menu.Menu.__init__(self, options, vals, names=names, title='Choose your game mode')
        self.modelabel = pyglet.text.Label('', font_size=self.titlesize,
                                           bold=False, color=(0, 0, 0, 255), batch=self.batch,
                                           x=wnd.window.width / 2, y=(wnd.window.height * 1) / 10,
                                           anchor_x='center', anchor_y='center')
        self.update_labels()
        self.newmode = md.mode.mode  # self.newmode will be False if an invalid mode is chosen

    def update_labels(self):
        self.calc_mode()
        try:
            if self.newmode:
                self.modelabel.text = md.mode.long_mode_names[self.newmode] + \
                                      (self.values['variable'] and ' V.' or '') + ' N-Back'
            else:
                self.modelabel.text = "An invalid mode has been selected."
        except AttributeError:
            pass
        menu.Menu.update_labels(self)

    def calc_mode(self):
        modes = [k for (k, v) in self.values.items() if v and not isinstance(v, g.Cycler)]
        # crab = 'crab' in modes
        if 'variable' in modes:
            modes.remove('variable')
        if 'combination' in modes:
            modes.remove('combination')
            modes.extend(['visvis', 'visaudio', 'audiovis'])  # audio should already be there
        base = 0
        base += 256 * (self.values['multi'].value() - 1)
        if 'crab' in modes:
            modes.remove('crab')
            base += 128
        if 'selfpaced' in modes:
            modes.remove('selfpaced')
            base += 1024

        candidates = set([k for k, v in md.mode.modalities.items() if not
                         [True for m in modes if m not in v] and not
                         [True for m in v if m not in modes]])
        candidates = candidates & set(range(0, 128))
        if len(candidates) == 1:
            candidate = list(candidates)[0] + base
            if candidate in md.mode.modalities:
                self.newmode = candidate
            else:
                self.newmode = False
        else:
            if param.DEBUG:
                print candidates, base
            self.newmode = False

    def close(self):
        menu.Menu.close(self)
        if not md.mode.manual:
            md.mode.enforce_standard_mode()
            st.stats.retrieve_progress()
        g.update_all_labels()
        g.circles.update()

    def save(self):
        self.calc_mode()
        config.cfg.VARIABLE_NBACK = self.values['variable']
        config.cfg.MULTI_MODE = self.values['multimode'].value()
        config.cfg.CHANCE_OF_INTERFERENCE = self.values['interference'].value()
        if self.newmode:
            md.mode.mode = self.newmode

    def select(self):
        choice = self.options[self.selpos]
        if choice == 'combination':
            self.values['arithmetic'] = False
            self.values['image'] = False
            self.values['audio2'] = False
            self.values['audio'] = True
            self.values['multi'].i = 0  # no multi mode
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
            mm = self.values['multimode'].value()  # what we're changing from
            notmm = (mm == 'image') and 'color' or 'image'  # changing to
            self.values[mm] = self.values[notmm]
            self.values[notmm] = False

        menu.Menu.select(self)
        modes = [k for k, v in self.values.items() if v]
        if not [v for k, v in self.values.items()
                if v and k not in ('crab', 'combination', 'variable')] \
                or len(modes) == 1 and modes[0] in ['image', 'color']:
            self.values['position1'] = True
            self.update_labels()
        self.calc_mode()
