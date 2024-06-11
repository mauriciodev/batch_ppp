import pandas as pd
import argparse
import numpy as np
import matplotlib.pyplot as plt

class SimilarityTool:

    def __init__(self, series_path, ref_path, freq) -> None:
        # Series and reference dataframes
        series = pd.read_parquet(series_path)
        ref = pd.read_parquet(ref_path)

        # Intersecting with the reference to align the timestamps
        series = series.loc[series.index.intersection(ref.index)]

        # Computing the difference to the reference
        diff_series = series - ref

        # Resampling according to the frequency
        self.diff_series = diff_series.resample(freq).mean()
        self.series = series.resample(freq).mean()
        self.ref = ref.resample(freq).mean()

    def similarity(self):
        mae = self.diff_series.mean(axis=0).abs()
        rmse = self.diff_series.pow(2).mean(axis=0).pow(0.5)
        stdev = self.diff_series.std(axis=0)
        r2 = self.series.corrwith(self.ref, method="pearson")

        print(f"MAE: {mae}")
        print(f"RMSE: {rmse}")
        print(f"STDEV: {stdev}")
        print(f"R2: {r2}")
        return mae, rmse, stdev, r2

    def calculate_correlation_all(self, x):
        correlations = x.corr(self.ref, method="spearman")
        return correlations.unstack(fill_value=np.nan)  # Reshape to DataFrame

    def plot(self, concat_series):
        # MAE plot
        group = concat_series.groupby("metric")
        plt.title("Metrics")  # Capitalize title
        group.plot.bar()
        plt.xlabel("Network")
        plt.ylabel("Metric")
        plt.legend(title="Metrics")  # Add legend title
        plt.grid(True)  # Add grid lines (optional)
        plt.tight_layout()  # Adjust spacing (optional)
        plt.savefig("plots/mae.pdf")
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
        default="data/rtklib_ionfree/onrj.parquet",
    )
    parsed_args = parser.parse_args()
    series_path_list = parsed_args.s
    series_names_list = parsed_args.n
    series_list = []
    for series_path, series_name in zip(series_path_list, series_names_list):
        st = SimilarityTool(series_path, parsed_args.r, freq="1D")
        mae, rmse, stdev, r2 = st.similarity()

        mae["metric"] = "MAE"
        rmse["metric"] = "RMSE"
        stdev["metric"] = "STDEV"
        r2["metric"] = "R2"

        mae = mae.to_frame().T
        rmse = rmse.to_frame().T
        stdev = stdev.to_frame().T
        r2 = r2.to_frame().T

        series = pd.concat([mae, rmse, stdev, r2], axis=0)
        series["network"] = series_name
        series_list.append(series)

    concat_series = pd.concat(series_list, axis=0)
    print(concat_series)

    st.plot(concat_series=concat_series)
