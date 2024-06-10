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
    fig, axs = plt.subplots(4)
    # fig.suptitle('Vertically stacked subplots')
    for ax in axs:
        # ax.grid(True, which='both')
        ax.axhline(y=0, color="k")
    for series, label in zip(series_list, label_list):
        series = series.resample(frequency).mean()

        axs[0].plot(
            np.linalg.norm(series[["X(m)", "Y(m)", "Z(m)"]].to_numpy(), axis=-1),
            label=label,
            marker=".",
            markersize=2,
            linewidth=0.5,
        )
        axs[1].plot(
            series["X(m)"], label=label, marker=".", markersize=2, linewidth=0.5
        )
        axs[2].plot(
            series["Y(m)"], label=label, marker=".", markersize=2, linewidth=0.5
        )
        axs[3].plot(
            series["Z(m)"], label=label, marker=".", markersize=2, linewidth=0.5
        )

    axs[0].set(ylabel="Norm deviation")
    axs[1].set(ylabel="X deviation")
    axs[2].set(ylabel="Y deviation")
    axs[3].set(ylabel="Z deviation")
    plt.legend(loc="lower center", ncol=len(series_list), bbox_to_anchor=(0.5, -1))
    plt.tight_layout()

    plt.savefig(fname)
    print(f"File {fname} saved.")
    plt.close()


def plot_experiments(cfg):
    igs_dict = {}
    if not cfg["files"]["ref"] is None:
        ref_name = cfg["files"]["ref"][0]
        ref_path = cfg["files"]["ref"][1]
   
        igs_dict[f"{ref_name}"] = pd.read_parquet(ref_path)
    else:
        ref_path = None
        ref_name = ''

    igs_data_list = cfg["files"]["igs"]
    for igs_data in igs_data_list:
        igs_name = igs_data[0]
        igs_path = igs_data[1]

        # Intersecting with ref and adding to the dictionary
        igs_dict[f"{igs_name}"] = intersect_series(igs_path, ref_path)

    series_data_list = cfg["files"]["series"]
    series_dict = {}
    for series_data in series_data_list:
        series_name = series_data[0]
        series_path = series_data[1]

        # Intersecting with ref and adding to the dictionary
        if not cfg["files"]["ref"] is None:
            series_dict[f"{series_name}"] = (
                intersect_series(series_path, ref_path) - igs_dict[f"{ref_name}"]
            )
        else:
            series_dict[f"{series_name}"] = (
                intersect_series(series_path, ref_path)
            )

    # First plot with base data: Broadcast, C1PG GIM prediction, IONEX GIM post processing and IONFREE (dual freq)
    plot(
        igs_dict.values(),
        igs_dict.keys(),
        fname="plots/plot_igs.pdf",
        frequency=cfg["resample"],
    )

    # Plot the networks against the reference
    plot(
        series_dict.values(),
        [f"{key} to {ref_name}" for key in series_dict.keys()],
        fname="plots/plot_networks.pdf",
        frequency=cfg["resample"],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "-config",
        type=argparse.FileType("r"),
        default="configurations/plots.yml",
    )
    parsed_args = parser.parse_args()

    config = yaml.safe_load(parsed_args.c)
    plot_experiments(config)
