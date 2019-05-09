# transcode-h264

From https://www.mythtv.org/wiki/Transcode_Mpeg2_to_H264

Bulk conversion:

```bash
#!/bin/bash

#
# Change reflect UTC offset for the date of the current file
#
OFFSET=-0700
for i in *.ts ; do 
    transcode-h264-v2.py \
		--chanid= `echo $i | sed -e 's/^\(.*\)_.*/\1/' \
		--starttime=`echo $i | sed -e 's/1041_\(.*\).ts/\1/'`${OFFSET} \
		--tzoffset=`echo $OFFSET | sed -e 's/0//g'
done
