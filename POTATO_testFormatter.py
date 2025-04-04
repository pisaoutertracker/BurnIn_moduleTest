### Code used to add additional variables to the ROOT file
## require as input a ROOT file which is the merge of Results.root and MonitorDQM.root (see POTATO_mergeFile.py)
## it requires https://gitlab.cern.ch/otsdaq/potatoconverters/-/tree/master


import os
from POTATO_PisaFormatter import POTATOPisaFormatter as Formatter

from POTATO_mergeFile import mergeTwoROOTfiles


###############################################################################################
def main():
#    trackerFileRadix        = "TrackerHistos"
#    trackerMonitorFileRadix = "TrackerMonitorHistos"
#    trackerFilesDir         = os.environ['TRACKER_FILES']
#    outputFilesDir          = os.environ['OUTPUT_FILES']

    ### Now looping on all output files to add monitoring infos
#    theFormatter = Formatter(outputFilesDir + "/../Result/")
#    theFormatter = Formatter(outputFilesDir + "/../TestFiles/Run_500009")
    #theFormatter = Formatter("/home/thermal/BurnIn_moduleTest/potatoconverters/Test2/")
    
   
    #outputFileNamesList = ['/home/uplegger/Programming/potatoconverters/OutputFiles/2S_18_5_FNL-00001_2024-07-12_11h13m29s_+15C_v1-00.root', '/home/uplegger/Programming/potatoconverters/OutputFiles/2S_18_5_FNL-00001_2024-07-12_11h15m32s_+15C_v1-00.root', '/home/uplegger/Programming/potatoconverters/OutputFiles/2S_18_5_FNL-00001_2024-07-12_11h17m23s_+15C_v1-00.root', '/home/uplegger/Programming/potatoconverters/OutputFiles/2S_18_5_FNL-00001_2024-07-12_11h19m55s_+15C_v1-00.root', '/home/uplegger/Programming/potatoconverters/OutputFiles/2S_18_5_FNL-00001_2024-07-12_11h21m46s_+15C_v1-00.root', '/home/uplegger/Programming/potatoconverters/OutputFiles/2S_18_5_FNL-00001_2024-07-12_11h24m11s_+15C_v1-00.root']
#    outputFileNamesList = ['/home/uplegger/Programming/potatoconverters/test.root']
    #outputFileNamesList = ['/home/thermal/BurnIn_moduleTest/potatoconverters/SilvioTest/test.root']
    
    resultsFile = "potatoconverters/TestFiles/Run_500009/Results.root"
    monitorDQMFile = "potatoconverters/TestFiles/Run_500009/MonitorDQM_2025-03-25_17-17-32.root"

    outDir = "POTATOFiles"
    theFormatter = Formatter(outDir)

    rootTrackerFileName = "/home/thermal/BurnIn_moduleTest/potatoconverters/SilvioTest/Results.root"

    mergeTwoROOTfiles(resultsFile, monitorDQMFile, rootTrackerFileName)
    print("Merged file created:", rootTrackerFileName)

    rootTrackerFileName = "/home/thermal/BurnIn_moduleTest/potatoconverters/SilvioTest/Results.root"
    runNumber = "150"
    moduleBurninName = "Module4L"
    moduleCarrierName = "ModuleCarrier4Left"
    opticalGroup = '1'

    theFormatter.do_burnin_format(rootTrackerFileName, runNumber, opticalGroup, moduleBurninName, moduleCarrierName)


############################################################################################
if __name__ == "__main__":
    main()
