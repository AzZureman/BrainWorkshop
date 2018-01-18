import os
import config
import menu


class LanguageScreen(menu.Menu):
    def __init__(self):
        self.languages = languages = [fn for fn in os.listdir(os.path.join('res', 'i18n')) if fn.lower().endswith('mo')]
        try:
            default = languages.index(config.cfg.LANGUAGE + '.mo')
        except:
            default = 0
            menu.Menu.__init__(self, options=languages,
                      title=("Please select your preferred language"),
                      choose_once=True,
                      default=default)

    def save(self):
        self.select()
        menu.Menu.save(self)

    def choose(self, k, i):
        newlang = self.languages[i]
        # set the new language here