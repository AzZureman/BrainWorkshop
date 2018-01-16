# All changeable game state variables are located in an instance of the Mode class
class Mode:
    def __init__(self):
        self.mode=cfg.GAME_MODE
        self.back=default_nback_mode(self.mode)
        self.ticks_per_trial=default_ticks(self.mode)
        self.num_trials=cfg.NUM_TRIALS
        self.num_trials_factor=cfg.NUM_TRIALS_FACTOR
        self.num_trials_exponent=cfg.NUM_TRIALS_EXPONENT
        self.num_trials_total=self.num_trials+self.num_trials_factor*\self.back ** self.num_trials_exponent

        self.short_mode_names = {2:'D',
            3:'PCA',
            4:'DC',
            5:'TC',
            6:'QC',
            7:'A',
            8:'DA',
            9:'TA',
            10:'Po',
            11:'Au',
            12:'TCC',
            20:'PC',
            21:'PI',
            22:'CA',
            23:'IA',
            24:'CI',
            25:'PCI',
            26:'PIA',
            27:'CIA',
            28:'Q',
            100:'AA',
            101:'PAA',
            102:'CAA',
            103:'IAA',
            104:'PCAA',
            105:'PIAA',
            106:'CIAA',
            107:'P'
        }

        self.long_mode_names =  {2:_('Dual'),
            3:_('Position, Color, Sound'),
            4:_('Dual Combination'),
            5:_('Tri Combination'),
            6:_('Quad Combination'),
            7:_('Arithmetic'),
            8:_('Dual Arithmetic'),
            9:_('Triple Arithmetic'),
            10:_('Position'),
            11:_('Sound'),
            12:_('Tri Combination (Color)'),
            20:_('Position, Color'),
            21:_('Position, Image'),
            22:_('Color, Sound'),
            23:_('Image, Sound'),
            24:_('Color, Image'),
            25:_('Position, Color, Image'),
            26:_('Position, Image, Sound'),
            27:_('Color, Image, Sound'),
            28:_('Quad'),
            100:_('Sound, Sound2'),
            101:_('Position, Sound, Sound2'),
            102:_('Color, Sound, Sound2'),
            103:_('Image, Sound, Sound2'),
            104:_('Position, Color, Sound, Sound2'),
            105:_('Position, Image, Sound, Sound2'),
            106:_('Color, Image, Sound, Sound2'),
            107:_('Pentuple')
        }

        self.modalities = { 2:['position1', 'audio'],
            3:['position1', 'color', 'audio'],
            4:['visvis', 'visaudio', 'audiovis', 'audio'],
            5:['position1', 'visvis', 'visaudio', 'audiovis', 'audio'],
            6:['position1', 'visvis', 'visaudio', 'color', 'audiovis', 'audio'],
            7:['arithmetic'],
            8:['position1', 'arithmetic'],
            9:['position1', 'arithmetic', 'color'],
            10:['position1'],
            11:['audio'],
            12:['visvis', 'visaudio', 'color', 'audiovis', 'audio'],
            20:['position1', 'color'],
            21:['position1', 'image'],
            22:['color', 'audio'],
            23:['image', 'audio'],
            24:['color', 'image'],
            25:['position1', 'color', 'image'],
            26:['position1', 'image', 'audio'],
            27:['color', 'image', 'audio'],
            28:['position1', 'color', 'image', 'audio'],
            100:['audio', 'audio2'],
            101:['position1', 'audio', 'audio2'],
            102:['color', 'audio', 'audio2'],
            103:['image', 'audio', 'audio2'],
            104:['position1', 'color', 'audio', 'audio2'],
            105:['position1', 'image', 'audio', 'audio2'],
            106:['color', 'image', 'audio', 'audio2'],
            107:['position1', 'color', 'image', 'audio', 'audio2']
        }

        self.flags = {}

        # generate crab modes
        for m in self.short_mode_names.keys():
            nm = m | 128                          # newmode; Crab DNB = 2 | 128 = 130
            self.flags[m]  = {'crab':0, 'multi':1, 'selfpaced':0  }# forwards
            self.flags[nm] = {'crab':1, 'multi':1, 'selfpaced':0  }# every (self.back) stimuli are reversed for matching
            self.short_mode_names[nm] = 'C' + self.short_mode_names[m]
            self.long_mode_names[nm] = _('Crab ') + self.long_mode_names[m]
            self.modalities[nm] = self.modalities[m]
            [:] # the [:] at the end is
            # so we take a copy of the list, in case we want to change it later

        # generate multi-stim modes
        for m in self.short_mode_names.keys():
            for n, s in [(2, _('Double-stim')), (3, _('Triple-stim')), (4, _('Quadruple-stim'))]:
                if set(['color', 'image']).issubset(self.modalities[m])\
                        or not 'position1' in self.modalities[m]\
                        or set\
                    (['visvis', 'arithmetic']).intersection(self.modalities[m]):  # Combination? AAAH! Scary!
                    continue
                nm = m | 256 * (n-1)               # newmode; 3xDNB = 2 | 512 = 514
                self.flags[nm] = dict(self.flags[m]) # take a copy
                self.flags[nm]['multi'] = n
                self.short_mode_names[nm] = `n` + 'x' + self.short_mode_names[m]
                self.long_mode_names[nm] = s + ' ' + self.long_mode_names[m]
                self.modalities[nm] = self.modalities[m][:] # take a copy ([:])
                for i in range(2, n+1):
                    self.modalities[nm].insert(i-1, 'position'+`i`)
                if 'color' in self.modalities[m] or 'image' in self.modalities[m]:
                    for i in range(1, n+1):
                        self.modalities[nm].insert(n+i-1, 'vis'+`i`)
                for ic in 'image', 'color':
                    if ic in self.modalities[nm]:
                        self.modalities[nm].remove(ic)

        for m in self.short_mode_names.keys():
            nm = m | 1024
            self.short_mode_names[nm] = 'SP-' + self.short_mode_names[m]
            self.long_mode_names[nm] = 'Self-paced ' + self.long_mode_names[m]
            self.modalities[nm] = self.modalities[m][:]
            self.flags[nm] = dict(self.flags[m])
            self.flags[nm]['selfpaced'] = 1


        self.variable_list = []

        self.manual = cfg.MANUAL
        if not self.manual:
            self.enforce_standard_mode()

        self.inputs = {'position1': False,
            'position2': False,
            'position3': False,
            'position4': False,
            'color':     False,
            'image':     False,
            'vis1':      False,
            'vis2':      False,
            'vis3':      False,
            'vis4':      False,
            'visvis':    False,
            'visaudio':  False,
            'audiovis':  False,
            'audio':     False,
            'audio2':    False}

        self.input_rts = {'position1': 0.,
            'position2': 0.,
            'position3': 0.,
            'position4': 0.,
            'color':     0.,
            'image':     0.,
            'vis1':      0.,
            'vis2':      0.,
            'vis3':      0.,
            'vis4':      0.,
            'visvis':    0.,
            'visaudio':  0.,
            'audiovis':  0.,
            'audio':     0.,
            'audio2':    0.}

        self.hide_text = cfg.HIDE_TEXT

        self.current_stim = {'position1': 0,
            'position2': 0,
            'position3': 0,
            'position4': 0,
            'color':     0,
            'vis':       0, # image or letter for non-multi mode
            'vis1':      0, # image or color for multi mode
            'vis2':      0,
            'vis3':      0,
            'vis4':      0,
            'audio':     0,
            'audio2':    0,
            'number':    0}

        self.current_operation = 'none'

        self.started = False
        self.paused = False
        self.show_missed = False
        self.sound_select = False
        self.draw_graph = False
        self.saccadic = False
        if cfg.SKIP_TITLE_SCREEN:
            self.title_screen = False
        else:
            self.title_screen = True
        self.shrink_brain = False

        self.session_number = 0
        self.trial_number = 0
        self.tick = 0
        self.progress = 0

        self.sound_mode = 'none'
        self.sound2_mode = 'none'
        self.soundlist = []
        self.soundlist2 = []

        self.bt_sequence = []

    def enforce_standard_mode(self):
        self.back = default_nback_mode(self.mode)
        self.ticks_per_trial = default_ticks(self.mode)
        self.num_trials = cfg.NUM_TRIALS
        self.num_trials_factor = cfg.NUM_TRIALS_FACTOR
        self.num_trials_exponent = cfg.NUM_TRIALS_EXPONENT
        self.num_trials_total = self.num_trials + self.num_trials_factor *\
                                self.back ** self.num_trials_exponent
        self.session_number = 0

    def short_name(self, mode=None, back=None):
        if mode == None: mode = self.mode
        if back == None: back = self.back
        return self.short_mode_names[mode] + str(back) + 'B'
