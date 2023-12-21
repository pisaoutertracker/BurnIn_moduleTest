import os

logs = os.listdir("logs")

ROOTfiles = set()
for log in logs:
    log_ = open("logs/%s"%log)
    for l in log_.readlines():
        if ".root" in l:
            l = l.split("Closing result file: ")[1].replace("\n","")
            import re
            
            # 7-bit C1 ANSI sequences
            ansi_escape = re.compile(r'''
                \x1B  # ESC
                (?:   # 7-bit C1 Fe (except CSI)
                    [@-Z\\-_]
                |     # or [ for CSI, followed by a control sequence
                    \[
                    [0-?]*  # Parameter bytes
                    [ -/]*  # Intermediate bytes
                    [@-~]   # Final byte
                )
            ''', re.VERBOSE)
            l = ansi_escape.sub('', l)
            ROOTfiles.add(l)


errors = []
from ROOT import TFile
for a in ROOTfiles:
    try:
        TFile.Open(a)
        print("python3 moduleTest.py session --useExistingModuleTest %s  >& uploadLogs/%s "%(a.split("/")[1],a.split("/")[1]))
    except:
        errors.append(a)

print(errors)
