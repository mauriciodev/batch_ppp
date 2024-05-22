#!/usr/bin/env python
# coding: utf-8
import os
import sys
import subprocess
import shutil
from datetime import date
import urllib.request
from pathlib import Path
import argparse
import stat


from tqdm import tqdm
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


#This method is not really used, but it can be used to clean GNSS data.
def rinex_with_gps_only(rinexFile):
    if not os.path.exists("Binary/teqc"):
        urllib.request.urlretrieve("https://www.unavco.org/software/data-processing/teqc/development/teqc_CentOSLx86_64s.zip", "Binary/teqc.zip")
        shutil.unpack_archive("Binary/teqc.zip", extract_dir='Binary')
        f = Path("Binary/teqc")
        f.chmod(f.stat().st_mode | stat.S_IEXEC) #change permission to run the file]
    newFile=rinexFile.replace(".", "-new.")
    #./teqc -E -C -R -S -O.obs L1L2C1P2S1S2 +out $newFile $rnx2file 
    subprocess.run(f'Binary/teqc -E -C -R -S -O.obs L1L2C1P2S1S2 +out {newFile} {rinexFile}', shell=True)
    return newFile
    


def temporaryConf(replaceDict, templateFile="template.conf", temporaryFile="temporary.conf"):
    with open(templateFile, 'r') as template:
        template_text=template.read()
        for key, value in replaceDict.items():
            template_text=template_text.replace(key, str(value))
        with open(temporaryFile, 'w') as tempConf:
            tempConf.write(template_text)
            
def downloadIonex(doy,year):
    baseurl=f"ftp://igs.ign.fr/pub/igs/products/ionosphere/{year}/{doy:03}/codg{doy:03}0.{year%100}i.Z"
    os.makedirs("ionex",exist_ok=True)
    local_filename = os.path.join("ionex",baseurl.split('/')[-1])
    dcb_file=local_filename.replace('.Z','')
    if not os.path.exists(dcb_file):
        print("Downloading ", baseurl, dcb_file)
        #urllib.request.urlretrieve(baseurl, local_filename)
        get_ipython().system('wget $baseurl -O $local_filename')
        print("Saved ",local_filename)
        if os.path.getsize(local_filename) == 0:
            print("Trying to get rapid, because final ionex was not found.")
            baseurl=baseurl.replace("codg","corg")
            get_ipython().system('wget $baseurl -O $local_filename')
        get_ipython().system('gunzip $local_filename -f')
    return local_filename

def run_rt_ppp(obsFile, outFile, template_conf, replaceDict):
    #rtkcmd=f'./rnx2rtkp -x 2 -y 0 -k temporary.conf -o {outFile} {obsFile} {navFile} {navFile2}'
    if not os.path.exists(outFile):
        temporaryConf(replaceDict, template_conf, 'temporary.inp')
        cmd = f"{ppp_executable} {obsFile} temporary.inp"
        #obsFile = rinex_with_gps_only(obsFile) #cleaning to leave only GPS data
        print(f"Running {cmd}")
        result=subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.rename('output/RT_PPP.out', outFile)
    df = pd.read_csv(outFile, comment='%', delim_whitespace=True, parse_dates=True, header='infer')
    pos = df[['X(m)', 'Y(m)', 'Z(m)']].mean(axis=0).to_numpy()
    return pos

def run_rtklib(obsFile, outFile, template_conf, replaceDict):
    if not os.path.exists(outFile):
        temporaryConf(replaceDict, template_conf, 'temporary.inp')
        cmd=f'./rnx2rtkp -x 2 -y 0 -k temporary.inp -o {outFile} {obsFile} {navFile} {navFile2}'
        print(f"Running {cmd}")
        result=subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.rename('output/RT_PPP.out', outFile)
    df = pd.read_csv(outFile, comment='%', delim_whitespace=True, parse_dates=True, header='infer')
    pos = df[['X(m)', 'Y(m)', 'Z(m)']].mean(axis=0).to_numpy()
    return pos

def absError(m):
    return np.sqrt(np.sum(np.array(m)**2,axis=1))

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('config',  type=argparse.FileType('r'), default='config.yml')

    #CONFIGURATION
    ppp_solution = 'rtklib' # either 'rt_ppp' or 'rtklib'
    if ppp_solution =='rt_ppp':
        ppp_executable = "./rt_ppp" #In windows: ..\rt_ppp.exe
        run_folder = './rt_ppp'
        template_conf = 'batch_run/template.conf'
    if ppp_solution == 'rtklib':
        ppp_executable = "./rt_ppp" #In windows: ..\rt_ppp.exe
        run_folder = './rt_ppp'
        template_conf = 'batch_run/template.conf'
    end_year = 2015
    start_year = 2015
    station = "onrj"
    basePos = [4283638.3610, -4026028.8230, -2466096.8370]
    
    d0=date(year=start_year, month=1, day=1)
    d1=date(year=end_year, month=12, day=31)

    print(f"Downloading data from IBGE for station {station}")
    for day in tqdm(pd.date_range(d0,d1,freq='D')):
        link="""https://geoftp.ibge.gov.br/informacoes_sobre_posicionamento_geodesico/rbmc/dados/{2}/{0:03}/{1}{0:03}1.zip""".format(day.day_of_year,station,day.year)
        rbmcfile=link.split("/")[-1]
        zipFile=os.path.join(str(day.year),rbmcfile)
        os.makedirs(str(day.year),exist_ok=True)
        if not os.path.exists(zipFile) or os.path.getsize(zipFile)<1024:
            try:
                urllib.request.urlcleanup()
                local_filename, headers = urllib.request.urlretrieve(link, zipFile)
                if os.path.getsize(zipFile)<1024: os.unlink(zipFile)
            except urllib.error.URLError as e:
                print(f"Failed {zipFile}. {link}")
                print("Error", e.reason)
                if os.path.exists(zipFile):
                    os.unlink(zipFile)
        else:
            print(f"skipping {zipFile}")


    os.chdir(run_folder)
    print(os.getcwd())

    if not os.path.exists(ppp_executable):
        print(f"Could not find RT_PPP in {ppp_executable}. Did you compile it?")
        sys.exit(0)
    else:
        print(f"Using RT_PPP in {ppp_executable}.")

    codgError=[]
    c1pgError=[]
    brdcError=[]
    predError=[]

    #basecommand="./rnx2rtkp -x 0 -y 0 -k "
    basecommand=ppp_executable

    for day in tqdm(pd.date_range(d0,d1,freq='D')):
        os.makedirs('output',exist_ok=True)
        #day=pd.to_datetime(d0)+pd.Timedelta('117D')
        year=str(day.year)
        fname=f'{station}{day.day_of_year:03}1.zip'
        if not os.path.exists(os.path.join(year,fname)):
            codgError.append([0,0,0])
            brdcError.append([0,0,0])
            print(day,day.day_of_year)
            continue
        #downloadIonex(day.day_of_year,day.year)

        y2d=day.year%100
        outFileIonex=os.path.join('output',f'ionex_{year}_{fname.replace(".zip",".pos")}')
        outFileBrdc=os.path.join('output',f'brdc_{year}_{fname.replace(".zip",".pos")}')
        outFilePred=os.path.join('output',f'pred_{year}_{fname.replace(".zip",".pos")}')
        obsFile=os.path.join('current',fname.replace(".zip",f".{y2d}o"))
        navFile=os.path.join('current',fname.replace(".zip",f".{y2d}n"))
        navFile2=os.path.join('current',fname.replace(".zip",f".{y2d}g"))
        ionex=f"ionex/codg{day.day_of_year:03}0.{day.year%100}i"


        shutil.unpack_archive(os.path.join(year,fname), 'current')

        replaceDict = {
            '{ionex}': ionex,
            '{x0}' : basePos[0],
            '{y0}' : basePos[1],
            '{z0}' : basePos[2],
            }

        position = run_rt_ppp(obsFile, outFileBrdc, 'batch_run/template_brdc.conf', replaceDict = replaceDict)

        brdcError.append(position - basePos)

        position = run_rt_ppp(obsFile, outFileIonex, 'batch_run/template_ionex.conf', replaceDict = replaceDict)
        codgError.append(position - basePos)

        #position = run_rt_ppp(obsFile, outFilePred, 'batch_run/template_ionex.conf', replaceDict = replaceDict)
        #predError.append(np.linalg.norm(position - basePos))


    codgError = np.array(codgError)
    brdcError = np.array(brdcError)





    df = pd.DataFrame()
    df['date'] = pd.date_range(d0,d1,freq='D')
    df['CODG_ex'] = codgError[:,0]
    df['CODG_ey'] = codgError[:,1]
    df['CODG_ez'] = codgError[:,2]
    df['CODG_norm'] = np.linalg.norm(codgError,axis=1)
    df['Klobuchar_ex'] = brdcError[:,0]
    df['Klobuchar_ey'] = brdcError[:,1]
    df['Klobuchar_ez'] = brdcError[:,2]
    df['Klobuchar_norm'] = np.linalg.norm(brdcError,axis=1)
    csvFileName = f'output/data_{d0}_to_{d1}.csv'
    print(f"Saving the errors to {csvFileName}")
    df.to_csv(csvFileName)
    df.plot(x='date', y=['CODG_ex', 'CODG_ey', 'CODG_ez'], figsize=(10, 10))
    df.plot(x='date', y=['Klobuchar_ex', 'Klobuchar_ey', 'Klobuchar_ez'], figsize=(10, 10))
    df.plot(x='date', y=['CODG_norm', 'Klobuchar_norm'], figsize=(10, 10))




    pos_mean = [df['X(m)'].mean(), df['Y(m)'].mean(), df['Z(m)'].mean()]

    df['err_X'] = df['X(m)']-df['X(m)'].mean()
    df['err_Y'] = df['Y(m)']-df['Y(m)'].mean()
    df['err_Z'] = df['Z(m)']-df['Z(m)'].mean()

    df['err_norm'] = np.linalg.norm(df[['err_X', 'err_Y', 'err_Z']],axis=1)


    df.plot(x='GPS_TIME', y = ['err_X', 'err_Y', 'err_Z', 'err_norm'])

    df.plot(x='GPS_TIME', y = 'err_norm')

if __name__ == "__main__":
    main()
