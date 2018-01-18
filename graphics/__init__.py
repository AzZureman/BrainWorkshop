import pyglet
import modes as md
import config
import stats as st
from decimal import Decimal
from circles import Circles
from cycler import Cycler
from cycler import PercentCycler
from field import Field
from graph import Graph
# import labels
from labels import (UpdateLabel, GameModeLabel, JaeggiWarningLabel, KeysListLabel,
                    TitleMessageLabel, TitleKeysLabel, LogoUpperLabel, LogoLowerLabel,
                    PausedLabel, CongratsLabel, FeedbackLabel, ArithmeticAnswerLabel,
                    SessionInfoLabel, ThresholdLabel, SpaceLabel, AnalysisLabel,
                    ChartTitleLabel, ChartLabel, AverageLabel, TodayLabel, TrialsRemainingLabel)
import panhandle
from saccadic import Saccadic
from textInputScreen import TextInputScreen
from visual import Visual

visuals = [visual.Visual() for i in range(4)]
graph = Graph()
field = Field()
circles = Circles()
saccadic = Saccadic()
updateLabel = UpdateLabel()
gameModeLabel = GameModeLabel()
jaeggiWarningLabel = JaeggiWarningLabel()
keysListLabel = KeysListLabel()
logoUpperLabel = LogoUpperLabel()
logoLowerLabel = LogoLowerLabel()
titleMessageLabel = TitleMessageLabel()
titleKeysLabel = TitleKeysLabel()
pausedLabel = PausedLabel()
congratsLabel = CongratsLabel()
sessionInfoLabel = SessionInfoLabel()
thresholdLabel = ThresholdLabel()
spaceLabel = SpaceLabel()
analysisLabel = AnalysisLabel()
chartTitleLabel = ChartTitleLabel()
chartLabel = ChartLabel()
averageLabel = AverageLabel()
todayLabel = TodayLabel()
trialsRemainingLabel = TrialsRemainingLabel()
arithmeticAnswerLabel = ArithmeticAnswerLabel()
input_labels = []


def check_match(input_type, check_missed=False):
    current = 0
    correct_answer = None
    operation = 0
    # FIXME:  I'm not going to think about whether crab_back will work with
    # config.cfg.VARIABLE_NBACK yet, since I don't actually understand how the latter works

    if md.mode.flags[md.mode.mode]['crab'] == 1:
        back = 1 + 2 * ((md.mode.trial_number - 1) % md.mode.back)
    else:
        back = md.mode.back

    if config.cfg.VARIABLE_NBACK:
        nback_trial = md.mode.trial_number - md.mode.variable_list[md.mode.trial_number - back - 1] - 1
    else:
        nback_trial = md.mode.trial_number - back - 1

    if len(st.stats.session['position1']) < md.mode.back:
        return 'unknown'

    if input_type in ('visvis', 'visaudio', 'image'):
        current = md.mode.current_stim['vis']
    elif input_type in ('audiovis',):
        current = md.mode.current_stim['audio']
    if input_type in ('visvis', 'audiovis', 'image'):
        back_data = 'vis'
    elif input_type in ('visaudio',):
        back_data = 'audio'
    elif input_type is 'arithmetic':
        current = md.mode.current_stim['number']
        back_data = st.stats.session['numbers'][nback_trial]
        operation = md.mode.current_operation
    else:
        current = md.mode.current_stim[input_type]
        back_data = input_type

    if input_type == 'arithmetic':
        if operation == 'add':
            correct_answer = back_data + current
        elif operation == 'subtract':
            correct_answer = back_data - current
        elif operation == 'multiply':
            correct_answer = back_data * current
        elif operation == 'divide':
            correct_answer = Decimal(back_data) / Decimal(current)
        if correct_answer == arithmeticAnswerLabel.parse_answer():
            return 'correct'

    elif current == st.stats.session[back_data][nback_trial]:
        if check_missed:
            return 'missed'
        else:
            return 'correct'
    return 'incorrect'


def generate_input_labels():
    labels_list = []
    modalities = md.mode.modalities[md.mode.mode]
    pos = 0
    total = len(modalities)
    for m in modalities:
        if m != 'arithmetic':

            labels_list.append(labels.FeedbackLabel(m, pos, total))
        pos += 1
    return labels_list


def update_all_labels(do_analysis=False):
    updateLabel.update()
    congratsLabel.update()
    if do_analysis:
        analysisLabel.update()
    else:
        analysisLabel.update(skip=True)

    pyglet.clock.tick(poll=True)  # Prevent music/applause skipping 1

    gameModeLabel.update()
    keysListLabel.update()
    pausedLabel.update()
    sessionInfoLabel.update()
    thresholdLabel.update()
    spaceLabel.update()
    chartTitleLabel.update()
    chartLabel.update()

    pyglet.clock.tick(poll=True)  # Prevent music/applause skipping 2

    averageLabel.update()
    todayLabel.update()
    trialsRemainingLabel.update()

    update_input_labels()


def update_input_labels():
    arithmeticAnswerLabel.update()
    for label in input_labels:
        label.update()
