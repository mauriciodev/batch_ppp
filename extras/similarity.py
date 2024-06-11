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

        return mae, rmse, stdev, r2

    def plot(self, concat_series):
        # MAE plot
        grouped = concat_series.groupby("metric")

        fig, axes = plt.subplots(nrows=1, ncols=len(grouped))
        i=0
        # plt.title("Metrics")  # Capitalize title
        for name, group in grouped:
            group.plot.bar(ax=axes[i], x='network', legend=False)
            # axes[i].set_xlabel("Network")
            axes[i].set_title(name)

            axes[i].grid(True)  # Add grid lines (optional)
            # if i == 0:
            #    axes[i].legend(loc=1)
            i+=1

        axes[-1].legend(title="Coordinates", loc = 'lower left')  # Add legend title~
        # axes[2].legend(title="Coordinates",loc='upper center', bbox_to_anchor=(0.6, -0.05),fancybox=True, shadow=True,ncol=3)
        plt.tight_layout()  # Adjust spacing (optional)
        plt.savefig("plots/metrics.pdf")
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
    parser.add_argument(
        "-o",
        "-output",
        default="plots/metrics.csv",
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

        # As the metrics are Pandas Series, we need to convert them do dataframes and transpose them
        mae = mae.to_frame().T
        rmse = rmse.to_frame().T
        stdev = stdev.to_frame().T
        r2 = r2.to_frame().T

        # Concatenating the metrics
        series = pd.concat([mae, rmse, stdev, r2], axis=0, ignore_index=True)
        series["network"] = series_name
        series_list.append(series)

    # Making the final dataframe with all values
    concat_series = pd.concat(series_list, axis=0, ignore_index=True)

    # Plotting and saving the metrics as csv
    st.plot(concat_series=concat_series)
    concat_series.to_csv(parsed_args.o, index=False)
