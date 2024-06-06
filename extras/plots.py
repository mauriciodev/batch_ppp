import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import yaml


def plot(file_list, label_list, fname="plot.png", frequency="1D"):  # 2H
    fig, axs = plt.subplots(4)
    # fig.suptitle('Vertically stacked subplots')
    for ax in axs:
        # ax.grid(True, which='both')
        ax.axhline(y=0, color="k")
    for file_name, label in zip(file_list, label_list):
        if not os.path.exists(file_name):
            print(f"Could not find {file_name}. Skipping.")
            continue
        series = pd.read_parquet(file_name)
        series = series.resample(frequency).mean()

        axs[0].plot(
            np.linalg.norm(series[["X(m)", "Y(m)", "Z(m)"]].to_numpy(), axis=-1),
            label=label,
            marker=".",
        )
        axs[1].plot(series["X(m)"], label=label, marker=".")
        axs[2].plot(series["Y(m)"], label=label, marker=".")
        axs[3].plot(series["Z(m)"], label=label, marker=".")

    axs[0].set(ylabel="Norm deviation")
    axs[1].set(ylabel="X deviation")
    axs[2].set(ylabel="Y deviation")
    axs[3].set(ylabel="Z deviation")
    plt.legend(loc="lower center", ncol=len(file_list), bbox_to_anchor=(0.5, -1))
    plt.tight_layout()

    plt.savefig(fname)
    print(f"File {fname} saved.")
    plt.close()


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()

    # parser.add_argument('-c' '-config',  type=argparse.FileType('r'), default='config.yml')
    # parsed_args = parser.parse_args()
    # config = yaml.safe_load(parsed_args.c_config)
    plot(
        [
            "data/rtklib_brdc/onrj.parquet",
            "data/spp_rtklib_ionex/onrj.parquet",
            "data/spp_rtklib_c1pg/onrj.parquet",
        ],
        ["rtklib_brdc", "spp_rtklib_ionex", "spp_rtklib_c1pg"],
        "plot_igs.pdf",
        frequency="2H",
    )
    plot(
        [
            "data/spp_rtklib_c1pg/onrj.parquet",
            "data/unet/onrj.parquet",
            "data/spp_rtklib_ionex/onrj.parquet",
        ],
        [
            "spp_rtklib_c1pg",
            "spp_rtklib_unet",
            "spp_rtklib_ionex",
        ],
        "plot_unet.pdf",
    )
    """plot([
      'data/spp_rtklib_ionex/onrj.parquet',
      'data/spp_rtklib_c1pg/onrj.parquet',
      'data/spp_rtklib_simvp/onrj.parquet',
      ],[
      'spp_rtklib_ionex',
      'spp_rtklib_c1pg',
      'spp_rtklib_simvp',
     ], 'plot_simvp.pdf')"""
    plot(
        [
            #'data/rtklib_brdc/onrj.parquet',
            "data/spp_rtklib_c1pg/onrj.parquet",
            "data/edconvlstm_nd/onrj.parquet",
            "data/spp_rtklib_ionex/onrj.parquet",
            #'data/spp_rtklib_c1pg/onrj.parquet',
        ],
        [
            #'brdc',
            "spp_rtklib_c1pg",
            "spp_rtklib_edconvlstm_nd",
            "spp_rtklib_ionex",
        ],
        "plot_nd.pdf",
    )
