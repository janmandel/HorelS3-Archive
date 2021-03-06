# Brian Blaylock
# 28 August 2018

"""
Pando allocation is at 130 TB, but horel-group7, the Pando backup, only has
60 TB. Hence, we need to remove some files from Pando. I am willing to risk a 
few of the forecasts to reduce the amount of files on horel-group7. These files
will still be available on Pando, as long as Pando stays a live and doesn't die
again.

I am KEEPING the following:
    F00, F01, F02, F03, F06, F09, F12, F15, F18

I am RISKING the following:
    F04, F05, F07, F08, F10, F11, F13, F14, F16, F17

The risk files will only be removed if they are older than 600 days (23 months)
"""

from datetime import datetime, timedelta
import os
import getpass
import socket

if getpass.getuser() != 'mesohorse' or socket.gethostname() != 'meso1.chpc.utah.edu':
    print "--> You are %s on %s" % (getpass.getuser(), socket.gethostname())
    print "--> Please run this operational download script with the mesohorse user on meso1."
#    exit()

# List of dates from archive begining to 25 months ago. These are the dates we
# want to risk on the Pando archive and not backup on horel-group7.
sDATE = datetime(2016, 7, 15)
eDATE = datetime.now()-timedelta(days=600)
DATES = [sDATE + timedelta(days=d) for d in range((eDATE-sDATE).days)]

# In each DATE directory, remove the files we want to risk

RISK = ['f04', 'f05', 'f07', 'f08', 'f10', 'f11', 'f13', 'f14', 'f16', 'f17']

for D in DATES:
    DIR = '/uufs/chpc.utah.edu/common/home/horel-group7/Pando/hrrr/sfc/%s/' % D.strftime('%Y%m%d')
    print DIR
    for r in RISK: 
        print "\n    !!! REMOVING these files..."
        print os.system('ls %s*%s.grib2*' % (DIR, r))
        os.system('rm %s*%s.grib2*' % (DIR, r))
