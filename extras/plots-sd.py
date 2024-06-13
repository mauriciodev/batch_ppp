import argparse
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import yaml


def intersect_series(series_path, ref_path=None):
    series = pd.read_parquet(series_path)
    if not ref_path is None:
        ref = pd.read_parquet(ref_path)
        series = series.loc[series.index.intersection(ref.index)]

    return series


def plot(series_list, label_list, fname="plot.png", frequency="1D"):  # 2H
    fig, axs = plt.subplots(3)
    # fig.suptitle('Vertically stacked subplots')
    for ax in axs:
        # ax.grid(True, which='both')
        ax.axhline(y=0, color="k")
    for series, label in zip(series_list, label_list):
        series = series.resample(frequency).mean()

        axs[0].plot(
            series['sdx(m)'], label=label, marker=".", markersize=2, linewidth=0.5
        )
        axs[1].plot(
            series['sdy(m)'], label=label, marker=".", markersize=2, linewidth=0.5
        )
        axs[2].plot(
            series['sdz(m)'], label=label, marker=".", markersize=2, linewidth=0.5
        )

    #axs[0].set(ylabel="Norm deviation")
    #axs[1].set(ylabel="N deviation")
    #axs[2].set(ylabel="E deviation")
    #axs[3].set(ylabel="U deviation")
    axs[0].set(ylabel="SDX")
    axs[1].set(ylabel="SDY")
    axs[2].set(ylabel="SDZ")
    plt.legend(loc="lower center", ncol=len(series_list), bbox_to_anchor=(0.5, -1))
    plt.tight_layout()

    plt.savefig(fname)
    print(f"File {fname} saved.")
    plt.close()


def plot_experiments(cfg, yml_name):
    series_data_list = cfg["files"]["series"]
    series_dict = {}
    for series_data in series_data_list:
        series_name = series_data[0]
        series_path = series_data[1]

        series_dict[f"{series_name}"] = (
            intersect_series(series_path, None)
        )


    # Plot the networks against the reference
    new_name = os.path.split(yml_name)[-1].replace('yaml','pdf')
    labels = [f"{key}" for key in series_dict.keys()]

    plot(
        series_dict.values(),
        labels,
        fname=f"plots/{new_name}",
        frequency=cfg["resample"],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "-config",
        type=argparse.FileType("r"),
        default="configurations/plot/plots_sd.yaml",
    )
    parsed_args = parser.parse_args()

    config = yaml.safe_load(parsed_args.c)
    plot_experiments(config, yml_name = parsed_args.c.name)
