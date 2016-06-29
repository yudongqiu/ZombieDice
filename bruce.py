import itertools

def memo(f):
    """Decorator that caches the return value for each call to f(args).
    Then when called again with same args, we can just look it up."""
    cache = {}
    def _f(*args):
        try:
            return cache[args]
        except KeyError:
            cache[args] = result = f(*args)
            return result
        except TypeError:
            # some element of args refuses to be a dict key
            return f(args)
    _f.cache = cache
    return _f

def strategy(state):
    """ Yudong's strategy """

    """ Information provided to you:

    state = {'bag':bag, 'table':table, 'players':players, 'playing':playing}

    bag : a list containing the remaining dices' color in the bag
        i.e. bag = ['Green', 'Green', 'Red', 'Yellow', 'Green', ...]

    table : a Table class object showing the dices on the table. i.e.
        table.n_brains   = (number of brains on the table)
        table.n_shotguns = (number of shotguns on the table)
        table.n_runners  = (number of runners on the table)
        table.dices = [('Green', 'brain'), ('Red', 'shotgun'), ...]
        table.dices[0].color = 'Green'   |   table.dices[0].face = 'brain'
        table.dices[1].color = 'Red'     |   table.dices[1].face = 'shotgun'

    players : a list of namedtuples (name, score) representing the players in the game.
        The playing order is kept throughout the game.
        i.e. players = [('Yudong', 0), ('Yiwen', 1)]
        players[0].name = 'Yudong'   |    players[0].score = 0
        players[1].name = 'Yiwen'    |    players[1].score = 1

    playing: the player that is currently playing. (You)
        i.e. playing = ('Yudong', 0)  means Yudong is playing and his score is 0

    goal: the goal to win the game. If multiple players reached goal after one round, the players
        with the highest score win.

    Your strategy will return either 'hold' or 'roll' based the state.
    Please write code in Python3.
    """

    # Read information from state
    bag = state['bag']
    table = state['table']
    n_brains, n_shotguns, n_runners = table.n_brains, table.n_shotguns, table.n_runners
    dices = table.dices
    players = state['players']
    me = state['playing']
    goal = state['goal']

    # keep rolling if I'm losing
    max_score = max([p.score for p in players])
    if max_score >= goal and max_score > me.score:
        if me.score + n_brains < max_score:
            return 'roll'
        else:
            return 'hold'

    # If I got more than goal already
    if me.score + n_brains >= goal:
        if len(players) > 1:
            # hold when I got 2 more brains than the other players
            if me.score + n_brains > max([p.score for p in players if p != me]) + 1:
                return 'hold'
            else:
                return 'roll'
        else:
            return 'hold'

    # Let me think about the possiblility of getting 3 shotguns
    # Number of shotguns remaining
    shotguns_remain = 3 - n_shotguns
    # the colors of the runners I got
    runners_color = tuple([ d[0] for d in dices if d[1] == 'runner' ])
    # the possiblility of getting 3 or more shotguns
    danger = danger_shot(tuple(bag), runners_color, shotguns_remain)
    gain = expected_gain(tuple(bag), runners_color)
    #print("Bruce: I got %f chance to get shot, and get %f brain on average"%(danger, gain))

    # if the danger exceeds the gain, I hold
    if danger * n_brains > gain:
        return 'hold'
    else:
        return 'roll'

@memo
def expected_gain(bag, runners_color):
    dice_brain_p = {'Green': 0.5, 'Yellow': 0.33333333, 'Red': 0.1666666667}
    n_draw = 3 - len(runners_color)
    runners_gain = sum([dice_brain_p[c] for c in runners_color])
    if n_draw > 0:
        return runners_gain + n_draw * sum([dice_brain_p[c] for c in bag]) / len(bag)
    else:
        return runners_gain


@memo
def danger_shot(bag, runners_color, shotguns_remain):
    if len(runners_color) < 3:
        possible_draws_from_bag = itertools.combinations(bag, 3-len(runners_color))
        shot_p_list = []
        for draw in possible_draws_from_bag:
            shot_p_list.append( shot_probability(runners_color+draw, shotguns_remain) )
        return sum(shot_p_list) / len(shot_p_list)
    else:
        return shot_probability(runners_color, shotguns_remain)

@memo
def shot_probability(colors, shotguns_remain):
    if not hasattr(shot_probability, 'diceinfo'):
        shot_probability.diceinfo = {'Green'  : (['brain']*3 + ['shotgun']*1 + ['runner']*2),
                                     'Yellow' : (['brain']*2 + ['shotgun']*2 + ['runner']*2),
                                     'Red'    : (['brain']*1 + ['shotgun']*2 + ['runner']*2)}
    # loop over all cases for the 3 dices
    n_shot = 0
    for faces in itertools.product(shot_probability.diceinfo[colors[0]], shot_probability.diceinfo[colors[1]], shot_probability.diceinfo[colors[2]]):
        if faces.count('shotgun') >= shotguns_remain:
            n_shot += 1
    return n_shot / 216.
