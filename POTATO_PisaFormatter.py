import os
import yaml
import json
import shutil
import datetime
import ROOT
import uproot
import numpy as np
import pandas as pd
import math
from ROOT import TObjString, gROOT
from updateTestResult import getTimeFromRomeToUTC

## This code requires https://gitlab.cern.ch/otsdaq/potatoconverters/-/tree/master
try:
    from potatoconverters.Histogrammer import Histogrammer, TIME_FORMAT
except ImportError:
    raise ImportError("potatoconvertes.Histogrammer cannot be loaded. Please install potatoconvertes from https://gitlab.cern.ch/otsdaq/potatoconverters/-/tree/master or add it to your PYTHONPATH.")

from potatoconverters.BurninMappings import opticalGroupToBurninSlot
from datetime import datetime, timedelta

extraTime = 3 # minutes (time)

temperatureSensor = "Temp0" ###FIXME: devo prenderlo da MonitorDQM??
ambientTemperatureSensor = "/fnalbox/full/AirTemp"
moduleCarrierTemperatureSensor = "/fnalbox/full/OW%s"
dewPointSensor = "/fnalbox/full/DewPoint" 
chillerSetPointName = "/julabo/full/Temp_SP1" ##can we please get rid of the 3 setpoint stuff in the BurnIN GUI ? we do not need it

#ambientHumiditySensor = "/fnalbox/full/Humidity"
#


verbose = 1000
# Define the path to the main directory
#main_directory = "./data"
#output_directory = "./potato"
# output_directory = "../potato/POTATO_data/LocalFiles/TestOutput"

def getConnectionMap(rootTrackerFileName):
    import glob
    print(rootTrackerFileName)
    path = "/".join(rootTrackerFileName.split("/")[:-1])+"/connectionMap_*.json"
    connectionMapFileNames = glob.glob(path)
    if len(connectionMapFileNames) == 1:
        with open(connectionMapFileNames[0]) as json_file:
            print("ConnectionMap file: ", connectionMapFileNames[0])
            txt = str(json_file.read())
            if verbose>1000: print("ConnectionMap: ", txt)
            connectionMap = eval(txt)
    elif len(connectionMapFileNames) > 1:
        print()
        print("###########################################################")
        print("WARNING: multiple connectionMap found in ", path)
        print("###########################################################")
        print()
        connectionMap = {}
    elif len(connectionMapFileNames) == 0:
        print()
        print("###########################################################")
        print("WARNING: connectionMap not found in ", path)
        print("###########################################################")
        print()
        connectionMap = {}
    return connectionMap

def getHVLVchannels(connectionMap):
    hv_channel = -1
    lv_channel = -1
    ## check if the last connection of each cable is either ASLOT or LV
    for con in connectionMap.values():
        lastConn = con['connections'][-1]
        ### see https://github.com/pisaoutertracker/integration_tools/blob/625aaca54ddd45893fe118b1f0e6d7ce7f69facc/ui/main.py#L1600-L1603
        if "ASLOT" in lastConn['cable']:
            hv_channel = "HV"+lastConn['cable'][5:]+f".{lastConn['line']}"
        elif "XSLOT" in lastConn['cable']:
            lv_channel = "LV"+lastConn['cable'][5:]+f".{lastConn['line']}"
    if hv_channel == -1 or lv_channel == -1:
        print("HV/LV found: ", hv_channel, lv_channel)
        #raise Exception("No HV or LV found in connectionMap")
    if verbose>0:
        print("HV/LV found: ", hv_channel, lv_channel)
    return hv_channel, lv_channel
    #            connectionMap = json.load(json_file)

class POTATOPisaFormatter():
    def __init__ ( self, pDirectory ):
        self.main_directory = pDirectory
        self.output_directory = pDirectory
        self.verbose = 1000
        self.influxQuery = self.getInfluxQueryAPI()
        self.extraTime = extraTime # minutes (time)
        gROOT.SetBatch(True)
    
    def getGraphValuesByTimestamp(self, graph, timestamps):
        #print('Graph name: ', graph.GetName())
        values = []
        for timestamp in timestamps:
            #print(timestamp, graph.Eval(timestamp))
            values.append(graph.Eval(timestamp))
        return values

    def getInfluxQueryAPI(self, token_location = "~/private/influx.sct"):
        token = open(os.path.expanduser(token_location)).read().strip()
        from influxdb_client import InfluxDBClient
        client = InfluxDBClient(url="http://cmslabserver:8086/", token=token)
        return client.query_api()

    def getTemperatureAt(self, timestamp, sensorName="Temp0", org="pisaoutertracker"):
        # Define a small window around the timestamp (±30 seconds)
        if self.verbose>2: print('Calling getTemperatureAt(timestamp=%s, sensorName=%s, org=%s)'%(timestamp, sensorName, org))
        window = timedelta(seconds=30)
        timestamp = datetime.fromisoformat(timestamp)
        start_window = (timestamp - window).isoformat("T") + "Z"
        end_window = (timestamp + window).isoformat("T") + "Z"
        query = f'''
        from(bucket: "sensor_data")
            |> range(start: {start_window}, stop: {end_window})
            |> filter(fn: (r) => r["_measurement"] == "mqtt_consumer")
            |> filter(fn: (r) => r["_field"] == "{sensorName}")
            |> aggregateWindow(every: 1s, fn: mean, createEmpty: false)
            |> yield(name: "mean")
        '''
        tables = self.influxQuery.query(query, org=org)
        # Gather the temperature values found within the time window.
        temps = [record.get_value() for table in tables for record in table.records]
        if temps:
            # Average values if more than one record is returned.
            return sum(temps) / len(temps)
        else:
            print('WARNING: Something wrong calling getTemperatureAt(timestamp=%s, sensorName=%s, org=%s)'%(timestamp, sensorName, org))
            return -999

    def getGraphFromInfluxDB(self, sensorName, start_time_TS, stop_time_TS, org="pisaoutertracker"):
        start_time = (datetime.fromisoformat(start_time_TS)+timedelta(minutes=-self.extraTime)).isoformat("T") + "Z"
        stop_time = (datetime.fromisoformat(stop_time_TS)+timedelta(minutes=self.extraTime)).isoformat("T") + "Z"
        topicLine = ""
        if "/" in sensorName:
            topic, sensorName = sensorName.rsplit("/",1)
            topicLine = f'\n                |> filter(fn: (r) => r["topic"] == "{topic}")'
        query = f'''
                from(bucket: "sensor_data")
                |> range(start: {start_time}, stop: {stop_time})
                |> filter(fn: (r) => r["_measurement"] == "mqtt_consumer")
                |> filter(fn: (r) => r["_field"] == "{sensorName}" ){topicLine} 
                |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
                |> yield(name: "mean")
                '''
                
        times = []
        values = []

        if verbose>3: print(query)
        tables = self.influxQuery.query(query, org=org)
        
        for table in tables:
            if verbose>3: print(table)
            for record in table.records:
                times.append(record.get_time().timestamp())
                values.append(record.get_value())
        import array as arr
        if len(times) == 0 or len(values) == 0:
            print(query)
            from updateTestResult import printAllSensors
            print("########################################")
            print("No data found for sensor: ", sensorName)
            print("########################################")
            print("List of all sensors:")
            printAllSensors()
            print("########################################")
        graph = ROOT.TGraph(len(times), arr.array('f',times), arr.array('f',values))
        graph.SetName(sensorName)
        print("Graph name: ", graph.GetName(), " N: ", graph.GetN(), " Start: ", start_time, " Stop: ", stop_time)
        return graph
    '''
    def makeFileList(self):
        # Walk through the directory structure       
        for root, dirs, files in os.walk(self.main_directory):
            if 'Results.root' in files:
                print("Files")
                print(root)
                #print(dirs)
                #print(files)
                print("Done")
                root_file = os.path.join(root, 'Results.root')
                print(root_file)
                monitor_files              = [os.path.join(root, f) for f in files if f.startswith("Monitor") and f.endswith(".yml")]
                monitor_summary_files      = [os.path.join(root, f) for f in files if f.startswith("summary_AnalyseMonitorData") and f.endswith(".yml")]
                monitor_file               = monitor_files[0] if monitor_files else None
                monitor_file_exits         = os.path.exists(monitor_file) if monitor_file is not None else False
                monitor_summary_file       = monitor_summary_files[0] if monitor_files else None
                monitor_summary_file_exist = os.path.exists(monitor_summary_file) if monitor_summary_file is not None else False
                iv_files                   = [os.path.join(root, f) for f in files if f.startswith("IV_") and f.endswith(".yml")]
                iv_file                    = iv_files[0] if iv_files else None
                iv_file_exist              = os.path.exists(iv_file) if iv_file is not None else False
                i += 1

    def extractMonitorInfos(self, graph, start=None, stop=None):
        timestamps = []
        values     = []
        x = graph.GetX()
        y = graph.GetY()
        #print(graph.GetName(), graph.GetN(), start, stop)
        for n in range(graph.GetN()):
            #print(x[n])            
            if (start == None or x[n] >= start) and (stop == None or x[n] <= stop):
                timestamps.append(x[n])
                values.append(y[n])
                #print(x[n], y[n])
        if len(timestamps) == 0:
            raise Exception('Graph ' + graph.GetName() + ' had no entries between the start and stop test times!')
        return timestamps, values

    '''
    def calculateHumidity(self, dewPointGraph, temperatureGraph, start=None, stop=None):
        timestamps = []
        values     = []
        if(dewPointGraph.GetN() != temperatureGraph.GetN()):
            raise RuntimeError(f"DewPoint and Temperature Graphs have different number of points!")
        
        xDewPoint    = dewPointGraph.GetX()
        yDewPoint    = dewPointGraph.GetY()
        #xTemperature = temperatureGraph.GetX()
        yTemperature = temperatureGraph.GetY()
        for n in range(dewPointGraph.GetN()):            
            if (start == None or xDewPoint[n] >= start) and (stop == None or xDewPoint[n] <= stop):
                timestamps.append(xDewPoint[n])
                numerator   = math.exp((17.625 * yDewPoint[n]) / (243.04 + yDewPoint[n]))
                denominator = math.exp((17.625 * yTemperature[n]) / (243.04 + yTemperature[n]))
                RH = 100 * (numerator / denominator)
                values.append(RH)
        return timestamps, values
    '''

    def getCurrentVoltageGraphs(self, canvas):
        currentGraph = None
        voltageGraph = None
        for pad in canvas.GetListOfPrimitives():
            if pad.InheritsFrom("TPad"):
                #print(pad.GetName())
                for obj in pad.GetListOfPrimitives():
                    #print(obj.GetName())
                    if obj.InheritsFrom("TGraph"):
                        if obj.GetName().find("Current") > 0:
                            currentGraph = obj
                        elif obj.GetName().find("Voltage") > 0:
                            voltageGraph = obj
        return currentGraph, voltageGraph
    
    def getGraphFromCanvas(self, canvas):
        #print(canvas.GetName())
        for primitive in canvas.GetListOfPrimitives():
            if primitive.InheritsFrom("TGraph"):
                return primitive
        raise RuntimeError(f"Can't find TGraph in canvas: {canvas.GetName()}")              
        '''

    def getCurrentAfterPowerOff(self, graph):
        values = np.array(graph.GetY())
        powerOff = False
        numberOfMeasurements = 4
        begin = end = 0

        for n in range(graph.GetN()):
            #print("Val: ", values[n], " PowerOff: ", powerOff, " NMeas: ", numberOfMeasurements, " Begin: ", begin)
            if values[n] < 0.05:
                powerOff = True
            if powerOff and values[n] > 0.05:
                begin = n
                break
        end = begin + numberOfMeasurements
        if begin+numberOfMeasurements >= values.size:
            end = values.size
        #print("Begin: ", begin, " End: ", end, "Size: ", values.size)
        return np.mean(values[begin:end])

    def do_burnin_format(self, rootTrackerFileName, runNumber, opticalGroupNumber, moduleBurninName, moduleCarrierName):
        print("Calling do_burnin_format with: rootTrackerFileName: ", rootTrackerFileName, " runNumber: ", runNumber, " opticalGroupNumber: ", opticalGroupNumber, " moduleBurninName: ", moduleBurninName, " moduleCarrierName: ", moduleCarrierName)
        theHistogrammer = Histogrammer()
        print("Opening ROOT file: ", rootTrackerFileName)
        theHistogrammer.openRootFile(rootTrackerFileName)

#        rootTrackerMonitorFileName = os.environ['TRACKER_FILES'] + "/TrackerMonitorHistos_" + runNumber + ".root"
#        trackerMonitorFile = ROOT.TFile.Open(rootTrackerMonitorFileName)
#        if not trackerMonitorFile or trackerMonitorFile.IsZombie():
#            raise IOError(f"Could not open the ROOT file: {trackerMonitorFile}")
        
#        rootPowerSupplyFileName = os.environ['BURNIN_FILES'] + "/PowerSuppliesHistos_" + runNumber + ".root"
#        powerSupplyFile = ROOT.TFile.Open(rootPowerSupplyFileName)
#        if not powerSupplyFile or powerSupplyFile.IsZombie():
#            raise IOError(f"Could not open the ROOT file: {powerSupplyFile}")
        
#        rootBurninFileName = os.environ['BURNIN_FILES'] + "/BurninBoxHistos_" + runNumber + ".root"
#        burninFile = ROOT.TFile.Open(rootBurninFileName)
#        if not burninFile or burninFile.IsZombie():
#            raise IOError(f"Could not open the ROOT file: {burninFile}")
        
        detectorTrackerDirectory        = theHistogrammer.outputRootFile.Get("Detector")
        detectorTrackerMonitorDirectory = theHistogrammer.outputRootFile.Get("MonitorDQM")
        if detectorTrackerDirectory == None:
            raise RuntimeError(f"Detector directory not found in file: {rootTrackerFileName}")
        if detectorTrackerMonitorDirectory == None:
            raise RuntimeError(f"MonitorDQM directory not found in file: {rootTrackerFileName}")
#        print(theHistogrammer.Print())
        print(detectorTrackerDirectory.Print())
        print(detectorTrackerMonitorDirectory.Print())
        moduleName = str(detectorTrackerDirectory.Get("Board_0/OpticalGroup_" + opticalGroupNumber + "/D_B(0)_NameId_OpticalGroup(" + opticalGroupNumber + ")"))
        print("Formatting file for module: " + moduleName)


        timeStamp_start = detectorTrackerDirectory.Get("CalibrationStartTimestamp_Detector").GetName()
        timeStamp_stop  = detectorTrackerDirectory.Get("CalibrationStopTimestamp_Detector").GetName()
        
        startTime_rome, startTime_utc = getTimeFromRomeToUTC(timeStamp_start, timeFormat = "%Y-%m-%d %H:%M:%S")
        stopTime_rome, stopTime_utc = getTimeFromRomeToUTC(timeStamp_stop, timeFormat = "%Y-%m-%d %H:%M:%S")

        ### For influxDB:
        timeStamp_start_utc = startTime_utc.isoformat("T").split("+")[0] 
        timeStamp_stop_utc = stopTime_utc.isoformat("T").split("+")[0] 


        testTimeStart = datetime.strptime(timeStamp_start, TIME_FORMAT).timestamp()
        testTimeStop  = datetime.strptime(timeStamp_stop, TIME_FORMAT).timestamp()

#        powerSupplyStatusDirectory = powerSupplyFile.Get("PowerSupply/Status") ## To be fixed
#        burninStatusDirectory      = burninFile.Get("BurninBox/Status")
#        moduleLVCanvas = powerSupplyStatusDirectory.Get(moduleBurninName + "_LV")
#        [moduleLVCurrentGraph, moduleLVVoltageGraph] = self.getCurrentVoltageGraphs(moduleLVCanvas)



#     plots = []
#     startTime_local = str(rootFile.Get("Detector/CalibrationStartTimestamp_Detector")).replace(" ","T")
#     stopTime_local = str(rootFile.Get("Detector/CalibrationStopTimestamp_Detector")).replace(" ","T")
#     ## add Influxdb plot
    
#     if not skipInfluxDb: 
#         plots.append(  makePlotInfluxdb(startTime_local, stopTime_local, tempSensor, tmpFolder) )
#         hv_current = "caen_%s_Current"%(hv_channel) ## eg. caen_HV001_Current
#         hv_voltage = "caen_%s_Voltage"%(hv_channel) ## eg. caen_HV001_Voltage
#         lv_current = "caen_%s_Current"%(lv_channel) ## eg. caen_BLV01_Current
#         lv_voltage = "caen_%s_Voltage"%(lv_channel) ## eg. caen_BLV01_Voltage

# #        "caen_BLV{:0>2}_Voltage".format(lv_channel),"caen_BLV{:0>2}_Current".format(lv_channel),"caen_HV{:0>3}_Voltage".format(hv_channel),"caen_HV{:0>3}_Current".format(hv_channel)]
#         plots.append(  makePlotInfluxdbVoltageAndCurrent(startTime_local, stopTime_local, tmpFolder, sensors=[hv_current, hv_voltage, lv_current, lv_voltage]) )
        

        connectionMap = getConnectionMap(rootTrackerFileName)
        hv_channel, lv_channel = getHVLVchannels(connectionMap)
        moduleLVVoltageGraph = self.getGraphFromInfluxDB(f"caen_{lv_channel}_Voltage", start_time_TS=timeStamp_start_utc, stop_time_TS=timeStamp_stop_utc)
        moduleLVCurrentGraph = self.getGraphFromInfluxDB(f"caen_{lv_channel}_Current", start_time_TS=timeStamp_start_utc, stop_time_TS=timeStamp_stop_utc)
        moduleHVVoltageGraph = self.getGraphFromInfluxDB(f"caen_{hv_channel}_Voltage", start_time_TS=timeStamp_start_utc, stop_time_TS=timeStamp_stop_utc)
        moduleHVCurrentGraph = self.getGraphFromInfluxDB(f"caen_{hv_channel}_Current", start_time_TS=timeStamp_start_utc, stop_time_TS=timeStamp_stop_utc)

        ## No extra time as we want the temperature spot, not in a range
        temp = self.getTemperatureAt(timeStamp_start_utc, sensorName=temperatureSensor, org="pisaoutertracker")
        print("Temperature at start of test: ", temp)
        sensorTemperatureGraph         = self.getGraphFromInfluxDB(temperatureSensor, start_time_TS=timeStamp_start_utc, stop_time_TS=timeStamp_stop_utc)
        ambientTemperatureGraph        = self.getGraphFromInfluxDB(ambientTemperatureSensor, start_time_TS=timeStamp_start_utc, stop_time_TS=timeStamp_stop_utc)
        moduleCarrierTemperatureGraph  = self.getGraphFromInfluxDB(moduleCarrierTemperatureSensor, start_time_TS=timeStamp_start_utc, stop_time_TS=timeStamp_stop_utc)
        dewPointGraph                  = self.getGraphFromInfluxDB(dewPointSensor, start_time_TS=timeStamp_start_utc, stop_time_TS=timeStamp_stop_utc)
        chillerSetPointGraph           = self.getGraphFromInfluxDB(chillerSetPointName, start_time_TS=timeStamp_start_utc, stop_time_TS=timeStamp_stop_utc)

        lvCurrentHistoryGraph = theHistogrammer.makeMonitorLVCurrent  (moduleLVCurrentGraph.GetX(), moduleLVCurrentGraph.GetY(), module=moduleName)
        lvCurrentGraph        = theHistogrammer.makeMonitorLVCurrent  (moduleLVCurrentGraph.GetX(), moduleLVCurrentGraph.GetY(), testTimeStart, testTimeStop, module=moduleName)

        theHistogrammer.makeMonitorLVVoltage  (moduleLVVoltageGraph.GetX(), moduleLVVoltageGraph.GetY(), module=moduleName)
        theHistogrammer.makeMonitorLVVoltage  (moduleLVVoltageGraph.GetX(), moduleLVVoltageGraph.GetY(), testTimeStart, testTimeStop, module=moduleName)

        #theHistogrammer.makeMonitorLVOn       (moduleLVOnGraph.GetX(), moduleLVOnGraph.GetY(), testTimeStart, testTimeStop))

        hvCurrentHistoryGraph = theHistogrammer.makeMonitorHVCurrent  (moduleHVCurrentGraph.GetX(), moduleHVCurrentGraph.GetY(), module=moduleName)
        hvCurrentGraph        = theHistogrammer.makeMonitorHVCurrent  (moduleHVCurrentGraph.GetX(), moduleHVCurrentGraph.GetY(), testTimeStart, testTimeStop, module=moduleName)

        theHistogrammer.makeMonitorHVVoltage  (moduleHVVoltageGraph.GetX(), moduleHVVoltageGraph.GetY(), module=moduleName)
        theHistogrammer.makeMonitorHVVoltage  (moduleHVVoltageGraph.GetX(), moduleHVVoltageGraph.GetY(), testTimeStart, testTimeStop, module=moduleName)

        #theHistogrammer.makeMonitorHVOn       (moduleHVOnGraph.GetX(), moduleHVOnGraph.GetY(), testTimeStart, testTimeStop))

        #print(*ambientTemperatureGraph.GetX(), *ambientTemperatureGraph.GetY())
        #exit()
        temperatureHistoryGraph = theHistogrammer.makeMonitorTemperature(ambientTemperatureGraph.GetX(), ambientTemperatureGraph.GetY(), module=moduleName)
        temperatureGraph        = theHistogrammer.makeMonitorTemperature(ambientTemperatureGraph.GetX(), ambientTemperatureGraph.GetY(), testTimeStart, testTimeStop, module=moduleName)

        humidityHistoryGraph = theHistogrammer.makeMonitorHumidity   (*self.calculateHumidity(dewPointGraph, ambientTemperatureGraph), module=moduleName)
        humidityGraph        = theHistogrammer.makeMonitorHumidity(humidityHistoryGraph.GetX(), humidityHistoryGraph.GetY(), testTimeStart, testTimeStop, module=moduleName)

        theHistogrammer.makeMonitorDewPoint   (dewPointGraph.GetX(), dewPointGraph.GetY(), module=moduleName)
        theHistogrammer.makeMonitorDewPoint   (dewPointGraph.GetX(), dewPointGraph.GetY(), testTimeStart, testTimeStop, module=moduleName)

        theHistogrammer.makeCarrierTemperature(moduleCarrierTemperatureGraph.GetX(), moduleCarrierTemperatureGraph.GetY(), module=moduleName)
        theHistogrammer.makeCarrierTemperature(moduleCarrierTemperatureGraph.GetX(), moduleCarrierTemperatureGraph.GetY(), testTimeStart, testTimeStop, module=moduleName)

        theHistogrammer.makeChillerSetPointTemperature(chillerSetPointGraph.GetX(), chillerSetPointGraph.GetY(), module=moduleName)
        theHistogrammer.makeChillerSetPointTemperature(chillerSetPointGraph.GetX(), chillerSetPointGraph.GetY(), testTimeStart, testTimeStop, module=moduleName)
        '''

        ############################
        #Adding IV curve
        powerSupplyIVDirectory = powerSupplyFile.Get("PowerSupply/IVCurves")
        moduleIVGraph           = self.getGraphFromCanvas(powerSupplyIVDirectory.Get(moduleBurninName + "_HV_IVCurve"))
        moduleIVTimestampGraph  = self.getGraphFromCanvas(powerSupplyIVDirectory.Get(moduleBurninName + "_HV_IVCurveTimestamp"))


        #voltages = -np.array(moduleIVGraph.GetX())
        voltages = np.array(moduleIVGraph.GetX())
        
        #theHistogrammer.makeIVCurve(voltages, -np.array(moduleIVGraph.GetY()), moduleName)
        theHistogrammer.makeIVCurve(voltages, np.array(moduleIVGraph.GetY()), moduleName)

        ambientTemperatureDuringIV = np.array(self.getGraphValuesByTimestamp(ambientTemperatureGraph, moduleIVTimestampGraph.GetY()))
        theHistogrammer.makeIVEnvironment("ENV_Temperature", voltages, ambientTemperatureDuringIV, moduleName)

        carrierTemperatureDuringIV = np.array(self.getGraphValuesByTimestamp(moduleCarrierTemperatureGraph, moduleIVTimestampGraph.GetY()))
        theHistogrammer.makeIVEnvironment("CARRIER_Temperature", voltages, carrierTemperatureDuringIV, moduleName)


        humidityDuringIV = np.array(self.getGraphValuesByTimestamp(humidityHistoryGraph, moduleIVTimestampGraph.GetY()))
        theHistogrammer.makeIVEnvironment("Humidity"   , voltages, humidityDuringIV, moduleName)

        theHistogrammer.makeIVEnvironment("Timestamp"  , voltages, np.array(moduleIVTimestampGraph.GetY()), moduleName)#The X data points match the one in the moduleIVGraph, so it is all good

        sensorTemperatureDuringIV = np.array(self.getGraphValuesByTimestamp(sensorTemperatureGraph, moduleIVTimestampGraph.GetY()))
        theHistogrammer.makeIVEnvironment("SENSOR_Temperature", voltages, sensorTemperatureDuringIV, moduleName)
        '''


        ##############################################################################
        print(detectorTrackerDirectory.Get("CalibrationStartTimestamp_Detector").GetName())
        #Setting Info
        # Create a TObjString to store the string
        theHistogrammer.info_directory.cd()
        TObjString("Burnin").Write("Setup")
        print("Task: ", detectorTrackerDirectory.Get("CalibrationName_Detector").GetName())
        TObjString(detectorTrackerDirectory.Get("CalibrationName_Detector").GetName()).Write("Task")
        print("Date: ", detectorTrackerDirectory.Get("CalibrationStartTimestamp_Detector").GetName())
        TObjString(detectorTrackerDirectory.Get("CalibrationStartTimestamp_Detector").GetName()).Write("Date")
        print("LocalRunNumber: ", str(runNumber))
        TObjString(str(runNumber)).Write("LocalRunNumber") ##Our local run number corresponds to the run number 
        print("Location: ", moduleName[moduleName.find("-")-3:moduleName.find("-")])
        location = moduleName[moduleName.find("-")-3:moduleName.find("-")] ###  how it was defined in the old code
        location = "PSA"
        TObjString(location).Write("Location")
        print("Module_ID: ", moduleName)
        TObjString(moduleName).Write("Module_ID")
        TObjString("Unknown").Write("Operator")
        TObjString("Unknown").Write("Result_Folder")
        TObjString("mod_final").Write("Run_Type")
        print("Module_Slot: ", opticalGroupToBurninSlot[opticalGroupNumber])
        TObjString(opticalGroupToBurninSlot[opticalGroupNumber]).Write("Module_Slot")
        

        '''
        #Setting Summary
        theHistogrammer.summary_directory.cd()
        print("HV Current at start of IV (uA): ", str(moduleIVGraph.GetY()[0]))
        TObjString(str(moduleIVGraph.GetY()[0])).Write("HV Current at start of IV (uA)")
        print("HV Current at end of IV (uA): ", str(moduleIVGraph.GetY()[-1]))
        TObjString(str(moduleIVGraph.GetY()[-1])).Write("HV Current at stop of IV (uA)")
        print("HV Current at start of module test (uA): ", str(hvCurrentHistoryGraph.Eval(testTimeStart)))
        TObjString(str(hvCurrentHistoryGraph.Eval(testTimeStart))).Write("HV Current at start of Module Test (uA)")
        print("HV Current at end of module test (uA): ", str(hvCurrentHistoryGraph.Eval(testTimeStop)))
        TObjString(str(hvCurrentHistoryGraph.Eval(testTimeStop))).Write("HV Current at stop of Module Test (uA)")
        
        #Takes the time at 1/2 IV curves and uses it to get the LV current
        print("LV Current during IV (A): ", str(lvCurrentHistoryGraph.Eval(moduleIVTimestampGraph.GetY()[0])))
        #print("Time: ", moduleIVTimestampGraph.GetY()[math.ceil(moduleIVGraph.GetN()/2)])
        TObjString(str(lvCurrentHistoryGraph.Eval(moduleIVTimestampGraph.GetY()[math.ceil(moduleIVGraph.GetN()/2)]))).Write("LV Current during IV (A)")
        '''

        #Measurement taken after a power off
        print("LV Current module unconfigured (A): ", str(self.getCurrentAfterPowerOff(lvCurrentHistoryGraph)))
        TObjString(str(self.getCurrentAfterPowerOff(lvCurrentHistoryGraph))).Write("LV Current module unconfigured (A)")

        #Mean value of the module LV current during the test (+-TimeExtension)        
        print("LV Current module configured (A): ", str(sum(lvCurrentGraph.GetY())/len(lvCurrentGraph.GetY())))
        TObjString(str(sum(lvCurrentGraph.GetY())/len(lvCurrentGraph.GetY()))).Write("LV Current module configured (A)")
        
        #Last test current value  (+-TimeExtension)        
        print("LV Current at start of Module Test (A): ", str(lvCurrentGraph.Eval(testTimeStart)))
        TObjString(str(lvCurrentGraph.Eval(testTimeStart))).Write("LV Current at start of Module Test (A)")
        #Last test current value  (+-TimeExtension)        
        print("LV Current at stop of Module Test (A): ", str(lvCurrentGraph.Eval(testTimeStop)))
        TObjString(str(lvCurrentGraph.Eval(testTimeStop))).Write("LV Current at stop of Module Test (A)")

        '''
        print("Environment T at start of IV: ", str(ambientTemperatureDuringIV[0]))
        TObjString(str(ambientTemperatureDuringIV[0])).Write("Environment T at start of IV (C)")
        print("Environment T at end of IV: ", str(ambientTemperatureDuringIV[-1]))
        TObjString(str(ambientTemperatureDuringIV[-1])).Write("Environment T at stop of IV (C)")
        '''
        print("Environment T at start of Module Test: ", str(ambientTemperatureGraph.Eval(testTimeStart)))
        TObjString(str(ambientTemperatureGraph.Eval(testTimeStart))).Write("Environment T at start of Module Test (C)")
        print("Environment T at end of Module Test: ", str(ambientTemperatureGraph.Eval(testTimeStop)))
        TObjString(str(ambientTemperatureGraph.Eval(testTimeStop))).Write("Environment T at stop of Module Test (C)")
        '''
        print("Carrier T at start of IV: ", str(carrierTemperatureDuringIV[0]))
        TObjString(str(carrierTemperatureDuringIV[0])).Write("Carrier T at start of IV (C)")
        print("Carrier T at end of IV: ", str(carrierTemperatureDuringIV[-1]))
        TObjString(str(carrierTemperatureDuringIV[-1])).Write("Carrier T at stop of IV (C)")
        '''
        print("Carrier T at start of Module Test: ", str(moduleCarrierTemperatureGraph.Eval(testTimeStart)))
        TObjString(str(moduleCarrierTemperatureGraph.Eval(testTimeStart))).Write("Carrier T at start of Module Test (C)")
        print("Carrier T at end of Module Test: ", str(moduleCarrierTemperatureGraph.Eval(testTimeStop)))
        TObjString(str(moduleCarrierTemperatureGraph.Eval(testTimeStop))).Write("Carrier T at stop of Module Test (C)")
        '''
        print("Sensor T at start of IV: ", str(sensorTemperatureDuringIV[0]))
        TObjString(str(sensorTemperatureDuringIV[0])).Write("Sensor T at start of IV (C)")
        print("Sensor T at end of IV: ", str(sensorTemperatureDuringIV[-1]))
        TObjString(str(sensorTemperatureDuringIV[-1])).Write("Sensor T at stop of IV (C)")
        print("Chiller set T at start of IV: ", str(chillerSetPointGraph.Eval(moduleIVTimestampGraph.GetY()[0])))
        TObjString(str(chillerSetPointGraph.Eval(moduleIVTimestampGraph.GetY()[0]))).Write("Chiller Setpoint T at start of IV (C)")
        print("Chiller set T at end of IV: ", str(chillerSetPointGraph.Eval(moduleIVTimestampGraph.GetY()[-1])))
        TObjString(str(chillerSetPointGraph.Eval(moduleIVTimestampGraph.GetY()[-1]))).Write("Chiller Setpoint T at stop of IV (C)")
        '''
        print("Chiller set T at start of Module Test: ", str(chillerSetPointGraph.Eval(testTimeStart)))
        TObjString(str(chillerSetPointGraph.Eval(testTimeStart))).Write("Chiller Setpoint T at start of Module Test (C)")
        print("Chiller set T at end of Module Test: ", str(chillerSetPointGraph.Eval(testTimeStop)))
        TObjString(str(chillerSetPointGraph.Eval(testTimeStop))).Write("Chiller Setpoint T at stop of Module Test (C)")
        '''
        print("RH at start of IV: ", str(humidityDuringIV[0]))
        TObjString(str(humidityDuringIV[0])).Write("Relative Humidity at start of IV (%)")
        print("RH at end of IV: ", str(humidityDuringIV[-1]))
        TObjString(str(humidityDuringIV[-1])).Write("Relative Humidity at stop of IV (%)")
        '''
        print("RH at start of Module Test: ", str(humidityGraph.Eval(testTimeStart)))
        TObjString(str(humidityGraph.Eval(testTimeStart))).Write("Relative Humidity at start of Module Test (%)")
        print("RH at end of Module Test: ", str(humidityGraph.Eval(testTimeStop)))
        TObjString(str(humidityGraph.Eval(testTimeStop))).Write("Relative Humidity at stop of Module Test (%)")
        print("Sensor T at start of Module Test: ", str(sensorTemperatureGraph.Eval(testTimeStart)))
        TObjString(str(sensorTemperatureGraph.Eval(testTimeStart))).Write("Sensor T at start of Module Test (C)")
        print("Sensor T at end of Module Test: ", str(sensorTemperatureGraph.Eval(testTimeStop)))
        TObjString(str(sensorTemperatureGraph.Eval(testTimeStop))).Write("Sensor T at stop of Module Test (C)")

        theHistogrammer.closeRootFile()
#        powerSupplyFile.Close()
#        burninFile.Close()
