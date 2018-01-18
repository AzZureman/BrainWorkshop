import pyglet
import config
import window as wnd


messagequeue = []  # add messages generated during loading here


class Message:
    def __init__(self, msg):
        if not 'window' in globals():
            print msg  # dump it to console just in case
            messagequeue.append(msg)  # but we'll display this later
            return
        self.batch = pyglet.graphics.Batch()
        self.label = pyglet.text.Label(msg,
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

    def on_key_press(self, sym, mod):
        if sym:
            self.close()
        return pyglet.event.EVENT_HANDLED

    def close(self):
        return wnd.window.remove_handlers(self.on_key_press, self.on_draw)

    def on_draw(self):
        wnd.window.clear()
        self.batch.draw()
        return pyglet.event.EVENT_HANDLED