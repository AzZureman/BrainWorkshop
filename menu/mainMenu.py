import gameSelect
import soundSelect
import imageSelect
import userScreen
import menu


class MainMenu(menu.Menu):
    def __init__(self):
        def NotImplemented():
            raise NotImplementedError
        ops = [('game', 'Choose Game Mode', gameSelect.GameSelect),
               ('sounds', 'Choose Sounds', soundSelect.SoundSelect),
               ('images', 'Choose Images', imageSelect.ImageSelect),
               ('user', 'Choose User', userScreen.UserScreen),
               ('graph', 'Daily Progress Graph', NotImplemented),
               ('help', 'Help / Tutorial', NotImplemented),
               ('donate', 'Donate', NotImplemented),
               ('forum', 'Go to Forum / Mailing List', NotImplemented)]
        options =       [  op[0]         for op in ops]
        names   = dict( [ (op[0], op[1]) for op in ops])
        actions = dict( [ (op[0], op[2]) for op in ops])
