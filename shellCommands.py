import subprocess
from moduleTest import verbose, useExistingModuleTest

### Launch a command from shell

def runCommand(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, executable='/bin/bash'):
    if verbose>2: print(command)
    return subprocess.run(command, check=check, stdout=stdout, stderr=stderr, shell=shell)

#def loadBashRC(location = "/home/thermal/.bashrc"):
#    if verbose>0: print("Calling loadBashRC()")
#    output = runCommand(". %s"%location)
    
### Burn-in commands
    
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
    temps = output.stdout.decode().split("buffer: [")[1].split("]\n")[0]
    temps = [float(temp) for temp in temps.split(",")]
    if verbose>1: print(output)
    return temps

def burnIn_setTemperature(temperature):
    if verbose>0: print("Calling burnIn_setTemperature(%f)"%temperature)
    output = runCommand("/home/thermal/suvankar/power_supply//setTemperatureJulabo.sh .3%f"%temperature)
    if verbose>1: print(output)

### Launch FPGA config (to be used after FC7 reset)

def fpgaconfig(xmlFile, firmware):
    if verbose>0: print("Calling fpgaconfig()", xmlFile, firmware)
    output = runCommand("fpgaconfig -c %s -i %s"%(xmlFile, firmware))
    if verbose>1: print(output)

### Make testID from current date and time

from datetime import datetime
def getDateTimeAndTestID():
    date = str(datetime.now())
    testID = "T"+date.replace("-","_").replace(":","_").replace(" ","_").replace(".","_")
    return date, testID

### Launch ot_module_test, given an xml file.
# if useExistingModuleTest, skip the test and read the existing log file

def runModuleTest(xmlFile="PS_Module.xml", useExistingModuleTest=False, logFolder="logs"):
    if verbose>0: print("Calling runModuleTest()", xmlFile, logFolder)
    date, testID = getDateTimeAndTestID()
    if not useExistingModuleTest:
        logFile = "%s/%s.log"%(logFolder,testID)
    else:
        logFile = "%s/%s.log"%(logFolder,useExistingModuleTest)
    if verbose>0: print(testID,logFile)
    if not useExistingModuleTest:
        output = runCommand("ot_module_test -f %s -t -m -a --reconfigure -b --moduleId %s --readIDs | tee %s"%(xmlFile,testID,logFile)) #or --readlpGBTIDs ?
    else:
        output = runCommand("cat logs/2023_11_08_14_36_06_465927.log | tee %s"%(logFile)) #or --readlpGBTIDs ?
#    hwID = getID(output)
    if verbose>10: print(output)
    return testID, date #, hwID


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

