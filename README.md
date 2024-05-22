# batch_ppp

## Download rtklib explorer
git clone https://github.com/rtklibexplorer/RTKLIB.git  
cd RTKLIB/app/consapp/rnx2rtkp/gcc  
make  
cd ../../../../..  
cp RTKLIB/app/consapp/rnx2rtkp/gcc/rnx2rtkp ./  

## Configure the markdown
config.yml  

## Configure the templates
templates/rtklib_template_brdc.conf  

## Run
python ppp_batch.py -c config.yml  
