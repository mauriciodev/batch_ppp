# batch_ppp
This repository allows the use of RTKLIB fork from [rtklibexplorer](https://github.com/rtklibexplorer/RTKLIB) to perform Precise Point Positioning

# Usage
## Docker
We provide a Dockerfile (available in rtklib_docker folder) for those who want to build a docker image.
### Building the Dockerfile
docker build rtklib_docker -t rtklib:demo5

### Checking the docker image
docker images


### Running the image with the data folder as volume to check the installation (first run only)
docker run -d -it -v ${PWD}/data:/data --name rtklib rtklib:demo5


### Running the container already created
docker start rtklib

### Testing if the daemon is reponding
docker exec rtklib /rnx2rtkp --help

## Locally
### Download and install rtklib explorer
git clone https://github.com/rtklibexplorer/RTKLIB.git  
cd RTKLIB/app/consapp/rnx2rtkp/gcc  
make  
cd ../../../../..  
cp RTKLIB/app/consapp/rnx2rtkp/gcc/rnx2rtkp ./

### Checking the installation
./rnx2rtkp --help

# Configuration YAML file
config.yml  

# Configure the templates
templates/rtklib_template_brdc.conf  

# Run
docker start rtklib
python3 ppp_processor/ppp_batch_processor.py -c configurations/spp_rtklib_ionex.yml  
python3 ppp_processor/ppp_batch_processor.py -c configurations/spp_rtklib_c1pg.yml  
python3 ppp_processor/ppp_batch_processor.py -c configurations/spp_rtklib_brdc.yml  

