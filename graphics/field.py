import config
import window as wnd
import modes as md
from pyglet.gl import *


# this class controls the field.
# the field is the grid on which the squares appear
class Field:
    def __init__(self):
        self.v_crosshair = 0
        if config.cfg.FIELD_EXPAND:
            self.size = int(wnd.window.height * 0.85)
        else:
            self.size = int(wnd.window.height * 0.625)
        if config.cfg.BLACK_BACKGROUND:
            self.color = (64, 64, 64)
        else:
            self.color = (192, 192, 192)
        self.color4 = self.color * 4
        self.color8 = self.color * 8
        self.center_x = wnd.window.width // 2
        if config.cfg.FIELD_EXPAND:
            self.center_y = wnd.window.height // 2
        else:
            self.center_y = wnd.window.height // 2 + 20
        self.x1 = self.center_x - self.size / 2
        self.x2 = self.center_x + self.size / 2
        self.x3 = self.center_x - self.size / 6
        self.x4 = self.center_x + self.size / 6
        self.y1 = self.center_y - self.size / 2
        self.y2 = self.center_y + self.size / 2
        self.y3 = self.center_y - self.size / 6
        self.y4 = self.center_y + self.size / 6

        # add the inside lines
        if config.cfg.GRIDLINES:
            self.v_lines = wnd.batch.add(8, GL_LINES, None, ('v2i', (
                self.x1, self.y3,
                self.x2, self.y3,
                self.x1, self.y4,
                self.x2, self.y4,
                self.x3, self.y1,
                self.x3, self.y2,
                self.x4, self.y1,
                self.x4, self.y2)),
                                     ('c3B', self.color8))

        self.crosshair_visible = False
        # initialize crosshair
        self.crosshair_update()

    # draw the target cross in the center
    def crosshair_update(self):
        if not config.cfg.CROSSHAIRS:
            return
        if (not md.mode.paused) and 'position1' in md.mode.modalities[md.mode.mode] and not config.cfg.VARIABLE_NBACK:
            if self.crosshair_visible:
                return
            else:
                self.v_crosshair = wnd.batch.add(4, GL_LINES, None, ('v2i', (
                    self.center_x - 8, self.center_y,
                    self.center_x + 8, self.center_y,
                    self.center_x, self.center_y - 8,
                    self.center_x, self.center_y + 8)), ('c3B', self.color4))
                self.crosshair_visible = True
        else:
            if self.crosshair_visible:
                self.v_crosshair.delete()
                self.crosshair_visible = False
            else:
                return


