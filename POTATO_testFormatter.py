### Code used to add additional variables to the ROOT file
## require as input a ROOT file which is the merge of Results.root and MonitorDQM.root (see POTATO_mergeFile.py)
## it requires https://gitlab.cern.ch/otsdaq/potatoconverters/-/tree/master


import os
from POTATO_PisaFormatter import POTATOPisaFormatter as Formatter

from POTATO_mergeFile import mergeTwoROOTfiles


if __name__ == "__main__":
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
    
    ### Example file: https://cernbox.cern.ch/remote.php/dav/public-files/zcvWnJKEk7YgSBh//Run_500087/output_lahes.zip
    # (from webpage https://cmstkita.web.cern.ch/Pisa/TBPS/navigator.php/Uploads//test3/Module_PS_26_IBA-10003_Run_run500087_Result_Mar11/results_ueshi.zip/) 
    # wget https://cernbox.cern.ch/remote.php/dav/public-files/zcvWnJKEk7YgSBh//Run_500087/output_lahes.zip
    # unzip output_lahes.zip -d Run_500087_output_lahes

    resultsFile = "Run_500087_output_lahes/Results.root"
    monitorDQMFile = "Run_500087_output_lahes/MonitorDQM_2025-04-04_11-34-05.root"

    outDir = "POTATOFiles"
    theFormatter = Formatter(outDir)

    rootTrackerFileName = outDir + "/" + "ResultsWithMonitorDQM.root"

    mergeTwoROOTfiles(resultsFile, monitorDQMFile, rootTrackerFileName)
    print("Merged file created:", rootTrackerFileName)

    ## copy the connectionMap file to the same folder as the ROOT file
    connectionMapFile = "connectionMap_PS_26_IBA-10003.json"
    connectionMapFilePath = os.path.join(os.path.dirname(resultsFile), connectionMapFile)
    if os.path.exists(connectionMapFilePath):
        os.system("cp " + connectionMapFilePath + " " + outDir)
    else:
        print("Connection map file not found:", connectionMapFilePath)

    runNumber = "Run_500087"
    moduleBurninName = "Module4L"
    moduleCarrierName = "01" ## used to read sensor OW01 was "ModuleCarrier4Left"
    opticalGroup = '0'

    ### Important: PISA Formatter requires the connectionMap file to be in the same folder as the ROOT file (eg. connectionMap_PS_26_IBA-10003.json)
    theFormatter.do_burnin_format(rootTrackerFileName, runNumber, opticalGroup, moduleBurninName, moduleCarrierName)

    print()
    print("PISA Formatter done")
    print("Output file:", rootTrackerFileName)
    print()
    ### Now looping on all output files to add monitoring infos

