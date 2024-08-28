ARG VERSION
#FROM gitlab-registry.cern.ch/cms_tk_ph2/docker_exploration/cmstkph2_user_c7:ph2_acf_${VERSION} ## for old version (<5)
FROM gitlab-registry.cern.ch/cms_tk_ph2/docker_exploration/cmstkph2_user_al9:ph2_acf_${VERSION}
RUN yum install -y  python3-lxml
RUN pip3 install requests xmltodict webdav bs4 PySide2
WORKDIR /home/cmsTkUser/Ph2_ACF/
RUN source /home/cmsTkUser/Ph2_ACF/setup.sh
WORKDIR /home/cmsTkUser/Ph2_ACF/build
RUN source /home/cmsTkUser/Ph2_ACF/setup.sh && cmake ..
RUN source /home/cmsTkUser/Ph2_ACF/setup.sh && make -j8 

