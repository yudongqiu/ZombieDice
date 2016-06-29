#!/usr/bin/env python3

import os, pickle
import sys

cachefilename = 'cachehigh'

if os.path.exists(cachefilename):
    cachehigh = pickle.load( open(cachefilename,"rb") )
    print('Successfully loaded %d high quality cache data'%len(cachehigh))
    new_cache = {}
    count = 0
    for state, result in cachehigh.items():
        new_cache[state] = result
        bag, dices, players, myidx, goal, me = state
        if me == 0:
            state1 = (bag, dices, players, myidx, goal, 1)
            result1 = ( 1.-result[0], result[1] )
            new_cache[state1] = result1
            count += 1
            #if count < 10:
            #    print(state1, result1)
    print("Duplicated %d results for player 1."%count)

# save the highcache to pickled file
pickle.dump( new_cache, open(cachefilename,"wb") )
print('Successfully updated cachehigh data, %d '%len(new_cache))
