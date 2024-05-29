from urllib import request, error
import os
import argparse
import yaml
import pandas as pd
from tqdm import tqdm
import subprocess

class Preprocessor():
    def __init__(self, config) -> None:
        self.config = config

    def get_dates(self) -> tuple[pd.Timestamp, pd.Timestamp]:
        start_date = self.config['start_date']
        end_date = self.config['end_date']

        # Defining dates for Jan, 1st and Dec, 31st
        d0=pd.to_datetime(start_date) #date(year=start_year, month=1, day=1)
        d1=pd.to_datetime(end_date) #date(year=end_year, month=12, day=31)

        return d0, d1

    def download_station(self) -> None:
        run_folder = self.config['run_folder']
        station = self.config['station']

        d0, d1 = self.get_dates()

        # Station folder
        station_folder = os.path.join(run_folder, station)

        print(f"Running in {run_folder}...")
        print(f"Downloading data from IBGE for station {station}...")
        for day in tqdm(pd.date_range(d0,d1,freq='D')):
            link=f'https://geoftp.ibge.gov.br/informacoes_sobre_posicionamento_geodesico/rbmc/dados/{day.year}/{day.day_of_year:03}/{station}{day.day_of_year:03}1.zip'
            rbmcfile=link.split("/")[-1]
            year_folder = os.path.join(station_folder, str(day.year))
            zipFile=os.path.join(year_folder, rbmcfile)
            os.makedirs(year_folder, exist_ok=True)
            if not os.path.exists(zipFile) or os.path.getsize(zipFile)<1024:
                try:
                    request.urlcleanup()
                    local_filename, headers = request.urlretrieve(link, zipFile)
                    if os.path.getsize(zipFile)<1024: os.unlink(zipFile)
                except error.URLError as e:
                    print(f"Failed {zipFile} from {link}")
                    print(f"Error: {e.reason}")
                    if os.path.exists(zipFile):
                        os.unlink(zipFile)
            else:
                print(f"skipping {zipFile}")        

    def download_ionex(self, prefix='codg') -> None:
        ionex_folder = self.config['ionex_folder']

        d0, d1 = self.get_dates()

        for day in tqdm(pd.date_range(d0,d1,freq='D')):
            baseurl = f'ftp://igs.ign.fr/pub/igs/products/ionosphere/{day.year}/{day.day_of_year:03}/{prefix}{day.day_of_year:03}0.{day.year%100}i.Z'
            os.makedirs(ionex_folder, exist_ok=True)
            local_filename = os.path.join(ionex_folder, baseurl.split('/')[-1])
            dcb_file = local_filename.replace('.Z','')
            if not os.path.exists(dcb_file):
                print(f'Downloading {baseurl} to {local_filename}')
                request.urlretrieve(baseurl, local_filename)
                print(f'File saved to {local_filename}')
                if os.path.getsize(local_filename) == 0:
                    print('Trying to get rapid, because final ionex was not found.')
                    baseurl=baseurl.replace(prefix,"corg")
                    request.urlretrieve(baseurl, local_filename)

                subprocess.run(f'gunzip {local_filename} -f', shell=True)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c' '-config',  type=argparse.FileType('r'), default='configurations/preprocess.yml')
    parsed_args = parser.parse_args()

    config = yaml.safe_load(parsed_args.c_config)

    preprocessor = Preprocessor(config)
    preprocessor.download_station()
    preprocessor.download_ionex(prefix='codg')
    preprocessor.download_ionex(prefix='c1pg')
