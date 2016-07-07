#!/usr/bin/env python3

import os, pickle
import sys

cachefilename = 'cachehigh'
cache_high_target = float(sys.argv[1])


if os.path.exists(cachefilename):
    cachehigh = pickle.load( open(cachefilename,"rb") )
    print('Successfully loaded %d high quality cache data'%len(cachehigh))
    cachehighnew = {k:v for (k,v) in cachehigh.items() if all(p<20 for p in k[-4])}
    n_removed = len(cachehigh) - len(cachehighnew)
    if n_removed:
        print('%d states is removed from cachehigh'%(n_removed))
# save the highcache to pickled file
pickle.dump( cachehighnew, open(cachefilename,"wb") )
print('Successfully updated cachehigh data, %d left'%len(cachehighnew))
