import pandas as pd
import argparse


class SimilarityTool:

    def __init__(self, series_path, ref_path) -> None:
        series = pd.read_parquet(series_path)
        ref = pd.read_parquet(ref_path)

        series = series.loc[series.index.intersection(ref.index)]
        ref = ref.loc[ref.index.intersection(series.index)]

        self.series = series - ref
        self.ref = ref - ref

        self.series = self.series.apply(self.min_max_scaling)

        print(self.series.head())
        print(self.ref.head())

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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "-series",
        default="data/rtklib_brdc/onrj.parquet",
    )
    parser.add_argument(
        "-r",
        "-ref",
        default="data/spp_rtklib_ionex/onrj.parquet",
    )
    parsed_args = parser.parse_args()

    st = SimilarityTool(parsed_args.s, parsed_args.r)
    st.similarity()
