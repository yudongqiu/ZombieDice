
def strategy(state):
    """ Yiwen's strategy """

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
    strategy.goal = state['goal']

    # if there is someone else got > 13 brains, roll until I got more brains
    max_score = max([p.score for p in players])
    if max_score >= strategy.goal:
        if me.score + n_brains < max_score:
            return 'roll'
        else:
            return 'hold'

    # If I got more than 13 brains and at least 1 shotgun, I hold
    if me.score + n_brains >= strategy.goal and n_shotguns > 0:
        return 'hold'

    '''
    # If I got 3 green runners, roll
    runners = [ d for d in dices if d.face == 'runner' ]
    if len([r for r in runners if r.color == 'Green']) > 2:
        return 'roll'

    # If the bag and runners on the table are all green, roll
    if (len([r for r in runners if r.color != 'Green']) + len([c for c in bag if c != 'Green'])) == 0:
        return 'roll'
    '''

    # If I got 2 or more brains and 2 shotguns, I hold
    if n_brains > 1 and n_shotguns > 1:
        return 'hold'

    # In all other cases, I roll
    return 'roll'
