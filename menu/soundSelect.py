import random
import config
import menu
import resource as res
import graphics as g


class SoundSelect(menu.Menu):
    def __init__(self):
        audiosets = res.resourcepaths['sounds']  # we don't want to delete 'operations' from resourcepaths['sounds']
        self.new_sets = {}
        for audio in audiosets:
            if not audio == 'operations':
                self.new_sets['1' + audio] = audio in config.cfg.AUDIO1_SETS
                self.new_sets['2' + audio] = audio in config.cfg.AUDIO2_SETS
        for audio in audiosets:
            if not audio == 'operations':
                self.new_sets['2' + audio] = audio in config.cfg.AUDIO2_SETS
        options = self.new_sets.keys()
        options.sort()
        options.insert(len(self.new_sets) / 2, "Blank line")  # menu.Menu.update_labels and .select will ignore this
        options.append("Blank line")
        options.extend(['config.cfg.CHANNEL_AUDIO1', 'config.cfg.CHANNEL_AUDIO2'])
        lcr = ['left', 'right', 'center']
        vals = self.new_sets
        vals['config.cfg.CHANNEL_AUDIO1'] = g.Cycler(lcr, default=lcr.index(config.cfg.CHANNEL_AUDIO1))
        vals['config.cfg.CHANNEL_AUDIO2'] = g.Cycler(lcr, default=lcr.index(config.cfg.CHANNEL_AUDIO2))
        names = {}
        for op in options:
            if op.startswith('1') or op.startswith('2'):
                names[op] = "Use sound set '%s' for channel %s" % (op[1:], op[0])
            elif 'CHANNEL_AUDIO' in op:
                names[op] = 'Channel %i is' % (op[-1] == '2' and 2 or 1)
        menu.Menu.__init__(self, options, vals, {}, names, title='Choose sound sets to Sound n-back tasks.')

    def close(self):
        config.cfg.AUDIO1_SETS = []
        config.cfg.AUDIO2_SETS = []
        for k, v in self.new_sets.items():
            if k.startswith('1') and v:
                config.cfg.AUDIO1_SETS.append(k[1:])
            elif k.startswith('2') and v:
                config.cfg.AUDIO2_SETS.append(k[1:])
        config.cfg.CHANNEL_AUDIO1 = self.values['config.cfg.CHANNEL_AUDIO1'].value()
        config.cfg.CHANNEL_AUDIO2 = self.values['config.cfg.CHANNEL_AUDIO2'].value()
        menu.Menu.close(self)
        g.update_all_labels()

    def select(self):
        menu.Menu.select(self)
        for c in ('1', '2'):
            if not [v for k, v in self.values.items() if (k.startswith(c) and v and not isinstance(v, g.Cycler))]:
                options = res.resourcepaths['sounds'].keys()
                options.remove('operations')
                i = 0
                if self.selpos == 0:
                    i = random.randint(1, len(options) - 1)
                elif self.selpos == len(options) + 1:
                    i = random.randint(len(options) + 2, 2 * len(options))
                elif self.selpos > len(options) + 1:
                    i = len(options) + 1
                self.values[self.options[i]] = True
            self.update_labels()
