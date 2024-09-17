import subprocess
from moduleTest import verbose, podmanCommand, prefixCommand, lastPh2ACFversion

### Launch a command from shell

def runCommand(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, executable='/bin/bash'):
    if verbose>2: print(command)
    return subprocess.run(command, check=check, stdout=stdout, stderr=stderr, shell=shell)

#def loadBashRC(location = "/home/thermal/.bashrc"):
#    if verbose>0: print("Calling loadBashRC()")
#    output = runCommand(". %s"%location)
    
### Burn-in commands

def updateSettingsLink(settingFolder):
    if verbose>0: print("Calling updateSettingsLink()")
    print(updateSettingsLink)
    output = runCommand("rm settings ; ln -s %s ."%settingFolder)
    if verbose>1: print(output)

def burnIn_lockOn():
    if verbose>0: print("Calling burnIn_lockOn()")
    output = runCommand("/home/thermal/suvankar/power_supply//simbxcntrl lock-on")
    if verbose>1: print(output)

def burnIn_switchOn():
    if verbose>0: print("Calling burnIn_switchOn()")
    output = runCommand("echo -ne '\''out_mode_05 1\nin_sp_00\nexit\n'\'' | /home/thermal/suvankar/power_supply//runjulabo")
    if verbose>1: print(output)

def burnIn_valveOn():
    if verbose>0: print("Calling burnIn_valveOn()")
    output = runCommand("/home/thermal/suvankar/power_supply//simbxcntrl valve-on")
    if verbose>1: print(output)

def burnIn_readSensors():
    if verbose>0: print("Calling burnIn_readSensors()")
    output = runCommand("/home/thermal/suvankar/power_supply//simbxcntrl read-sensors")
    temps = output.stdout.decode().split("buffer: [")[1].split("]")[0]
    temps = [float(temp) for temp in temps.split(",")]
    if verbose>1: print(output)
    return temps

def burnIn_setTemperature(temperature):
    if verbose>0: print("Calling burnIn_setTemperature(%f)"%temperature)
    output = runCommand("/home/thermal/suvankar/power_supply//setTemperatureJulabo.sh .3%f"%temperature)
    if verbose>1: print(output)

### Copy settings/PS_Module_v2p1.xml locally (note: settings is in Docker, unless --localPh2ACF is used)

def copyXml(ph2ACFversion=lastPh2ACFversion):
    if verbose>0: print("Calling copyXml()")
    if ph2ACFversion=="local":
        print("Copying settings/PS_Module_v2p1.xml locally.")
        command = "cp settings/PS_Module_v2p1.xml ."
        output = runCommand(command)
    else:
        print("Copying settings/PS_Module_v2p1.xml (from Docker) locally.")
        command = "%s && cp settings/PS_Module_v2p1.xml ."%(prefixCommand)
        print(podmanCommand)
        output = runCommand(podmanCommand%(ph2ACFversion,command))
    error = output.stderr.decode()
    if error:
        print()
        print("|"+error+"|")
        raise Exception("Generic Error running copyXml. Check the error above. Command: %s"%output.args)
    if verbose>1: print(output)

### Launch FPGA config (to be used after FC7 reset)

def fpgaconfig(xmlFile, firmware, ph2ACFversion=lastPh2ACFversion):
    if verbose>0: print("Calling fpgaconfig()", xmlFile, firmware)
    if ph2ACFversion=="local":
        command = "fpgaconfig -c %s -i %s"%(xmlFile, firmware)
        output = runCommand(command)
    else:
        command = "%s && fpgaconfig -c %s -i %s"%(prefixCommand, xmlFile, firmware)
        output = runCommand(podmanCommand%(ph2ACFversion,command))
    error = output.stderr.decode()
    if error:
        print()
        print("|"+error+"|")
        raise Exception("Generic Error running fpgaconfig. Check the error above. Command: %s"%output.args)
    if verbose>1: print(output)

### Make testID from current date and time

from datetime import datetime
def getDateTimeAndTestID():
    date = str(datetime.now())
    testID = "T"+date.replace("-","_").replace(":","_").replace(" ","_").replace(".","_")
    return date, testID

### Launch ot_module_test, given an xml file.
# if useExistingModuleTest, skip the test and read the existing log file

def runModuleTest(xmlFile="PS_Module.xml", useExistingModuleTest=False, ph2ACFversion=lastPh2ACFversion, logFolder="logs", minimal=False):
    global error 
    if verbose>0: print("Calling runModuleTest()", xmlFile, logFolder)
    date, testID = getDateTimeAndTestID()
    logFile = "%s/%s.log"%(logFolder,testID)
    if verbose>0: print(testID,logFile)
    if not useExistingModuleTest: # -w $PWD 
        if not minimal:
            step = "calibrationandpedenoise"
        else:
            step = "configureonly"
        if ph2ACFversion=="local":
            command = "runCalibration -b -f %s -c %s  | tee %s"%(xmlFile, step, logFile)
            output = runCommand(command)
        else:
            command = "%s && runCalibration -b -f %s -c %s  | tee %s"%(prefixCommand, xmlFile, step, logFile)
            output = runCommand(podmanCommand%(ph2ACFversion,command))
#        command = "%s && ot_module_test -f %s -t -m -a --reconfigure -b --moduleId %s --readIDs | tee %s"%(prefixCommand, xmlFile,testID,logFile)
    else:
        output = runCommand("cat logs/%s.log | tee %s"%(useExistingModuleTest, logFile))
    if verbose>10: print(output)
    error = output.stdout.decode() ## if you are not launching command through podman/Docker you should use "stderr" instead.
    ## Remove known warning
    error = error.replace("Warning in <EnableImplicitMT>: Cannot enable implicit multi-threading with 0 threads, please build ROOT with -Dimt=ON\n", "")
    ## Raise an exception, with an explanation, if something went wrong
    if "ControlHub returned error code 3" in error:
        print()
        print(error)
        raise Exception("ControlHub returned error code 3.  \n Please check that: 1) your FC7 is on, 2) FC7 is connected to the Ethernet (check LEDs in the router), 3) you are using the correct port (eg. 50001).  \n Command: %s"%output.args)
    if "Host not found (authoritative)" in error:
        print()
        print(error)
        raise Exception("Host not found.  \n Please check that all hosts used (eg. fc7ot3) are defined in /etc/hosts.  \n Command: %s"%output.args)
    if "ExceptionHandler Error: No object enabled in fDetectorContainer" in error:
        print()
        print(error)
        if "lpGBT TX Ready\x1b[1m\x1b[31m\t : FAILED" in output.stdout.decode():
            print("ExceptionHandler Error: No object enabled in fDetectorContainer.  \n Please check that you have installed the firmware (fpgaconfig). Command: %s"%output.args)
            return "Run fpgaconfig"
        else:
            raise Exception("ExceptionHandler Error: No object enabled in fDetectorContainer.  \n All modules seem off. Please check that the low voltages are turned on. Check that some light is coming out from the optical fibers that you selected.  \n It might be due to a wrong version of the firmware installed in the FC7. \n Command: %s"%output.args)
#    if "ExceptionHandler Error: No object enabled in fDetectorContainer" in error:
#        print()
#        print(error)
#        raise Exception("ExceptionHandler Error: No object enabled in fDetectorContainer. All modules seem off. Please check that the low voltages are turned on. Check that some light is coming out from the 
    if error and not "Closing result file:" in error:
        print()
        print("|"+error+"|")
        raise Exception("Generic Error running ot_module_test. Check the error above. Command: %s"%output.args)
    
    ## find ROOT file from log file:
    if "Closing result file: " in error:
        rootFile = error.split("Closing result file: ")[1].split(".root")[0]+".root" ##eg. Results/Run_28/Results.root
        newTestID = rootFile.split("/")[1] ## get "Run_28"
        import os
        os.rename(logFile, logFile.replace(testID, newTestID))
        
    elif useExistingModuleTest:
        newTestID = testID
    return newTestID, date


### This code allow you to test this code using "python3 shellCommands.py"

if __name__ == '__main__':
#    verbose = -1
    xmlFile = "ModuleTest_settings.xml"
    firmware="ps_twomod_oct23.bin"
    useExistingModuleTest=False
    
    temps = burnIn_readSensors()
    print("\ntemps:")
    print(temps)
    
    date, testID = getDateTimeAndTestID()
    print("\ntestID-1:")
    print(date, testID)
    print()
    
#    fpgaconfig(xmlFile, firmware)
    print()
    testID, date = runModuleTest(xmlFile, useExistingModuleTest)
    print("\ntestID-2:")
    print(date, testID)

