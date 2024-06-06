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
    def __init__(self, config, update_pos=False) -> None:
        self.config = config
        self.update_pos = update_pos

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
    
    def temporaryConf(self, replaceDict:dict, temporaryFile:str, templateFile:str='data/templates/rtklib_template_brdc.conf') -> None:
        with open(templateFile, 'r') as template:
            template_text=template.read()
            for key, value in replaceDict.items():
                template_text=template_text.replace(key, str(value))
            with open(temporaryFile, 'w') as tempConf:
                tempConf.write(template_text)

    def run_rt_ppp(self, ppp_executable:str, obsFile:str, outFile:str, template_conf:str, temporary_conf:str, replaceDict:dict, cwd:str='.', move_to='.'):
        out_file = obsFile.split('.')[0]+'.pos'#'temp.obs'
        move_file = os.path.join(move_to, os.path.split(out_file)[-1])
        #rtkcmd=f'./rnx2rtkp -x 2 -y 0 -k temporary.conf -o {outFile} {obsFile} {navFile} {navFile2}'
        if not os.path.exists(outFile) or (self.update_pos==True):
            self.temporaryConf(replaceDict, temporary_conf, template_conf)
            cmd = f"{ppp_executable} {obsFile} {temporary_conf}"
            #obsFile = rinex_with_gps_only(obsFile) #cleaning to leave only GPS data
            print(f"Running {cmd}")
            result = subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=cwd)
            os.rename('output/RT_PPP.out', outFile)
        if os.path.exists(out_file): 
            if os.path.exists(move_file): os.unlink(move_file)
            shutil.move(out_file, move_to)
        df = pd.read_csv(outFile, comment='%', sep='\s+', parse_dates=True, header='infer')
        pos = df[['X(m)', 'Y(m)', 'Z(m)']].to_numpy().mean(axis=0) #.mean(axis=0)
        return pos

    def run_rtklib(self, ppp_executable:str, obsFile:str, navFile:str, template_conf:str, temporary_conf:str, replaceDict:dict, cwd:str='.', groups_per_file:int=12, move_to='.'):
        out_file = obsFile.split('.')[0]+'.pos'#'temp.obs'
        move_file = os.path.join(move_to, os.path.split(out_file)[-1])
        if not os.path.exists(move_file) or (self.update_pos==True):
            self.temporaryConf(replaceDict, temporary_conf, template_conf)
            cmd = f'{ppp_executable} -x 2 -y 0 -k {temporary_conf} -o {move_file} {obsFile} {navFile}'
            print(f"Running {cmd}")
            result = subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=cwd)
        if not os.path.exists(move_file):
            #return np.array([np.nan, np.nan, np.nan])
            return None #np.repeat([[np.nan, np.nan, np.nan]], axis=0, repeats=groups_per_file)

        header = ['date', 'GPST', 'X(m)', 'Y(m)', 'Z(m)' , 'Q', 'ns', 'sdx(m)', 'sdy(m)', 'sdz(m)', 'sdxy(m)', 'sdyz(m)', 'sdzx(m)', 'age(s)', 'ratio']
        df = pd.read_csv(move_file, comment='%', sep='\s+',  names=header)#header='infer') parse_dates=['date'],
        df['datetime'] = pd.to_datetime(df['date'].astype(str)+' '+df['GPST'].astype(str), format='%Y/%m/%d %H:%M:%S.%f')
        #df_grouped = df.groupby([pd.Grouper(key='GPST', freq='2H')])
        
        #pos = df_grouped.mean(['X(m)', 'Y(m)', 'Z(m)'])[['X(m)', 'Y(m)', 'Z(m)']].to_numpy() #.mean(axis=0)
        #pos = df[['x-ecef(m)', 'y-ecef(m)', 'z-ecef(m)']].to_numpy().mean(axis=0) #.mean(axis=0)
        return  df[['datetime','X(m)', 'Y(m)', 'Z(m)']]

    def absError(self, m):
        return np.sqrt(np.sum(np.array(m)**2,axis=1))
    
    def get_dates(self) -> tuple[pd.Timestamp, pd.Timestamp]:
        start_date = self.config['start_date']
        end_date = self.config['end_date']

        # Defining dates for Jan, 1st and Dec, 31st
        d0=pd.to_datetime(start_date) #date(year=start_year, month=1, day=1)
        d1=pd.to_datetime(end_date) #date(year=end_year, month=12, day=31)

        return d0, d1
    
    def test_executable(self, ppp_executable):
        # Checking if the executable is available
        test_run = subprocess.run(ppp_executable, shell=True)
        if test_run.returncode==127:
            print(f"Could not find a PPP executable in {ppp_executable}.")
            sys.exit(0)
        else:
            print(f"Using PPP executable: {ppp_executable}.")

    def main(self):
        # Getting configs from the yaml file
        experiment_name = self.config['experiment_name']
        run_folder = self.config['run_folder']
        if self.config['ppp_solution'] =='rt_ppp':
            run_ppp_method = self.run_rt_ppp #this is a function
        elif self.config['ppp_solution'] == 'rtklib':
            run_ppp_method = self.run_rtklib #this is a function
        ppp_executable = self.config['ppp_executable']
        template_conf = self.config['ppp_template_conf']
        temporary_conf = os.path.join(run_folder,'temporary.inp')
        station = self.config['station']
        reference_position = self.config['reference_position']
        save_array_as = self.config['save_array_as']
        ionex_pattern = self.config['ionex_pattern']
        ionex_folder = self.config['ionex_pattern']
        
        # Getting dates
        d0, d1 = self.get_dates()

        # Station folder
        station_folder = os.path.join(run_folder, station)

        # Experiment folder
        experiment_folder = os.path.join(run_folder, experiment_name)

        # Checking if the executable is available
        self.test_executable(ppp_executable)

        error=[]

        # Output folder
        output_folder = os.path.join(experiment_folder, 'output')

        for day in tqdm(pd.date_range(d0,d1,freq='D')):
            os.makedirs(output_folder, exist_ok=True)
            #day=pd.to_datetime(d0)+pd.Timedelta('117D')
            year=str(day.year)
            year_folder = os.path.join(station_folder, year)
            fname=f'{station}{day.day_of_year:03}1.zip'

            # Checking if the file exists
            if not os.path.exists(os.path.join(year_folder, fname)):
                #error.append([np.nan,np.nan,np.nan])
                print(day,day.day_of_year)
                continue

            # Trying to unzip it
            try:
                archive_path = os.path.join(year_folder, fname)
                shutil.unpack_archive(archive_path, year_folder)
            except Exception as e:
                print(f"Error unpacking archive {archive_path}: {e}")
                #error.append([np.nan,np.nan,np.nan])
                print(day,day.day_of_year)
                continue

            y2d=day.year%100
            outFilePos=os.path.join(year_folder, f'{fname.replace(".zip",".pos")}')
            obsFile=os.path.join(year_folder, fname.replace(".zip",f".{y2d}o"))
            navFile=os.path.join(year_folder, fname.replace(".zip",f".{y2d}n"))
            navFile2=os.path.join(year_folder, fname.replace(".zip",f".{y2d}g"))
            ionex=os.path.join(config['ionex_folder'], config['ionex_pattern'].format(doy=day.day_of_year, y2d=day.year%100))#f"ionex/codg{day.day_of_year:03}0.{day.year%100}i"
            replaceDict = {
                '{ionex}': ionex,
                '{x0}' : reference_position[0],
                '{y0}' : reference_position[1],
                '{z0}' : reference_position[2],
                }

            position = run_ppp_method(ppp_executable, obsFile, navFile, template_conf, temporary_conf, replaceDict = replaceDict, move_to=output_folder)
            if not position is None:
                error.append(position)  #- reference_position

        #error = np.array(error)
        final_df = pd.concat(error).set_index('datetime')
        final_df['X(m)']-=reference_position[0]
        final_df['Y(m)']-=reference_position[1]
        final_df['Z(m)']-=reference_position[2]
        final_df.to_parquet(save_array_as)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c' '-config',  type=argparse.FileType('r'), default='configurations/experiment.yml')
    parsed_args = parser.parse_args()

    config = yaml.safe_load(parsed_args.c_config)

    ppp_processor = PPPBatchProcessor(config, update_pos=False)
    ppp_processor.main()
