#!/usr/bin/env python3
# -- coding: utf-8 --

import itertools, time, copy
import collections, random
import os, pickle

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

    # if there is someone else got > 13 brains, roll until I got more brains
    max_score = max([p.score for p in players])
    if max_score >= goal:
        if playing.score + n_brains < max_score:
            return 'roll'
        elif playing.score + n_brains > goal + 5:
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
    myidx = players.index(playing)
    me = myidx
    players = tuple(p[1] for p in players)

    state = (bag, dices, players, myidx, goal, me)

    return best_action(state)

# For the rest of the code, state is now simplified

@memo
def best_action(state):
    "Return the optimal action for a state"
    def EU(action): return Q_dice(state, action, level=0)
    return max(zombie_actions(state), key=EU)

def Q_dice(state, action, level=0):
    "The expected value of U of choosing action in state."
    if action == 'hold':
        result, result_qual = U_dice(hold(state), level=level)
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
                new_runners = tuple(d[1] for d in rolled_dices)
                n_new_runners = sum(new_runners)
                if n_new_runners != 3: # skip the 3 runners
                    dices1 = updated_dices(dices, rolled_dices)
                    bag1 = updated_bag(bag, draw_colors, new_runners)
                    new_state = (bag1, dices1, players, myidx, goal, me) # update the bag and dices before passing to roll
                    rolled_state = roll(new_state)
                    u, qual = U_dice(roll(new_state), level=level)
                    q_color += u * n_d
                    qual_color += qual * n_d # accumulate quality over dices
                    counted_dices += n_d
            result += q_color / counted_dices * n_c  # there are 6x6x6 possibilities for 3 faces
            result_qual += qual_color / counted_dices * n_c # accumulate quality over color
        f_possible_colors = 1. / sum(cc[1] for cc in possible_colors_counter) # factor for all possible_colors
        result *= f_possible_colors
        result_qual *= f_possible_colors
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
        dice_transferred = [[0 for _ in range(3)] for _ in range(3)]
        for dice in dices_c_f:
            dice_transferred['GYR'.index(dice[0])][['brain','runner','shotgun'].index(dice[1])] += 1
        #result.append((dice_transferred, n_d))
        result.append(( tuple(tuple(i) for i in dice_transferred) ,n_d))
    return result

def U_dice(state, level=0):
    """ The utility of a state, the probability of me to win the game,
    Assuming all the opponents are playing with the optimal strategy"""

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
            result, quality = U_dice((bag, dices, players, 0, goal, me), level=level)
    # If this is a player
    else:
        scores = list(players)
        pending = sum(d[0] for d in dices)
        scores[myidx] += pending
        myscore = scores[myidx]
        max_other_score = max(scores[:myidx] + scores[myidx+1:])
        # If this is the last player of the round, I know when I got enough points
        if myidx == len(players)-1 and myscore >= goal and myscore > max_other_score:
            result = 1. if myidx == me else 0.
            quality = 1.
        # If not the last player, don't keep rolling infinitely, you win if you got so many points
        #elif myscore > goal + 8:
        #    result = 1. if myidx == me else 0.
        #    quality = 1.
        # If recursion level is high, return an estimation with quality 0
        elif level > 7:
            result, quality = estimate_u(scores, myidx, me, goal)
            # if me_score = 12 and max_other_score = 12 and mydix == me: 0.5
            # me : 12 , other:12 and mydix != me: 0.05

        # If no one is winning right now, keep searching for winning conditions
        else:
            # go to the next recursive level of calculating winning rate
            if myidx == me:
                # if it's me playing, i'm maximizing the chance I win
                result, quality = max(Q_dice(state, action, level=level+1) for action in zombie_actions(state))
            else: # if it's not me playing, they will minimize the chance I win
                result, quality = min(Q_dice(state, action, level=level+1) for action in zombie_actions(state))

    if quality > 0.80:
        U_dice.cachehigh[state] = (result, quality)
    else:
        U_dice.cachelow[state] = (result, quality)

    return (result, quality)

@memo
def estimate_u(scores, myidx, me, goal):
    myscore = scores[myidx]
    max_before = max(scores[:myidx]) if myidx > 0 else 0
    max_after = max(scores[myidx+1:]) if myidx < len(scores)-1 else 0
    damping = 5 # add to each player to damp the low scores
    if myidx == me:
        # comparing to the maxscore before me
        if max_before > max_after:
            buff_above_goal = (max_before - goal + 1)**3 if max_before >= goal else 0
            fixed_before = max_before + buff_above_goal + damping
            buff_close_to_goal = (myscore + 4 - goal)**3 if myscore+4 > goal else 0 # the buff for me being close to goal
            fixed_me = myscore + buff_close_to_goal + damping
            result = fixed_me / (fixed_me + fixed_before)
        else: # comparing to players after me
            buff_above_goal = (myscore - goal + 1)**3 if myscore >= goal else 0
            fixed_me = myscore + buff_above_goal + damping
            buff_close_to_goal = (max_after + 4 - goal)**3 if max_after+4 > goal else 0
            fixed_after = max_after + buff_close_to_goal + damping
            result = fixed_me / (fixed_me + fixed_after)
    else:
        me_score = scores[me]
        if myidx < me:
            buff_above_goal = (myscore - goal + 1)**3 if myscore >= goal else 0
            fixed_myidx = myscore + buff_above_goal + damping
            buff_close_to_goal = (me_score + 4 - goal)**3 if me_score+4 > goal else 0
            fixed_me = me_score + buff_close_to_goal + damping
        elif myidx > me:
            buff_above_goal = (me_score - goal + 1)**3 if me_score >= goal else 0
            fixed_me = me_score + buff_above_goal + damping
            buff_close_to_goal = (myscore + 4 - goal)**3 if myscore+4 > goal else 0
            fixed_myidx = myscore + buff_close_to_goal + damping
        result = fixed_me  / (fixed_me + fixed_myidx)
    quality = 0.
    return result, quality

def zombie_actions(state):
    bag, dices, players, myidx, goal, me = state
    # cut off on goal + 10 brains
    pending = sum(d[0] for d in dices)
    if pending == 0:
        return ['roll']
    # if we already got a very high score, do not cotinue to roll
    if players[myidx] + pending > goal + 5:
        return ['hold']
    else:
        return ['hold', 'roll']

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


# load the cachehigh
if os.path.exists('cachehigh'):
    U_dice.cachehigh = pickle.load( open('cachehigh',"rb") )
    n_exist = len(U_dice.cachehigh)
    print('Successfully loaded %d high quality cache data'%n_exist)
else:
    n_exist = 0
    print("cachehigh is not found, I will be very stupid!")

# training
if __name__ == '__main__':
    import sys
    goal = 13
    me = 0

    starting_score = (int(sys.argv[1]), int(sys.argv[2]))
    starting_player = 0

    state = ((6, 4, 3), ((0, 0, 0), (0, 0, 0), (0, 0, 0)), starting_score, starting_player, goal, me)
    print('Starting computing from state', state)
    level = 0
    # compute rolling win rate
    print('hold', Q_dice(state, 'hold', level=level))
    print('roll', Q_dice(state, 'roll', level=level))
    number_lowcache = len(U_dice.cachelow)
    print('%d is left in U_dice.cachelow'%(number_lowcache))

    target_q = 0.80
    l = list(U_dice.cachelow.items())
    for k,v in l[:]:
        #print(k, v)
        U_dice.cachelow = {}
        v1 = U_dice(k)
        if v1[1] > target_q:
            print(k, v, v1)
    if len(U_dice.cachehigh) > n_exist:
        # save the highcache to pickled file
        pickle.dump( U_dice.cachehigh, open(cachefilename,"wb") )
        print('Successfully updated U_dice.cachehigh data')

def finish():
    try:
        if len(U_dice.cachehigh) > n_exist:
            # save the highcache to pickled file
            pickle.dump( U_dice.cachehigh, open("cachehigh","wb") )
            print('Successfully updated U_dice.cachehigh data with %d states'%len(U_dice.cachehigh))
        if len(U_dice.cachelow) > 0:
            print("%d states were left in U_dice.cachelow"%len(U_dice.cachelow))
    except:
        pass
