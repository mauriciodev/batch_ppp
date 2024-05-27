# batch_ppp
This repository allows the use of RTKLIB fork from [rtklibexplorer](https://github.com/rtklibexplorer/RTKLIB) to perform Precise Point Positioning

## Usage
# Docker
We provide a Dockerfile (available in rtklib_docker folder) for those who want to build a docker image.
# Building the Dockerfile
docker build rtklib_docker

# Checking the docker image
docker images

# Running the image with the data folder as volume to check the installation
docker run -v ${PWD}/data:/data rtklib:demo5 --help

## Locally
# Download and install rtklib explorer
git clone https://github.com/rtklibexplorer/RTKLIB.git  
cd RTKLIB/app/consapp/rnx2rtkp/gcc  
make  
cd ../../../../..  
cp RTKLIB/app/consapp/rnx2rtkp/gcc/rnx2rtkp ./

# Checking the installation
./rnx2rtkp --help

## Configuration YAML file
config.yml  

## Configure the templates
templates/rtklib_template_brdc.conf  

## Run
python ppp_batch.py -c config.yml  
