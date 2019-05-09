#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# 2015 Michael Stucky
# This script is based on Raymond Wagner's transcode wrapper stub.
# Designed to be a USERJOB of the form </path to script/transcode-h264.py %JOBID%>

from MythTV import Job, Recorded, System, MythDB, findfile, MythError, MythLog, datetime

from optparse import OptionParser
from glob import glob
from shutil import copyfile
import sys
import os
import errno
import time

transcoder = '/usr/bin/ffmpeg'
flush_commskip = True
build_seektable = True

def runjob(jobid=None, chanid=None, starttime=None):
    db = MythDB()
    if jobid:
        job = Job(jobid, db=db)
        chanid = job.chanid
        starttime = job.starttime
    rec = Recorded((chanid, starttime), db=db)

    sg = findfile('/'+rec.basename, rec.storagegroup, db=db)
    if sg is None:
        print 'Local access to recording not found.'
        sys.exit(1)

    infile = os.path.join(sg.dirname, rec.basename)
    tmpfile = '%s.tmp' % infile.rsplit('.',1)[0]
    outfile = '%s.mp4' % infile.rsplit('.',1)[0]

    # reformat 'starttime' for use with mythtranscode/ffmpeg/mythcommflag
    starttime = str(starttime.utcisoformat().replace(u':', '').replace(u' ', '').replace(u'T', '').replace('-', ''))

    # Lossless transcode to strip cutlist
    if rec.cutlist == 1:
        if jobid:
            job.update({'status':4, 'comment':'Removing Cutlist'})

        task = System(path='mythtranscode', db=db)
        try:
            output = task('--chanid "%s"' % chanid,
                          '--starttime "%s"' % starttime,
                          '--mpeg2',
                          '--honorcutlist',
                          '-o "%s"' % tmpfile,
                          '2> /dev/null')
        except MythError, e:
            print 'Command failed with output:\n%s' % e.stderr
            if jobid:
                job.update({'status':304, 'comment':'Removing Cutlist failed'})
            sys.exit(e.retcode)
    else:
        copyfile('%s' % infile, '%s' % tmpfile)

    # Transcode to mp4
    if jobid:
        job.update({'status':4, 'comment':'Transcoding to mp4'})

    task = System(path=transcoder, db=db)
    try:
        output = task('-i "%s"' % tmpfile,
                      '-filter:v yadif=0:-1:1',
                      '-c:v libx264',
                      '-preset:v slow',
                      '-crf:v 18',
                      '-strict -2',
                      '-metadata:s:a:0',
                      'language="eng"',
                      '"%s"' % outfile,
                      '2> /dev/null')
    except MythError, e:
        print 'Command failed with output:\n%s' % e.stderr
        if jobid:
            job.update({'status':304, 'comment':'Transcoding to mp4 failed'})
        sys.exit(e.retcode)

    rec.basename = os.path.basename(outfile)
    os.remove(infile)
    # Cleanup the old *.png files
    for filename in glob('%s*.png' % infile):
        os.remove(filename)
    os.remove(tmpfile)
    try:
        os.remove('%s.map' % tmpfile)
    except OSError:
        pass
    rec.filesize = os.path.getsize(outfile)
    rec.transcoded = 1
    rec.seek.clean()

    if flush_commskip:
        for index,mark in reversed(list(enumerate(rec.markup))):
            if mark.type in (rec.markup.MARK_COMM_START, rec.markup.MARK_COMM_END):
                del rec.markup[index]
        rec.bookmark = 0
        rec.cutlist = 0
        rec.markup.commit()

    rec.update()

    if jobid:
        job.update({'status':4, 'comment':'Rebuilding seektable'})

    if build_seektable:
        task = System(path='mythcommflag')
        task.command('--chanid %s' % chanid,
                     '--starttime %s' % starttime,
                     '--rebuild',
                     '2> /dev/null')

    if jobid:
        job.update({'status':272, 'comment':'Transcode Completed'})

def main():
    parser = OptionParser(usage="usage: %prog [options] [jobid]")

    parser.add_option('--chanid', action='store', type='int', dest='chanid',
            help='Use chanid for manual operation')
    parser.add_option('--starttime', action='store', type='int', dest='starttime',
            help='Use starttime for manual operation')
    parser.add_option('-v', '--verbose', action='store', type='string', dest='verbose',
            help='Verbosity level')

    opts, args = parser.parse_args()

    if opts.verbose:
        if opts.verbose == 'help':
            print MythLog.helptext
            sys.exit(0)
        MythLog._setlevel(opts.verbose)

    if len(args) == 1:
        runjob(jobid=args[0])
    elif opts.chanid and opts.starttime:
        runjob(chanid=opts.chanid, starttime=opts.starttime)
    else:
        print 'Script must be provided jobid, or chanid and starttime.'
        sys.exit(1)

if __name__ == '__main__':
    main()
