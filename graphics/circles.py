import config
from pyglet.gl import *
import window as wnd
import modes as md


# Circles is the 3-strikes indicator in the top left corner of the screen.
class Circles:
    def __init__(self):
        self.y = wnd.window.height - 20
        self.start_x = 30
        self.radius = 8
        self.distance = 20
        if config.cfg.BLACK_BACKGROUND:
            self.not_activated = [64, 64, 64, 255]
        else:
            self.not_activated = [192, 192, 192, 255]
        self.activated = [64, 64, 255, 255]
        if config.cfg.BLACK_BACKGROUND:
            self.invisible = [0, 0, 0, 0]
        else:
            self.invisible = [255, 255, 255, 0]

        self.circle = []
        for index in range(0, config.cfg.THRESHOLD_FALLBACK_SESSIONS - 1):
            self.circle.append(wnd.batch.add(4, GL_QUADS, None, ('v2i', (
                self.start_x + self.distance * index - self.radius,
                self.y + self.radius,
                self.start_x + self.distance * index + self.radius,
                self.y + self.radius,
                self.start_x + self.distance * index + self.radius,
                self.y - self.radius,
                self.start_x + self.distance * index - self.radius,
                self.y - self.radius)),
                                         ('c4B', self.not_activated * 4)))

        self.update()

    def update(self):
        if md.mode.manual or md.mode.started or config.cfg.JAEGGI_MODE:
            for i in range(0, config.cfg.THRESHOLD_FALLBACK_SESSIONS - 1):
                self.circle[i].colors = (self.invisible * 4)
        else:
            for i in range(0, config.cfg.THRESHOLD_FALLBACK_SESSIONS - 1):
                self.circle[i].colors = (self.not_activated * 4)
            for i in range(0, md.mode.progress):
                self.circle[i].colors = (self.activated * 4)
