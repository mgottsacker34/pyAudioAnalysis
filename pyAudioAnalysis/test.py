from pyAudioAnalysis import audioSegmentation as aS

inputWavFile = "data/meeting-021219/part-1-nosilence.wav"
gtFile = inputWavFile.replace(".wav", ".segments")

[flagsInd, classesAll, acc, CM] = aS.mtFileClassification(inputWavFile, "data/knnSpeakerFemaleMale", "knn", plot_results=False, gt_file=gtFile)
print('flagsInd:   ', flagsInd)
print('classesAll: ', classesAll)
print('acc:        ', acc)
print('CM:         ', CM)
