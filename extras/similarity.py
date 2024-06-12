import pandas as pd
import argparse
import numpy as np
import matplotlib.pyplot as plt
import sklearn.metrics
import yaml

class SimilarityTool:

    def __init__(self, series_path, ref_path, freq) -> None:
        # Series and reference dataframes
        series = pd.read_parquet(series_path)
        ref = pd.read_parquet(ref_path)

        # Adding the norm to the series and ref
        series["Norm"] = np.linalg.norm(
            series[["X(m)", "Y(m)", "Z(m)"]].to_numpy(), axis=-1
        )
        ref["Norm"] = np.linalg.norm(ref[["X(m)", "Y(m)", "Z(m)"]].to_numpy(), axis=-1)

        # Intersecting with the reference to align the timestamps
        series = series.loc[series.index.intersection(ref.index)]

        # Computing the difference to the reference
        diff_series = series - ref

        # Resampling according to the frequency
        self.diff_series = diff_series.resample(freq).mean()
        self.series = series.resample(freq).mean()
        self.ref = ref.resample(freq).mean()

    def similarity(self):
        mae = self.series.corrwith(self.ref, method=sklearn.metrics.mean_absolute_error)
        rmse = self.series.corrwith(self.ref, method=sklearn.metrics.root_mean_squared_error)
        stdev = self.diff_series.std(axis=0)
        r2 = self.series.corrwith(self.ref, method=sklearn.metrics.r2_score)#"pearson")

        return mae, rmse, stdev, r2

    def plot(self, concat_series, save_plot):
        # MAE plot
        grouped = concat_series.groupby("metric")

        fig, axes = plt.subplots(nrows=1, ncols=len(grouped))
        i = 0
        axes[0].set_ylabel('Difference (m)')
        for name, group in grouped:
            group.plot.bar(ax=axes[i], x="network", legend=False)
            axes[i].set_title(name)
            axes[i].set_xlabel(None)

            axes[i].grid(True)  # Add grid lines (optional)

            i+=1

        plt.tight_layout()  # Adjust spacing (optional)
        handles, labels = axes[0].get_legend_handles_labels()
        legend = fig.legend(
            handles,
            labels,
            loc="lower center",
            ncol=4,
            title="Coordinates",
            bbox_to_anchor=(0.5, -0.1),
        )
        plt.savefig(save_plot, bbox_inches="tight")
        plt.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "-config",
        type=argparse.FileType("r"),
        default="configurations/similarity.yml",
    )
    parsed_args = parser.parse_args()

    config = yaml.safe_load(parsed_args.c)

    series_info_list = config["series"]
    series_list = []
    for series_info in series_info_list:
        series_name = series_info[0]
        series_path = series_info[1]
        st = SimilarityTool(series_path, config["ref"], freq="1D")
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
        series = pd.concat([mae, rmse, r2], axis=0, ignore_index=True) #stdev, 
        series["network"] = series_name
        series_list.append(series)

    # Making the final dataframe with all values
    concat_series = pd.concat(series_list, axis=0, ignore_index=True)

    # Plotting and saving the metrics as csv
    st.plot(concat_series=concat_series, save_plot=config["plot"])
    concat_series.to_csv(config["output"], index=False)
