#!/usr/bin/env python3

import os, pickle
import sys

cachefilename = 'cachehigh'

if os.path.exists(cachefilename):
    cachehigh = pickle.load( open(cachefilename,"rb") )
    print('Successfully loaded %d high quality cache data'%len(cachehigh))
    cachehighnew = {}
    for k,v in cachehigh.items():
        bag, dices, players, myidx, goal, me = k
        players = list(players)
        if myidx < len(players): 
            players[myidx] += sum(c[0] for c in dices)
        if all(p < 22 for p in players):
            cachehighnew[k] = v
    n_removed = len(cachehigh) - len(cachehighnew)
    if n_removed:
        print('%d states is removed from cachehigh'%(n_removed))
# save the highcache to pickled file
pickle.dump( cachehighnew, open(cachefilename,"wb") )
print('Successfully updated cachehigh data, %d left'%len(cachehighnew))
