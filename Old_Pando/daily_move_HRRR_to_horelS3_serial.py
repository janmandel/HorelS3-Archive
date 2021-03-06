# Brian Blaylock
# February 27, 2017                    It's snowing, again. Been a good winter.

"""
Attempt to copy all possible hours, forecast hours, etc. for HRRR from the
horel-group/archive to the horelS3:HRRR archive.

This script will be run daily after the HRRR files are all downloaded.

Use python to execute an rclone command that copies HRRR files from the
the horel-group/archive/models/ to the horelS3:HRRR archive buckets.
This script should be run by the meteo19 ldm user.

Requirements:
    rclone        <- module load rclone
    rclone-beta   <- should be here in this directory
    g2ctl.pl      <- should be here in this directory
    grads         <- module load grads
"""

from datetime import datetime, timedelta
import os
import numpy as np
import stat

# Date to transfer (yesterday's data)
#DATE = datetime.today() - timedelta(days=1)
DATE = datetime(2017, 6, 29)

# rclone config file
config_file = '/uufs/chpc.utah.edu/sys/pkg/ldm/.rclone.conf' # meteo19 LDM user

#model_options = {1:'hrrr', 2:'hrrrX', 3:'hrrr_alaska'} # name in horel-group/archive
#model_S3_names = {1:'oper', 2:'exp', 3:'alaska'}       # name in horelS3:
types = ['sfc', 'prs', 'buf']                          # model file types
types = ['sfc']

model_options = {1:'hrrr_alaska'} # name in horel-group/archive
model_S3_names = {1:'alaska'}       # name in horelS3:

def copy_to_horelS3(from_here, to_there):
    """
    Copy the file to the horelS3: archive using rclone
    Input:
        from_here - string of full path and file name you want to copy
        to_there  - string of path on the horelS3 archive
    """
    # Copy the file from_here to_there (the path will be created if it doesn't exist)
    os.system('rclone --config %s copy %s horelS3:%s' \
              % (config_file, from_here, to_there))

    #if from_here[-6:] == '.grib2':
    #    # Create the .idx and .ctl files and copy those to the horelS3.
    #    # (only create these for .grib2 files)
    #    create_grb_idx(from_here)
    #    os.system('rclone --config %s copy %s horelS3:%s' \
    #              % (config_file, from_here+'.ctl', to_there))
    #    os.system('rclone --config %s copy %s horelS3:%s' \
    #              % (config_file, from_here+'.idx', to_there))

def copy_to_horelS3_rename(from_here, to_there, new_name):
    """
    Uses rclone-beta release to make a copy and rename the file on the S3 archive.
    Copy the file to the horelS3: archive using rclone-beta
    Input:
        from_here - string of full path and file name you want to copy
        to_there  - string of path on the horelS3 archive
        DATE      - used to generate a new name for the Alaska file that follow
                    the rest of the file names.
    NOTE: There is a difference between 'moveto' and 'copyto'
          'moveto' will replace the file in the destination?
          'copyto' will not replace the file if it exists?
    """
    beta_rclone = '/uufs/chpc.utah.edu/common/home/horel-group/archive_s3/rclone-beta/rclone'

    # Copy the file from_here to_there
    os.system(beta_rclone +' --config %s copyto %s horelS3:%s/%s' \
              % (config_file, from_here, to_there, new_name))

def create_idx(for_this_file, put_here, rename):
    """
    Create a .idx file and move to horel-group/archive/HRRR
    """
    file_name = rename
    idx_dir = '/uufs/chpc.utah.edu/common/home/horel-group/archive/' + put_here
    if not os.path.exists(idx_dir):
        os.makedirs(idx_dir)
    idx_name = idx_dir + file_name + '.idx'
    os.system('wgrib2 ' + for_this_file + ' -t -var -lev -ftime > ' + idx_name)
    print "created idx file:", idx_name

# =============================================================================
# =============================================================================

while DATE < datetime(2017, 7, 7):
    print DATE
    # Start doing lots of loops...
    for M in model_options.keys():
        model_type = M
        model = model_options[model_type]

        # Build the current day directory and file to move
        DIR = '/uufs/chpc.utah.edu/common/home/horel-group/archive/%04d%02d%02d/models/%s/' \
            % (DATE.year, DATE.month, DATE.day, model)


        # HRRR has 18 hour forcasts, Alaska has 36 hour forecasts
        if model == 'hrrr_alaska':
            forecasts = np.arange(0, 37)
            hours = np.arange(0,24,3)
        else:
            forecasts = np.arange(0, 19)
            hours = np.arange(0,24)

        # Do lots of loops...file type (t), hour of day (h), forecast hour (f).
        # loop for each type: sfc, prs, buf
        for t in types:
            # Files already on S3 (we don't want to repeat downloads)
            #s3_list = os.popen('rclone ls horelS3:HRRR/%s/%s/%04d%02d%02d/ | cut -c 11-' \
            #                    % (model_S3_names[model_type], t, DATE.year, DATE.month, DATE.day)).read().split('\n')


            # Known conditions that don't exist
            if t == 'buf' and (model == 'hrrr_alaska' or model == 'hrrrX'):
                # no bufer files for alaska for experimental HRRR, so don't even check
                continue

            # Build the new S3 directory path name (e.g. HRRR/oper/sfc/20171201)
            DIR_S3 = 'HRRR/%s/%s/%04d%02d%02d/' \
                        % (model_S3_names[model_type], t, DATE.year, DATE.month, DATE.day)

            # loop for each hour (0,24)
            for h in hours:
                
                # loop for each forecast hour, depenent on model type.
                for f in forecasts:
                    print M, t, h, f
                    # Known condition that doesn't exist
                    #if t == 'buf' and f > 0:
                        # bufr files not dependent on the forecast hour becuase
                        # analysis and forecast are in the same file.
                    #    continue

                    #print ""
                    #print "===================================="
                    #print "  Where am I?"
                    #print "      Date  =", DATE
                    #print "      model =", model
                    #print "      type  =", t
                    #print "      hour  =", h
                    #print "      forec =", f

                    # File path and name for hrrr and hrrrx (e.g hrrr.t00.wrfsfcf00.grib2)
                    #if model == 'hrrr' or model == 'hrrrX':
                    #    FILE = DIR + '%s.t%02dz.wrf%sf%02d.grib2' % (model, h, t, f)

                    # File path and name for hrrr_alaska prs (e.g hrrr_ak_prs_17010203.grib2)
                    if model == 'hrrr_alaska' and t == 'prs':
                        if f == 0:
                            # only get the prs field analysis hour
                            FILE = DIR + 'hrrr_ak_%s_%02d%02d%02d%02d.grib2' \
                                        % (t, DATE.year-2000, DATE.month, DATE.day, h)
                        else:
                            # Don't even try to get forecast prs fields
                            continue

                    # File path and name for hrrr_alaska sfc (e.g hrrr_ak_prs_17010203_0012.grib2)
                    if model == 'hrrr_alaska' and t == 'sfc':
                        FILE = DIR + 'hrrr_ak_%s_%02d%02d%02d%02d_00%02d.grib2' \
                                    % (t, DATE.year-2000, DATE.month, DATE.day, h, f)

                    # Bufr files are a special, so do this stuff...
                    '''
                    if t == 'buf':
                        for b in ['kslc', 'kpvu', 'kogd']:
                            # File path and name for bufr soundings stations (e.g. kslc_2017010223.buf)
                            FILE = DIR + '%s_%04d%02d%02d%02d.buf' \
                                        % (b, DATE.year, DATE.month, DATE.day, h)
                            if os.path.isfile(FILE):
                                # If the bufr file exists, then copy to S3
                                copy_to_horelS3(FILE, DIR_S3)
                                
                            # Change permissions of S3 directory to public
                            s3cmd = '/uufs/chpc.utah.edu/common/home/horel-group/archive_s3/s3cmd-1.6.1/s3cmd'
                            os.system(s3cmd + ' setacl s3://%s --acl-public --recursive' % DIR_S3)
                        continue
                    '''

                    # Check if the grib2 file exists. If it does, then copy the file to S3
                    if os.path.isfile(FILE):
                        if model == 'hrrr_alaska':
                            # Rename the alaska files to match naming convention
                            rename_AK = 'hrrrAK.t%02dz.wrf%sf%02d.grib2' % (h, t, f)
                            #if rename_AK not in s3_list:
                            try:
                                copy_to_horelS3_rename(FILE, DIR_S3, rename_AK)
                                print 'copy %s as %s' % (FILE, rename_AK)
                                create_idx(FILE, DIR_S3, rename_AK)
                            except:
                                print '\n!!! skipped', FILE
                            #else:
                            #    print rename_AK, 'is in Pando already'
                        else:
                            copy_to_horelS3(FILE, DIR_S3)

                    # Change permissions of S3 directory to public
                    s3cmd = '/uufs/chpc.utah.edu/common/home/horel-group/archive_s3/s3cmd-1.6.1/s3cmd'
                    os.system(s3cmd + ' setacl s3://%s --acl-public --recursive' % DIR_S3)
                    
    DATE = DATE + timedelta(days=1)