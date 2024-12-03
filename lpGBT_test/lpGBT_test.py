import os
from datetime import datetime
import subprocess


verbose = False
podmanCommand = 'podman run --rm -ti -v $PWD/Results:/home/cmsTkUser/Ph2_ACF/Results/:z -v $PWD/logs:/home/cmsTkUser/Ph2_ACF/logs/:z -v $PWD:$PWD:z -v /etc/hosts:/etc/hosts -v ~/private/webdav.sct:/root/private/webdav.sct:z --net host --entrypoint bash gitlab-registry.cern.ch/cms-pisa/pisatracker/pisa_module_test:%s -c "%s"'
ph2ACFversion = "ph2_acf_v6-00"
prefixCommand = 'cd /home/cmsTkUser/Ph2_ACF && source setup.sh && cd %s' % os.getcwd()

def runCommand(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, executable='/bin/bash'):
    if verbose>2: print(command)
    try:
        return subprocess.run(command, check=check, stdout=stdout, stderr=stderr, shell=shell)
    except subprocess.CalledProcessError as e:
        raise Exception("{}".format(e.output.decode('utf-8')))

def runModuleTest(testID, xmlFile="PS_Module.xml", useExistingModuleTest=False, ph2ACFversion="ph2_acf_v6-00", commandOption="readOnlyID", logFolder="logs"):
    testID = str(testID)
    logFile = "%s/%s.log" % (logFolder, testID)
    commandOption = "configureonly" if commandOption == "readOnlyID" else commandOption
    command = "%s && runCalibration -b -f %s -c %s | tee %s" % (prefixCommand, xmlFile, commandOption, logFile)
    output = runCommand(podmanCommand % (ph2ACFversion, command))
    error = str(output.stdout)
    # if verbose: print(error)

    if "ControlHub returned error code 3" in error:
        print("ControlHub returned error code 3. Please check your FC7 and network connection.")

    if "what():  Error: calibration tag " in error and "does not exist" in error:
        print("Invalid calibration tag. Use -c help for more info.")

    if "Host not found (authoritative)" in error:
        print("Host not found. Check /etc/hosts.")

    if "ExceptionHandler Error: No object enabled in fDetectorContainer" in error:
        if "lpGBT TX Ready\x1b[1m\x1b[31m\t : FAILED" in error:
            raise Exception("Run fpgaconfig")
        else:
            print("No object enabled in fDetectorContainer. Check low voltages and firmware.")

    if "Closing result file: " in error:
        rootFile = error.split("Closing result file: ")[1].split(".root")[0] + ".root"
        newTestID = rootFile.split("/")[1]
        os.rename(logFile, logFile.replace(testID, newTestID))
        return newTestID
    else:
        newTestID = testID
        print("Some error occurred. Check the log file: %s" % logFile)
        return "Failed"

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from time import sleep
from time import time

parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("-f", "--xml", dest="xmlFile", required=True, 
                    help="xml file (eg. ModuleTest_settings.xml)")
parser.add_argument("-c", "--channel", dest="channel", required=True,
                    help="channel number for LV Caen control. e.g. BLV02")

print("Example:    python3 -u lpGBT_test.py -f ModuleTest_settings_OG01.xml -c BLV01,BLV02 > log_11.txt ")

args = parser.parse_args()

channels = args.channel.split(",") if "," in args.channel else [args.channel]

from CAEN_controller import caen

#caen_controller = caen()
restartCaen = True
for testID in range(1000000):
    timestamp = str(datetime.fromtimestamp(datetime.now().timestamp())).replace("-","_").replace(" ","_").replace(".","_").replace(":","_")
    if restartCaen:
        caen_controller = caen()
        restartCaen = False
    try:
        for ch in channels: caen_controller.on(ch, verbose)
    except Exception as e:
        print("Test %d (%s). Problems with LV Caen switch on. Check the connection."%(testID,timestamp))
        print("Error: %s" % str(e))
        restartCaen = True
        del caen_controller
        sleep(1)
        continue
    sleep(1)
    ## timer start
    start = time()
    out = runModuleTest(timestamp, args.xmlFile)
    deltaTime = time() - start
    if out == "Failed":
        print("Test %d FAILED (%.1f s) !!!!!!!!!!!!!!!!!!!!!! " % (testID, deltaTime) )
    else:
        print("Test %d (%s) passed (%.1f s)" % (testID, out, deltaTime) )
        try:
            for ch in channels: caen_controller.off(ch, verbose)
            sleep(10)
        except Exception as e:
            print("Test %d (%s). Problems with LV Caen switch off. Check the connection."%(testID,timestamp))
            print("Error: %s" % str(e))
            restartCaen = True
            del caen_controller


for ch in channels: caen_controller.off(ch, verbose)




