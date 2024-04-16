export VERSION="v4-23"
docker login gitlab-registry.cern.ch
docker build -t gitlab-registry.cern.ch/cms-pisa/pisatracker/pisa_module_test:ph2_acf_$VERSION --build-arg "VERSION=$VERSION" .
docker login
docker push gitlab-registry.cern.ch/cms-pisa/pisatracker/pisa_module_test:ph2_acf_$VERSION
