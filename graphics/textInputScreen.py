import pyglet
from pyglet.window import key
import config
import window as wnd


class TextInputScreen:
    titlesize = 18
    textsize = 16

    def __init__(self, title='', text='', callback=None, catch=''):
        self.titletext = title
        self.text = text
        self.starttext = text
        self.bgcolor = (255 * int(not config.cfg.BLACK_BACKGROUND),) * 3
        self.textcolor = (255 * int(config.cfg.BLACK_BACKGROUND),) * 3 + (255,)
        self.batch = pyglet.graphics.Batch()
        self.title = pyglet.text.Label(title, font_size=self.titlesize,
                                       bold=True, color=self.textcolor, batch=self.batch,
                                       x=wnd.window.width / 2, y=(wnd.window.height * 9) / 10,
                                       anchor_x='center', anchor_y='center')
        self.document = pyglet.text.document.UnformattedDocument()
        self.document.set_style(0, len(self.document.text), {'color': self.textcolor})
        self.layout = pyglet.text.layout.IncrementalTextLayout(self.document,
                                                               (wnd.window.width / 2 - 20 - len(title) * 6),
                                                               (wnd.window.height * 10) / 11, batch=self.batch)
        self.layout.x = wnd.window.width / 2 + 15 + len(title) * 6
        if not callback:
            callback = lambda x: x
        self.callback = callback
        self.caret = pyglet.text.caret.Caret(self.layout)
        wnd.window.push_handlers(self.caret)
        wnd.window.push_handlers(self.on_key_press, self.on_draw)
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
            self.caret.select_paragraph(600, 0)

        wnd.window.clear()
        self.batch.draw()
        return pyglet.event.EVENT_HANDLED

    def on_key_press(self, k):
        if k in (key.ESCAPE, key.RETURN, key.ENTER):
            if k is key.ESCAPE:
                self.text = self.starttext
            else:
                self.text = self.document.text
            wnd.window.pop_handlers()
            wnd.window.pop_handlers()
        self.callback(self.text.strip())
        return pyglet.event.EVENT_HANDLED
