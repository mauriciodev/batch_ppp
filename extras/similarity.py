import pandas as pd
import argparse
import numpy as np
import matplotlib.pyplot as plt


class SimilarityTool:

    def __init__(self, series_path, ref_path, freq) -> None:
        series = pd.read_parquet(series_path)
        ref = pd.read_parquet(ref_path)

        # Intersectin with the reference to align the timestamps
        series = series.loc[series.index.intersection(ref.index)]

        # Computing the difference to the reference
        series = series - ref

        # Scaling in the range 0-1
        series = series.apply(self.min_max_scaling)

        # Resampling according to the frequency
        self.series = series.resample(freq).mean()

    def min_max_scaling(self, column):
        """Function to scale to 0-1"""
        return (column - column.min()) / (column.max() - column.min())

    def similarity(self):
        mae = self.series.mean(axis=0).abs()
        rmse = self.series.pow(2).mean(axis=0).pow(0.5)
        stdev = self.series.std(axis=0)

        print(f"MAE: {mae}")
        print(f"RMSE: {rmse}")
        print(f"STDEV: {stdev}")
        return mae, rmse, stdev


def plot(concat_series):
    # MAE plot
    concat_series_agg = concat_series.groupby("network").agg(
        lambda x: abs(x.mean(axis=0))
    )
    plt.title("Mean Absolute Error")  # Capitalize title
    concat_series_agg.plot.bar()
    plt.xlabel("Network")
    plt.ylabel("MAE")
    plt.legend(title="Metrics")  # Add legend title
    plt.grid(True)  # Add grid lines (optional)
    plt.tight_layout()  # Adjust spacing (optional)
    plt.savefig("plots/mae.pdf")
    plt.close()

    # RMSE plot
    concat_series_agg = concat_series.groupby("network").agg(
        lambda x: np.sqrt(np.power(x, 2).mean(axis=0))
    )
    plt.title("Root Mean Square Error")  # Capitalize title
    concat_series_agg.plot.bar()
    plt.xlabel("Network")
    plt.ylabel("RMSE")
    plt.legend(title="Metrics")  # Add legend title
    plt.grid(True)  # Add grid lines (optional)
    plt.tight_layout()  # Adjust spacing (optional)
    plt.savefig("plots/rmse.pdf")
    plt.close()

    # STDEV plot
    concat_series_agg = concat_series.groupby("network").agg("std")
    plt.title("Standard Deviation")  # Capitalize title
    concat_series_agg.plot.bar()
    plt.xlabel("Network")
    plt.ylabel("STDEV")
    plt.legend(title="Metrics")  # Add legend title
    plt.grid(True)  # Add grid lines (optional)
    plt.tight_layout()  # Adjust spacing (optional)
    plt.savefig("plots/stdev.pdf")
    plt.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "-series",
        nargs="*",
        default=["data/unet/onrj.parquet", "data/edconvlstm_nd/onrj.parquet"],
    )
    parser.add_argument(
        "-n",
        "-names",
        nargs="*",
        default=["UNET", "ND"],
    )
    parser.add_argument(
        "-r",
        "-ref",
        default="data/spp_rtklib_ionex/onrj.parquet",
    )
    parsed_args = parser.parse_args()
    series_path_list = parsed_args.s
    series_names_list = parsed_args.n
    series_list = []
    for series_path, series_name in zip(series_path_list, series_names_list):
        st = SimilarityTool(series_path, parsed_args.r, freq="1D")
        st.similarity()
        series = st.series
        series["network"] = series_name
        series_list.append(series)

    concat_series = pd.concat(series_list, axis=0)

    plot(concat_series=concat_series)
