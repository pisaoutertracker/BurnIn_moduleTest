#!/bin/env python3

### Default values 
verbose = -1
lastPh2ACFversion = "ph2_acf_v6-04"
xmlPyConfigFile = "PS_Module_settings.py"
ip="192.168.0.45"
port=5000
xmlOutput="ModuleTest_settings.xml"
defaultCommand="PSquickTest"
##xmlTemplate="PS_Module_template.xml"
xmlTemplate="PS_Module_v2p1.xml"
firmware_5G="ps8m5gcic2l12octal8dio5v301" #"ps8m5gcic2l12octal8dio5tluv300" ##5 GBps - https://udtc-ot-firmware.web.cern.ch/?dir=v3-00/ps_8m_5g_cic2_l12octa_l8dio5_tlu
firmware_10G="ps8m10gcic2l12octal8dio5v301" ##10 GBps - https://udtc-ot-firmware.web.cern.ch/?dir=v3-00/ps_8m_10g_cic2_l12octa_l8dio5_tlu
runFpgaConfig = False ## it will run automatically if necessary
## command used to launch commands through Docker (podman)
## -v /home/thermal/suvankar/power_supply/:/home/thermal/suvankar/power_supply/
podmanCommand = 'podman run  --rm -ti -v $PWD/Results:/home/cmsTkUser/Ph2_ACF/Results/:z -v $PWD/logs:/home/cmsTkUser/Ph2_ACF/logs/:z -v $PWD:$PWD:z -v /etc/hosts:/etc/hosts -v ~/private/webdav.sct:/root/private/webdav.sct:z  --net host  --entrypoint bash  gitlab-registry.cern.ch/cms-pisa/pisatracker/pisa_module_test:%s -c "%s"' ## For older version: docker.io/sdonato/pisa_module_test:ph2_acf_v4-23
import os
prefixCommand = '\cp  /usr/share/zoneinfo/Europe/Rome /etc/localtime && cd /home/cmsTkUser/Ph2_ACF && source setup.sh && cd %s' %os.getcwd()
settingFolder_docker = "/home/cmsTkUser/Ph2_ACF/settings"
connectionMapFileName = "connectionMap_%s.json"

## assign these lpGBT hardware IDs to some random modules (they will be in the module database)
#lpGBTids = ['3962125297', '42949672', '42949673', '42949674', '2762808384', '0x00', '0x67']
lpGBTids = []

### webdav keys
hash_value_location = "~/private/webdav.sct" #echo "xxxxxxxxxxxxxxx|xxxxxxxxxxxxxxx" > ~/private/webdav.sct
webdav_url = "https://cernbox.cern.ch/remote.php/dav/public-files"
from webdavclient import WebDAVWrapper
hash_value_read, hash_value_write = open(os.path.expanduser(hash_value_location)).read()[:-1].split("\n")[0].split("|")
webdav_wrapper = WebDAVWrapper(webdav_url, hash_value_read, hash_value_write)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Script used to launch the test of the Phase-2 PS module, using Ph2_ACF. More info at https://github.com/pisaoutertracker/BurnIn_moduleTest. \n Example: \npython3 moduleTest.py --module PS_26_05-IBA_00102 --slot 0,1 --session session1 . ')
    required = parser.add_argument_group('required arguments')
    required.add_argument('--session', type=str, default='-1', help='Name of the existing session (eg. session1). ', required=False)
    required.add_argument('-m', '--message', type=str, default='-1', help='Messagge used to create a new session. It requires "|" to separate between the author and the message ', required=False)
    required.add_argument('--module', type=str,  help='Optical group number (eg. PS_26_05-IBA_00102). "auto" will select the expected module according to the connection database.', required=True)
    required.add_argument('--slot', type=str, default='-1', help='Module name (eg. 0,1,2).', required=False)
    required.add_argument('--board', type=str, default='-1', help='Board name (eg. fc7ot2).', required=False)
    required.add_argument('--strip', type=str, default='0,1,2,3,4,5,6,7', help='strip number (eg. 0,1,2 default=all).', required=False)
    required.add_argument('--pixel', type=str, default='8,9,10,11,12,13,14,15', help='pixel number (eg. 8,9,15 default=all).', required=False)
    required.add_argument('--hybrid', type=str, default='0,1', help='hybrid number (default=0,1).', required=False)
    required.add_argument('--lpGBT', type=str, default='lpGBT_v1_PS.txt', help='lpGBT file (default=lpGBT_v1_PS.txt).', required=False)
    
    parser.add_argument('--useExistingModuleTest', type=str, nargs='?', const='', help='Read results from an existing module test. Skip ot_module_test run (for testing).')
    parser.add_argument('-f','--useExistingXmlFile', type=str, nargs='?', const='', help='Specify an existing xml file without generating a new one (for testing).  ')
    parser.add_argument('-c','--command', type=str, default=defaultCommand, nargs='?', const='', help='Specify which command will be passed to runCalibration -c (calibrationandpedenoise, configureonly, PSquickTest, PSfullTest, readOnlyID). Default: %s'%defaultCommand)
#    parser.add_argument('--verbose', type=int, nargs='?', const=10000, default=-1, help='Verbose settings.')
    parser.add_argument('--edgeSelect', type=str, default='None', help='Select edgeSelect parameter (Default taken from PS_Module_template.xml).')
    parser.add_argument('--version', type=str, default=lastPh2ACFversion, nargs='?', const=True, help='Select the Ph2ACF version used in Docker. Use "local" to select the Ph2ACF locally installed. Default: %s'%lastPh2ACFversion)
    parser.add_argument('--addNewModule', type=bool, default=False, nargs='?', const=True, help='Add new module to the database without asking y/n.')
    parser.add_argument('--g10', type=bool, nargs='?', const=True, help='Install 10g firmware (%s).'%firmware_10G)
    parser.add_argument('--g5', type=bool, nargs='?', const=True, help='Install 5g firmware (%s).'%firmware_5G)
    parser.add_argument('--runFpgaConfig', type=bool, nargs='?', const=True, help='Force run runFpgaConfig.')
    parser.add_argument('--vetoFpgaConfig', type=bool, nargs='?', const=True, help='Veto on runFpgaConfig (useful for runCalibrationPisa).')
    parser.add_argument('--skipUploadResults', type=bool, nargs='?', const=True, default=False, help='Skip running updateTestResults at the end of the test.')
    parser.add_argument('--skipMongo', type=bool, nargs='?', const=True, help='Skip upload to mondoDB (for testing).')
    parser.add_argument('--skipModuleCheck', type=bool, default=False, nargs='?', const=True, help='Do not throw exception if the module declared does not correspond to the module in the slot.')
    parser.add_argument('--firmware', type=str, nargs='?', const='', help='Firmware used in fpgaconfig. Default=%s'%firmware_5G)
    parser.add_argument('--xmlPyConfigFile', type=str, nargs='?', const="PS_Module_settings.py", default="PS_Module_settings.py", help='location of PS_Module_settings.py file with the XML configuration.')
    parser.add_argument('--ignoreConnection', type=bool, default=False, nargs='?', const=True, help='Ignore database connection check, ie. do not throw exception if there is a mismatch between the database connection and the module declared')
    parser.add_argument('--tempSensor', type=str, default="Temp0", nargs='?', const=True, help='Select which temperature sensor will be displayed in the analysis page.')

    
    print("Example: python3 moduleTest.py --module PS_26_05-IBA_00102 --slot 0 --board fc7ot2 -c readOnlyID  --session session1")
    args = parser.parse_args()
    if not args.useExistingModuleTest and not args.useExistingXmlFile:
        if args.slot == "-1":
            raise Exception("Please provide a slot number. Eg. --slot 0")
        if args.board == "-1":
            raise Exception("Please provide a board name. Eg. --board fc7ot2")
    if not args.useExistingModuleTest:
        if args.module == "-1":
            raise Exception("Please provide a module name. Eg. --module PS_26_05-IBA_00102")
    if args.session == "-1" and args.message == "-1" and args.command!="readOnlyID":
        raise Exception("Please provide either a session name (eg. --session session1) or a message (eg. -m 'Mickey Mouse|Test of the burnin controller with the new firmware').")
    if args.message != "-1" and not "|" in args.message:
        raise Exception("The message passed with -m must contain a '|', eg. -m 'Silvio|Test', while you used -m '%s'."%args.message)
    ph2ACFversion = args.version
    if ph2ACFversion == "local":
        print()
        print("I will use local Ph2ACF instead of Docker!")
        if "PH2ACF_BASE_DIR" in os.environ: 
            ph2acf = os.environ['PH2ACF_BASE_DIR']
        else:
            raise Exception("No Ph2ACF available (eg. no runCalibration). Please do 'source setup.sh' from an Ph2ACF folder!")
        settingFolder = "%s/settings"%ph2acf
        print("Local Ph2ACF folder: %s"%ph2acf)
        print()
    else:
        settingFolder = settingFolder_docker
    from shellCommands import updateSettingsLink
    updateSettingsLink(settingFolder)
    print()
    print("moduleTest configuration:")
    print()
    print("Copying settings folder from: %s"%settingFolder)
    print("Ph2ACF version: %s"%ph2ACFversion)
    print("Verbose: %d"%verbose)
    print("Command: %s"%args.command)
    print("Session: %s"%args.session)
    print("Module: %s"%args.module)
    print("Slot: %s"%args.slot)
    print("Board: %s"%args.board)
    print("EdgeSelect: %s"%args.edgeSelect)
    print("Firmware: %s"%args.firmware)
    print("xmlPyConfigFile: %s"%args.xmlPyConfigFile)
    print("ignoreConnection: %s"%args.ignoreConnection)
    print("skipMongo: %s"%args.skipMongo)
    print("skipModuleCheck: %s"%args.skipModuleCheck)
    print("runFpgaConfig: %s"%args.runFpgaConfig)
    print("useExistingModuleTest: %s"%args.useExistingModuleTest)
    print("useExistingXmlFile: %s"%args.useExistingXmlFile)
    print("addNewModule: %s"%args.addNewModule)
    print("g10: %s"%args.g10)
    print("g5: %s"%args.g5)
    print("skipUploadResults: %s"%args.skipUploadResults)
    print("lpGBT: %s"%args.lpGBT)
    print("strip: %s"%args.strip)
    print("pixel: %s"%args.pixel)
    print("hybrid: %s"%args.hybrid)
    print("xmlTemplate: %s"%xmlTemplate)
    print("xmlOutput: %s"%xmlOutput)
    print("xmlPyConfigFile: %s"%xmlPyConfigFile)
    print("connectionMapFileName: %s"%connectionMapFileName)
    print()
    print("++++++++++++++++++ Preliminary checks ++++++++++++++++++")
    board = args.board
    lpGBTfile = args.lpGBT
    slots = args.slot.split(",")
    modules = args.module.split(",")
    if len(slots)!=len(modules):
        raise Exception("--slots and --modules must have the same number of objects. Check %s and %s."%(slots,modules))
    edgeSelect = args.edgeSelect
    hybrids = [int(h) for h in args.hybrid.split(",") if h != ""]
    pixels = [int(h) for h in args.pixel.split(",") if h != ""]
    strips = [int(h) for h in args.strip.split(",") if h != ""]
    if len(strips)>0 and max(strips)>7 or min(strips)<0: raise Exception("strip numbers are allowed in [0,7] range. Strips: %s"%(str(strips)))
    if len(pixels)>0 and (max(pixels)>15 or min(strips)<0): raise Exception("strip numbers are allowed in [8,15] range. Pixels: %s"%(str(pixels)))
    
    if args.useExistingXmlFile:
        from tools import parse_module_settings
        print("As you are using an existing module test, I will overwrite the board, slots, hybrids, strips, pixels with the one from the existing module test.")
        print("Value passed in the command line will be ignored (ie %s, %s, %s, %s, %s)."%(board, slots, hybrids, strips, pixels))
        board, slots, hybrids, strips, pixels  = parse_module_settings(args.useExistingXmlFile)
        opticalGroups = [int(s) for s in slots]
        print("The new values are: %s, %s, %s, %s, %s."%(board, slots, hybrids, strips, pixels))
    
    readOnlyID = (args.command=="readOnlyID")
    commandOption = args.command
    if readOnlyID: ##enable minimal configuration to get the hardware ID of the module
        hybrids = [hybrids[0]]
        pixels = []
        strips = [0]
    
    if args.firmware and args.g10:
        raise Exception("You cannot use --firmware and --10g option at the same time.")
    elif args.firmware:
        firmware = args.firmware
    elif args.g10:
        firmware = firmware_10G
    else:
        firmware = firmware_5G

    
    ## This will be replaced by a function that check which optical group are conntected to a specific slot
    opticalGroups = [int(s) for s in slots]

#    print("firmware",firmware)
#    verbose = args.verbose
    
    from pprint import pprint
    from tools import getROOTfile, getIDsFromROOT, getNoisePerChip, getResultsPerModule, checkAndFixRunNumbersDat
    from shellCommands import fpgaconfig, runModuleTest, burnIn_readSensors 
    from makeXml import makeXml, makeNoiseMap, readXmlConfig, makeXmlPyConfig
    from databaseTools import  uploadRunToDB, makeModuleNameMapFromDB, getRunFromDB, updateNewModule
#    from databaseTools import getTestFromDB, addTestToModuleDB, getModuleFromDB, addNewModule, uploadTestToDB
    
    ### make a symbolic link from ~/RunNumber.dat to local folder
    checkAndFixRunNumbersDat()

    ### read xml config file and create XML
    print("++++++++++++++++++ Creation of the XML file++++++++++++++++++")
    import shutil
    if args.useExistingModuleTest:
        matches = [folder for folder in os.listdir("Results") if args.useExistingModuleTest in folder ]
        if len(matches) != 1: raise Exception("%d matches of %s in ./Results/. %s"%( len(matches), args.useExistingModuleTest, str(matches)))
        folder = matches[0]
        xmlPyConfigPath = "%s/%s"%("Results/"+folder, xmlPyConfigFile)
        if os.path.exists("%s/%s"%(xmlPyConfigPath, xmlPyConfigFile)):
            xmlConfig = readXmlConfig(xmlPyConfigFile, folder=xmlPyConfigPath)
        else:
            xmlPyConfigFile = None
            from makeXml import makeConfigFromROOTfile, getInfosFromXmlPyConfig
            print("%s not found. Creating it from ROOT file."%xmlPyConfigPath)
            xmlConfig = makeConfigFromROOTfile("Results/"+folder+"/Results.root")
            print("As you are using an existing module test, I will overwrite the board, slots, hybrids, strips, pixels with the one from the existing module test.")
            print("Value passed in the command line will be ignored (ie %s, %s, %s, %s, %s)."%(board, slots, hybrids, strips, pixels))
            board, slots, hybrids, strips, pixels  = getInfosFromXmlPyConfig(xmlConfig)
            opticalGroups = [int(s) for s in slots]
            print("The new values are: %s, %s, %s, %s, %s."%(board, slots, hybrids, strips, pixels))
            if verbose>1: print(xmlConfig)      
        xmlFile = "Results/%s/%s"%(folder,xmlOutput)
        if os.path.exists(xmlFile):
            print("Using existing xml file: %s"%xmlFile)
        else:
            xmlFile = makeXml(xmlOutput, xmlConfig, xmlTemplate)
    else:
        outFile="PS_Module_settings_autogenerated.py"
        xmlPyConfigFile = outFile
        if not args.useExistingXmlFile:
            from shellCommands import copyXml
            copyXml(ph2ACFversion)
        xmlConfig = makeXmlPyConfig(board, opticalGroups, hybrids, strips, pixels, lpGBTfile, edgeSelect, outFile, Nevents=50)
        if args.useExistingXmlFile:
            xmlFile = args.useExistingXmlFile
        else:
            xmlFile = makeXml(xmlOutput, xmlConfig, xmlTemplate)

    if verbose>1:
        print("xmlConfig:")
        pprint(xmlConfig)


    if verbose>10:
        print(board)
        print(slots)
    #### check if the expected modules match the modules declared in the database for the slots ####
    print("++++++++++++++++++ Check if expected modules matches the modules from DB ++++++++++++++++++")
    from databaseTools import checkIfExpectedModulesMatchModulesInDB
    checkIfExpectedModulesMatchModulesInDB(board, slots, modules, args)

    ###########################################################
    #################### START OF THE TEST ####################
    ###########################################################
    ### launch fpga_config
    print("#### Launch the test ###")
    if args.runFpgaConfig or args.g10 or args.g5: fpgaconfig(xmlFile, firmware, ph2ACFversion)
    
    ### launch ot_module_test (if useExistingModuleTest is defined, read the existing test instead of launching a new one)
    print("args.useExistingModuleTest",args.useExistingModuleTest)
    out = runModuleTest(xmlFile, args.useExistingModuleTest, ph2ACFversion, commandOption) # 
    if out == "Run fpgaconfig":
        print("\n\nWARNING: You forgot to run fpgaconfig. I'm launching it now.\n")
        if args.vetoFpgaConfig:
            raise Exception("You forgot to run fpgaconfig. Please run it before running the module test. Eg. remove --vetoFpgaConfig flag or use --runFpgaConfig flag or run fpgaconfig manually.")
        else:
            print("\n\nWARNING: You forgot to run fpgaconfig. I'm launching it now.\n")
        fpgaconfig(xmlFile, firmware, ph2ACFversion)
        out = runModuleTest(xmlFile, args.useExistingModuleTest, ph2ACFversion, commandOption) # 
        if out == "Run fpgaconfig":
            raise Exception("fpgaconfig failed. Please check the error above.")
    testID, date = out
    print("++++++++++++++++++ Test completed. Parse ROOT file ++++++++++++++++++")
    
    ### read the output file (if args.useExistingModuleTest is defined, read the that ROOT file)
    rootFile = getROOTfile(testID) if not args.useExistingModuleTest else getROOTfile(args.useExistingModuleTest) 
    
    ### get the lpGBT hardware ID for each module from the ROOT file (CHIPID registers, CHIPID0)
    # Note: each module is identified by (board_id, opticalGroup_id)
    # IDs is a map: IDs[(board_id, opticalGroup_id)] --> hardware ID
    IDs = getIDsFromROOT(rootFile, xmlConfig)

    if verbose>3: print("xmlPyConfigFile=",xmlPyConfigFile)

## To change hardware ID for testing ##
#    for bo in IDs:
#        IDs[bo] = IDs[bo]+1
    if args.useExistingXmlFile: ## remove missing IDs if running useExistingXmlFile (xmlConfigFil is fake)
        for x in list(IDs.keys()):
            if IDs[x] == "-1":
                print("Deleting ", x)
                del IDs[x]
                del xmlConfig["boards"][str(x[0])]["opticalGroups"][str(x[1])]
    if verbose>5: pprint(IDs)
    
    if readOnlyID and args.skipMongo:
        pprint (IDs)
        print()
        print("readOnlyID finished successfully.")
        print()
        exit(0) ##if you just want the hardware ID, stop here.
    
    ### Read noise "NoiseDistribution_Chip" for each chip
    # noisePerChip is a map "D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)" --> noise
    print("++++++++++++++++++ Get noise and evaluate module: pass/failed (to be removed?) ++++++++++++++++++")
    noisePerChip = getNoisePerChip(rootFile , xmlConfig)
    if verbose>5: pprint(noisePerChip)
    
    ### Define an outcome result "pass" or "failed"
    result = getResultsPerModule(noisePerChip, xmlConfig)
    
    print()
    print("++++++++++++++++++  Check  module name vs hardware ID ++++++++++++++++++")
    if not args.skipMongo: 
        ### create a map between lpGBT hardware ID to ModuleName and to MongoID, reading the module database
        hwToModuleName, hwToMongoID = makeModuleNameMapFromDB()
        
#            for b, o in board_opticals:
        board = 0 
        error = False
        allModules = hwToModuleName.values()
        for i, opticalGroup in enumerate(opticalGroups):
            moduleExpected = modules[i] ## module passed from command line
            id_ = IDs[(board, opticalGroup)] if (board, opticalGroup) in IDs else -2 ## hardware IDs found in the test
            if int(id_)==-1 or int(id_)==-2:
                try:
                    message = "+++ Board %s Optical %d Module %d (NO MODULE FOUND). Expected %s. +++"%(xmlConfig["boards"][str(board)]["ip"], opticalGroup, int(id_), moduleExpected)
                except:
                    message = "+++ Board %s Optical %d Module %d (NO MODULE FOUND). Expected %s. +++"%(xmlConfig["boards"][board]["ip"], opticalGroup, int(id_), moduleExpected)
                print(message)
                if not args.skipModuleCheck: raise Exception(message + ". You can skip this error using --skipModuleCheck flag.")
                continue
            moduleFound = hwToModuleName[id_] if id_ in hwToModuleName else "unknown module" ## module found in the database matching the hardware ID
            if moduleExpected == None or moduleExpected == "auto":
                print("As you don't know any expected module, I will take the module name from the module ID.")
                modules[i] = moduleFound
            try:
                print("+++ Board %s Optical %d Module %s (%d). Expected %s. +++"%(xmlConfig["boards"][board]["ip"], opticalGroup, moduleFound, int(id_), moduleExpected))
            except:
                print("+++ Board %s Optical %d Module %s (%d). Expected %s. +++"%(xmlConfig["boards"][str(board)]["ip"], opticalGroup, moduleFound, id_, moduleExpected))
            if moduleExpected in allModules: ## if the expected module is already in the database, check that the module found matches with the expected module
                if moduleFound!=moduleExpected:
                    print("DIFFERENT MODULE FOUND!!")
                    error = True
            else: ## if the expected module is not in the database, add it to the DB
                print("List of known modules:")
                for hwId in hwToModuleName:
                    print("%s (%d)"%(hwToModuleName[hwId], int(hwId)))
                print("Module %s is not yet in the database."%(moduleExpected))
                print("HwId %d found."%(int(id_)))
                if id_ in hwToModuleName and int(id_)!=-1:
                    message = "HwId %d is already associated to module %s.\nPlease fix the module name used."%(id_, hwToModuleName[id_])
                    print(message)
                    if not args.skipModuleCheck: raise Exception(message)
                print(id_, args.skipModuleCheck)
                if int(id_)!=-1 and not args.skipModuleCheck:
                    if args.addNewModule:
                        answer = "y" ## add the module without asking
                    else:
                        answer = input("Do you want to add module with hwID %d as %s in the database? (y/n): "%(id_, moduleExpected))
                    if answer == "y" or answer == "yes" or answer == "Y":
                        updateNewModule(moduleExpected, id_) ## the DB function will check if the hardware ID is already used by another module
                        ##update map
                        hwToModuleName, hwToMongoID = makeModuleNameMapFromDB()
                        allModules = hwToModuleName.values()
                    else:
                        raise Exception("I cannot work with unknown modules.")

        if error:
            message = "The modules declared in --modules (%s) do not correspond to the module found in --slots (%s) of --board (%s). See above for more details."%(str(modules), str(opticalGroups),str(board))
            print(message)
            if not args.skipModuleCheck: raise Exception(message) 
        if readOnlyID:
            print()
            print("readOnlyID finished successfully.")
            print()
            exit(0) ##if you just want the hardware module names, stop here.
        
        ### convert IDs of modules used in the test to ModuleID and to MongoID ()
        board_opticals = list(IDs.keys())
        moduleNames = [ hwToModuleName[IDs[bo]] for bo in board_opticals ]
        moduleMongoIDs = [ hwToMongoID[IDs[bo]] for bo in board_opticals ]

        print("++++++++++++++++++  Make a folder on CERNbox, create a zip file of Result folder, upload the zip file ++++++++++++++++++")
    
        ## make a folder in CernBox
        if verbose>10: print("Creating folder %s"%testID)
        webdav_wrapper.mkDir("/%s"%testID)

        ''' ### Old code used to upload single files to CERN box. Not used anymore, as everything is uploaded through the zip file ###
        ## upload all files
        for file in [xmlPyConfigFile, xmlFile, rootFile.GetName(), "logs/%s.log"%testID]: #copy output files to CernBox
            if file: 
                if verbose>10: print("Uploading %s"%file)
                newFile = webdav_wrapper.write_file(file, "/%s/%s"%(testID, file))
                if verbose>1: print("Uploaded %s"%newFile)
        '''
        
        ## copy some important files (xml, log, py) in .../Results folder
        resultFolder = rootFile.GetName()[:rootFile.GetName().rfind("/")]
        logFile = "logs/%s.log"%testID
        for file in [xmlPyConfigFile, xmlFile, logFile]: #copy output files to CernBox
            ## make a symbolic link to the file in the Results folder
            if args.useExistingModuleTest and file == logFile: 
                logsFiles = [f for f in os.listdir("Results/"+folder) if ".log" in f]
                os.symlink(logsFiles[-1],logFile.replace("logs/",resultFolder+"/"))
            ## do not copy py, xml, log if using existing module test (they are meaningless and they are already in the CernBox)
            if args.useExistingModuleTest and (file == xmlPyConfigFile or file == xmlFile or file == logFile): continue
            if file and file != rootFile.GetName():
                shutil.copy(file, resultFolder)
                print("Copied %s to %s"%(file, resultFolder))

        ''' ### Old code used to upload single files to CERN box. Not used anymore, as everything is uploaded through the zip file ###
        ## create and upload connectionMap files
        from databaseTools import getConnectionMap, saveMapToFile
        for module in modules:
            if not args.useExistingModuleTest:
            ## I had a real test so I will make a new connection map
                connectionMap = getConnectionMap(module)
                saveMapToFile(connectionMap, resultFolder+"/"+connectionMapFileName%module)
                newFile = webdav_wrapper.write_file(resultFolder+"/"+connectionMapFileName%module, "/%s/%s"%(testID, connectionMapFileName%module))
                if verbose>1: print("Uploaded %s"%newFile)
            else: ## Use existing test --> no need to generate a new connection map
                print("Use existing module test I will not generate a new connection map")
                if os.path.exists(resultFolder+"/"+connectionMapFileName%module):
                    newFile = webdav_wrapper.write_file(resultFolder+"/"+connectionMapFileName%module, "/%s/%s"%(testID, connectionMapFileName%module))
                    if verbose>1: print("Uploaded %s"%newFile)
                else:
                    print("No connection map found in %s. I will not make a new one."%(resultFolder+"/"+connectionMapFileName%module))
        '''

        ## make a zip file and upload it
        zipFile = "output"
        if verbose>20: print("shutil.make_archive(zipFile, 'zip', resultFolder)", zipFile, resultFolder)
        shutil.make_archive(zipFile, 'zip', resultFolder)
        if verbose>20: print("Done")
        newFile = webdav_wrapper.write_file(zipFile+".zip", "/%s/output.zip"%(testID))
        if verbose>0: print("Uploaded %s"%newFile)
        
        print("++++++++++++++++++  Create session and run and upload it to DB ++++++++++++++++++")

        boardMap, moduleMap, noiseMap = makeNoiseMap(xmlConfig, noisePerChip, IDs, hwToModuleName)
        fakeRunResults = dict()
        for hwId in noiseMap:
            fakeRunResults[hwId] = "boh"
        date = date.replace(" ","T").split(".")[0] # drop ms
        if args.useExistingModuleTest:
            date = str(rootFile.Get("Detector/CalibrationStartTimestamp_Detector")).replace(" ","T")
            ## NOT NECESSARY ANYMORE: we use local time everywhere
            ## convert date from UTC to Rome time 
            #from datetime import datetime
            #from pytz import timezone
            #import pytz
            #rome = timezone('Europe/Rome')
            #utc = timezone('UTC')
            #if date[0:2] != "20": date = "20"+date
            #date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
            #date = utc.localize(date)
            #date = date.astimezone(rome)
            #date = date.strftime("%Y-%m-%dT%H:%M:%S")            
        
        if args.session != "-1":
            session = args.session
        else:
            from databaseTools import createSession
            session = createSession(args.message, modules)
        newRun = {
            'runDate': date, 
            'runSession': session,
            'runStatus': 'done',
            'runType': commandOption,
            'runBoards': boardMap, 
#            E.g.
#            {
#                3: 'fc7ot2',
#                4: 'fc7ot3',
#            },
            'runModules' : moduleMap,
#            E.g.
#            { ## (board, optical group) : (moduleID, hwIDmodule)
#                'fc7ot2_optical0' : ("M123", 67),
#                'fc7ot2_optical1' : ("M124", 68),
#                'fc7ot3_optical2' : ("M125", 69),
#            },
            'runNoise' : noiseMap,
#            E.g.
#            {
#                67 : {
#                    "SSA0": 4.348,
#                    "SSA4": 3.348,
#                    "MPA9": 2.348,
#                },
#                68 : {
#                    "SSA0": 3.348,
#                    "SSA1": 3.648,
#                },
#                69 : {
#                    "SSA0": 3.548,
#                    "SSA4": 3.248,
#                }
#            },
#            'runResults' : fakeRunResults, ##E.g pass/failed
            'runConfiguration' : xmlConfig,
            'runFile' : "https://cernbox.cern.ch/files/link/public/%s/%s"%(hash_value_read,newFile)
        }
        
        print("Output uploaded to %s"%newFile)
        print("CERN box link (folder): https://cernbox.cern.ch/files/link/public/%s/%s"%(hash_value_read,testID))
        print("CERN box link (zip file): https://cernbox.cern.ch/files/link/public/%s/%s"%(hash_value_read,newFile))
        
        test_runName = uploadRunToDB(newRun)
        
        print("moduleTest.py completed.")
        print("test_runName: %s."%test_runName)
        run = getRunFromDB(test_runName)
        from updateTestResult import updateTestResult
        print()
        print("RUN:")
        print(run)
        print()
        print("SINGLE MODULE TEST:")
        for moduleTestName in run['moduleTestName']:
            print("######## Single Module Test: %s ########################" %moduleTestName)
            if not args.skipUploadResults and moduleTestName[0]!="-": ## skip analysis if skipUploadResults or test failed (moduleName = -1)
                print("Running updateTestResult")
                print("++++++++++++++++++  Run updateTestResult on %s ++++++++++++++++++"%moduleTestName)
                updateTestResult(moduleTestName, tempSensor=args.tempSensor)
                #print("################################################")


