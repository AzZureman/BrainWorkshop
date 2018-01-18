import config
import window as wnd
import modes as md
import pyglet
from pyglet.gl import *
import time
import stats as st


class Saccadic:
    def __init__(self):
        self.position = 'left'
        self.counter = 0
        self.radius = 10
        self.color = (0, 0, 255, 255)
        self.start_time = None

    def tick(self):
        self.counter += 1
        if self.counter == config.cfg.SACCADIC_REPETITIONS:
            self.stop()
        elif self.position == 'left':
            self.position = 'right'
        else:
            self.position = 'left'

    def start(self):
        self.start_time = time.time()
        self.position = 'left'
        md.mode.saccadic = True
        self.counter = 0
        pyglet.clock.schedule_interval(self.tick, config.cfg.SACCADIC_DELAY)

    def stop(self):
        elapsed_time = time.time() - self.start_time
        st.stats.log_saccadic(self.start_time, elapsed_time, self.counter)

        pyglet.clock.unschedule(self.tick)
        md.mode.saccadic = False

    def draw(self):
        x = 0
        y = wnd.window.height / 2
        if self.position == 'left':
            x = self.radius
        elif self.position == 'right':
            x = wnd.window.width - self.radius
        pyglet.graphics.draw(4, GL_POLYGON, ('v2i', (
            x - self.radius, y - self.radius,  # lower-left
            x + self.radius, y - self.radius,  # lower-right
            x + self.radius, y + self.radius,  # upper-right
            x - self.radius, y + self.radius,  # upper-left
        )), ('c4B', self.color * 4))
