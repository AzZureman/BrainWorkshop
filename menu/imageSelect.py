import random
import config
import resource as res
import menu
import graphics as g


class ImageSelect(menu.Menu):
    def __init__(self):
        imagesets = res.resourcepaths['sprites']
        self.new_sets = {}
        for image in imagesets:
            self.new_sets[image] = image in config.cfg.IMAGE_SETS
        options = self.new_sets.keys()
        options.sort()
        vals = self.new_sets
        menu.Menu.__init__(self, options, vals, title='Choose images to use for the Image n-back tasks.')

    def close(self):
        while config.cfg.IMAGE_SETS:
            config.cfg.IMAGE_SETS.remove(config.cfg.IMAGE_SETS[0])
        for k, v in self.new_sets.items():
            if v:
                config.cfg.IMAGE_SETS.append(k)
            menu.Menu.close(self)
        g.update_all_labels()

    def select(self):
        menu.Menu.select(self)
        if not [val for val in self.values.values() if (val and not isinstance(val, g.Cycler))]:
            i = 0
            if self.selpos == 0:
                i = random.randint(1, len(self.options) - 1)
            self.values[self.options[i]] = True
            self.update_labels()
