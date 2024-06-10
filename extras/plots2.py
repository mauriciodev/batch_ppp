import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import yaml


def intersect_series(series1_path, series2_path):
    series1 = pd.read_parquet(series1_path)
    series2 = pd.read_parquet(series2_path)

    series1 = series1.loc[series1.index.intersection(series2.index)]
    series2 = series2.loc[series2.index.intersection(series1.index)]

    return series1, series2


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


def plot_experiments():
    brdc_path = "data/rtklib_brdc/onrj.parquet"
    c1pg_path = "data/spp_rtklib_c1pg/onrj.parquet"
    ionex_path = "data/spp_rtklib_ionex/onrj.parquet"
    unet_path = "data/unet/onrj.parquet"
    simvp_path = "data/spp_rtklib_simvp/onrj.parquet"
    nd_path = "data/edconvlstm_nd/onrj.parquet"

    # Intersecting with ionex
    brdc, ionex = intersect_series(brdc_path, ionex_path)
    c1pg, ionex = intersect_series(c1pg_path, ionex_path)
    unet, ionex = intersect_series(unet_path, ionex_path)
    nd, ionex = intersect_series(nd_path, ionex_path)
    # simvp, ionex = intersect_series(brdc_path, ionex_path)

    # First plot with base data: Broadcast, C1PG GIM prediction and IONEX GIM post processing
    plot(
        [
            brdc,
            c1pg,
            ionex,
        ],
        [
            "BRDC",
            "C1PG",
            "IONEX",
        ],
        fname="plots/plot_igs.pdf",
        frequency="1D",
    )

    # Unet plot using IONEX as reference
    unet_ionex = unet - ionex
    unet_c1pg = unet - c1pg
    plot(
        [
            unet_ionex,
            unet_c1pg,
        ],
        [
            "UNET to IONEX",
            "UNET to C1PG",
        ],
        fname="plots/plot_unet.pdf",
        frequency="1D",
    )

    # Edconvlstm_nd plot using IONEX as reference
    nd_ionex = nd - ionex
    nd_c1pg = nd - c1pg
    plot(
        [
            nd_ionex,
            nd_c1pg,
        ],
        [
            "ND to IONEX",
            "ND to C1PG",
        ],
        fname="plots/plot_nd.pdf",
        frequency="1D",
    )

    # Plotting UNET and ND together referenced against IONEX
    plot(
        [
            nd_ionex,
            unet_ionex,
        ],
        [
            "ND to IONEX",
            "UNET to IONEX",
        ],
        fname="plots/plot_nd_unet.pdf",
        frequency="1D",
    )


if __name__ == "__main__":
    plot_experiments()
