# Brian Blaylock
# 28 February 2017              I learned who to play a new card game on Sunday

"""
Download eXperimental HRRR Alaska (hrrr_AK) files from ESRL via FTP
Contact: Taylor McCorkle, taylor.mccorkle@utah.edu

This script should be run by the mesohorse user on meso1.

Run the CRON job at 6:10 PM Mountain Time (18:10) to get all fields for the
UTC "previous day" (i.e. Since 6:10 PM Mountain Time is the next day in UTC,
when I download from ESRL I am getting the data from "yesterday")

This Script does the following:
1) Downloads analyses and all forecast hours for HRRR Alaska sfc fields
   (found in the wrftwo directory on the ESRL FTP site). Saves as a .temp file.
2) CANCELED THIS STEP: NO LONGER TRUNCATE THE SFC FILES
3) Downloads analyses for HRRR Alaska pressure fields (found in the wrfprs
   directory on the ESRL FTP site). Taylor keeps the full file.

NOTE: HRRR Alaska is only run every three hours [00, 03, 06, 09, 12, 15, 18, 21]
"""

from ftplib import FTP
from datetime import date, datetime, timedelta
import os
import stat
import multiprocessing

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v2/')
sys.path.append('B:/pyBKB_v2')
from BB_MesoWest.get_token import get_ESRL_credentials

# ----------------------------------------------------------------------------
#                      Stuff you may want to change
# ----------------------------------------------------------------------------
# fxx is a list of forecast hours we want to download for sfc and prs fields.
# f00 is the analysis hour. Forecasts go out 36 hours.
# Currently grabbing analyses and forecasts for sfc files, and analyses for prs
sfc_fxx = range(0, 37)
prs_fxx = [0]

# ----------------------------------------------------------------------------
#                    Introductory Global Variables
# ----------------------------------------------------------------------------
# Date.today() returns the local time date. If it's after 6:00 PM local, then,
# acording to the UTC clock, that date is "yesterday."
if datetime.now().hour < 12:
    # if it before noon (local) then get yesterdays date. Reasons:
    #   1) maybe the download script ran long and it's just after midnight
    #   2) maybe you need to rerun this script in the morning
    yesterday = datetime.today() -timedelta(days=1)
    DATE = yesterday
else:
    # it's probably after 6 local
    yesterday = datetime.today()
    DATE = yesterday

# Directory to save the downloads. Create it if it doesn't exist
OUTDIR = '/uufs/chpc.utah.edu/common/home/horel-group/archive/%04d%02d%02d/BB_test/models/hrrrAK/' \
        % (yesterday.year, yesterday.month, yesterday.day)
if not os.path.exists(OUTDIR):
    os.makedirs(OUTDIR)
    # Change directory permissions
    os.chmod(OUTDIR, stat.S_IRWXU | \
                     stat.S_IRGRP | stat.S_IXGRP | \
                     stat.S_IROTH | stat.S_IXOTH)
                    # User can read, write, execute
                    # Group can read and execute
                    # Others can read and execute

# Credentials for logging into ESRL FTP database
user, password = get_ESRL_credentials()

# rclone config file
config_file = '/scratch/local/mesohorse/.rclone.conf' # meso1 mesohorse user
# ----------------------------------------------------------------------------

def create_idx(for_this_file, put_here):
    """
    Create a .idx file and move to horel-group/archive/HRRR
    """
    file_name = for_this_file.split('/')[-1]
    idx_dir = '/uufs/chpc.utah.edu/common/home/horel-group/archive/' + put_here
    if not os.path.exists(idx_dir):
        os.makedirs(idx_dir)
    idx_name = idx_dir + file_name + '.idx'
    os.system('wgrib2 ' + for_this_file + ' -t -var -lev -ftime > ' + idx_name)
    print "created idx file:", idx_name

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

def download_hrrrAK_sfc(item):
    """
    Download Surface 2D fields
        Download files that contain only numbers (these represent dates).
        and files for which the date matches the OUTDIR date. (We don't want
        to accidentally put "todays" data in "yesterdays" directory.)
    Input:
        item  - filename is in the form... YYJJJHH00FF00
                Year, Day of Year, Model Hour 00, Forecast 00
    """

    if item.isdigit() \
       and datetime.strptime(item[0:5], '%y%j').day == yesterday.day:
        # 1)
        # Log onto the FTP for each file downloaded (so it doesn't time out)
        # FTP login:
        ftp = FTP('gsdftp.fsl.noaa.gov')
        ftp.login(user, password)
        ftp.cwd('hrrr_ak/alaska/wrftwo')

        # What is the initalized hour and forecast?
        hour = item[5:7]
        forecast = item[9:11]

        # Save the file similar to the standard hrrr file naming convention
        NEWFILE = 'hrrrAK.t%sz.wrfsfcf%s.grib2' % (hour, forecast)
        if os.path.isfile(OUTDIR+NEWFILE):
            print "looks like that file already exists", OUTDIR+NEWFILE
        else:
            # or name the file with Taylor's convention
            #NEWFILE = 'hrrr_ak_sfc_%02d%02d%02d%s_00%s' \
            #           % (yesterday.year-2000, yesterday.month, yesterday.day, hour, forecast)
            # Append the file name with ".temp" because we'll truncate and remove
            # this file to reduce file size.
            print "Downloading:", OUTDIR+NEWFILE
            ftp.retrbinary('RETR '+ item, open(OUTDIR+NEWFILE, 'wb').write)
            ftp.quit()
            
            print "Saved:", OUTDIR+NEWFILE

            # 2) NO LONGER TRUNCATE THE FILE     

            # Move to Pando S3 archive
            FILE = OUTDIR+NEWFILE
            DIR_S3 = 'HRRR/%s/%s/%04d%02d%02d/' \
                        % ('alaska', 'sfc', DATE.year, DATE.month, DATE.day)
            if os.path.isfile(FILE):
                copy_to_horelS3(FILE, DIR_S3)
                create_idx(FILE, DIR_S3)
            else:
                print "%s does not exist", FILE

            print "Moved to Pando:", FILE

            # Change permissions of S3 directory to public
            s3cmd = '/uufs/chpc.utah.edu/common/home/horel-group/archive_s3/s3cmd-1.6.1/s3cmd'
            os.system(s3cmd + ' setacl s3://%s --acl-public --recursive' % DIR_S3)


def download_hrrrAK_prs(item):
    """
    Download Pressure (3D) Fields
        Download files that contain only numbers (these represent dates)
        and files for which the date matches the OUTDIR date. (We don't want
        to accidentally put "todays" data in "yesterdays" directory.)
    Input:
        item  - filename is in the form... YYJJJHH00FF00
                Year, Day of Year, Model Hour 00, Forecast 00
    """

    if item.isdigit() \
       and datetime.strptime(item[0:5], '%y%j').day == yesterday.day:
        # 3)
        # Log onto the FTP for each file downloaded (prevents time-out)
        # FTP login:
        ftp = FTP('gsdftp.fsl.noaa.gov')
        ftp.login(user, password)
        ftp.cwd('hrrr_ak/alaska/wrfprs')

        # What is the initalized hour and forecast?
        hour = item[5:7]
        forecast = item[9:11]

        # Save the file similar to the standard hrrr file naming convention
        # except insert an X to represent that this is the experimental version
        NEWFILE = 'hrrrAK.t%sz.wrfprsf%s.grib2' % (hour, forecast)
        if os.path.isfile(OUTDIR+NEWFILE):
            print "looks like that file already exists", OUTDIR+NEWFILE
        else:
            # name the file with Taylor's convention
            #NEWFILE = 'hrrr_ak_prs_%02d%02d%02d%s' \
            #          % (yesterday.year-2000, yesterday.month, yesterday.day, hour)
            print "Downloading:", OUTDIR+NEWFILE
            ftp.retrbinary('RETR '+ item, open(OUTDIR+NEWFILE, 'wb').write)
            ftp.quit()

            # Don't truncate any variables.

            print "Saved:", OUTDIR+NEWFILE

            # Move to Pando S3 archive
            FILE = OUTDIR+NEWFILE
            DIR_S3 = 'HRRR/%s/%s/%04d%02d%02d/' \
                        % ('alaska', 'prs', DATE.year, DATE.month, DATE.day)
            if os.path.isfile(FILE):
                copy_to_horelS3(FILE, DIR_S3)
                create_idx(FILE, DIR_S3)
            else:
                print "%s does not exist", FILE

            print "Moved to Pando:", FILE

            # Change permissions of S3 directory to public
            s3cmd = '/uufs/chpc.utah.edu/common/home/horel-group/archive_s3/s3cmd-1.6.1/s3cmd'
            os.system(s3cmd + ' setacl s3://%s --acl-public --recursive' % DIR_S3)

# -----------------------------------------------------------------------------
if __name__ == '__main__':

    print "\n================================================"
    print "Downloading HRRR Alaska"

    timer1 = datetime.now()

    """
    Get a list of all available files from the FTP site, then
    regenerate the list for files that have the desired forecast hours (fxx).
    Download files from that list.
    """
    # Get surface fields file names
    ftp = FTP('gsdftp.fsl.noaa.gov')
    ftp.login(user, password)
    ftp.cwd('hrrr_ak/alaska/wrftwo')
    ftp_filenames = ftp.nlst()
    ftp.quit()

    # Only list the files for the desired forecast hours
    sfc_fxxlist = ['%02d00' % (f) for f in sfc_fxx]
    sfc_filenames = [ftp_filenames[i] for i in range(len(ftp_filenames)) \
                        if ftp_filenames[i][-4:] in sfc_fxxlist]

    # Download surface fields on multiple processors
    num_proc = 5
    p = multiprocessing.Pool(num_proc)
    p.map(download_hrrrAK_sfc, sfc_filenames)
    p.close()

    # Get pressure fields file names
    ftp = FTP('gsdftp.fsl.noaa.gov')
    ftp.login(user, password)
    ftp.cwd('hrrr_ak/alaska/wrfprs')
    prs_filenames = ftp.nlst()
    ftp.quit()

    # Only list the files for the desired forecast hours
    prs_fxxlist = ['%02d00' % (f) for f in prs_fxx]
    prs_filenames = [prs_filenames[i] for i in range(len(prs_filenames)) \
                     if prs_filenames[i][-4:] in prs_fxxlist]

    # Download pressure fields on multiple processors
    num_proc = 5
    p = multiprocessing.Pool(num_proc)
    p.map(download_hrrrAK_prs, prs_filenames)
    p.close()

    print "Time to download HRRR-AK:", datetime.now() - timer1

    exit()