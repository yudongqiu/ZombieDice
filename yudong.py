#!/usr/bin/env python3
# -- coding: utf-8 --

import itertools, time, copy
import collections, random
import numpy as np

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
            return f(*args)
    _f.cache = cache
    return _f

def strategy(state):
    """ Yudong's strategy """

    """ Information provided to you:

    state = {'bag':bag, 'table':table, 'players':players, 'playing':playing, 'goal':goal}

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
    playing = state['playing']
    goal = state['goal']

    # If I haven't got any brains yet
    if n_brains == 0:
        return 'roll'
    # keep rolling if I'm losing
    max_score = max([p.score for p in players])
    if max_score >= 13 and max_score > me.score:
        if me.score + n_brains < max_score:
            return 'roll'
        else:
            return 'hold'

    # simplify the state and make it a tuple for caching
    # bag: (n_green, n_yellow, n_red)
    # dices: (green:(n_brain, n_runner, n_shotgun), yellow:(n_brain, n_runner, n_shotgun), red:(n_brain, n_runner, n_shotgun))
    # players: (score1, score2, score3 ...)
    # myidx : the index of the current player
    # me : index of 'me'

    bag = tuple(collections.Counter(bag)[color] for color in ['Green', 'Yellow', 'Red'])
    dice_new = []
    for color in ['Green', 'Yellow', 'Red']:
        d_c = [d for d in dices if d[0] == color]
        n_faces = []
        for face in ['brain', 'runner', 'shotgun']:
            d_f = [d for d in d_c if d[1] == face]
            n_faces.append(len(d_f))
        dice_new.append(tuple(n_faces))
    dices = tuple(dice_new)
    players = tuple(p[1] for p in players)
    myidx = players.index(me)
    me = myidx

    state = (bag, dices, players, myidx, goal, me)



    #state = (tuple(sorted(bag)), tuple(sorted([tuple(d) for d in dices])), tuple([tuple(p) for p in players]), players.index(me))
    # get best action
    #if hasattr(U_dice, 'cache'):
    #    print("U_dice cache length:", len(U_dice.cache))
    return best_action(state, zombie_actions, Q_dice, U_dice)

# For the rest of the code, state is now simplified

def best_action(state, actions, Q, U):
    "Return the optimal action for a state, given U."
    def EU(action): return Q(state, action, level=0)
    return max(actions(state), key=EU)

#@memo
def Q_dice(state, action, level=0, quality=0.):
    "The expected value of U of choosing action in state."
    #print("Q_level", level)
    if action == 'hold':
        result, result_qual = U_dice(hold(state), level=level, quality=quality)
    if action == 'roll':
        # going over all possible draws from bag and all possible rolled faces
        bag, dices, players, myidx, goal, me = state
        runners_color = tuple(d[1] for d in dices) # (2,0,0) means 2 green runners
        possible_colors_counter = possible_colors(bag, runners_color)
        result = 0.
        result_qual = 0.
        # enumerate all possible results from rolling
        for colors, n_c, draw_colors in possible_colors_counter:
            q_color = 0.
            qual_color = 0.
            dices_counter = dices_with_color(colors)
            counted_dices = 0
            for rolled_dices, n_d in dices_counter:
                #new_runners = rolled_dices.T[1]
                new_runners = tuple(d[1] for d in rolled_dices)
                n_new_runners = sum(new_runners)
                #if np.sum(new_runners) != 3: # skip the 3 runners
                if n_new_runners != 3: # skip the 3 runners
                    dices1 = updated_dices(dices, rolled_dices)
                    bag1 = updated_bag(bag, draw_colors, new_runners)
                    new_state = (bag1, dices1, players, myidx, goal, me) # update the bag and dices before passing to roll
                    state_after_roll = roll(new_state)
                    if state_after_roll not in U_dice.pendingstates:
                        u, qual = U_dice(state_after_roll, level=level, quality=quality)
                        q_color += u * n_d
                        qual_color += qual * n_d # accumulate quality over dices
                        counted_dices += n_d
            result += q_color / counted_dices * n_c  # there are 6x6x6 possibilities for 3 faces
            result_qual += qual_color / counted_dices * n_c # accumulate quality over color
            #print(colors, 'result: ', result, float(sum(cc[1] for cc in possible_colors_counter)))
        f_possible_colors = 1. / sum(cc[1] for cc in possible_colors_counter) # factor for all possible_colors
        result *= f_possible_colors
        result_qual *= f_possible_colors
    #if level == 0:
    #    print(level, state, action, result)

    return result, result_qual

@memo
def updated_dices(dices, rolled_dices):
    result = [list(d_c) for d_c in rolled_dices]
    for i in range(3):
        for j in (0,2): # skip the runners
            result[i][j] += dices[i][j]
    return tuple(tuple(d_c) for d_c in result)

@memo
def updated_bag(bag, draw_colors, new_runners):
    new_bag = tuple(bag[i] - draw_colors[i] for i in range(3))
    if sum(new_bag) + sum(new_runners) < 3: # if bag is empty
        return (6-new_runners[0], 4-new_runners[1], 3-new_runners[2])
    else:
        return new_bag

@memo
def possible_colors(bag, runners_color):
    """ Given a bag and runner dices, return a counter of all possible colors:
    possible_colors((6, 4, 3), (0, 2, 0)) -->
    [(('G', 'Y', 'Y'), 6, (1, 0, 0)),
     (('Y', 'Y', 'Y'), 4, (0, 1, 0)),
     (('Y', 'Y', 'R'), 3, (0, 0, 1))]"""
    n_runners = sum(runners_color)
    runner_c = tuple(['G']*runners_color[0] + ['Y']*runners_color[1] + ['R']*runners_color[2])
    if n_runners == 3: # no need to draw
        return [(runner_c, 1, (0,0,0))]
    else:
        n_draw = 3 - n_runners
        # Expand the bag into "GGGYYYRR" and take combinations
        bag_c = ['G']*bag[0] + ['Y']*bag[1] + ['R']*bag[2]
        # Count the combinations appear
        counter = collections.Counter( itertools.combinations(bag_c, n_draw) )
        result = []
        for c_draw, n_draw in counter.items():
            draw_colors = (c_draw.count('G'), c_draw.count('Y'), c_draw.count('R'))
            result.append((tuple(sorted(runner_c + c_draw, key=lambda c:'GYR'.index(c))), n_draw, draw_colors))
        return sorted(result, key=lambda x:x[1], reverse=True)


@memo
def dices_with_color(colors):
    """ Given the colors of 3 dices, e.g. ('G', 'G', 'Y')
    generate a collection of rolled dices, return a list of (dices, numbers) tuple:
    dices_with_color(('G', 'G', 'Y')) =
    [(array([[1, 1, 0], [0, 1, 0], [0, 0, 0]]), 24),
     (array([[1, 1, 0], [0, 0, 1], [0, 0, 0]]), 24),
     (array([[1, 1, 0], [1, 0, 0], [0, 0, 0]]), 24),
     (array([[2, 0, 0], [0, 1, 0], [0, 0, 0]]), 18),
     (array([[2, 0, 0], [0, 0, 1], [0, 0, 0]]), 18),
     (array([[2, 0, 0], [1, 0, 0], [0, 0, 0]]), 18),
     (array([[1, 0, 1], [0, 0, 1], [0, 0, 0]]), 12),
     (array([[1, 0, 1], [1, 0, 0], [0, 0, 0]]), 12),
     (array([[1, 0, 1], [0, 1, 0], [0, 0, 0]]), 12),
     (array([[0, 2, 0], [0, 0, 1], [0, 0, 0]]), 8),
     (array([[0, 1, 1], [1, 0, 0], [0, 0, 0]]), 8),
     (array([[0, 2, 0], [0, 1, 0], [0, 0, 0]]), 8),
     (array([[0, 2, 0], [1, 0, 0], [0, 0, 0]]), 8),
     (array([[0, 1, 1], [0, 0, 1], [0, 0, 0]]), 8),
     (array([[0, 1, 1], [0, 1, 0], [0, 0, 0]]), 8),
     (array([[0, 0, 2], [0, 0, 1], [0, 0, 0]]), 2),
     (array([[0, 0, 2], [0, 1, 0], [0, 0, 0]]), 2),
     (array([[0, 0, 2], [1, 0, 0], [0, 0, 0]]), 2)]
    """
    if not hasattr(dices_with_color, 'diceinfo'):
        dices_with_color.diceinfo = {'G' : (['brain']*3 + ['runner']*2 + ['shotgun']*1),
                                     'Y' : (['brain']*2 + ['runner']*2 + ['shotgun']*2),
                                     'R' : (['brain']*1 + ['runner']*2 + ['shotgun']*3)}
    throw_result = [tuple(sorted(zip(colors,faces))) for faces in itertools.product(dices_with_color.diceinfo[colors[0]], dices_with_color.diceinfo[colors[1]], dices_with_color.diceinfo[colors[2]])]
    dices_counter = collections.Counter(throw_result).items()
    #dices_counter.sort(key=lambda x:x[1], reverse=True)
    # transfer dice into 3*3 matrix
    result = []
    for dices_c_f, n_d in dices_counter:
        dice_transferred = np.reshape([0]*9, (3,3))
        for dice in dices_c_f:
            dice_transferred['GYR'.index(dice[0]), ['brain','runner','shotgun'].index(dice[1])] += 1
        #result.append((dice_transferred, n_d))
        result.append(( tuple(tuple(i) for i in dice_transferred) ,n_d))
    return result

#@memo
def U_dice(state, level=0, quality=0.):
    "The utility of a state, the probability of me to win the game"
    # Assume all the opponents are playing with the optimal strategy


    # Build a quality controlled cache system for U_dice
    if not hasattr(U_dice, 'cachehigh'):
        U_dice.cachehigh = {}
    if not hasattr(U_dice, 'cachelow'):
        U_dice.cachelow = {}
    # try to find existing answer from the high quality cache first
    try:
        return U_dice.cachehigh[state]
    except:
        pass
    # then try to find from the low quality cache
    try:
        return U_dice.cachelow[state]
    except:
        pass

    # store the pending states to prevent infinite loop
    if not hasattr(U_dice, 'pendingstates'):
        U_dice.pendingstates = set()

    U_dice.pendingstates.add(state)
    #print('pending state added:  ',state)

    # get information
    bag, dices, players, myidx, goal, me = state

    # If this is the end of the round, let me see if game is ending
    if myidx == len(players):
        max_score = max(players)
        # if anyone got more than goal, the game is ending
        if max_score >= goal:
            result = 1. if players[me] == max_score else 0.
            quality = 1.
            # no need to proceed to next Q_dice here because game is ending at this point
        else: # game is not ending, we need to go to next round
            result, quality = U_dice((bag, dices, players, 0, goal, me), level=level, quality=quality)
    # If this is a player
    else:
        scores = list(players)
        pending = sum(d[0] for d in dices)
        scores[myidx] += pending
        max_score = max(scores)
        # If this is the last player of the round, I know if I got enough points
        if myidx == len(players)-1 and scores[myidx] >= goal and scores[myidx] == max_score:
            result = 1. if myidx == me else 0.
            quality = 1.
        # If not the last player, don't keep rolling infinitely, you win if you got so many points
        elif scores[myidx] > goal + 10:
            result = 1. if myidx == me else 0.
            quality = 1.
        # If no one is winning right now, keep searching for winning conditions
        else:
            # go to the next recursive level of calculating winning rate
            if myidx == me:
                # if it's me playing, i'm maximizing the chance I win
                result, quality = max(Q_dice(state, action, level=level+1, quality=quality) for action in zombie_actions(state))
            else: # if it's not me playing, they will minimize the chance I win
                result, quality = min(Q_dice(state, action, level=level+1, quality=quality) for action in zombie_actions(state))

    U_dice.pendingstates.remove(state)
    #print('pending state removed:',state)
    # put the high quality results into the high quality cache
    if quality == 1.0:
        U_dice.cachehigh[state] = (result, quality)
    else:
        U_dice.cachelow[state] = (result, quality)

    #print(state, result)
    #time.sleep(1)
    return (result, quality)



def zombie_actions(state):
    bag, dices, players, myidx, goal, me = state
    return ['hold','roll'] if sum(d[0] for d in dices) > 0 else ['roll']


@memo
def hold(state):
    bag, dices, players, myidx, goal, me = state
    # get my point
    players = list(players)
    players[myidx] += sum(d[0] for d in dices)
    bag = (6, 4, 3)
    dices = ((0, 0, 0), (0, 0, 0), (0, 0, 0))
    #myidx = (myidx+1)%len(players)
    myidx += 1
    return (bag, dices, tuple(players), myidx, goal, me)

@memo
def roll(state):
    # most of the work are already done in Q_dice
    # we only need to check if we got 3 or more shotguns here
    bag, dices, players, myidx, goal, me = state
    n_shotguns = sum(d[2] for d in dices)
    # if got 3 or more shotguns, lost all brains and end turn
    if n_shotguns > 2:
        bag = (6, 4, 3)
        dices = ((0, 0, 0), (0, 0, 0), (0, 0, 0))
        #myidx = (myidx+1)%len(players)
        myidx += 1
        state = (bag, dices, players, myidx, goal, me)
    return state


# training
if __name__ == '__main__':
    import os, pickle
    goal = 13
    me = 0
    #state = ((4, 4, 3), ((2, 0, 0), (0, 0, 2), (0, 0, 0)), (10, 11), 0)
    #state = hold(state)

    #Q_dice(state, 'hold', level=0)
    #Q_dice(state, 'roll', level=0)
    #print(U_dice(state, level=1))

    # Load previous highcache from pickled file
    cachefilename = 'cachehigh'
    if os.path.exists(cachefilename):
        U_dice.cachehigh = pickle.load( open(cachefilename,"rb") )
        print('Successfully loaded %d high quality cache data'%len(U_dice.cachehigh))
        #print(cachehigh)
        #U_dice.cachehigh = {k:v for (k,v) in cachehigh.items() if v[1] >= cache_high_target}
        #n_removed = len(cachehigh) - len(U_dice.cachehigh)
        #if n_removed:
        #    print('%d states with quality lower than %f is removed from cachehigh'%(n_removed, cache_high_target))


    state = ((6, 4, 3), ((0, 0, 0), (0, 0, 0), (0, 0, 0)), (12, 12), 0, goal, me)
    print('Starting computing from state', state)

    U_dice.pendingstates = set()

    # compute rolling win rate
    print(Q_dice(state, 'roll', level=0, quality=1.0))
    number_lowcache = len(U_dice.cachelow)
    print('%d is left in U_dice.cachelow'%(number_lowcache))

    # save the highcache to pickled file
    pickle.dump( U_dice.cachehigh, open(cachefilename,"wb") )
    print('Successfully updated U_dice.cachehigh data')
