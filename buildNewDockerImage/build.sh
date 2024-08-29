export VERSION="v5-03"
echo "IMPORTANT: you should use real Docker (not podman) to build the image"
docker login gitlab-registry.cern.ch
#skopeo copy docker://gitlab-registry.cern.ch/cms_tk_ph2/docker_exploration/cmstkph2_user_al9:ph2_acf_${VERSION} dir:local-oci-image_${VERSION}
docker build -t gitlab-registry.cern.ch/cms-pisa/pisatracker/pisa_module_test:ph2_acf_${VERSION} --build-arg "VERSION=${VERSION}" .
docker login
docker push gitlab-registry.cern.ch/cms-pisa/pisatracker/pisa_module_test:ph2_acf_${VERSION}
