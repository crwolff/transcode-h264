# transcode-h264

From https://www.mythtv.org/wiki/Transcode_Mpeg2_to_H264

Convert a single file:
```bash
/usr/local/bin/transcode-h264-v2.py \
	--chanid=1061 \
	--starttime=20190509020000-0700 \
	--tzoffset=-7
```

Bulk conversion:

```bash
#!/bin/bash

#
# Change reflect UTC offset for the date of the current file
#
OFFSET=-0700
for i in *.ts ; do 
    /usr/local/bin/transcode-h264-v2.py \
		--chanid=`echo $i | sed -e 's/^\(.*\)_.*/\1/'` \
		--starttime=`echo $i | sed -e 's/.*_\(.*\).ts/\1/'`${OFFSET} \
		--tzoffset=`echo $OFFSET | sed -e 's/0//g'`
done
```
