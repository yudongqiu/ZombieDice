#!/usr/bin/env python3
# -- coding: utf-8 --

#==========================
#=  Zombie Dice Game      =
#==========================

import os, sys, random, time, copy, collections
from functools import update_wrapper

def decorator(d):
    "Make function d a decorator: d wraps a function fn."
    def _d(fn):
        return update_wrapper(d(fn), fn)
    update_wrapper(_d, d)
    return _d

@decorator
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

@memo
def colored(s, color=''):
    if color.lower() == 'green':
        return '\033[92m' + s + '\033[0m'
    elif color.lower() == 'yellow':
        return '\033[93m' + s + '\033[0m'
    elif color.lower() == 'red':
        return '\033[91m' + s + '\033[0m'
    elif color.lower() == 'blue':
        return '\033[94m' + s + '\033[0m'
    elif color.lower() == 'bold':
        return '\033[1m' + s + '\033[0m'
    else:
        return s

class Zombiedice(object):
    """ Zombie Dice Game Rules: (From Wikipedia)
    The player has to shake a cup containing 13 dice and randomly select 3 of them without looking into the cup and
    then roll them. The faces of each die represent either, brains, shotgun blasts or "runners" with different colours
    containing a different distribution of faces (the 6 green dice have 3 brains, 1 shotgun and 2 runners, the 4 yellow
    dice have 2 of each and the 3 red dice have 1 brain, 3 shotguns and 2 runners). The object of the game is to roll 13
    brains. If a player rolls 3 shotgun blasts their turn ends and they lose the brains they have accumulated so far that
    turn. It is possible for a player to roll 3 blasts in a single roll, but if only one or two blasts have been rolled the
    player will have to decide whether it is worth it to risk rolling again or "bank" the brains acquired so far and pass
    play to the next player. A "runner" is represented by feet and rolling a runner means that the player can roll that
    same dice if they choose to press their luck. A winner is determined if a player rolls 13 brains and all other players
    have taken at least one more turn without reaching 13 brains.
    """

    def __init__(self, goal=13, players=None, fastmode=False):
        print("*********************************")
        print("*          Zombie Dice          *")
        print("*********************************")
        print(self.__doc__)
        self.reset()
        self.dicetype = {'Green'  : (['brain']*3 + ['shotgun']*1 + ['runner']*2),
                         'Yellow' : (['brain']*2 + ['shotgun']*2 + ['runner']*2),
                         'Red'    : (['brain']*1 + ['shotgun']*3 + ['runner']*2)}
        self.emoji = {'brain'  : '🎃',
                      'shotgun': '🔫',
                      'runner' : '👟'}
        self.goal = goal
        self.players = []
        self.fastmode = fastmode
        self.playing = None
        self.add_players(players)
        self.simple_player = collections.namedtuple('simple_player', 'name, score')
        self.dice = collections.namedtuple('dice', 'color, face')

    def add_players(self, players=None):
        if players is None or len(players) == 0:
            names = input('Please Enter the Names of Players: ')
            players = names.split()
        for p in players:
            self.players.append(Player(p))

    def reset(self):
        self.reset_table()
        self.reset_bag()
        self.reset_player_score()

    def reset_table(self):
        self.table = Table()

    def reset_bag(self):
        self.bag = ['Green'] * 6 + ["Yellow"] * 4 + ["Red"] * 3
        random.shuffle(self.bag)

    def reset_player_score(self):
        if hasattr(self, 'players'):
            for p in self.players:
                p.score = 0

    @property
    def state(self):
        bag = copy.copy(self.bag)
        table = Table(copy.copy(self.table.dices))
        players = [self.simple_player(p.name, p.score) for p in self.players]
        playing = players[self.players.index(self.playing)]
        return {'bag':bag, 'table':table, 'players':players, 'playing':playing, 'goal':self.goal}

    def play(self):
        if self.fastmode < 2:
            print("******************")
            print("**  Game Start  **")
            print("******************")
        i_round = 0
        while True:
            i_round += 1
            if self.fastmode < 2:
                print("\n**************************")
                print("**       ROUND %2d       **"%i_round)
                print("**************************")
                self.delay(1)
            for p in self.players:
                if self.fastmode < 2:
                    print("\n========== %s's Turn ==========\n"%p.name)
                    self.delay(1)
                    self.print_scores()
                self.playing = p
                while True:
                    move = self.get_strategy(p)
                    if move == 'hold':
                        if self.fastmode < 2:
                            print("😊  %s collected %d brains"%(p.name, self.table.n_brains))
                        p.score += self.table.n_brains
                        break
                    elif move == 'roll':
                        if self.fastmode < 2:
                            print("🎲  %s is rolling the dice ! 🎲"%p.name)
                        dices = self.roll()
                        self.table.add(dices)
                        if self.fastmode < 2:
                            self.delay(1)
                            self.show_table()
                            self.delay(1)
                        if self.table.n_shotguns > 2:
                            if self.fastmode < 2:
                                print("😢  %s got %d shotguns and lost the brains"%(p.name, self.table.n_shotguns))
                            break
                        self.check_bag_empty()
                    else:
                        raise RuntimeError('%s is not a valid move!'%move)
                self.reset_bag()
                self.reset_table()
                self.delay(2)
            # check if anyone wins, if multiple people reached goal, the highest wins
            max_score = max([p.score for p in self.players])
            if max_score >= self.goal:
                if self.fastmode < 2:
                    self.delay(1)
                    print("\n\n***************************************")
                    print("** Game is over ! We have a winner ! **")
                    print("***************************************")
                    print('\nWinner ', end='')
                    print('is : ', end='')
                    self.delay(1)
                    for _ in range(max_score):
                        print('🎃 ', end='')
                        sys.stdout.flush()
                        self.delay(0.1)
                winners = [ p.name for p in self.players if p.score == max_score ]
                if self.fastmode < 2:
                    self.delay(1.5)
                    winnerbar = ' and '.join(winners)
                    title_bar = '     ▛'+ ''.join( ['▀']*(len(winnerbar)+8) ) + '▜'
                    print('\n\n'+colored(title_bar,'red'))
                    print(colored('     ▌    ' + '\033[1m' + winnerbar + '    ▐', 'yellow'))
                    bot_bar = '     ▙'+ ''.join( ['▄']*(len(winnerbar)+8) ) + '▟'
                    print(colored(bot_bar, 'green'), end='\n\n\n')
                return winners, i_round

    def roll(self):
        n_draw = 3 - self.table.n_runners
        # get the colors for the existing runner dice
        runner_colors = [dice[0] for dice in self.table.dices if dice[1] == 'runner']
        # pick up the runner dices (remove from table)
        self.table.dices = [d for d in self.table.dices if d[1]!='runner']
        # draw dices from bag so we have 3 in hand
        dice_colors = runner_colors + self.bag[:n_draw]
        self.bag = self.bag[n_draw:]
        # print a rolling picture
        self.dice_rolling(dice_colors)
        # roll each dice to get the face
        dice_faces = [random.choice(self.dicetype[d]) for d in dice_colors]
        # zip the color and face to form a list of dices
        result = [self.dice(color,face) for color,face in zip(dice_colors, dice_faces)]
        if self.fastmode < 2:
            self.dices_pic(result)
        return result

    def check_bag_empty(self):
        runners = [d for d in self.table.dices if d.face == 'runner']
        if len(self.bag) < 3 - len(runners):
            if self.fastmode < 2:
                print("Bag is empty! Putting all dices back and keep the scores.")
            self.reset_bag()
            # remove existing runners from new bag
            for d in runners:
                self.bag.remove(d.color)

    def dices_pic(self, dices):
        """ Draw the pic for dices """
        print('  '.join([ colored("▛▀▀▜", c) for c,d in dices ]))
        print('  '.join([ colored("▌%s ▐"%self.emoji[d],c) for c,d in dices ]))
        print('  '.join([ colored("▙▄▄▟", c) for c,d in dices ]))

    def dice_rolling(self, dice_colors):
        if not self.fastmode:
            for _ in range(5):
                print(' '+'     '.join([ colored("%s"%(random.choice(["⬛︎","⬜︎","▣","◈"])),c) for c in dice_colors ]), end='\r')
                self.delay(0.5)

    def print_scores(self):
        np = len(self.players)
        title_len = max((np-1) * 13 + len(self.players[-1].name[:12]) + 2, 16)
        title_bar = ''.join(['-']*(title_len // 2 - 7)) + '- Score Board -' + ''.join(['-']*(title_len // 2 - 7))
        print(title_bar)
        print(' '+' '.join(['%-12s'%p.name[:12] for p in self.players]))
        for p in self.players:
            indent = len(p.name[:12]) // 2
            print( ''.join([' ']*indent) + "%2d"%p.score + ''.join([' ']*(11-indent)) , end='')
        print('\n' + ''.join(['-']*(len(title_bar))) + '\n')

    def show_table(self):
        nd = len(self.table.dices)
        title_len = max((nd * 6 - 1), 20)
        title_bar = ''.join(['-']*(title_len // 2 - 4)) + '- Table -' + ''.join(['-']*(title_len // 2 - 4))
        print(title_bar)
        self.table.dices.sort(key=lambda x: x[1])
        self.dices_pic(self.table.dices)
        print(''.join(['-']*(len(title_bar))) + '\n')

    def delay(self, n):
        """ Delay n seconds if not in fastmode"""
        if not self.fastmode:
            time.sleep(n)

    def get_strategy(self, p):
        return p.strategy(self.state)

class Player(object):
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        try:
            self._name = str(value)
        except:
            raise TypeError("Player Name must be a string.")

    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, value):
        if isinstance(value, int):
            self._score = value
        else:
            raise TypeError("Player score must be an integer.")

    def __repr__(self):
        return "Player %s"%self.name

    def __init__(self, name='ROBOT', score=0):
        self.name = name
        self.score = score
        print("Setting up player %s"%name)
        # Allow name to be appended by a number
        if (not name[0].isdigit()) and (name[-1].isdigit()):
            name = name[:-1]
        # search for the strategy file
        for f in os.listdir('.'):
            if name.lower() in f.lower() and os.path.splitext(f)[1] == '.py':
                print('-- strategy found in %s'%f)
                p = __import__(os.path.splitext(f)[0])
                self.strategy = p.strategy
        # if not found, use manual input
        if not hasattr(self, 'strategy'):
            print('-- strategy file is not found, set as manual input.')
            self.strategy = self.human_input

    def human_input(self, state):
        """ Ask player to choose Roll or Hold """
        for _ in range(3):
            s = input('Please Enter 1 to hold or 2 to roll: ')
            if s == '1':
                return 'hold'
            elif s == '2':
                return 'roll'
        # After 3 failiers
        return 'hold'

class Table(object):
    @property
    def n_brains(self):
        return len([d for d in self.dices if d[1] == 'brain'])

    @property
    def n_shotguns(self):
        return len([d for d in self.dices if d[1] == 'shotgun'])

    @property
    def n_runners(self):
        return len([d for d in self.dices if d[1] == 'runner'])

    def __init__(self, dices=None):
        self.dices = []
        if dices is not None:
            self.add(dices)

    def add(self, dices):
        self.dices += dices


def main():
    import argparse

    parser = argparse.ArgumentParser("Play the Zombie Dice Game!", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('players', nargs='*', help='Names of Players.')
    parser.add_argument('--goal', type=int, default=13, help='Goal to win the game.')
    parser.add_argument('--fast', action='store_true', help='Run the game in fast mode.')
    parser.add_argument('-n', '--ngames', type=int, help='Play a number of games to gather statistics.')
    parser.add_argument('--fixorder', action='store_true', help='Fix the order of players in a multi-game series.')
    args = parser.parse_args()

    game = Zombiedice(goal=args.goal, players=args.players, fastmode=args.fast)
    if args.ngames is None:
        game.play()
    else:
        # check if all players have stategy function setup
        for p in game.players:
            if p.strategy.__name__ == 'human_input':
                print("%s need a strategy function to enter the auto-play mode. Exiting.."%p.name)
                return
        print("Gathering result of %d games..."%args.ngames)
        game.fastmode = 2
        game_output = open('game_results.txt','w')
        winner_board = collections.OrderedDict([(p.name, 0) for p in game.players])
        for i in range(args.ngames):
            game_output.write('Game %-4d '%(i+1))
            game.reset()
            # Let's rotate the order
            if not args.fixorder and len(game.players) > 1:
                game.players = game.players[1:] + [game.players[0]]
            winners, nround = game.play()
            game_output.write('Round %2d : '%nround)
            for w in winners:
                winner_board[w] += 1
            game_output.write(' | '.join(['%s %3d'%(p.name, p.score) for p in sorted(game.players, key=lambda p:p.name)]) + '\n')
            game_output.flush()
        game_output.close()
        print("Name    |   Games Won")
        for name, nwin in winner_board.items():
            print("%-7s | %7d"%(name, nwin))




if __name__ == "__main__":
    main()
