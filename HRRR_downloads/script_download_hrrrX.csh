#!/bin/csh

# ----------------------------------------------------------------------------
# Brian Blaylock
# August 3, 2017               Everyone in the group is getting tacos for lunch
#
# CRON tab on meso1 mesohorse user, run at 12:05 and 18:05 local time 
# Download the HRRR files for "yesterday" UTC
# Move HRRR Files to horelS3, create .idx, and change S3 directory files to public
# ----------------------------------------------------------------------------

set dateStart = `date +%Y-%m-%d_%H:%M`

setenv SCRIPTDIR "/uufs/chpc.utah.edu/common/home/horel-group/archive_s3/HRRR_downloads"

# Load some modules
module load rclone
module load python/2.7.3          # until meso1 upgrades to centOS 7, then load python/2.7.11
module load wgrib2

# Download HRRR to horel-group archive and copy to Pando S3 archive
python ${SCRIPTDIR}/download_hrrrX_multipro.py

echo Begin: $dateStart
echo End:   `date +%Y-%m-%d_%H:%M`
exit