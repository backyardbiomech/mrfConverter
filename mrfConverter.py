#!/usr/bin/env python3

import numpy as np
import cv2
from pathlib import Path
import subprocess
import argparse
import shutil
import bz2

# example call: python mrfConverter.py ./Red.mrf -crf 21

# reads info from mrf file header https://media.idtvision.com/docs/manuals/mstudio_man_en.pdf
def mrfInfo(fpath):
    dt = ['S1', 'int32', 'int32', 'int32', 'int32', 'int32', 'int32', 'int32', 'int32', 'int32', np.ushort, np.ushort,
          'int32', 'int32']
    chunks = [8, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 59, 1]
    names = ['header', 'blank1', 'headerPad', 'numFrames', 'width', 'height', 'bitDepth', 'nCams', 'blank2', 'blank3',
             'nBayer', 'nCFAPattern', 'userdata', 'frameRate']
    info = {}
    with open(fpath, 'rb') as f:
        for n, d, c in zip(names, dt, chunks):
            info[n] = np.fromfile(f, count=c, dtype=d)
    f.close()
    return (info)

# reads video one frame at a time
def mrfRead(fpath, frameNum):
    # get info
    info = mrfInfo(fpath)
    if info['bitDepth'] > 8 and info['bitDepth'] < 17:  # bit depth probably 10, just confirm
        bpp = 16
        nDim = 1
    # offset is the location of the start of the target frame in the file:
    # the pad + 8bits for each frame + the size of all of the prior frames
    offset = int(info['headerPad']) + (frameNum) * (info['height'] * info['width'] * bpp / 8)
    # read the image data
    with open(fpath, 'rb') as f:
        idata = np.fromfile(f, count=int(info['height'] * info['width']), offset=offset, dtype='uint16')
    f.close()
    # shift away the bottom 2 bits
    idata = np.right_shift(idata, 2)
    idata = idata.astype(np.uint8)
    # the data come in as a 1 dimensional array; here we
    # reshape them to a 2-dimensional array of the appropriate size
    idata = np.reshape(idata, (int(info['height']), int(info['width'])))
    return idata


# read video and output as image stack to be converted with ffmpeg
def cvtMrf(fpath, extractframes=True, savevid=True, crf=1):
    # to use extracted frames, set extractframes=False
    # to not save a new video, set savevid=False
    # crf is an int (1-51) for video compression (1 ~ lossless, 21 ~ very good compression with little visual loss)
    fp = fpath
    newdir = fp.parent / fp.stem
    newdir.mkdir(exist_ok=True)
    # get info
    info = mrfInfo(fp)
    nframes = int(info['numFrames'])
    if extractframes is True:
        for i in range(nframes):
            print("converting frame {} of {}".format(i+1, nframes))
            idata = mrfRead(fpath, i)
            idata = cv2.cvtColor(idata, cv2.COLOR_GRAY2RGB)
            iname = newdir / "frame{:05d}.tiff".format(i)
            cv2.imwrite(str(iname), idata)
    if savevid is True:
        print("converting tiffs to mp4")
        # convert to vid with ffmpeg

        istr = str(newdir / 'frame%05d.tiff')
        ostr = str(newdir) + '_c{}.mp4'.format(crf)
        cmd = 'ffmpeg -i "{}" -y -crf {} -c:v libx264 -vf fps=30 -pix_fmt yuv420p "{}"'.format(istr, crf, ostr)
        print(cmd)
        subprocess.call(cmd, shell=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'convert mrf to tiffs and vid')
    parser.add_argument('filename', help='path to mrf video')
    parser.add_argument('-exfr', default = True, help='extract frames from vid to save as tiff')
    parser.add_argument('-vid', default = True, help='save tiffs as vid with ffmpeg')
    parser.add_argument('-crf', default = 1, type =int, help='compression ratio for video (1-51)')
    args = parser.parse_args()

    fname=Path(args.filename)
    #if it's compressed, save uncompressed file before running
    if fname.suffix == '.bz2':
        outname = fname.parent / fname.stem
        with bz2.BZ2File(fname) as fr, open("/Users/jacksonbe3/repos/mrfConverter/Red2.mrf", "wb+") as fw:
            shutil.copyfileobj(fr, fw, length=100000000)  # 100 MB chunks
        fname=outname

    cvtMrf(fname, extractframes=args.exfr, savevid=args.vid, crf=args.crf)
