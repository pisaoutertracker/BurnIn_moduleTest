### Default values 
verbose = 1000
#sessionName = 'session1'
xmlConfigFile = "PS_Module_settings.py"
ip="192.168.0.45"
port=5005
xmlOutput="ModuleTest_settings.xml"
xmlTemplate="PS_Module_template.xml"
firmware_5G="ps_twomod_oct23.bin" ##5 GBps
firmware_10G="ps8m10gcic2l12octa.bin" ##10 GBps
runFpgaConfig = False ## it will run automatically if necessary
## command used to launch commands through Docker (podman)
podmanCommand = 'podman run  --rm -ti -v $PWD/Results:/home/cmsTkUser/Ph2_ACF/Results/ -v $PWD/logs:/home/cmsTkUser/Ph2_ACF/logs/ -v $PWD/..:$PWD/.. -v /etc/hosts:/etc/hosts -v ~/private/webdav.sct:/root/private/webdav.sct  -v /home/thermal/suvankar/power_supply/:/home/thermal/suvankar/power_supply/ --net host  --entrypoint sh  docker.io/sdonato/pisa_module_test:ph2_acf_v4-17 -c "%s"'
prefixCommand = 'source /home/cmsTkUser/Ph2_ACF/setup.sh && cd /home/thermal/Ph2_ACF_docker/BurnIn_moduleTest '

## assign these lpGBT hardware IDs to some random modules (they will be in the module database)
#lpGBTids = ['3962125297', '42949672', '42949673', '42949674', '2762808384', '0x00', '0x67']
lpGBTids = []

### webdav keys
hash_value_location = "~/private/webdav.sct" #echo "xxxxxxxxxxxxxxx|xxxxxxxxxxxxxxx" > ~/private/webdav.sct
webdav_url = "https://cernbox.cern.ch/remote.php/dav/public-files"
from webdavclient import WebDAVWrapper
import os
hash_value_read, hash_value_write = open(os.path.expanduser(hash_value_location)).read()[:-1].split("\n")[0].split("|")
webdav_wrapper = WebDAVWrapper(webdav_url, hash_value_read, hash_value_write)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Script used to launch the test of the Phase-2 PS module, using Ph2_ACF. More info at https://github.com/pisaoutertracker/BurnIn_moduleTest. \n Example: python3 moduleTest.py session1 . ')
    parser.add_argument('session_name', type=str, help='Name of the session')
    parser.add_argument('--useExistingModuleTest', type=str, nargs='?', const='', help='Read results from an existing module test. Skip ot_module_test run (for testing)!')
    parser.add_argument('--useExistingXmlFile', type=str, nargs='?', const='', help='Specify an existing xml file without generating a new one (for testing). ')
#    parser.add_argument('--verbose', type=int, nargs='?', const=10000, default=-1, help='Verbose settings.')
    parser.add_argument('--runFpgaConfig', type=bool, nargs='?', const=True, help='Force run runFpgaConfig.')
    parser.add_argument('--skipMongo', type=bool, nargs='?', const=True, help='Skip upload to mondoDB (for testing).')
    parser.add_argument('--firmware', type=str, nargs='?', const=True, default="ps_twomod_oct23.bin", help='Firmware used in fpgaconfig. Default=ps_twomod_oct23.bin')
    parser.add_argument('--xmlConfigFile', type=str, nargs='?', const="PS_Module_settings.py", default="PS_Module_settings.py", help='location of PS_Module_settings.py file with the XML configuration.')
    
    args = parser.parse_args()
#    verbose = args.verbose
    
    from pprint import pprint
    from tools import getROOTfile, getIDsFromROOT, getNoisePerChip, getResultsPerModule
    from shellCommands import fpgaconfig, runModuleTest, burnIn_readSensors
    from makeXml import makeXml, makeNoiseMap, readXmlConfig
    from databaseTools import uploadTestToDB, uploadRunToDB, getTestFromDB, addTestToModuleDB, getModuleFromDB, makeModuleNameMapFromDB, getRunFromDB
    
    ### read xml config file and create XML
    import shutil
    if args.useExistingXmlFile:
        xmlFile = args.useExistingXmlFile
        xmlOutput = xmlFile
        xmlConfigFile = xmlOutput
        xmlConfig = {"boards" : {} }
    else:
        xmlConfigFile = args.xmlConfigFile
        xmlConfig = readXmlConfig(xmlConfigFile)
        xmlFile = makeXml(xmlOutput, xmlConfig, xmlTemplate)
    
    ### launch fpga_config
    if args.runFpgaConfig: fpgaconfig(xmlFile, args.firmware)
    
    ### launch ot_module_test (if useExistingModuleTest is defined, read the existing test instead of launching a new one)
    print("args.useExistingModuleTest",args.useExistingModuleTest)
    out = runModuleTest(xmlFile, args.useExistingModuleTest) # 
    if out == "Run fpgaconfig":
        print("\n\nWARNING: You forgot to run fpgaconfig. I'm launching it now.\n")
        fpgaconfig(xmlFile, args.firmware)
        out = runModuleTest(xmlFile, args.useExistingModuleTest) # 
    testID, date = out
    
    ### read the output file (if args.useExistingModuleTest is defined, read the that ROOT file)
    rootFile = getROOTfile(testID) if not args.useExistingModuleTest else getROOTfile(args.useExistingModuleTest) 
    
    ### Read noise "NoiseDistribution_Chip" for each chip
    # noisePerChip is a map "D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)" --> noise
    noisePerChip = getNoisePerChip(rootFile , xmlConfig)
    if verbose>5: pprint(noisePerChip)
    
    ### Define an outcome result "pass" or "failed"
    result = getResultsPerModule(noisePerChip, xmlConfig)
    
    ### get the lpGBT hardware ID for each module from the ROOT file (CHIPID registers, CHIPID0)
    # Note: each module is identified by (board_id, opticalGroup_id)
    # IDs is a map: IDs[(board_id, opticalGroup_id)] --> hardware ID
    IDs = getIDsFromROOT(rootFile, xmlConfig)
    if verbose>5: pprint(IDs)
    
    if not args.skipMongo: 
        ### create a map between lpGBT hardware ID to ModuleName and to MongoID, reading the module database
        hwToModuleName, hwToMongoID = makeModuleNameMapFromDB()
        
        ### convert IDs of modules used in the test to ModuleID and to MongoID ()
        board_opticals = list(IDs.keys())
        moduleNames = [ hwToModuleName[IDs[bo]] for bo in board_opticals ]
        moduleMongoIDs = [ hwToMongoID[IDs[bo]] for bo in board_opticals ]
        
        ## upload all files
        for file in [xmlConfigFile, xmlOutput, rootFile.GetName(), "logs/%s.log"%testID]: #copy output files to CernBox
            newFile = webdav_wrapper.write_file(file, "/%s/%s"%(testID, file))
            if verbose>1: print("Uploaded %s"%newFile)
        
        ## copy some important files (xml, log, py) in .../Results folder
        resultFolder = rootFile.GetName()[:rootFile.GetName().rfind("/")]
        for file in [xmlConfigFile, xmlOutput, "logs/%s.log"%testID]: #copy output files to CernBox
            if file != rootFile.GetName():
                shutil.copy(file, resultFolder)
        
        ## make a zip file and upload it
        zipFile = "output"
        if verbose>20: print("shutil.make_archive(zipFile, 'zip', resultFolder)", zipFile, resultFolder)
        shutil.make_archive(zipFile, 'zip', resultFolder)
        if verbose>20: print("Done")
        newFile = webdav_wrapper.write_file(zipFile+".zip", "/%s/output.zip"%(testID))
        if verbose>0: print("Uploaded %s"%newFile)
        
        boardMap, moduleMap, noiseMap = makeNoiseMap(xmlConfig, noisePerChip, IDs, hwToModuleName)
        fakeRunResults = dict()
        for hwId in noiseMap:
            fakeRunResults[hwId] = "boh"
        newRun = {
            'runDate': date.replace(" ","T").split(".")[0], # drop ms
            'runSession': args.session_name,
            'runStatus': 'done',
            'runType': 'Type1',
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
        print()
        print("RUN:")
        print(run)
        print()
        print("SINGLE MODULE TEST:")
        for moduleTestName in run['moduleTestName']:
            print("Single Module Test: %s" %moduleTestName)

