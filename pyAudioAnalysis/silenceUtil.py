import sys
import os
import re
import glob
import argparse
from pydub import AudioSegment
import scipy.io.wavfile as wavfile

from pyAudioAnalysis import audioBasicIO as aIO
from pyAudioAnalysis import audioSegmentation as aS

parser = argparse.ArgumentParser(description='Generate audio file without silence.')
parser.add_argument('--inputfile', '-i', type=str, required=True, help='.wav file to analyze')
parser.add_argument('--smoothingWindow', '-sw', type=float, required=True, help='window (in seconds) used to smooth the SVM probabilistic sequence of silence removal')
parser.add_argument('--weight', '-w', type=float, required=True, help='a factor between  and 1 defining the weight, or strictness, for thresholding in silence removal')
args = parser.parse_args()

# if '.wav' not in sys.argv[1]:
#     print('ERROR: Please enter a .wav file as the first argument. Exiting.')
#     sys.exit()
# if not os.path.isfile(sys.argv[1]):
#     print('ERROR: Please enter a valid .wav file as the first argument. Exiting.')
#     sys.exit()
#
# # Read commandline args.
# filename = sys.argv[1]
# smoothing = float(sys.argv[2])
# weightThresh = float(sys.argv[3])
filename = args.inputfile
smoothing = args.smoothingWindow
weightThresh = args.weight


print('Removing silence from ' + filename + '...')

# Use pAA to remove silence and get the segments with audio.
[Fs, x] = aIO.readAudioFile(filename)
segments = aS.silenceRemoval(x, Fs, 0.020, 0.020, smoothWindow = smoothing, weight = weightThresh, plot = False)

# TODO: Possibility to do more processing on the speech segments. For example, if the
# gap is very short, and the speaker switches from a man to a woman, it could
# be evidence of an interruption.

# Produce .wav files with speech activity.
print('Creating .wav files from silent segments...')
for i, s in enumerate(segments):
    strOut = "{0:s}_{1:.3f}-{2:.3f}.wav".format(filename[0:-4], s[0], s[1])
    wavfile.write(strOut, Fs, x[int(Fs * s[0]):int(Fs * s[1])])

# Get basename of file without .wav extension.
basename = re.findall('.*[^.wav]', filename)[0]
pattern = basename + '_*.wav'
infiles = glob.glob(pattern)

# Insertion sort on filenames. Default sort() does not work here.
print('Sorting filenames...')
for i in range(1,len(infiles)):
    # Get starting timestamp of filename.
    currentFile = infiles[i]
    currentStartTime = re.findall('_[0-9]+\.[0-9]+', infiles[i])
    currentStartTime = float(currentStartTime[0][1:]) # remove leading underscore
    # Get starting timestamp of preceding filename.
    previousFile = infiles[i-1]
    previousStartTime = re.findall('_[0-9]+\.[0-9]+', infiles[i-1])
    previousStartTime = float(previousStartTime[0][1:])

    # print('previousStart: ' + str(previousStartTime) + ', currentstart: ' + str(currentStartTime))

    # Swap out of order elements until sorted.
    while i > 0 and previousStartTime > currentStartTime:
        infiles[i] = previousFile
        i = i - 1
        infiles[i] = currentFile
        # Update timestamps.
        previousFile = infiles[i-1]
        previousStartTime = re.findall('_[0-9]+\.[0-9]+', infiles[i-1])
        previousStartTime = float(previousStartTime[0][1:])
        currentFile = infiles[i]
        currentStartTime = re.findall('_[0-9]+\.[0-9]+', infiles[i])
        currentStartTime = float(currentStartTime[0][1:])

        # print('  i = ' + str(i) + ', previousStartTime = ' + str(previousStartTime) + ', currentStartTime = ' + str(currentStartTime))
        # print('    infiles[i-1]: ' + infiles[i-1] + ', infiles[i]: ' + infiles[i])

# Use pydub to combine the list of files into a single .wav file.
print('Combining segments with speech activity and removing files generated by pyAudioAnalysis silenceRemoval()')
combined_sounds = AudioSegment.silent(duration=10) # create audio segment with 10 ms of silence
for infile in infiles:
    # print(infile)
    combined_sounds = combined_sounds + AudioSegment.from_wav(infile)
    # Clean up and remove files generated by pAA silenceRemoval.
    os.remove(infile)

outfile = basename + '-nosilence.wav'
print('Writing output file: ' + outfile + '.')
combined_sounds.export(outfile, format="wav")
