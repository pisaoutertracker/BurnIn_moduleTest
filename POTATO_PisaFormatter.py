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
from datetime import datetime, timedelta, timezone

extraTime = 0 # minutes (time)
#iv_csv_path = "Run_500087_output_lahes/IV_curve_HV005_PS_40_05_IPG-00002_before_encapsulation_changed.csv"
#iv_csv_path = "IVdata/IV_curve_HV0.1_TEST_after_encapsulation_20250522_211105.csv"

sensorTempPlotName = "LpGBT_DQM_SensorTemp"
#temperatureSensor = "Temp0" ###FIXME/CHECK: non lo uso piu', lo prendo da MonitorDQM (vedi sensorTempPlotName) 
ambientTemperatureSensor = "/fnalbox/full/AirTemp"
moduleCarrierTemperatureSensor = "/fnalbox/full/OW%s"
dewPointSensor = "/fnalbox/full/DewPoint" 
chillerSetPointName = "/julabo/full/Temp_SP1" ##can we please get rid of the 3 setpoint stuff in the BurnIN GUI ? we do not need it
#ambientHumiditySensor = "/fnalbox/full/Humidity"
#

# The maximum number of hours since the start of the run to query InfluxDB.
maxNumHoursSinceStartRun_influxQuery = 24*4 # hours (time) ## 4 days for the full burn-in
#from moduleTest import verbose ## to be updated

verbose = 10
# Define the path to the main directory
#main_directory = "./data"
#output_directory = "./potato"
# output_directory = "../potato/POTATO_data/LocalFiles/TestOutput"

import pandas as pd

def spikeRemoval(graph, threshold=0.1):
    '''        Remove spikes from a TGraph by checking if the difference between consecutive points exceeds a threshold.
    '''
    first = True
    x = graph.GetX()
    y = graph.GetY()
    n = graph.GetN()
    toDo = True
    new_x = list(x)
    new_y = list(y)
    while toDo:
        toDo = False
        x = list(new_x)
        y = list(new_y)
        new_x = []
        new_y = []
        for i in range(len(y) - 1):
            if first or True: 
                print("SpikeRemoval: ", i, " ", y[i], " ", y[i + 1], " ", abs(y[i + 1] - y[i]), " ", threshold)
                first = False
            if abs(y[i + 1] - y[i]) < threshold:
                new_x.append(x[i])
                new_y.append(y[i])
            else:
                print("REMOVED SPIKE: ", i, " ", y[i], " ", y[i + 1], " ", abs(y[i + 1] - y[i]), " ", threshold)
                toDo = True
        # Add the last point
        new_x.append(x[-1])
        new_y.append(y[-1])
    print(x, y)
    from array import array
    return ROOT.TGraph(len(new_x), array('d', new_x), array('d', new_y))

def makeGraphFromDataframe(df, x_col, y_col, is_datetime=False):
    """
    Create a ROOT TGraph from a Pandas DataFrame.
    
    Parameters:
        df (pd.DataFrame): The DataFrame containing the data.
        x_col (str): The name of the column to use for the x-axis.
        y_col (str): The name of the column to use for the y-axis.
    
    Returns:
        ROOT.TGraph: A TGraph object created from the DataFrame.
    """
    import array as arr
    print(x_col, y_col)
    print(df[x_col].values)
    print(df[y_col].values)

    x = arr.array('d', df[x_col].values)
    print(type(df[y_col].values[0]))
    if is_datetime:
        # Convert datetime to timestamp
        df[y_col] = pd.to_datetime(df[y_col])
        df[y_col] = df[y_col].astype(np.int64) // 10**9  # Convert to seconds since epoch 
    y = arr.array('d', df[y_col].values)
    graph = ROOT.TGraph(len(x), x, y)
    print("Y: ", y)
    return graph

def readIVcsv(filename):
    """
    Parses a custom text file containing:
      - '#' metadata lines (key, value)
      - multiple CSV-like sections with header lines and data lines
    Returns:
      - metadata: a dict of metadata from lines starting with '#'
      - dataframes: a list of Pandas DataFrames, one per CSV section
    """
    # -- Read all non-empty lines (strip whitespace), store in a list:
    with open(filename, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    # -- Step 1: Parse metadata lines
    metadata = {}
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if line.startswith('#'):
            # Remove '#' at the start and split into two parts max
            no_hash = line[1:].strip()
            if ',' in no_hash:
                key, value = no_hash.split(',', 1)
                metadata[key.strip()] = value.strip()
            idx += 1
        else:
            break

    # -- Step 2: Parse data sections
    dataframes = []
    while idx < len(lines):
        # The next line should be a header line
        header_line = lines[idx]
        idx += 1
        header_cols = [col.strip() for col in header_line.split(',')]

        rows = []
        # Capture lines until we reach end-of-file or a line
        # that has a different number of comma-separated fields (new header).
        while idx < len(lines):
            candidate = lines[idx]
            split_candidate = candidate.split(',')
            ## convert to float
            floats = []
            for col in split_candidate:
                try:
                    floats.append(float(col))
                except ValueError: ## keep dates as strings
                    floats.append(col)
            split_candidate = floats
            # If the line doesn't match the column count, it's likely the next header
            if len(split_candidate) != len(header_cols):
                break
            rows.append(split_candidate)
            idx += 1

        # Create a DataFrame for this section
        df = pd.DataFrame(rows, columns=header_cols)
        dataframes.append(df)

    return metadata, dataframes[1], dataframes[0]


def getGraphFromMonitorDQM(trackerMonitorDirectory, plotName="LpGBT_DQM_SensorTemp", board=0, opticalGroup=0):
    #print("Getting plot from MonitorDQM: ", plotName, " Board: ", board, " OpticalGroup: ", opticalGroup)
    #trackerMonitorFile = ROOT.TFile.Open(trackerMonitorFileName)
    if trackerMonitorDirectory == None:
        raise RuntimeError(f"MonitorDQM directory not found in file: {trackerMonitorDirectory.GetName()}")
    plotPath = "Board_" + str(board) + "/OpticalGroup_" + str(opticalGroup) + "/" + "D_B(%d)_%s_OpticalGroup(%s)"%(board, plotName, opticalGroup)
    moduleCanvas = trackerMonitorDirectory.Get(plotPath)
    if moduleCanvas == None:
        raise RuntimeError(f"Module canvas not found in file: {trackerMonitorDirectory.GetName()} with path: {plotPath}")
    print("getGraphFromMonitorDQM: X-max: ", moduleCanvas.GetXaxis().GetXmax())
    print("getGraphFromMonitorDQM: X-min: ", moduleCanvas.GetXaxis().GetXmin())
    return moduleCanvas

'''
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
'''
    
def readConnectionMap(connectionMapFileName):
    import glob
    print(connectionMapFileName)
    with open(connectionMapFileName) as json_file:
        print("ConnectionMap file: ", connectionMapFileName)
        txt = str(json_file.read())
        if verbose>1000: print("ConnectionMap: ", txt)
        connectionMap = eval(txt)
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
            if timestamp < min(graph.GetX()) or timestamp > max(graph.GetX()):
                print("################################")
                print(f"WARNING: Reading value outside graph range: {graph.GetName()} {timestamp} Range({min(graph.GetX())}, {max(graph.GetX())}). Extrapolated value: {graph.Eval(timestamp)}")
                print("################################")
        if len(values) == 0:
            print("################################")
            print(f"WARNING: Something wrong calling getGraphValuesByTimestamp {graph.GetName()} {timestamps}")
            print("################################")
        print("getGraphValuesByTimestamp: Graph name: ", graph.GetName(), " N: ", graph.GetN(), " Start: ", graph.GetX()[0], " Stop: ", graph.GetX()[graph.GetN()-1])
        return values

    def getInfluxQueryAPI(self, token_location = "~/private/influx.sct"):
        token = open(os.path.expanduser(token_location)).read().strip()
        from influxdb_client import InfluxDBClient
        client = InfluxDBClient(url="http://cmslabserver:8086/", token=token)
        return client.query_api()

    # def getTemperatureAt(self, timestamp, sensorName="Temp0", org="pisaoutertracker"):
    #     # Define a small window around the timestamp (±30 seconds)
    #     if self.verbose>2: print('Calling getTemperatureAt(timestamp=%s, sensorName=%s, org=%s)'%(timestamp, sensorName, org))
    #     window = timedelta(seconds=30)
    #     timestamp = datetime.fromisoformat(timestamp)
    #     start_window = (timestamp - window).isoformat("T") + "Z"
    #     end_window = (timestamp + window).isoformat("T") + "Z"
    #     query = f'''
    #     from(bucket: "sensor_data")
    #         |> range(start: {start_window}, stop: {end_window})
    #         |> filter(fn: (r) => r["_measurement"] == "mqtt_consumer")
    #         |> filter(fn: (r) => r["_field"] == "{sensorName}")
    #         |> aggregateWindow(every: 1s, fn: mean, createEmpty: false)
    #         |> yield(name: "mean")
    #     '''
    #     tables = self.influxQuery.query(query, org=org)
    #     # Gather the temperature values found within the time window.
    #     temps = [record.get_value() for table in tables for record in table.records]
    #     if temps:
    #         # Average values if more than one record is returned.
    #         return sum(temps) / len(temps)
    #     else:
    #         print('WARNING: Something wrong calling getTemperatureAt(timestamp=%s, sensorName=%s, org=%s)'%(timestamp, sensorName, org))
    #         return -999

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
                if verbose>500: print("Record: ", record.get_time(), " Value: ", record.get_value(), record.get_time().timestamp(), float(record.get_time().timestamp()))
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
        graph = ROOT.TGraph(len(times), arr.array('d',times), arr.array('d',values))
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

    def do_burnin_format(self, rootTrackerFileName, runNumber, opticalGroupNumber, moduleBurninName, moduleCarrierName, iv_csv_path, connectionMapPath, sessionTimestampStart, sessionTimestampStop):
        print("Calling do_burnin_format with: rootTrackerFileName: ", rootTrackerFileName, " runNumber: ", runNumber, " opticalGroupNumber: ", opticalGroupNumber, " moduleBurninName: ", moduleBurninName, " moduleCarrierName: ", moduleCarrierName)
        theHistogrammer = Histogrammer()
        self.theHistogrammer = theHistogrammer
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
        detectorTrackerMonitorDirectory = theHistogrammer.outputRootFile.Get("MonitorDQM/Detector")
        if detectorTrackerDirectory == 0:
            raise RuntimeError(f"Detector directory not found in file: {rootTrackerFileName}")
        if detectorTrackerMonitorDirectory == 0:
            raise RuntimeError(f"MonitorDQM directory not found in file: {rootTrackerFileName}")
#        print(theHistogrammer.Print())
        if verbose>100:
            print("Detector directory: ", detectorTrackerDirectory.GetName())
            for el in detectorTrackerDirectory.GetListOfKeys():
                print("Key: ", el.GetName(), " Class: ", el.GetClassName())
            print("MonitorDQM directory: ", detectorTrackerMonitorDirectory.GetName())
            for el in detectorTrackerMonitorDirectory.GetListOfKeys():
                print("Key: ", el.GetName(), " Class: ", el.GetClassName())
        moduleNameIdStr = "Board_0/OpticalGroup_" + opticalGroupNumber + "/D_B(0)_NameId_OpticalGroup(" + opticalGroupNumber + ")"
        moduleName = str(detectorTrackerDirectory.Get(moduleNameIdStr))
        print("Formatting file for module: " + moduleName)
        if moduleName == None or moduleName == "":
            raise RuntimeError(f"Module name not found in file: {rootTrackerFileName}, moduleNameIdStr: {moduleNameIdStr}")


        timeFromRoot_start = detectorTrackerDirectory.Get("CalibrationStartTimestamp_Detector").GetName()
        timeFromRoot_stop  = detectorTrackerDirectory.Get("CalibrationStopTimestamp_Detector").GetName()

        timeSession_start = sessionTimestampStart.replace("T"," ")
        timeSession_stop  = sessionTimestampStop.replace("T"," ")

       
        startTime_rome, startTime_utc = getTimeFromRomeToUTC(timeFromRoot_start, timeFormat = "%Y-%m-%d %H:%M:%S")
        stopTime_rome, stopTime_utc = getTimeFromRomeToUTC(timeFromRoot_stop, timeFormat = "%Y-%m-%d %H:%M:%S")

        startSession_rome, startSession_utc = getTimeFromRomeToUTC(timeSession_start, timeFormat = "%Y-%m-%d %H:%M:%S")
        stopSession_rome, stopSession_utc = getTimeFromRomeToUTC(timeSession_stop, timeFormat = "%Y-%m-%d %H:%M:%S")

        if stopSession_utc > startSession_utc + timedelta(hours=maxNumHoursSinceStartRun_influxQuery):
            print("%"* 80)
            print("WARNING: Session stop time is MORE than %.1f hours after start time (%.2f). This may lead to missing data in InfluxDB queries." % (maxNumHoursSinceStartRun_influxQuery, (stopSession_utc - startSession_utc).total_seconds() / 3600.0 ) )
            print("Start time (UTC): ", startTime_utc, " Stop time (UTC): ", stopTime_utc)
            print("Session start time (UTC): ", startSession_utc, " Session stop time (UTC): ", stopSession_utc)
            stopSession_utc = startSession_utc + timedelta(hours=maxNumHoursSinceStartRun_influxQuery)
            stopSession_rome = stopSession_utc.astimezone(tz=None)  # Convert to local time zone
            print("Adjusted session stop time (UTC): ", stopSession_utc, " Adjusted session stop time (local): ", stopSession_rome)
            print("%"* 80)
            print("This might mean that the burnin was longer than %.1f hours or that there are no other session afterwards. You can fix this by increasing the maxNumHoursSinceStartRun_influxQuery parameter." % (maxNumHoursSinceStartRun_influxQuery) )
            print("%"* 80)

        ### For influxDB:
        time_start_utc = startTime_utc.isoformat("T").split("+")[0] 
        time_stop_utc = stopTime_utc.isoformat("T").split("+")[0] 

        session_start_utc = startSession_utc.isoformat("T").split("+")[0] 
        session_stop_utc = stopSession_utc.isoformat("T").split("+")[0]

        testTimeStart = datetime.strptime(timeFromRoot_start, TIME_FORMAT).timestamp()
        testTimeStop  = datetime.strptime(timeFromRoot_stop, TIME_FORMAT).timestamp()


        ## TO BE CHECKED:
        # move time from CEST to UTC

        import zoneinfo
        cest_zone = zoneinfo.ZoneInfo("Europe/Berlin")  # Berlin uses CEST in summer
        utc_zone = zoneinfo.ZoneInfo("UTC")  # Berlin uses CEST in summer

        #testTimeStart = datetime.fromtimestamp(testTimeStart, cest_zone).replace(tzinfo=utc_zone).timestamp()
        #testTimeStop = datetime.fromtimestamp(testTimeStop, cest_zone).replace(tzinfo=utc_zone).timestamp()


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
        

        self.IV_metadata, self.IV_df, self.IV_df_station = readIVcsv(iv_csv_path)
        startTime_IV_rome, startTime_IV_utc = getTimeFromRomeToUTC(self.IV_df.TIME.iloc[0], timeFormat = "%Y-%m-%d %H:%M:%S")
        stopTime_IV_rome, stopTime_IV_utc = getTimeFromRomeToUTC(self.IV_df.TIME.iloc[-1], timeFormat = "%Y-%m-%d %H:%M:%S")

        ### For influxDB:
        timeFromRoot_start_IV_utc = startTime_IV_rome.isoformat("T").split("+")[0] 
        timeFromRoot_stop_IV_utc = stopTime_IV_rome.isoformat("T").split("+")[0] 

        testTimeStart_IV = datetime.strptime(self.IV_df.TIME.iloc[0], TIME_FORMAT).timestamp()
        testTimeStop_IV  = datetime.strptime(self.IV_df.TIME.iloc[-1], TIME_FORMAT).timestamp()

        ## TO BE CHECKED:
        # move time from CEST to UTC

        testTimeStart_IV = datetime.fromtimestamp(testTimeStart_IV, cest_zone).replace(tzinfo=utc_zone).timestamp()
        testTimeStop_IV = datetime.fromtimestamp(testTimeStop_IV, cest_zone).replace(tzinfo=utc_zone).timestamp()

        print("IV metadata: ", self.IV_metadata)
        print("IV df: ", self.IV_df)

#        connectionMap = getConnectionMap(rootTrackerFileName)
        connectionMap = readConnectionMap(connectionMapPath)
        hv_channel, lv_channel = getHVLVchannels(connectionMap)
        moduleLVVoltageGraph = self.getGraphFromInfluxDB(f"caen_{lv_channel}_Voltage", start_time_TS=session_start_utc, stop_time_TS=session_stop_utc)
        moduleLVCurrentGraph = self.getGraphFromInfluxDB(f"caen_{lv_channel}_Current", start_time_TS=session_start_utc, stop_time_TS=session_stop_utc)
        moduleHVVoltageGraph = self.getGraphFromInfluxDB(f"caen_{hv_channel}_Voltage", start_time_TS=session_start_utc, stop_time_TS=session_stop_utc)
        moduleHVCurrentGraph = self.getGraphFromInfluxDB(f"caen_{hv_channel}_Current", start_time_TS=session_start_utc, stop_time_TS=session_stop_utc)

        ## No extra time as we want the temperature spot, not in a range
        sensorTemperatureGraph         = getGraphFromMonitorDQM(detectorTrackerMonitorDirectory, plotName=sensorTempPlotName, board=0, opticalGroup=opticalGroupNumber)
        ambientTemperatureGraph        = self.getGraphFromInfluxDB(ambientTemperatureSensor, start_time_TS=session_start_utc, stop_time_TS=session_stop_utc)
        moduleCarrierTemperatureGraph  = self.getGraphFromInfluxDB(moduleCarrierTemperatureSensor%(moduleCarrierName), start_time_TS=session_start_utc, stop_time_TS=session_stop_utc)
        dewPointGraph                  = self.getGraphFromInfluxDB(dewPointSensor, start_time_TS=session_start_utc, stop_time_TS=session_stop_utc)
        chillerSetPointGraph           = self.getGraphFromInfluxDB(chillerSetPointName, start_time_TS=session_start_utc, stop_time_TS=session_stop_utc)

        ambientTemperatureGraph_IV_Influx          = self.getGraphFromInfluxDB(ambientTemperatureSensor, start_time_TS=timeFromRoot_start_IV_utc, stop_time_TS=timeFromRoot_stop_IV_utc)
        moduleCarrierTemperatureGraph_IV_Influx    = self.getGraphFromInfluxDB(moduleCarrierTemperatureSensor%(moduleCarrierName), start_time_TS=timeFromRoot_start_IV_utc, stop_time_TS=timeFromRoot_stop_IV_utc)
        dewPointGraph_IV_Influx    = self.getGraphFromInfluxDB(dewPointSensor, start_time_TS=timeFromRoot_start_IV_utc, stop_time_TS=timeFromRoot_stop_IV_utc)

        print(moduleLVCurrentGraph.GetX()[0], moduleLVCurrentGraph.GetX()[-1])
        print(moduleName)
        print(moduleLVCurrentGraph.GetY()[0], moduleLVCurrentGraph.GetY()[-1])
        lvCurrentHistoryGraph = theHistogrammer.makeMonitorLVCurrent  (moduleLVCurrentGraph.GetX(), moduleLVCurrentGraph.GetY(), module=moduleName)
        print(f"Test time start: {datetime.fromtimestamp(testTimeStart)}, stop: {datetime.fromtimestamp(testTimeStop)}")
        print(f"Graph time min: {datetime.fromtimestamp(moduleLVCurrentGraph.GetX()[0])}, max: {datetime.fromtimestamp(moduleLVCurrentGraph.GetX()[-1])}")
        print(f"Session start UTC: {session_start_utc}, stop: {session_stop_utc}")
        # print(moduleLVCurrentGraph.GetX()[0]-testTimeStart, moduleLVCurrentGraph.GetX()[-1]-testTimeStart, testTimeStart-testTimeStart, testTimeStop-testTimeStart, session_start_utc - testTimeStart, session_stop_utc - testTimeStart)
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

        #humidityHistoryGraph_IV_Influx = theHistogrammer.makeMonitorHumidity   (*self.calculateHumidity(dewPointGraph_IV_Influx, ambientTemperatureGraph_IV_Influx), module=moduleName)
        #humidityGraph_IV        = theHistogrammer.makeMonitorHumidity(humidityHistoryGraph_IV_Influx.GetX(), humidityHistoryGraph_IV_Influx.GetY(), testTimeStart_IV, testTimeStop_IV, module=moduleName)

        theHistogrammer.makeMonitorDewPoint   (dewPointGraph.GetX(), dewPointGraph.GetY(), module=moduleName)
        theHistogrammer.makeMonitorDewPoint   (dewPointGraph.GetX(), dewPointGraph.GetY(), testTimeStart, testTimeStop, module=moduleName)

        theHistogrammer.makeCarrierTemperature(moduleCarrierTemperatureGraph.GetX(), moduleCarrierTemperatureGraph.GetY(), module=moduleName)
        theHistogrammer.makeCarrierTemperature(moduleCarrierTemperatureGraph.GetX(), moduleCarrierTemperatureGraph.GetY(), testTimeStart, testTimeStop, module=moduleName)

        theHistogrammer.makeChillerSetPointTemperature(chillerSetPointGraph.GetX(), chillerSetPointGraph.GetY(), module=moduleName)
        theHistogrammer.makeChillerSetPointTemperature(chillerSetPointGraph.GetX(), chillerSetPointGraph.GetY(), testTimeStart, testTimeStop, module=moduleName)

        moduleIVGraph           = makeGraphFromDataframe(self.IV_df, "VOLTS","CURRNT_NAMP") ## NanoAmps

        ## Convert to microAmps
        for i in range(moduleIVGraph.GetN()):
            moduleIVGraph.SetPoint(i, moduleIVGraph.GetX()[i], moduleIVGraph.GetY()[i] * 1e-3)
    
        moduleIVTimestampGraph  = makeGraphFromDataframe(self.IV_df, "VOLTS","TIME", is_datetime=True)

        print("IV Graph: ", moduleIVGraph.GetName(), " N: ", moduleIVGraph.GetN(), " Start: ", startTime_IV_utc, " Stop: ", stopTime_IV_utc)


        ############################
        #Adding IV curve
        #powerSupplyIVDirectory = powerSupplyFile.Get("PowerSupply/IVCurves")


        #voltages = -np.array(moduleIVGraph.GetX())
        voltages = np.array(moduleIVGraph.GetX())
        theHistogrammer.makeIVCurve(voltages, np.array(moduleIVGraph.GetY()), moduleName)
        #theHistogrammer.makeIVCurve(voltages, -np.array(moduleIVGraph.GetY()), moduleName)

        ### HERE TWO OPTIONS AVAILABLE. ONLY ONE OF THEM SHOULD BE USED
        ########################### Plots done using Influx data ##############################
        # We should always use the data from the IV .csv file, as it is more accurate and has the correct timestamps

        #ambientTemperatureDuringIV = np.array(self.getGraphValuesByTimestamp(ambientTemperatureGraph_IV_Influx, moduleIVTimestampGraph.GetY()))
        #theHistogrammer.makeIVEnvironment("ENV_Temperature", voltages, ambientTemperatureDuringIV, moduleName)

        carrierTemperatureDuringIV = np.array(self.getGraphValuesByTimestamp(moduleCarrierTemperatureGraph_IV_Influx, moduleIVTimestampGraph.GetY()))
        theHistogrammer.makeIVEnvironment("CARRIER_Temperature", voltages, carrierTemperatureDuringIV, moduleName)

        #humidityDuringIV = np.array(self.getGraphValuesByTimestamp(humidityHistoryGraph_IV_Influx, moduleIVTimestampGraph.GetY()))
        #theHistogrammer.makeIVEnvironment("Humidity"   , voltages, humidityDuringIV, moduleName)

        ## Remove spikes larger than 0.5 degrees from the sensorTemperatureGraph
        sensorTemperatureGraph = spikeRemoval(sensorTemperatureGraph, threshold=0.5)

        print("--------------------------------------------------------------------")
        print("KNOWN ISSUE... we don't have the sensor temperature during IV")
        values = moduleIVTimestampGraph.GetY()
        values = [val for val in values]  # Adjusting the values to match the sensor temperature range
#        sensorTemperatureDuringIV = np.array(self.getGraphValuesByTimestamp(sensorTemperatureGraph, moduleIVTimestampGraph.GetY()))
        sensorTemperatureDuringIV = np.array(self.getGraphValuesByTimestamp(sensorTemperatureGraph, values))
        theHistogrammer.makeIVEnvironment("SENSOR_Temperature", voltages, sensorTemperatureDuringIV, moduleName)
        print("KNOWN ISSUE... we don't have the sensor temperature during IV")
        print("--------------------------------------------------------------------")

        ########################### Plots done using IV .csv data ##############################

        ambientTemperatureDuringIV = np.array(self.IV_df["TEMP_DEGC"])
        theHistogrammer.makeIVEnvironment("ENV_Temperature", voltages, ambientTemperatureDuringIV, moduleName)

        #carrierTemperatureDuringIV = np.array(self.IV_df["TEMP_CARRIER"])  ### Missing Carrier temperature from .csv
        #theHistogrammer.makeIVEnvironment("CARRIER_Temperature", voltages, carrierTemperatureDuringIV, moduleName)

        humidityDuringIV = np.array(self.IV_df["RH_PRCNT"])
        theHistogrammer.makeIVEnvironment("Humidity"   , voltages, humidityDuringIV, moduleName)

        #sensorTemperatureDuringIV = = np.array(self.IV_df["TEMP_SENSOR"])  ### Missing Sensor temperature from .csv
        #theHistogrammer.makeIVEnvironment("SENSOR_Temperature", voltages, sensorTemperatureDuringIV, moduleName)

        ##############################################################################

        theHistogrammer.makeIVEnvironment("Timestamp"  , voltages, np.array(moduleIVTimestampGraph.GetY()), moduleName)#The X data points match the one in the moduleIVGraph, so it is all good

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
        
        # Set Run_Type based on carrier temperature at test start
        if(moduleCarrierTemperatureGraph.Eval(testTimeStart) > -15):
            ROOT.TObjString("mod_burnin_warm").Write("Run_Type")
        else:
            ROOT.TObjString("mod_burnin_cold").Write("Run_Type")
        
        print("Module_Slot: ", opticalGroupToBurninSlot[opticalGroupNumber])
        TObjString(opticalGroupToBurninSlot[opticalGroupNumber]).Write("Module_Slot")
        

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

        print("Environment T at start of IV: ", str(ambientTemperatureDuringIV[0]))
        TObjString(str(ambientTemperatureDuringIV[0])).Write("Environment T at start of IV (C)")
        print("Environment T at end of IV: ", str(ambientTemperatureDuringIV[-1]))
        TObjString(str(ambientTemperatureDuringIV[-1])).Write("Environment T at stop of IV (C)")
        print("Environment T at start of Module Test: ", str(ambientTemperatureGraph.Eval(testTimeStart)))
        TObjString(str(ambientTemperatureGraph.Eval(testTimeStart))).Write("Environment T at start of Module Test (C)")
        print("Environment T at end of Module Test: ", str(ambientTemperatureGraph.Eval(testTimeStop)))
        TObjString(str(ambientTemperatureGraph.Eval(testTimeStop))).Write("Environment T at stop of Module Test (C)")
        print("Carrier T at start of IV: ", str(carrierTemperatureDuringIV[0]))
        TObjString(str(carrierTemperatureDuringIV[0])).Write("Carrier T at start of IV (C)")
        print("Carrier T at end of IV: ", str(carrierTemperatureDuringIV[-1]))
        TObjString(str(carrierTemperatureDuringIV[-1])).Write("Carrier T at stop of IV (C)")
        print("Carrier T at start of Module Test: ", str(moduleCarrierTemperatureGraph.Eval(testTimeStart)))
        TObjString(str(moduleCarrierTemperatureGraph.Eval(testTimeStart))).Write("Carrier T at start of Module Test (C)")
        print("Carrier T at end of Module Test: ", str(moduleCarrierTemperatureGraph.Eval(testTimeStop)))
        TObjString(str(moduleCarrierTemperatureGraph.Eval(testTimeStop))).Write("Carrier T at stop of Module Test (C)")
        print("Sensor T at start of IV: ", str(sensorTemperatureDuringIV[0]))
        TObjString(str(sensorTemperatureDuringIV[0])).Write("Sensor T at start of IV (C)")
        print("Sensor T at end of IV: ", str(sensorTemperatureDuringIV[-1]))
        TObjString(str(sensorTemperatureDuringIV[-1])).Write("Sensor T at stop of IV (C)")
        print("Chiller set T at start of IV: ", str(chillerSetPointGraph.Eval(moduleIVTimestampGraph.GetY()[0])))
        TObjString(str(chillerSetPointGraph.Eval(moduleIVTimestampGraph.GetY()[0]))).Write("Chiller Setpoint T at start of IV (C)")
        print("Chiller set T at end of IV: ", str(chillerSetPointGraph.Eval(moduleIVTimestampGraph.GetY()[-1])))
        TObjString(str(chillerSetPointGraph.Eval(moduleIVTimestampGraph.GetY()[-1]))).Write("Chiller Setpoint T at stop of IV (C)")
        print("Chiller set T at start of Module Test: ", str(chillerSetPointGraph.Eval(testTimeStart)))
        TObjString(str(chillerSetPointGraph.Eval(testTimeStart))).Write("Chiller Setpoint T at start of Module Test (C)")
        print("Chiller set T at end of Module Test: ", str(chillerSetPointGraph.Eval(testTimeStop)))
        TObjString(str(chillerSetPointGraph.Eval(testTimeStop))).Write("Chiller Setpoint T at stop of Module Test (C)")
        print("RH at start of IV: ", str(humidityDuringIV[0]))
        TObjString(str(humidityDuringIV[0])).Write("RH at start of IV (%)")
        print("RH at end of IV: ", str(humidityDuringIV[-1]))
        TObjString(str(humidityDuringIV[-1])).Write("RH at stop of IV (%)")
        print("RH at start of Module Test: ", str(humidityGraph.Eval(testTimeStart)))
        TObjString(str(humidityGraph.Eval(testTimeStart))).Write("RH at start of Module Test (%)")
        print("RH at end of Module Test: ", str(humidityGraph.Eval(testTimeStop)))
        TObjString(str(humidityGraph.Eval(testTimeStop))).Write("RH at stop of Module Test (%)")

        print("Sensor T at start of Module Test: ", str(sensorTemperatureGraph.Eval(testTimeStart)))
        TObjString(str(sensorTemperatureGraph.Eval(testTimeStart))).Write("Sensor T at start of Module Test (C)")
        print("Sensor T at end of Module Test: ", str(sensorTemperatureGraph.Eval(testTimeStop)))
        TObjString(str(sensorTemperatureGraph.Eval(testTimeStop))).Write("Sensor T at stop of Module Test (C)")

        c1 = ROOT.TCanvas("c1", "Sensor Temperature Graph", 800, 600)
        sensorTemperatureGraph.Draw("AL*")
        c1.SaveAs("SensorTemperatureGraph.root")
        c1.SaveAs("SensorTemperatureGraph.png")

        sensorTemperatureGraphIV = sensorTemperatureGraph.Clone("SensorTemperatureGraphIV")
        for i in range(len(sensorTemperatureDuringIV)):
            sensorTemperatureGraphIV.SetPoint(len(sensorTemperatureGraphIV.GetX()), values[i], sensorTemperatureDuringIV[i])

        sensorTemperatureGraphIV.Draw("AL*")
        c1.SaveAs("sensorTemperatureGraphIV.root")
        c1.SaveAs("sensorTemperatureGraphIV.png")

        #print(moduleIVTimestampGraph.GetY())
        moduleCarrierTemperatureGraph_IV_Influx.Draw("AL*")
        c1.SaveAs("moduleCarrierTemperatureGraph_IV_Influx.root")
        c1.SaveAs("moduleCarrierTemperatureGraph_IV_Influx.png")

        ## print x-axis range of sensorTemperatureGraph
        print("Time test start: ", testTimeStart, " Time test stop: ", testTimeStop)
        print("X-min of Sensor T Graph: ", sensorTemperatureGraph.GetXaxis().GetXmin())
        print("X-max of Sensor T Graph: ", sensorTemperatureGraph.GetXaxis().GetXmax())
    
        theHistogrammer.closeRootFile()
#        powerSupplyFile.Close()
#        burninFile.Close()

if "__main__" == __name__:
    ## POTATOFiles/PS_26_IPG-10014_2025-10-19_11h14m43s_+23C_PSquickTest_v6-19.root

    ## Run potatoconverter (or formatter)
    from POTATO_PisaFormatter import POTATOPisaFormatter as Formatter
    print("#"*200)
    # mergeTwoROOTfiles(resultsFile, monitorDQMFile, rootTrackerFileName)
    # iv_csv_path = createIVScanCSVFile(runNumber, module_name, outDir)
    theFormatter = Formatter("")
    rootTrackerFileName = "POTATOFiles/PS_26_IPG-10014_2025-10-19_11h14m43s_+23C_PSquickTest_v6-19.root"
    iv_csv_path = "POTATOFiles/HV0.9_PS_26_IPG-10014_after_encapsulation_20251019_103201_IVScan.csv"
    print(f"Calling POTATO Pisa Formatter version with files {rootTrackerFileName}, {iv_csv_path}")
    runNumber = "26"
    opticalGroup = "0"
    moduleBurninName = "PSquickTest_v6-19"
    moduleCarrierName = "IPG-10014"
    connectionMapFilePath = "connectionMaps/connection_map_PS_26_IPG-10014.csv"
    session_timestamp = "2025-10-19T11:14:43"
    next_session_timestamp = "2025-10-19T15:14:43"

    print("#"*200)
    print( next_session_timestamp)
    print( session_timestamp)
    theFormatter.do_burnin_format(rootTrackerFileName, runNumber, opticalGroup, moduleBurninName, moduleCarrierName, iv_csv_path, connectionMapFilePath, session_timestamp, next_session_timestamp)

    pisaFormatter = POTATO_PisaFormatter()
    pisaFormatter.run()
