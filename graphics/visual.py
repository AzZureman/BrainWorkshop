import random
import math
import pyglet
from pyglet.gl import *
import config
import graphics as g
import resource as res
import window as wnd
import modes as md



# this class controls the visual cues (colored squares).
class Visual:
    def __init__(self):
        self.visible = False
        self.letters = None
        self.label = pyglet.text.Label(
            '',
            font_size=g.field.size // 6, bold=True,
            anchor_x='center', anchor_y='center', batch=wnd.batch)
        self.variable_label = pyglet.text.Label(
            '',
            font_size=g.field.size // 6, bold=True,
            anchor_x='center', anchor_y='center', batch=wnd.batch)

        self.spr_square = [pyglet.sprite.Sprite(pyglet.image.load(path))
                           for path in res.resourcepaths['misc']['colored-squares']]
        self.spr_square_size = self.spr_square[0].width

        if config.cfg.ANIMATE_SQUARES:
            self.size_factor = 0.9375
        elif config.cfg.OLD_STYLE_SQUARES:
            self.size_factor = 0.9375
        else:
            self.size_factor = 1.0
        self.size = int(g.field.size / 3 * self.size_factor)

        # load an image set
        self.load_set()

    def load_set(self, index=None):
        if type(index) == int:
            index = config.cfg.IMAGE_SETS[index]
        if index == None:
            index = random.choice(config.cfg.IMAGE_SETS)
        if hasattr(self, 'image_set_index') and index == self.image_set_index:
            return
        self.image_set_index = index
        self.image_set = [pyglet.sprite.Sprite(pyglet.image.load(path))
                          for path in res.resourcepaths['sprites'][index]]
        self.image_set_size = self.image_set[0].width

    def choose_random_images(self, number):
        self.image_indices = random.sample(range(len(self.image_set)), number)
        self.images = random.sample(self.image_set, number)

    def choose_indicated_images(self, indices):
        self.image_indices = indices
        self.images = [self.image_set[i] for i in indices]

    def spawn(self, position=0, color=1, vis=0, number=-1, operation='none', variable=0):

        self.position = position
        self.color = config.get_color(color)
        self.vis = vis

        self.center_x = g.field.center_x + (g.field.size / 3) * ((position + 1) % 3 - 1) + (g.field.size / 3 - self.size) / 2
        self.center_y = g.field.center_y + (g.field.size / 3) * ((position / 3 + 1) % 3 - 1) + (
                g.field.size / 3 - self.size) / 2

        if self.vis == 0:
            if config.cfg.OLD_STYLE_SQUARES:
                lx = self.center_x - self.size // 2 + 2
                rx = self.center_x + self.size // 2 - 2
                by = self.center_y - self.size // 2 + 2
                ty = self.center_y + self.size // 2 - 2
                cr = self.size // 5

                if config.cfg.OLD_STYLE_SHARP_CORNERS:
                    self.square = wnd.batch.add(4, GL_POLYGON, None, ('v2i', (
                        lx, by,
                        rx, by,
                        rx, ty,
                        lx, ty,)),
                                            ('c4B', self.color * 4))
                else:
                    # rounded corners: bottom-left, bottom-right, top-right, top-left
                    x = ([lx + int(cr * (1 - math.cos(math.radians(i)))) for i in range(0, 91, 10)] +
                         [rx - int(cr * (1 - math.sin(math.radians(i)))) for i in range(0, 91, 10)] +
                         [rx - int(cr * (1 - math.sin(math.radians(i)))) for i in range(90, -1, -10)] +
                         [lx + int(cr * (1 - math.cos(math.radians(i)))) for i in range(90, -1, -10)])

                    y = ([by + int(cr * (1 - math.sin(math.radians(i)))) for i in
                          range(0, 91, 10) + range(90, -1, -10)] +
                         [ty - int(cr * (1 - math.sin(math.radians(i)))) for i in
                          range(0, 91, 10) + range(90, -1, -10)])
                    xy = []
                    for a, b in zip(x, y): xy.extend((a, b))

                    self.square = wnd.batch.add(40, GL_POLYGON, None,
                                            ('v2i', xy), ('c4B', self.color * 40))

            else:
                # use sprite squares
                self.square = self.spr_square[color - 1]
                self.square.opacity = 255
                self.square.x = self.center_x - g.field.size // 6
                self.square.y = self.center_y - g.field.size // 6
                self.square.scale = 1.0 * self.size / self.spr_square_size
                self.square_size_scaled = self.square.width
                self.square.batch = wnd.batch

                # initiate square animation
                self.age = 0.0
                pyglet.clock.schedule_interval(self.animate_square, 1 / 60.)

        elif 'arithmetic' in md.mode.modalities[md.mode.mode]:  # display a number
            self.label.text = str(number)
            self.label.x = self.center_x
            self.label.y = self.center_y + 4
            self.label.color = self.color
        elif 'visvis' in md.mode.modalities[md.mode.mode]:  # display a letter
            self.label.text = self.letters[vis - 1].upper()
            self.label.x = self.center_x
            self.label.y = self.center_y + 4
            self.label.color = self.color
        elif 'image' in md.mode.modalities[md.mode.mode] \
                or 'vis1' in md.mode.modalities[md.mode.mode] \
                or (md.mode.flags[md.mode.mode]['multi'] > 1 and config.cfg.MULTI_MODE == 'image'):  # display a pictogram
            self.square = self.images[vis - 1]
            self.square.opacity = 255
            self.square.color = self.color[:3]
            self.square.x = self.center_x - g.field.size // 6
            self.square.y = self.center_y - g.field.size // 6
            self.square.scale = 1.0 * self.size / self.image_set_size
            self.square_size_scaled = self.square.width
            self.square.batch = wnd.batch

            # initiate square animation
            self.age = 0.0
            # self.animate_square(0)
            pyglet.clock.schedule_interval(self.animate_square, 1 / 60.)

        if variable > 0:
            # display variable n-back level
            self.variable_label.text = str(variable)

            if not 'position1' in md.mode.modalities[md.mode.mode]:
                self.variable_label.x = g.field.center_x
                self.variable_label.y = g.field.center_y - g.field.size // 3 + 4
            else:
                self.variable_label.x = g.field.center_x
                self.variable_label.y = g.field.center_y + 4

            self.variable_label.color = self.color

        self.visible = True

    def animate_square(self, dt):
        self.age += dt
        if md.mode.paused: return
        if not config.cfg.ANIMATE_SQUARES: return

        # factors which affect animation
        scale_addition = dt / 8
        fade_begin_time = 0.4
        fade_end_time = 0.5
        fade_end_transparency = 1.0  # 1 = fully transparent, 0.5 = half transparent

        self.square.scale += scale_addition
        dx = (self.square.width - self.square_size_scaled) // 2
        self.square.x = self.center_x - g.field.size // 6 - dx
        self.square.y = self.center_y - g.field.size // 6 - dx

        if self.age > fade_begin_time:
            factor = (1.0 - fade_end_transparency * (self.age - fade_begin_time) / (fade_end_time - fade_begin_time))
            if factor > 1.0: factor = 1.0
            if factor < 0.0: factor = 0.0
            self.square.opacity = int(255 * factor)

    def hide(self):
        if self.visible:
            self.label.text = ''
            self.variable_label.text = ''
            if 'image' in md.mode.modalities[md.mode.mode] \
                    or 'vis1' in md.mode.modalities[md.mode.mode] \
                    or (md.mode.flags[md.mode.mode]['multi'] > 1 and config.cfg.MULTI_MODE == 'image'):  # hide pictogram
                self.square.batch = None
                pyglet.clock.unschedule(self.animate_square)
            elif self.vis == 0:
                if config.cfg.OLD_STYLE_SQUARES:
                    self.square.delete()
                else:
                    self.square.batch = None
                    pyglet.clock.unschedule(self.animate_square)
            self.visible = False
