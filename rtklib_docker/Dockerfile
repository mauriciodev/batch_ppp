# Using the latest Ubuntu as base
FROM ubuntu:latest
# Updating apt
RUN apt-get update
# Installing base packages
RUN apt-get install -y --no-install-recommends apt-utils build-essential sudo git gfortran ca-certificates
# Updating ca certificates do avoid SSL issues
RUN update-ca-certificates
# Cloning rtkexplorer's RTKLIB
RUN git clone https://github.com/rtklibexplorer/RTKLIB.git
# Defining the working directory to allow the image to build rtklib
WORKDIR /RTKLIB/app/consapp/rnx2rtkp/gcc/
# Building rtklib
RUN make -j4
# Defining the command that will be executed when running the images
ENTRYPOINT ["./rnx2rtkp"]
