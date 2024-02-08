import os
from databaseTools import getModuleTestFromDB, getModuleFromDB, getRunFromDB, getSessionFromDB, getListOfSessionsFromDB, getListOfAnalysisFromDB


from analysis import all_analysis
def getLink(moduleTestName):
    links = []
    base = "https://cmstkita.web.cern.ch/Pisa/TBPS/navigator.php/%s/"
    test = moduleTestName.replace("__run", "_Run_run")
    for an in all_analysis:
        if test in an:
            links.append(base%an)
    text = ""
    for l in links:
        name = l.split("_Result_")[1].split("/results_")[0]
        text += "[%s](%s) "%(name, l)
    return text

def getTemperature(time):
    token_location = "~/private/influx.sct" 
    token = open(os.path.expanduser(token_location)).read()[:-1]
    
    from datetime import datetime, timedelta
    
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    
    import numpy as np
    import matplotlib.pyplot as plt
    
    org = "pisaoutertracker"
    bucket = "sensor_data"
    
    client = InfluxDBClient(url="http://cmslabserver:8086/", token=token)
    
    timeFormat = "%Y-%m-%dT%H:%M:%S"
    
    currentTime = datetime.strptime(time, timeFormat) - timedelta(hours=1) ## to move to UTC
    start_time = (currentTime).isoformat("T") + "Z"
    stop_time = (currentTime + timedelta(hours=0.1)).isoformat("T") + "Z"
#    stop_time = time + "Z"
#    start_time = "2023-12-20T03:03:34Z"
#    stop_time = "2023-12-20T15:03:34Z"
    
#    start_time = (datetime.utcnow() - timedelta(hours=12)).isoformat("T") + "Z"
#    stop_time = datetime.utcnow().isoformat("T") + "Z"

#    print(start_time)
#    print(stop_time)
#    
    sensorName = "Temp0"
    query = f'''
    from(bucket: "sensor_data")
     |> range(start: {start_time}, stop: {stop_time})
     |> filter(fn: (r) => r["_measurement"] == "mqtt_consumer")
     |> filter(fn: (r) => r["_field"] == "%s" )
     |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
     |> yield(name: "mean")
    '''%sensorName
    
    tables = client.query_api().query(query, org=org)
    
    time = []
    value = []
    
    for table in tables:
       for record in table.records:
           time.append(record.get_time())
           value.append(record.get_value())
           if len(value)>0 and type(value[0])==float:
               return value[0]
    return 999

## run245
moduleName = "PS_26_10-IPG_00103"


#analysis_map = {}
#for an in all_analysis:
#    test = an["moduleTestName"]
#    if not test in analysis_map:
#        analysis_map[test] = [test]
#    else:
#        analysis_map[test].append(test)
#        


#for p in analysis_map:
#    print(p)



for session in getListOfSessionsFromDB():
#for session in [getSessionFromDB("session34")]:
#    s =sessions[0]["sessionName"]
#    
#    session = getSessionFromDB("session1")
    
    testDate = {}
    if "test_runName" in session:
        print()
        print("SESSION: %s (%s) %s"%(session['sessionName'], session['operator'], session['timestamp'].replace("T"," ")))
        print("Descrizione: %s"%session['description'])
        
        for run in session["test_runName"]:
            if not (session['sessionName']=="session1" and int(run.split("run")[1])< 243): ## avoid duplicate runs
                run = getRunFromDB(run)
                for moduleTest in run['moduleTestName']:
                    test = getModuleTestFromDB(moduleTest)
        #            session = getSessionFromDB(run['runSession'])
        #            print(moduleName, run['runDate'])
                    testDate[run['runDate']+"+++"+test["moduleName"]] = (moduleTest, run['runFile'])
        #    run = getRunFromDB(runName)

    #    print()
    #    print()

        for date in sorted(list(testDate)):
            test, zip = testDate[date]
            date = date.split("+++")[0]
            module, run = test.split("__")
#            t = getModuleTestFromDB(test)
#            refAnalysis = ""
#            if 'referenceAnalysis' in t:
#                refAnalysis = t['referenceAnalysis']
#            elif 'analysesList' in t:
#                refAnalysis = t['analysesList'][-1]
            print("%s\t%s\t[%s](%s)\t%.1f\t%s"%(module, date.replace("T","\t"), test, zip.split("/output")[0], getTemperature(date), getLink(test)))
        #    print("python3 %s"%testDate[date])

    #    print()
    #    print()

#        for date in sorted(list(testDate)):
#            test, zip = testDate[date]
#            print("python3 updateTestResult.py %s >& uploadLogs/Analysis_%s "%(test, test))

    #    #testDate = {}
    #    #module = getModuleFromDB(moduleName)

