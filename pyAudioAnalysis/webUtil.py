import sys
import os
import re
import glob
import argparse
from pydub import AudioSegment
import scipy.io.wavfile as wavfile
from matplotlib import pyplot as mp

from pyAudioAnalysis import audioBasicIO as aIO
from pyAudioAnalysis import audioSegmentation as aS

def produceVisuals(filename,results):
    print('drawing visuals from evaluation')
    
    #labels = 'Male', 'Female', 'Unknown'
    #sizes = [results[0],results[1],results[2]]
    labels = 'Male', 'Female'
    sizes = [results[0], results[1]]

    fig0,ax0 = mp.subplots()
    ax0.pie(sizes, labels=labels, autopct='%1.1f%%',shadow=False, startangle=180, colors=['#75d2e5','#f7b2bd'])
    
    ax0.axis('equal')
    #mp.title('Evaluation')

    picPath = (filename + '.png')
    #picPath = picPath.replace('./uploads/', './uploads/viz/')
    print(picPath)
    mp.savefig(picPath)
    return picPath
    
def visualizeAggregateData(m_ratio, f_ratio):
    labels = 'Male', 'Female'
    sizes = [m_ratio, f_ratio]
    print(sizes)
    
    fig0,ax0 = mp.subplots()
    ax0.pie(sizes, labels=labels, autopct='%1.1f%%',shadow=False, startangle=180, colors=['#75d2e5','#f7b2bd'])
    
    ax0.axis('equal')
    #mp.title('Evaluation')

    picPath = "./uploads/aggregateData.png"
    mp.savefig(picPath)
    return picPath
    

def mf_classify(filename):
    print('processing: ', filename)
    
    m_flags = 0
    f_flags = 0
    unk_flags = 0 
    unk_ratio = 0 
    m_ratio = 0 
    f_ratio = 0
    unk_ratio = 0
    m_time = 0
    f_time = 0
    unk_time = 0
    
    # method of classifying male/female speakers
    gtFile = filename.replace(".wav", ".segments")

    [flagsInd, classesAll, acc, CM] = aS.mtFileClassification(filename, "data/knnSpeakerFemaleMale", "knn", plot_results=False, gt_file=gtFile)
    print('flagsInd:   ', flagsInd)
    print('classesAll: ', classesAll)
    print('acc:        ', acc)
    print('CM:         ', CM)
    
    # Add up each classified flag
    for i in flagsInd:
        if (i==0):
            m_flags += 1
        elif(i==1):
            f_flags += 1
        else:
            unk_flags += 1

    m_ratio = m_flags/len(flagsInd)
    f_ratio = f_flags/len(flagsInd)
    unk_ratio = unk_flags/len(flagsInd)

    m_time = m_flags
    f_time = f_flags
    unk_time = unk_flags*0.2

    #AGGREGATE THEM ALL INTO A LIST
    majorKeys = [m_ratio,f_ratio,unk_ratio,m_time,f_time,unk_time]
    return majorKeys

def removeSilence(filename, smoothing, weightThresh):
    print('Removing silence from ' + filename + '...')

    # Use pAA to remove silence and get the segments with audio.
    [Fs, x] = aIO.readAudioFile(filename)
    segments = aS.silenceRemoval(x, Fs, 0.020, 0.020, smoothWindow = smoothing, weight = weightThresh, plot = False)

    # FUTURE WORK: Possibility to do more processing on the speech segments. For example, if the
    # gap is very short, and the speaker switches from a man to a woman, it could
    # be evidence of an interruption.

    # Produce .wav files with speech activity.
    print('Creating .wav files from non-silent segments...')
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
    return outfile
