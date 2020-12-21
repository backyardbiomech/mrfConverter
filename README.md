## A simple converter for IDT mrf video files

`python mrfConverter.py vidpath -exfr True -vid True -crf 21`

+ replace `vidpath` with the full path to the video (uses pathlib so should be platform indpendent)
+ `-exfr` asks if you want to extract tiff from mrf. Set to False if already extracted (must be in dir next to mrf, with same name as video)
+ `-vid` asks if you want to use ffmpeg to convert the tiffs into an mp4. Set to False if no video output desired.
+ `crf` is an integer (1-51) describing ffmpeg compression under h264. 1 is nearly lossless, 18-21 provides very good looking videos but much smaller file sizes, and 51 is very small with obvious compression artefacts
