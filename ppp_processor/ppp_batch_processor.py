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
import yaml
import pymap3d as pm
import hydra
from omegaconf import DictConfig, OmegaConf

@hydra.main(
    version_base=None, config_path="../configurations", config_name="default_process"
)
def main(cfg: DictConfig):
    OmegaConf.to_yaml(cfg)
    ppp_processor = PPPBatchProcessor(config=cfg)
    ppp_processor.main()


class PPPBatchProcessor:

    def __init__(self, config) -> None:
        self.config = config
        self.update_pos = config["process"].get("update_pos")

    # This method is not really used, but it can be used to clean GNSS data.
    def rinex_with_gps_only(self, rinexFile: str):
        if not os.path.exists("Binary/teqc"):
            urllib.request.urlretrieve(
                "https://www.unavco.org/software/data-processing/teqc/development/teqc_CentOSLx86_64s.zip",
                "Binary/teqc.zip",
            )
            shutil.unpack_archive("Binary/teqc.zip", extract_dir="Binary")
            f = Path("Binary/teqc")
            f.chmod(
                f.stat().st_mode | stat.S_IEXEC
            )  # change permission to run the file
        newFile = rinexFile.replace(".", "-new.")
        subprocess.run(
            f"Binary/teqc -E -C -R -S -O.obs L1L2C1P2S1S2 +out {newFile} {rinexFile}",
            shell=True,
        )
        return newFile

    def temporaryConf(
        self,
        replaceDict: dict,
        temporaryFile: str,
        templateFile: str = "data/templates/rtklib_template_brdc.conf",
    ) -> None:
        with open(templateFile, "r") as template:
            template_text = template.read()
            for key, value in replaceDict.items():
                template_text = template_text.replace(key, str(value))
            with open(temporaryFile, "w") as tempConf:
                tempConf.write(template_text)

    def run_rt_ppp(
        self,
        ppp_executable: str,
        obsFile: str,
        outFile: str,
        template_conf: str,
        temporary_conf: str,
        replaceDict: dict,
        cwd: str = ".",
        move_to=".",
    ):
        out_file = obsFile.split(".")[0] + ".pos"  #'temp.obs'
        move_file = os.path.join(move_to, os.path.split(out_file)[-1])
        if not os.path.exists(outFile) or (self.update_pos == True):
            self.temporaryConf(replaceDict, temporary_conf, template_conf)
            cmd = f"{ppp_executable} {obsFile} {temporary_conf}"
            print(f"Running {cmd}")
            result = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=cwd,
            )
            os.rename("output/RT_PPP.out", outFile)
        if os.path.exists(out_file):
            if os.path.exists(move_file):
                os.unlink(move_file)
            shutil.move(out_file, move_to)
        df = pd.read_csv(
            outFile, comment="%", sep="\s+", parse_dates=True, header="infer"
        )
        pos = df[["X(m)", "Y(m)", "Z(m)"]].to_numpy().mean(axis=0)
        return pos

    def run_rtklib(
        self,
        ppp_executable: str,
        obsFile: str,
        navFile: str,
        template_conf: str,
        temporary_conf: str,
        replaceDict: dict,
        cwd: str = ".",
        groups_per_file: int = 12,
        move_to=".",
    ):
        out_file = obsFile.split(".")[0] + ".pos"  #'temp.obs'
        move_file = os.path.join(move_to, os.path.split(out_file)[-1])
        if not os.path.exists(move_file) or (self.update_pos == True):
            self.temporaryConf(replaceDict, temporary_conf, template_conf)
            cmd = f"{ppp_executable} -x 2 -y 0 -k {temporary_conf} -o {move_file} {obsFile} {navFile}"
            print(f"Running {cmd}")
            result = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=cwd,
            )
        if not os.path.exists(move_file):
            return None

        header = [
            "date",
            "GPST",
            "X(m)",
            "Y(m)",
            "Z(m)",
            "Q",
            "ns",
            "sdx(m)",
            "sdy(m)",
            "sdz(m)",
            "sdxy(m)",
            "sdyz(m)",
            "sdzx(m)",
            "age(s)",
            "ratio",
        ]
        df = pd.read_csv(move_file, comment="%", sep="\s+", names=header)
        df["datetime"] = pd.to_datetime(
            df["date"].astype(str) + " " + df["GPST"].astype(str),
            format="%Y/%m/%d %H:%M:%S.%f",
        )
        ellipsoid = pm.Ellipsoid.from_name("wgs84")
        baseLLH = pm.ecef2geodetic(
            replaceDict["{x0}"], replaceDict["{y0}"], replaceDict["{z0}"], ellipsoid
        )
        df["X(m)"], df["Y(m)"], df["Z(m)"] = pm.ecef2enu(
            df["X(m)"],
            df["Y(m)"],
            df["Z(m)"],
            baseLLH[0],
            baseLLH[1],
            baseLLH[2],
            ellipsoid,
        )
        return df[["datetime", "X(m)", "Y(m)", "Z(m)", "sdx(m)", "sdy(m)", "sdz(m)"]]

    def absError(self, m):
        return np.sqrt(np.sum(np.array(m) ** 2, axis=1))

    def get_dates(self) -> tuple[pd.Timestamp, pd.Timestamp]:
        start_date = self.config["process"].get("start_date")
        end_date = self.config["process"].get("end_date")

        # Defining dates for Jan, 1st and Dec, 31st
        d0 = pd.to_datetime(start_date)
        d1 = pd.to_datetime(end_date)

        return d0, d1

    def test_executable(self, ppp_executable):
        # Checking if the executable is available
        test_run = subprocess.run(ppp_executable, shell=True)
        if test_run.returncode > 0:
            print(f"Docker error while running {ppp_executable}.")
            print(
                """
                Perharps you forgot running the following steps:
                  1 - docker build rtklib_docker -t rtklib:demo5
                  2 - docker run -d -it -v ${PWD}/data:/data --name rtklib rtklib:demo5
                  3 - docker start rtklib
                """
            )
            sys.exit(0)
        else:
            print(f"Using PPP executable: {ppp_executable}.")

    def main(self):
        # Getting configs from the yaml file
        experiment_name = self.config["process"].get("experiment_name")
        run_folder = self.config["process"].get("run_folder")
        print(run_folder)
        if self.config["process"].get("ppp_solution") == "rt_ppp":
            run_ppp_method = self.run_rt_ppp  # this is a function
        elif self.config["process"].get("ppp_solution") == "rtklib":
            run_ppp_method = self.run_rtklib  # this is a function
        ppp_executable_test = self.config["process"].get("ppp_executable_test")
        ppp_executable = self.config["process"].get("ppp_executable")
        template_conf = self.config["process"].get("ppp_template_conf")
        temporary_conf = os.path.join(run_folder, "temporary.inp")
        station = self.config["process"].get("station")
        reference_position = self.config["process"].get("reference_position")
        save_array_as = self.config["process"].get("save_array_as")
        ionex_pattern = self.config["process"].get("ionex_pattern")
        ionex_folder = self.config["process"].get("ionex_folder")

        # Getting dates
        d0, d1 = self.get_dates()

        # Station folder
        station_folder = os.path.join(run_folder, station)

        # Experiment folder
        experiment_folder = os.path.join(run_folder, experiment_name)

        # Checking if the executable is available
        self.test_executable(ppp_executable_test)

        error = []

        # Output folder
        output_folder = os.path.join(experiment_folder, "output")

        for day in tqdm(pd.date_range(d0, d1, freq="D")):
            os.makedirs(output_folder, exist_ok=True)
            year = str(day.year)
            year_folder = os.path.join(station_folder, year)
            fname = f"{station}{day.day_of_year:03}1.zip"

            # Checking if the file exists
            if not os.path.exists(os.path.join(year_folder, fname)):
                print(day, day.day_of_year)
                continue

            # Trying to unzip it
            try:
                archive_path = os.path.join(year_folder, fname)
                shutil.unpack_archive(archive_path, year_folder)
            except Exception as e:
                print(f"Error unpacking archive {archive_path}: {e}")
                print(day, day.day_of_year)
                continue

            y2d = day.year % 100
            outFilePos = os.path.join(year_folder, f'{fname.replace(".zip",".pos")}')
            obsFile = os.path.join(year_folder, fname.replace(".zip", f".{y2d}o"))
            navFile = os.path.join(year_folder, fname.replace(".zip", f".{y2d}n"))
            navFile2 = os.path.join(year_folder, fname.replace(".zip", f".{y2d}g"))
            ionex = os.path.join(
                ionex_folder,
                ionex_pattern.format(doy=day.day_of_year, y2d=day.year % 100),
            )
            replaceDict = {
                "{ionex}": ionex,
                "{x0}": reference_position[0],
                "{y0}": reference_position[1],
                "{z0}": reference_position[2],
            }

            position = run_ppp_method(
                ppp_executable,
                obsFile,
                navFile,
                template_conf,
                temporary_conf,
                replaceDict=replaceDict,
                move_to=output_folder,
            )
            if not position is None:
                error.append(position)

        final_df = pd.concat(error).set_index("datetime")
        final_df.to_parquet(save_array_as)

if __name__ == "__main__":
    main()
