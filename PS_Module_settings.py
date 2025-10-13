### Configuration one-shot ###
config = {
    "commonSettings" : "pippo",
    "Nevents" : "50",
    "boards" : {
        "0": {
            "ip" : "fc7ot2:50001",
            "opticalGroups" : {
                "1" : {
                    "lpGBT" : "lpGBT_v1_PS.txt", ##it was lpGBT_v1.txt
                    "hybrids" : {
                        "0" : {
                            "edgeSelect" : 1,
#                            "strips" : [0],
#                            "pixels" : [8],
                            "strips" : [0, 1, 2, 3, 4, 5, 6, 7],
                            "pixels" : [8, 9, 10, 11, 12, 13, 14, 15],
                        },
                        "1" : {
#			     "strips" : [0]
                            "edgeSelect" : 0,
                            "strips" : [0, 1, 2, 3, 4, 5, 6, 7],
                            "pixels" : [8, 9, 10, 11, 12, 13, 14, 15],
                        },
                    } ## hybrids
                }, 
                "2" : {
                    "lpGBT" : "lpGBT_v1_PS.txt",
                    "hybrids" : {
                        "0" : {
#                            "strips" : [0],
#                            "pixels" : [8],
                            "edgeSelect" : 1,
                            "strips" : [0, 1, 2, 3, 4, 5, 6, 7],
                            "pixels" : [8, 9, 10, 11, 12, 13, 14, 15],
                        },
                        "1" : {
#			     "strips" : [0]
                            "edgeSelect" : 0,
                            "strips" : [0, 1, 2, 3, 4, 5, 6, 7],
                            "pixels" : [8, 9, 10, 11, 12, 13, 14, 15],
                        },
                    } ## hybrids
                }, 
            }## optical groups
        },
    }
}


### Configuration step-by-step ###
#
#config = {
#    "boards" : {}
#    "commonSettings" : "pippo",
#}

#config["boards"][0] = {
#    "ip" : "192.168.1.83:50001",
#    "opticalGroups" : {}
#}

#config["boards"][0]["opticalGroups"][0] = {
#"lpGBT" : "lpGBT_v0.txt",
#"hybrids" : {}
#}

#config["boards"][0]["opticalGroups"][0]["hybrids"][0] = {
#    "strips" : [2, 3, 4],
#    "pixels" : [8],
#}

#config["boards"][0]["opticalGroups"][0]["hybrids"][1] = {
#    "strips" : [2, 3, 4],
#    "pixels" : [8],
#}
