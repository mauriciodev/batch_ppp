import pandas as pd
from scipy.spatial.distance import euclidean, cityblock, jaccard, cosine, correlation
import argparse

class SimilarityTool:
    def __init__(self, series1_path, series2_path) -> None:
        self.series1 = pd.read_parquet(series1_path)
        self.series2 = pd.read_parquet(series2_path)

    def similarity(self, method):
        similarity_x = method(self.series1["X(m)"], self.series2["X(m)"])        
        similarity_y = method(self.series1["Y(m)"], self.series2["Y(m)"])
        similarity_z = method(self.series1["Z(m)"], self.series2["Z(m)"])
        return similarity_x, similarity_y, similarity_z

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s1", 
        "-series1",
        default="data/rtklib_brdc/onrj.parquet",
    )
    parser.add_argument(
        "-s2",
        "-series2",
        default="data/spp_rtklib_ionex/onrj.parquet",
    )
    parsed_args = parser.parse_args()

    st = SimilarityTool(parsed_args.s1, parsed_args.s2)

    methods = {'Euclidian':euclidean, 'Manhattan':cityblock, 'Jaccard':jaccard, 'Cosine':cosine, 'Correlation':correlation}
    for method in methods.items():
        print(f'{method[0]} similarity: {st.similarity(method[1])}')