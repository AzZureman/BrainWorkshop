import random
import webbrowser
import pyglet
from pyglet.gl import *
from pyglet.window import key
import config
import parameters as param
import window as wnd


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
""")]  # feel free to add more paragraphs or to change the chances for the
        # paragraphs you like and dislike, etc.
        chances = [-1, 10, 10, 10, 10, 0]  # if < 0, 100% chance of being included.  Otherwise, relative weight.
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
                options.extend([i] * chances[i])
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
                                       width=(4 * wnd.window.width) / 5,
                                       font_size=14,
                                       x=wnd.window.width // 2, y=wnd.window.height // 2,
                                       anchor_x='center', anchor_y='center')
        wnd.window.push_handlers(self.on_key_press, self.on_draw)
        self.on_draw()

    def on_key_press(self, sym):
        if sym in (key.ESCAPE, key.SPACE):
            self.close()
        elif sym in (key.RETURN, key.ENTER, key.D):
            self.select()
        return pyglet.event.EVENT_HANDLED

    def select(self):
        webbrowser.open_new_tab(param.WEB_DONATE)
        self.close()

    def close(self):
        return wnd.window.remove_handlers(self.on_key_press, self.on_draw)

    def on_draw(self):
        wnd.window.clear()
        self.batch.draw()
        return pyglet.event.EVENT_HANDLED
