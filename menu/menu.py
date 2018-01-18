import config
import pyglet
from pyglet.gl import *
from pyglet.window import key
import window as wnd
import graphics as g


class Menu:
    """
    Menu.__init__(self, options, values={}, actions={}, names={}, title='',  choose_once=False,
                  default=0):

    A generic menu class.  The argument options is edited in-place.  Instancing
    the Menu displays the menu.  Menu will install its own event handlers for
    on_key_press, on_text, on_text_motion and on_draw, all of which
    do not pass events to later handlers on the stack.  When the user presses
    esc,  Menu pops its handlers off the stack. If the argument actions is used,
    it should be a dict with keys being options with specific actions, and values
    being a python callable which returns the new value for that option.

    """
    titlesize = 18
    choicesize = 12
    footnotesize = 10
    fontlist = ['Courier New',  # try fixed width fonts first
                'Monospace', 'Terminal', 'fixed', 'Fixed', 'Times New Roman',
                'Helvetica', 'Arial']

    def __init__(self, options, values=None, actions={}, names={}, title='',
                 footnote=('Esc: cancel     Space: modify option     Enter: apply'),
                 choose_once=False, default=0):
        self.bgcolor = (255 * int(not config.cfg.BLACK_BACKGROUND),) * 3
        self.textcolor = (255 * int(config.cfg.BLACK_BACKGROUND),) * 3 + (255,)
        self.markercolors = (0, 0, 255, 0, 255, 0, 255, 0, 0)  # (255 * int(config.cfg.BLACK_BACKGROUND), )*3*3
        self.pagesize = min(len(options), (wnd.window.height * 6 / 10) / (self.choicesize * 3 / 2))
        if type(options) == dict:
            vals = options
            self.options = options.keys()
        else:
            vals = dict([[op, None] for op in options])
            self.options = options
        self.values = values or vals  # use values if there's anything in it
        self.actions = actions
        for op in self.options:
            if not op in names.keys():
                names[op] = op
        self.names = names
        self.choose_once = choose_once
        self.disppos = 0  # which item in options is the first on the screen
        self.selpos = default  # may be offscreen?
        self.batch = pyglet.graphics.Batch()
        self.title = pyglet.text.Label(title, font_size=self.titlesize,
                                       bold=True, color=self.textcolor, batch=self.batch,
                                       x=wnd.window.width / 2, y=(wnd.window.height * 9) / 10,
                                       anchor_x='center', anchor_y='center')
        self.footnote = pyglet.text.Label(footnote, font_size=self.footnotesize,
                                          bold=True, color=self.textcolor, batch=self.batch,
                                          x=wnd.window.width / 2, y=(wnd.window.height * 2) / 10,
                                          anchor_x='center', anchor_y='center')

        self.labels = [pyglet.text.Label('', font_size=self.choicesize,
                                         bold=True, color=self.textcolor, batch=self.batch,
                                         x=wnd.window.width / 8, y=(wnd.window.height * 8) / 10 - i * (self.choicesize * 3 / 2),
                                         anchor_x='left', anchor_y='center', font_name=self.fontlist)
                       for i in range(self.pagesize)]

        self.marker = self.batch.add(3, GL_POLYGON, None, ('v2i', (0,) * 6,),
                                     ('c3B', self.markercolors))

        self.update_labels()

        wnd.window.push_handlers(self.on_key_press, self.on_text,
                             self.on_text_motion, self.on_draw)

    def textify(self, x):
        if type(x) == bool:
            return x and ('Yes') or ('No')
        return str(x)

    def update_labels(self):
        for l in self.labels: l.text = 'Hello, bug!'

        markerpos = self.selpos - self.disppos
        i = 0
        di = self.disppos
        if not di == 0:  # displacement of i
            self.labels[i].text = '...'
            i += 1
        ending = int(di + self.pagesize < len(self.options))
        while i < self.pagesize - ending and i + self.disppos < len(self.options):
            k = self.options[i + di]
            if k == 'Blank line':
                self.labels[i].text = ''
            elif k in self.values.keys() and not self.values[k] == None:
                v = self.values[k]
                self.labels[i].text = '%s:%7s' % (self.names[k].ljust(52), self.textify(v))
            else:
                self.labels[i].text = self.names[k]
            i += 1
        if ending:
            self.labels[i].text = '...'
        w, h, cs = wnd.window.width, wnd.window.height, self.choicesize
        self.marker.vertices = [w / 10, (h * 8) / 10 - markerpos * (cs * 3 / 2) + cs / 2,
                                w / 9, (h * 8) / 10 - markerpos * (cs * 3 / 2),
                                w / 10, (h * 8) / 10 - markerpos * (cs * 3 / 2) - cs / 2]

    def move_selection(self, steps, relative=True):
        # FIXME:  pageup/pagedown can occasionally cause "Hello bug!" to be displayed
        if relative:
            self.selpos += steps
        else:
            self.selpos = steps
        self.selpos = min(len(self.options) - 1, max(0, self.selpos))
        if self.disppos >= self.selpos and not self.disppos == 0:
            self.disppos = max(0, self.selpos - 1)
        if self.disppos <= self.selpos - self.pagesize + 1 \
                and not self.disppos == len(self.options) - self.pagesize:
            self.disppos = max(0, min(len(self.options), self.selpos + 1) - self.pagesize + 1)

        if not self.selpos in (0, len(self.options) - 1) and self.options[self.selpos] == 'Blank line':
            self.move_selection(int(steps > 0) * 2 - 1)
        self.update_labels()

    def on_key_press(self, sym, mod):
        if sym == key.ESCAPE:
            self.close()
        elif sym in (key.RETURN, key.ENTER):
            self.save()
            self.close()
        elif sym == key.SPACE:
            self.select()
        return pyglet.event.EVENT_HANDLED

    def select(self):
        k = self.options[self.selpos]
        i = self.selpos
        if k == "Blank line":
            pass
        elif k in self.actions.keys():
            self.values[k] = self.actions[k](k)
        elif type(self.values[k]) == bool:
            self.values[k] = not self.values[k]  # todo: other data types
        elif isinstance(self.values[k], g.Cycler):
            self.values[k].nxt()
        elif self.values[k] == None:
            self.choose(k, i)
            self.close()
        if self.choose_once:
            self.close()
        self.update_labels()

    def choose(self, k, i):  # override this method in subclasses
        print "Thank you for beta-testing our software."

    def close(self):
        return wnd.window.remove_handlers(self.on_key_press, self.on_text,
                                      self.on_text_motion, self.on_draw)

    def save(self):
        "Override me in subclasses."
        return

    def on_text_motion(self, evt):
        if evt == key.MOTION_UP:            self.move_selection(steps=-1)
        if evt == key.MOTION_DOWN:          self.move_selection(steps=1)
        if evt == key.MOTION_PREVIOUS_PAGE: self.move_selection(steps=-self.pagesize)
        if evt == key.MOTION_NEXT_PAGE:     self.move_selection(steps=self.pagesize)
        return pyglet.event.EVENT_HANDLED

    def on_text(self, evt):
        return pyglet.event.EVENT_HANDLED  # todo: entering values after select()

    def on_draw(self):
        wnd.window.clear()
        self.batch.draw()
        return pyglet.event.EVENT_HANDLED