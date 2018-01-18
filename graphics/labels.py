import pyglet
from pyglet.window import key
import config
import parameters as param
import window as wnd
import field as f
import modes as md
import stats as st
import graphics as g
from decimal import Decimal

# __ALL__ = ["UpdateLabel", "GameModeLabel", "JaeggiWarningLabel", "KeysListLabel",
#             "TitleMessageLabel", "TitleKeysLabel", "LogoUpperLabel", "LogoLowerLabel",
#             "PausedLabel", "CongratsLabel", "FeedbackLabel", "ArithmeticAnswerLabel",
#             "SessionInfoLabel", "ThresholdLabel", "SpaceLabel", "AnalysisLabel",
#             "ChartTitleLabel", "ChartLabel", "AverageLabel", "TodayLabel", "TrialsRemainingLabel"]


# this is the update notification
class UpdateLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            multiline=True, width=f.field.size // 3 - 4, align='middle',
            font_size=11, bold=True,
            color=(0, 128, 0, 255),
            x=wnd.window.width // 2, y=f.field.center_x + f.field.size // 6,
            anchor_x='center', anchor_y='center', batch=wnd.batch)
        self.update()

    def update(self):
        if not md.mode.started and config.update_available:
            str_list = []
            str_list.append(('An update is available ('))
            str_list.append(str(config.update_version))
            str_list.append(('). Press W to open web site'))
            self.label.text = ''.join(str_list)
        else:
            self.label.text = ''


# this is the black text above the field
class GameModeLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            font_size=16,
            color=config.cfg.COLOR_TEXT,
            x=wnd.window.width // 2, y=wnd.window.height - 20,
            anchor_x='center', anchor_y='center', batch=wnd.batch)
        self.update()

    def update(self):
        if md.mode.started and md.mode.hide_text:
            self.label.text = ''
        else:
            str_list = []
            if config.cfg.JAEGGI_MODE and not param.CLINICAL_MODE:
                str_list.append(('Jaeggi mode: '))
            if md.mode.manual:
                str_list.append(('Manual mode: '))
            str_list.append(md.mode.long_mode_names[md.mode.mode] + ' ')
            if config.cfg.VARIABLE_NBACK:
                str_list.append(('V. '))
            str_list.append(str(md.mode.back))
            str_list.append(('-Back'))
            self.label.text = ''.join(str_list)

    def flash(self):
        pyglet.clock.unschedule(self.unflash)
        self.label.color = (255, 0, 255, 255)
        self.update()
        pyglet.clock.schedule_once(self.unflash, 0.5)

    def unflash(self, dt):
        self.label.color = config.cfg.COLOR_TEXT
        self.update()


class JaeggiWarningLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            font_size=12, bold=True,
            color=(255, 0, 255, 255),
            x=wnd.window.width // 2, y=f.field.center_x + f.field.size // 3 + 8,
            anchor_x='center', anchor_y='center', batch=wnd.batch)

    def show(self):
        pyglet.clock.unschedule(self.hide)
        self.label.text = ('Please disable Jaeggi Mode to access additional modes.')
        pyglet.clock.schedule_once(self.hide, 3.0)

    def hide(self, dt):
        self.label.text = ''


# this is the keyboard reference list along the left side
class KeysListLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            multiline=True, width=300, bold=False,
            font_size=9,
            color=config.cfg.COLOR_TEXT,
            x=10,
            anchor_x='left', anchor_y='top', batch=wnd.batch)
        self.update()

    def update(self):
        str_list = []
        if md.mode.started:
            self.label.y = wnd.window.height - 10
            if not md.mode.hide_text:
                str_list.append(('P: Pause / Unpause\n'))
                str_list.append('\n')
                str_list.append(('F8: Hide / Reveal Text\n'))
                str_list.append('\n')
                str_list.append(('ESC: Cancel Session\n'))
        elif param.CLINICAL_MODE:
            self.label.y = wnd.window.height - 10
            str_list.append(('ESC: Exit'))
        else:
            if md.mode.manual or config.cfg.JAEGGI_MODE:
                self.label.y = wnd.window.height - 10
            else:
                self.label.y = wnd.window.height - 40
            if 'morse' in config.cfg.AUDIO1_SETS or 'morse' in config.cfg.AUDIO2_SETS:
                str_list.append(('J: Morse Code Reference\n'))
                str_list.append('\n')
            str_list.append(('H: Help / Tutorial\n'))
            str_list.append('\n')
            if md.mode.manual:
                str_list.append(('F1: Decrease N-Back\n'))
                str_list.append(('F2: Increase N-Back\n'))
                str_list.append('\n')
                str_list.append(('F3: Decrease Trials\n'))
                str_list.append(('F4: Increase Trials\n'))
                str_list.append('\n')
            if md.mode.manual:
                str_list.append(('F5: Decrease Speed\n'))
                str_list.append(('F6: Increase Speed\n'))
                str_list.append('\n')
            str_list.append(('C: Choose Game Type\n'))
            str_list.append(('S: Select Sounds\n'))
            str_list.append(('I: Select Images\n'))
            if md.mode.manual:
                str_list.append(('M: Standard Mode\n'))
            else:
                str_list.append(('M: Manual Mode\n'))
            str_list.append(('D: Donate\n'))
            str_list.append('\n')
            str_list.append(('G: Daily Progress Graph\n'))
            str_list.append('\n')
            str_list.append(('W: Brain Workshop Web Site\n'))
            if config.cfg.WINDOW_FULLSCREEN:
                str_list.append(('E: Saccadic Eye Exercise\n'))
            str_list.append('\n')
            str_list.append(('ESC: Exit\n'))

        self.label.text = ''.join(str_list)


class TitleMessageLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            ('Brain Workshop'),
            # multiline = True, width = wnd.window.width // 2,
            font_size=32, bold=True, color=config.cfg.COLOR_TEXT,
            x=wnd.window.width // 2, y=wnd.window.height - 35,
            anchor_x='center', anchor_y='center')
        self.label2 = pyglet.text.Label(
            ('Version ') + str(param.VERSION),
            font_size=14, bold=False, color=config.cfg.COLOR_TEXT,
            x=wnd.window.width // 2, y=wnd.window.height - 75,
            anchor_x='center', anchor_y='center')

    def draw(self):
        self.label.draw()
        self.label2.draw()


class TitleKeysLabel:
    def __init__(self):
        str_list = []
        if not (config.cfg.JAEGGI_MODE or param.CLINICAL_MODE):
            str_list.append(('C: Choose Game Mode\n'))
            str_list.append(('S: Choose Sounds\n'))
            str_list.append(('I: Choose Images\n'))
        if not param.CLINICAL_MODE:
            str_list.append(('U: Choose User\n'))
            str_list.append(('G: Daily Progress Graph\n'))
        str_list.append(('H: Help / Tutorial\n'))
        if not param.CLINICAL_MODE:
            str_list.append(('D: Donate\n'))
            str_list.append(('F: Go to Forum / Mailing List\n'))
            str_list.append(('O: Edit configuration file'))

        self.keys = pyglet.text.Label(
            ''.join(str_list),
            multiline=True, width=260,
            font_size=12, bold=True, color=config.cfg.COLOR_TEXT,
            x=wnd.window.width // 2, y=230,
            anchor_x='center', anchor_y='top')

        self.space = pyglet.text.Label(
            ('Press SPACE to enter the Workshop'),
            font_size=20, bold=True, color=(32, 32, 255, 255),
            x=wnd.window.width // 2, y=35,
            anchor_x='center', anchor_y='center')

    def draw(self):
        self.space.draw()
        self.keys.draw()


# this is the word "brain" above the brain logo.
class LogoUpperLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            'Brain',  # I think we shouldn't translate the program name.  Yes?
            font_size=11, bold=True,
            color=config.cfg.COLOR_TEXT,
            x=f.field.center_x, y=f.field.center_y + 30,
            anchor_x='center', anchor_y='center')

    def draw(self):
        self.label.draw()


# this is the word "workshop" below the brain logo.
class LogoLowerLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            'Workshop',
            font_size=11, bold=True,
            color=config.cfg.COLOR_TEXT,
            x=f.field.center_x, y=f.field.center_y - 27,
            anchor_x='center', anchor_y='center')

    def draw(self):
        self.label.draw()


# this is the word "Paused" which appears when the game is paused.
class PausedLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            font_size=14,
            color=(64, 64, 255, 255),
            x=f.field.center_x, y=f.field.center_y,
            anchor_x='center', anchor_y='center', batch=wnd.batch)
        self.update()

    def update(self):
        if md.mode.paused:
            self.label.text = 'Paused'
        else:
            self.label.text = ''


# this is the congratulations message which appears when advancing N-back levels.
class CongratsLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            font_size=14,
            color=(255, 32, 32, 255),
            x=f.field.center_x, y=wnd.window.height - 47,
            anchor_x='center', anchor_y='center', batch=wnd.batch)
        self.update()

    def update(self, show=False, advance=False, fallback=False, awesome=False, great=False, good=False, perfect=False):
        str_list = []
        if show and not param.CLINICAL_MODE and config.cfg.USE_SESSION_FEEDBACK:
            if perfect:
                str_list.append(('Perfect score! '))
            elif awesome:
                str_list.append(('Awesome score! '))
            elif great:
                str_list.append(('Great score! '))
            elif good:
                str_list.append(('Not bad! '))
            else:
                str_list.append(('Keep trying. You\'re getting there! '))
        if advance:
            str_list.append(('N-Back increased'))
        elif fallback:
            str_list.append(('N-Back decreased'))
        self.label.text = ''.join(str_list)


class FeedbackLabel:
    def __init__(self, modality, pos=0, total=1):
        """
        Generic text label for giving user feedback during N-back sessions.  All
        of the feedback labels should be instances of this class.

        pos should be which label number this one is displayed as (order: left-to-right).
        total should be the total number of feedback labels for this mode.
        """
        self.modality = modality
        self.letter = key.symbol_string(config.cfg['KEY_%s' % modality.upper()])
        if self.letter == 'SEMICOLON':
            self.letter = ';'
        modalityname = modality
        if modalityname.endswith('vis'):
            modalityname = modalityname[:-3] + ' & n-vis'
        elif modalityname.endswith('audio') and not modalityname == 'audio':
            modalityname = modalityname[:-5] + ' & n-audio'
        if md.mode.flags[md.mode.mode]['multi'] == 1 and modalityname == 'position1':
            modalityname = 'position'

        if total == 2 and not config.cfg.JAEGGI_MODE and config.cfg.ENABLE_MOUSE:
            if pos == 0:
                self.mousetext = "Left-click or"
            if pos == 1:
                self.mousetext = "Right-click or"
        else:
            self.mousetext = ""

        self.text = "%s %s: %s" % ((self.mousetext), self.letter, (modalityname))  # FIXME: will this break pyglettext?

        if total < 4:
            self.text += (' match')
            font_size = 16
        elif total < 5:
            font_size = 14
        elif total < 6:
            font_size = 13
        else:
            font_size = 11

        self.label = pyglet.text.Label(
            text=self.text,
            x=-200, y=30,  # we'll fix this position later, after we see how big the label is
            anchor_x='left', anchor_y='center', batch=wnd.batch, font_size=font_size)
        # w = self.label.width  # this doesn't work; how are you supposed to find the width of a label texture?
        w = (len(self.text) * font_size * 4) / 5
        dis = (wnd.window.width - 100) / float(total - .99)
        x = 30 + int(pos * dis - w * pos / (total - .5))

        # draw an icon next to the label for multi-stim mode
        if md.mode.flags[md.mode.mode]['multi'] > 1 and self.modality[-1].isdigit():
            self.id = int(modality[-1])
            if config.cfg.MULTI_MODE == 'color':
                self.icon = pyglet.sprite.Sprite(
                    g.visuals[self.id - 1].spr_square[config.cfg.VISUAL_COLORS[self.id - 1] - 1].image)
                self.icon.scale = .125 * g.visuals[self.id - 1].size / g.visuals[self.id - 1].image_set_size
                self.icon.y = 22
                self.icon.x = x - 15
                x += 15

            else:  # 'image'
                self.icon = pyglet.sprite.Sprite(g.visuals[self.id - 1].images[self.id - 1].image)
                self.icon.color = config.get_color(1)[:3]
                self.icon.scale = .25 * g.visuals[self.id - 1].size / g.visuals[self.id - 1].image_set_size
                self.icon.y = 15
                self.icon.x = x - 25
                x += 25

            self.icon.opacity = 255
            self.icon.batch = wnd.batch

        self.label.x = x

        self.update()

    def draw(self):
        pass  # don't draw twice; this was just for debugging
        # self.label.draw()

    def update(self):
        if md.mode.started and not md.mode.hide_text and self.modality in md.mode.modalities[md.mode.mode]:  # still necessary?
            self.label.text = self.text
        else:
            self.label.text = ''
        if config.cfg.SHOW_FEEDBACK and md.mode.inputs[self.modality]:
            result = g.check_match(self.modality)
            # self.label.bold = True
            if result == 'correct':
                self.label.color = config.cfg.COLOR_LABEL_CORRECT
            elif result == 'unknown':
                self.label.color = config.cfg.COLOR_LABEL_OOPS
            elif result == 'incorrect':
                self.label.color = config.cfg.COLOR_LABEL_INCORRECT
        elif config.cfg.SHOW_FEEDBACK and (not md.mode.inputs['audiovis']) and md.mode.show_missed:
            result = g.check_match(self.modality, check_missed=True)
            if result == 'missed':
                self.label.color = config.cfg.COLOR_LABEL_OOPS
                # self.label.bold = True
        else:
            self.label.color = config.cfg.COLOR_TEXT
            self.label.bold = False

    def delete(self):
        self.label.delete()
        if md.mode.flags[md.mode.mode]['multi'] > 1 and self.modality[-1].isdigit():
            self.icon.batch = None


class ArithmeticAnswerLabel:
    def __init__(self):
        self.answer = []
        self.negative = False
        self.decimal = False
        self.label = pyglet.text.Label(
            '',
            x=wnd.window.width / 2 - 40, y=30,
            anchor_x='left', anchor_y='center', batch=wnd.batch)
        self.update()

    def update(self):
        if not 'arithmetic' in md.mode.modalities[md.mode.mode] or not md.mode.started:
            self.label.text = ''
            return
        if md.mode.started and md.mode.hide_text:
            self.label.text = ''
            return

        self.label.font_size = 16
        str_list = []
        str_list.append(('Answer: '))
        str_list.append(str(self.parse_answer()))
        self.label.text = ''.join(str_list)

        if config.cfg.SHOW_FEEDBACK and md.mode.show_missed:
            result = g.check_match('arithmetic')
            if result == ('correct'):
                self.label.color = config.cfg.COLOR_LABEL_CORRECT
                self.label.bold = True
            if result == ('incorrect'):
                self.label.color = config.cfg.COLOR_LABEL_INCORRECT
                self.label.bold = True
        else:
            self.label.color = config.cfg.COLOR_TEXT
            self.label.bold = False

    def parse_answer(self):
        chars = ''.join(self.answer)
        if chars == '' or chars == '.':
            result = Decimal('0')
        else:
            result = Decimal(chars)
        if self.negative:
            result = Decimal('0') - result
        return result

    def input(self, input):
        if input == '-':
            if self.negative:
                self.negative = False
            else:
                self.negative = True
        elif input == '.':
            if not self.decimal:
                self.decimal = True
                self.answer.append(input)
        else:
            self.answer.append(input)
        self.update()

    def reset_input(self):
        self.answer = []
        self.negative = False
        self.decimal = False
        self.update()


# this is the text that shows the seconds per trial and the number of trials.
class SessionInfoLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            multiline=True, width=128,
            font_size=11,
            color=config.cfg.COLOR_TEXT,
            x=20, y=f.field.center_y - 145,
            anchor_x='left', anchor_y='top', batch=wnd.batch)
        self.update()

    def update(self):
        if md.mode.started or param.CLINICAL_MODE:
            self.label.text = ''
        else:
            self.label.text = 'Session:\n%1.2f sec/trial\n%i+%i trials\n%i seconds' % \
                              (md.mode.ticks_per_trial / 10.0, md.mode.num_trials,
                               md.mode.num_trials_total - md.mode.num_trials,
                               int((md.mode.ticks_per_trial / 10.0) * md.mode.num_trials_total))

    def flash(self):
        pyglet.clock.unschedule(self.unflash)
        self.label.bold = True
        self.update()
        pyglet.clock.schedule_once(self.unflash, 1.0)

    def unflash(self, dt):
        self.label.bold = False
        self.update()


# this is the text that shows the seconds per trial and the number of trials.

class ThresholdLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            multiline=True, width=155,
            font_size=11,
            color=config.cfg.COLOR_TEXT,
            x=wnd.window.width - 20, y=f.field.center_y - 145,
            anchor_x='right', anchor_y='top', batch=wnd.batch)
        self.update()

    def update(self):
        if md.mode.started or md.mode.manual or param.CLINICAL_MODE:
            self.label.text = ''
        else:
            self.label.text = (u'Thresholds:\nRaise level: \u2265 %i%%\nLower level: < %i%%') % \
                              (config.get_threshold_advance(), config.get_threshold_fallback())  # '\u2265' = '>='


# this controls the "press space to begin session #" text.
class SpaceLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            font_size=16,
            bold=True,
            color=(32, 32, 255, 255),
            x=wnd.window.width // 2, y=62,
            anchor_x='center', anchor_y='center', batch=wnd.batch)
        self.update()

    def update(self):
        if md.mode.started:
            self.label.text = ''
        else:
            str_list = []
            str_list.append(('Press SPACE to begin session #'))
            str_list.append(str(md.mode.session_number + 1))
            str_list.append(': ')
            str_list.append(md.mode.long_mode_names[md.mode.mode] + ' ')

            if config.cfg.VARIABLE_NBACK:
                str_list.append(('V. '))
            str_list.append(str(md.mode.back))
            str_list.append(('-Back'))
            self.label.text = ''.join(str_list)


# this controls the statistics which display upon completion of a session.
class AnalysisLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            font_size=14,
            color=config.cfg.COLOR_TEXT,
            x=wnd.window.width // 2, y=92,
            anchor_x='center', anchor_y='center', batch=wnd.batch)
        self.update()

    def update(self, skip=False):
        if md.mode.started or md.mode.session_number == 0 or skip:
            self.label.text = ''
            return

        poss_mods = ['position1', 'position2', 'position3', 'position4',
                     'vis1', 'vis2', 'vis3', 'vis4', 'color', 'visvis',
                     'visaudio', 'audiovis', 'image', 'audio',
                     'audio2', 'arithmetic']  # arithmetic must be last so it's easy to exclude

        rights = dict([(mod, 0) for mod in poss_mods])
        wrongs = dict([(mod, 0) for mod in poss_mods])
        category_percents = dict([(mod, 0) for mod in poss_mods])

        mods = md.mode.modalities[md.mode.mode]
        data = st.stats.session

        for mod in mods:
            for x in range(md.mode.back, len(data['position1'])):

                if md.mode.flags[md.mode.mode]['crab'] == 1:
                    back = 1 + 2 * (x % md.mode.back)
                else:
                    back = md.mode.back
                if config.cfg.VARIABLE_NBACK:
                    back = md.mode.variable_list[x - back]

                # data is a dictionary of lists.
                if mod in ['position1', 'position2', 'position3', 'position4',
                           'vis1', 'vis2', 'vis3', 'vis4', 'audio', 'audio2', 'color', 'image']:
                    rights[mod] += int((data[mod][x] == data[mod][x - back]) and data[mod + '_input'][x])
                    wrongs[mod] += int((data[mod][x] == data[mod][x - back]) ^ data[mod + '_input'][x])  # ^ is XOR
                    if config.cfg.JAEGGI_SCORING:
                        rights[mod] += int(data[mod][x] != data[mod][x - back] and not data[mod + '_input'][x])

                if mod in ['visvis', 'visaudio', 'audiovis']:
                    modnow = mod.startswith('vis') and 'vis' or 'audio'  # these are the python<2.5 compatible versions
                    modthn = mod.endswith('vis') and 'vis' or 'audio'  # of 'vis' if mod.startswith('vis') else 'audio'
                    rights[mod] += int((data[modnow][x] == data[modthn][x - back]) and data[mod + '_input'][x])
                    wrongs[mod] += int((data[modnow][x] == data[modthn][x - back]) ^ data[mod + '_input'][x])
                    if config.cfg.JAEGGI_SCORING:
                        rights[mod] += int(data[modnow][x] != data[modthn][x - back] and not data[mod + '_input'][x])

                if mod in ['arithmetic']:
                    ops = {'add': '+', 'subtract': '-', 'multiply': '*', 'divide': '/'}
                    answer = eval(
                        "Decimal(data['numbers'][x-back]) %s Decimal(data['numbers'][x])" % ops[data['operation'][x]])
                    rights[mod] += int(
                        answer == Decimal(data[mod + '_input'][x]))  # data[...][x] is only Decimal if op == /
                    wrongs[mod] += int(answer != Decimal(data[mod + '_input'][x]))

        str_list = []
        if not param.CLINICAL_MODE:
            str_list += [('Correct-Errors:   ')]
            sep = '   '
            keys = dict([(mod, config.cfg['KEY_%s' % mod.upper()]) for mod in poss_mods[:-1]])  # exclude 'arithmetic'

            for mod in poss_mods[:-1]:  # exclude 'arithmetic'
                if mod in mods:
                    keytext = key.symbol_string(keys[mod])
                    if keytext == 'SEMICOLON': keytext = ';'
                    str_list += ["%s:%i-%i%s" % (keytext, rights[mod], wrongs[mod], sep)]

            if 'arithmetic' in mods:
                str_list += ["%s:%i-%i%s" % (("Arithmetic"), rights['arithmetic'], wrongs['arithmetic'], sep)]

        def calc_percent(r, w):
            if r + w:
                return int(r * 100 / float(r + w))
            else:
                return 0

        right = sum([rights[mod] for mod in mods])
        wrong = sum([wrongs[mod] for mod in mods])

        for mod in mods:
            category_percents[mod] = calc_percent(rights[mod], wrongs[mod])

        if config.cfg.JAEGGI_SCORING:
            percent = min([category_percents[m] for m in md.mode.modalities[md.mode.mode]])
            # percent = min(category_percents['position1'], category_percents['audio']) # config.cfg.JAEGGI_MODE forces md.mode.mode==2
            if not param.CLINICAL_MODE:
                str_list += [('Lowest score: %i%%') % percent]
        else:
            percent = calc_percent(right, wrong)
            str_list += [('Score: %i%%') % percent]

        self.label.text = ''.join(str_list)

        st.stats.submit_session(percent, category_percents)


# this controls the title of the session history chart.
class ChartTitleLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            font_size=10,
            bold=True,
            color=config.cfg.COLOR_TEXT,
            x=wnd.window.width - 10,
            y=wnd.window.height - 85,
            anchor_x='right',
            anchor_y='top',
            batch=wnd.batch)
        self.update()

    def update(self):
        if md.mode.started:
            self.label.text = ''
        else:
            self.label.text = ('Today\'s Last 20:')


# this controls the session history chart.
class ChartLabel:
    def __init__(self):
        self.start_x = wnd.window.width - 140
        self.start_y = wnd.window.height - 105
        self.line_spacing = 15
        self.column_spacing_12 = 30
        self.column_spacing_23 = 70
        self.font_size = 10
        self.color_normal = (128, 128, 128, 255)
        self.color_advance = (0, 160, 0, 255)
        self.color_fallback = (160, 0, 0, 255)
        self.column1 = []
        self.column2 = []
        self.column3 = []
        for zap in range(0, 20):
            self.column1.append(pyglet.text.Label(
                '', font_size=self.font_size,
                x=self.start_x, y=self.start_y - zap * self.line_spacing,
                anchor_x='left', anchor_y='top', batch=wnd.batch))
            self.column2.append(pyglet.text.Label(
                '', font_size=self.font_size,
                x=self.start_x + self.column_spacing_12, y=self.start_y - zap * self.line_spacing,
                anchor_x='left', anchor_y='top', batch=wnd.batch))
            self.column3.append(pyglet.text.Label(
                '', font_size=self.font_size,
                x=self.start_x + self.column_spacing_12 + self.column_spacing_23,
                y=self.start_y - zap * self.line_spacing,
                anchor_x='left', anchor_y='top', batch=wnd.batch))
        st.stats.parse_statsfile()
        self.update()

    def update(self):
        for x in range(0, 20):
            self.column1[x].text = ''
            self.column2[x].text = ''
            self.column3[x].text = ''
        if md.mode.started: return
        index = 0
        for x in range(len(st.stats.history) - 20, len(st.stats.history)):
            if x < 0: continue
            manual = st.stats.history[x][4]
            color = self.color_normal
            if not manual and st.stats.history[x][3] >= config.get_threshold_advance():
                color = self.color_advance
            elif not manual and st.stats.history[x][3] < config.get_threshold_fallback():
                color = self.color_fallback
            self.column1[index].color = color
            self.column2[index].color = color
            self.column3[index].color = color
            if manual:
                self.column1[index].text = 'M'
            elif st.stats.history[x][0] > -1:
                self.column1[index].text = '#%i' % st.stats.history[x][0]
            self.column2[index].text = md.mode.short_name(mode=st.stats.history[x][1], back=st.stats.history[x][2])
            self.column3[index].text = '%i%%' % st.stats.history[x][3]
            index += 1


# this controls the title of the session history chart.
class AverageLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            font_size=10, bold=False,
            color=config.cfg.COLOR_TEXT,
            x=wnd.window.width - 10, y=wnd.window.height - 55,
            anchor_x='right', anchor_y='top', batch=wnd.batch)
        self.update()

    def update(self):
        if md.mode.started or param.CLINICAL_MODE:
            self.label.text = ''
        else:
            sessions = [sess for sess in st.stats.history if sess[1] == md.mode.mode][-20:]
            if sessions:
                average = sum([sess[2] for sess in sessions]) / float(len(sessions))
            else:
                average = 0.
            self.label.text = ("%sNB average: %1.2f") % (md.mode.short_mode_names[md.mode.mode], average)


class TodayLabel:
    def __init__(self):
        self.labelTitle = pyglet.text.Label(
            '',
            font_size=9,
            color=config.cfg.COLOR_TEXT,
            x=wnd.window.width, y=wnd.window.height - 5,
            anchor_x='right', anchor_y='top', width=280, multiline=True, batch=wnd.batch)
        self.update()

    def update(self):
        if md.mode.started:
            self.labelTitle.text = ''
        else:
            total_trials = sum([md.mode.num_trials + md.mode.num_trials_factor * \
                                his[2] ** md.mode.num_trials_exponent for his in st.stats.history])
            total_time = md.mode.ticks_per_trial * param.TICK_DURATION * total_trials

            self.labelTitle.text = ("%i min %i sec done today in %i sessions\
			    %i min %i sec done in last 24 hours in %i sessions" % (
            st.stats.time_today // 60, st.stats.time_today % 60, st.stats.sessions_today, st.stats.time_thours // 60,
            st.stats.time_thours % 60, st.stats.sessions_thours))


class TrialsRemainingLabel:
    def __init__(self):
        self.label = pyglet.text.Label(
            '',
            font_size=12, bold=True,
            color=config.cfg.COLOR_TEXT,
            x=wnd.window.width - 10, y=wnd.window.height - 5,
            anchor_x='right', anchor_y='top', batch=wnd.batch)
        self.update()

    def update(self):
        if (not md.mode.started) or md.mode.hide_text:
            self.label.text = ''
        else:
            self.label.text = ('%i remaining') % (md.mode.num_trials_total - md.mode.trial_number)
