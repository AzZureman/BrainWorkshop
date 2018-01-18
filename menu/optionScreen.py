import menu
import config


class OptionsScreen(menu.Menu):
    def __init__(self):
        """
        Sorta works.  Not yet useful, though.
        """
        options = config.cfg.keys()
        options.sort()
        menu.Menu.__init__(self, options=options, values=config.cfg, title=('Configuration'))