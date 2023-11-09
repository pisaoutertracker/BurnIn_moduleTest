### Configuration one-shot ###
config = {
    "commonSettings" : "pippo",
    "boards" : {
#        0: {
#            "ip" : "fc7ot3:50001",
#            "opticalGroups" : {
#                0 : {
#                    "lpGBT" : "lpGBT_v0.txt",
#                    "hybrids" : {
#                        0 : {
#                            "strips" : [0],
##                            "strips" : [2, 3, 4],
##                            "pixels" : [8],
#                        },
##                        1 : {
##                            "strips" : [2, 3, 4],
##                            "pixels" : [8],
##                        },
#                    } ## hybrids
#                }, 
#            }## optical groups
#        },
        0: {
            "ip" : "fc7ot2:50001",
            "opticalGroups" : {
                0 : {
                    "lpGBT" : "lpGBT_v1.txt",
                    "hybrids" : {
                        0 : {
                            "strips" : [0],
#                            "strips" : [2, 3, 4],
                            "pixels" : [8],
                        },
                        1 : {
                            "strips" : [4],
#                            "pixels" : [8],
                        },
                    } ## hybrids
                }, 
                1 : {
                    "lpGBT" : "lpGBT_v0.txt",
                    "hybrids" : {
                        0 : {
                            "strips" : [0,2],
#                            "strips" : [2, 3, 4],
#                            "pixels" : [8],
                        },
                        1 : {
                            "strips" : [3],
                            "pixels" : [8],
                        },
                    } ## hybrids
                }, 
                2 : {
                    "lpGBT" : "lpGBT_v0.txt",
                    "hybrids" : {
                        0 : {
                            "strips" : [0,3],
#                            "strips" : [2, 3, 4],
#                            "pixels" : [8],
                        },
                        1 : {
                            "strips" : [1],
                            "pixels" : [9],
                        },
                    } ## hybrids
                }, 
            }## optical groups
        },
    } # boards
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
