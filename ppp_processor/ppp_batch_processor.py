import os
import sys
import subprocess
import shutil
from datetime import date
import urllib.request
from pathlib import Path
import argparse
import stat
import re

from tqdm import tqdm
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yaml

class PPPBatchProcessor():
    def __init__(self, config) -> None:
        self.config = config

    #This method is not really used, but it can be used to clean GNSS data.
    def rinex_with_gps_only(self, rinexFile:str):
        if not os.path.exists("Binary/teqc"):
            urllib.request.urlretrieve("https://www.unavco.org/software/data-processing/teqc/development/teqc_CentOSLx86_64s.zip", "Binary/teqc.zip")
            shutil.unpack_archive("Binary/teqc.zip", extract_dir='Binary')
            f = Path("Binary/teqc")
            f.chmod(f.stat().st_mode | stat.S_IEXEC) #change permission to run the file]
        newFile=rinexFile.replace(".", "-new.")
        #./teqc -E -C -R -S -O.obs L1L2C1P2S1S2 +out $newFile $rnx2file 
        subprocess.run(f'Binary/teqc -E -C -R -S -O.obs L1L2C1P2S1S2 +out {newFile} {rinexFile}', shell=True)
        return newFile
    
    def temporaryConf(self, replaceDict:dict, templateFile:str="template.conf", temporaryFile:str="temporary.conf"):
        with open(templateFile, 'r') as template:
            template_text=template.read()
            for key, value in replaceDict.items():
                template_text=template_text.replace(key, str(value))
            with open(temporaryFile, 'w') as tempConf:
                tempConf.write(template_text)

    def downloadIonex(self, doy:int, year:int) -> str:
        baseurl=f"ftp://igs.ign.fr/pub/igs/products/ionosphere/{year}/{doy:03}/codg{doy:03}0.{year%100}i.Z"
        os.makedirs("ionex",exist_ok=True)
        local_filename = os.path.join("ionex",baseurl.split('/')[-1])
        dcb_file=local_filename.replace('.Z','')
        if not os.path.exists(dcb_file):
            print("Downloading ", baseurl, dcb_file)
            #urllib.request.urlretrieve(baseurl, local_filename)
            #get_ipython().system('wget $baseurl -O $local_filename')
            print("Saved ",local_filename)
            if os.path.getsize(local_filename) == 0:
                print("Trying to get rapid, because final ionex was not found.")
                baseurl=baseurl.replace("codg","corg")
                #get_ipython().system('wget $baseurl -O $local_filename')
            #get_ipython().system('gunzip $local_filename -f')
        return local_filename
    
    def run_rt_ppp(self, ppp_executable:str, obsFile:str, outFile:str, template_conf:str, replaceDict:dict, cwd:str='.'):
        #rtkcmd=f'./rnx2rtkp -x 2 -y 0 -k temporary.conf -o {outFile} {obsFile} {navFile} {navFile2}'
        if not os.path.exists(outFile):
            self.temporaryConf(replaceDict, template_conf, 'temporary.inp')
            cmd = f"{ppp_executable} {obsFile} temporary.inp"
            #obsFile = rinex_with_gps_only(obsFile) #cleaning to leave only GPS data
            print(f"Running {cmd}")
            result=subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=cwd)
            os.rename('output/RT_PPP.out', outFile)
        df = pd.read_csv(outFile, comment='%', sep='\s+', parse_dates=True, header='infer')
        pos = df[['X(m)', 'Y(m)', 'Z(m)']].mean(axis=0).to_numpy()
        return pos

    def run_rtklib(self, ppp_executable:str, obsFile:str, navFile:str, template_conf:str, replaceDict:dict, cwd:str='.'):
        out_file = obsFile.split('.')[0]+'.rtklib'#'temp.obs'
        if not os.path.exists(out_file):
            self.temporaryConf(replaceDict, template_conf, 'temporary.inp')
            cmd=f'{ppp_executable} -x 2 -y 0 -k temporary.inp -o {out_file} {obsFile} {navFile}'
            print(f"Running {cmd}")
            result=subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=cwd)
        if not os.path.exists(out_file):
            return np.array([np.nan, np.nan, np.nan])
        header = ['GPST', 'x-ecef(m)', 'y-ecef(m)', 'z-ecef(m)', 'Q', 'ns', 'sdx(m)', 'sdy(m)', 'sdz(m)', 'sdxy(m)', 'sdyz(m)', 'sdzx(m)', 'age(s)', 'ratio']
        df = pd.read_csv(out_file, comment='%', sep='\s+', parse_dates=True, names=header)#header='infer')
        pos = df[['x-ecef(m)', 'y-ecef(m)', 'z-ecef(m)']].mean(axis=0).to_numpy()
        return pos

    def absError(self, m):
        return np.sqrt(np.sum(np.array(m)**2,axis=1))

    def main(self):
        # Getting configs from the yaml file
        if self.config['ppp_solution'] =='rt_ppp':
            run_ppp_method = self.run_rt_ppp #this is a function
        elif config['ppp_solution'] == 'rtklib':
            run_ppp_method = self.run_rtklib #this is a function
        ppp_executable = config['ppp_executable']
        run_folder = config['run_folder']
        template_conf = config['ppp_template_conf']
        save_array_as = os.path.join(run_folder, config['experiment_name'])
        end_year = config['end_year']
        start_year = config['start_year']
        station = config['station']
        
        d0=date(year=start_year, month=1, day=1)
        d1=date(year=end_year, month=12, day=31)

        print(f"Downloading data from IBGE for station {station}")
        for day in tqdm(pd.date_range(d0,d1,freq='D')):
            link=f'https://geoftp.ibge.gov.br/informacoes_sobre_posicionamento_geodesico/rbmc/dados/{day.year}/{day.day_of_year:03}/{station}{day.day_of_year:03}1.zip'
            rbmcfile=link.split("/")[-1]
            zipFile=os.path.join(str(day.year),rbmcfile)
            os.makedirs(str(day.year),exist_ok=True)
            if not os.path.exists(zipFile) or os.path.getsize(zipFile)<1024:
                try:
                    urllib.request.urlcleanup()
                    local_filename, headers = urllib.request.urlretrieve(link, zipFile)
                    if os.path.getsize(zipFile)<1024: os.unlink(zipFile)
                except urllib.error.URLError as e:
                    print(f"Failed {zipFile} from {link}")
                    print(f"Error: {e.reason}")
                    if os.path.exists(zipFile):
                        os.unlink(zipFile)
            else:
                print(f"skipping {zipFile}")

        if not os.path.exists(run_folder): os.makedirs(run_folder, exist_ok=True)
        print(f"Running in {run_folder}")

        test_run = subprocess.run(ppp_executable, shell=True)
        if test_run.returncode==127:
            print(f"Could not find PPP executable in {ppp_executable}.")
            sys.exit(0)
        else:
            print(f"Using PPP executable: {ppp_executable}.")

        error=[]

        #basecommand="./rnx2rtkp -x 0 -y 0 -k "

        for day in tqdm(pd.date_range(d0,d1,freq='D')):
            os.makedirs('output',exist_ok=True)
            #day=pd.to_datetime(d0)+pd.Timedelta('117D')
            year=str(day.year)
            fname=f'{station}{day.day_of_year:03}1.zip'
            if not os.path.exists(os.path.join(year,fname)):
                error.append([0,0,0])
                print(day,day.day_of_year)
                continue
            #downloadIonex(day.day_of_year,day.year)

            y2d=day.year%100
            outFilePos=os.path.join('output',f'{year}_{fname.replace(".zip",".pos")}')
            obsFile=os.path.join('current',fname.replace(".zip",f".{y2d}o"))
            navFile=os.path.join('current',fname.replace(".zip",f".{y2d}n"))
            navFile2=os.path.join('current',fname.replace(".zip",f".{y2d}g"))
            ionex=f"ionex/codg{day.day_of_year:03}0.{day.year%100}i"


            shutil.unpack_archive(os.path.join(year,fname), 'current')

            replaceDict = {
                '{ionex}': ionex,
                '{x0}' : config["reference_position"][0],
                '{y0}' : config["reference_position"][1],
                '{z0}' : config["reference_position"][2],
                }

            position = run_ppp_method(ppp_executable, obsFile, navFile, template_conf, replaceDict = replaceDict)
            error.append(position - config["reference_position"])

        error = np.array(error)
        np.save(save_array_as,error)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()

    parser.add_argument('-c' '-config',  type=argparse.FileType('r'), default='config.yml')
    parsed_args = parser.parse_args()
    config = yaml.safe_load(parsed_args.c_config)

    ppp_processor = PPPBatchProcessor(config)
    ppp_processor.main()