import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import hydra
from omegaconf import DictConfig, OmegaConf


@hydra.main(
    version_base=None,
    config_path="../configurations",
    config_name="plot_quantiles",
)
def my_app(cfg : DictConfig) -> None:
    print(OmegaConf.to_yaml(cfg))
    folder = cfg.get('folder')
    model = cfg.get('model')
    plot_path = cfg.get("plot")

    df1 = pd.read_parquet(folder.format(model=model))
    df1['norm'] = np.linalg.norm(df1.to_numpy(), axis=1)
    freq='1D'
    df1 = df1.resample(freq)

    data=df1['norm']
    x=data.mean().index
    plt.figure(figsize=(10,10))
    # plt.title("Percentiles of the VTEC values on every pixel on the GIMs from 2014 ")
    plt.plot(x,data.min(), label='Minimum/Maximum', color='red', marker='.', linestyle='', markersize=2)
    plt.plot(x,data.max(),  color='red', marker='.', linestyle='', markersize=2)
    per=data.quantile([0.5, 0.95, 0.20, 0.80])
    plt.fill_between(x,y1=data.quantile(0.05),y2=data.quantile(0.95), alpha=0.1, color='blue') #,label="90% of the pixels"
    plt.plot(x,data.quantile(0.05), color='blue', label="Percentiles of 5% and 95%.")
    plt.plot(x,data.quantile(0.95), color='blue')
    plt.fill_between(x,y1=data.quantile(0.2),y2=data.quantile(0.8), alpha=0.2, color='green', edgecolor='green') #,label="60% of the pixels"
    plt.plot(x,data.quantile(0.2), color='green', label="Percentiles of 20% and 80%.")
    plt.plot(x,data.quantile(0.8), color='green')
    plt.plot(x, data.mean(), label='Mean', color='yellow')
    plt.ylabel("Norm of the difference")
    plt.xlabel(f"Days of the years")
    # plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))#(loc=1)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.23), ncol =7 )   
    plt.tight_layout()
    plt.savefig(plot_path, bbox_inches="tight")

if __name__ == "__main__":
    my_app()
