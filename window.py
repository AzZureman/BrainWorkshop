import parameters as param
import config
from pyglet.gl import *
import sys
import utils
import resource as res


# Create the game window
caption = []
if param.CLINICAL_MODE:
    caption.append('BW-Clinical ')
else:
    caption.append('Brain Workshop by AzZu ')
caption.append(param.VERSION)
if param.USER != 'default':
    caption.append(' - ')
    caption.append(param.USER)
if config.cfg.WINDOW_FULLSCREEN:
    style = pyglet.window.Window.WINDOW_STYLE_BORDERLESS
else:
    style = pyglet.window.Window.WINDOW_STYLE_DEFAULT


class MyWindow(pyglet.window.Window):
    def on_key_press(self, symbol, modifiers):
        pass

    def on_key_release(self, symbol, modifiers):
        pass


window = MyWindow(config.cfg.WINDOW_WIDTH, config.cfg.WINDOW_HEIGHT, caption=''.join(caption), style=style, vsync=param.VSYNC)
# if DEBUG:
#    window.push_handlers(pyglet.window.event.WindowEventLogger())
if sys.platform == 'darwin' and config.cfg.WINDOW_FULLSCREEN:
    window.set_exclusive_keyboard()
if sys.platform == 'linux2':
    window.set_icon(pyglet.image.load(res.resourcepaths['misc']['brain'][0]))

# set the background color of the window
if config.cfg.BLACK_BACKGROUND:
    glClearColor(0, 0, 0, 1)
else:
    glClearColor(1, 1, 1, 1)
if config.cfg.WINDOW_FULLSCREEN:
    window.maximize()
    window.set_mouse_visible(False)


batch = pyglet.graphics.Batch()

try:
    test_polygon = batch.add(4, GL_QUADS, None, ('v2i', (
        100, 100,
        100, 200,
        200, 200,
        200, 100)),
              ('c3B', (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)))
    test_polygon.delete()
except:
    utils.quit_with_error('Error creating test polygon. Full text of error:\n')