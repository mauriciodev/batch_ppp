import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
import hydra
from omegaconf import DictConfig, OmegaConf
import pathlib
font = {'family' : 'Arial',
        'weight' : 'normal',
        'size'   : 12}

@hydra.main(
    version_base=None,
    config_path="../configurations/plot",
    config_name="plots_hist2",
)
def my_app(cfg : DictConfig) -> None:
    print(OmegaConf.to_yaml(cfg))
    series = cfg.get('series')
    bins = int(cfg.get('bins'))
    makeHistComparison(series, cfg.get("plot"), bins=bins)

def makeHistComparison(l,outfilename=f"compared_histogram_continuous.pdf",bins=100):
    plt.Figure((4,4))
    rmin=None
    rmax=None
    std = 0
    mean = 0

    for i,model in enumerate(l):
        df = pd.read_parquet(model[1])
        m = np.linalg.norm(df[['sdx(m)', 'sdy(m)', 'sdz(m)']].to_numpy(), axis=1).flatten()
        if rmin==rmax:
            rmin = int(np.floor(np.percentile(m, 1)))
            rmax = int(np.floor(np.percentile(m, 99)))
            #bins = int(rmax-rmin)
        hist, edges = np.histogram(m.reshape(-1), bins=bins, range=[rmin, rmax], density=True)
        width = edges[1] - edges[0]
        # Ajuste: Multiplicar hist por width e por 100 para obter percentagens corretas
        hist_percent = hist * width * 100  # Normaliza para que a soma das áreas seja 100%
        label = f"{model[0]} $\mu={m.mean():.2f}m$, $\sigma={m.std():.2f}m$"
        if i == 0:
            plt.bar(edges[:-1] + 0.5 * width, hist_percent, label=label, alpha=0.5, width=width)
        else:
            plt.step(edges, np.concatenate([[hist_percent[0]], hist_percent]), label=label)
            
        
    #plt.xlabel('Distance to the reference position.')
    #plt.ylabel('Percentage of positions estimated.')
    #plt.title(f'Histogram of the distance to the reference position')
    plt.xlabel('Norma do vetor de incertezas da posição ($\sigma_x, \sigma_y, \sigma_z$) (em metros).')
    plt.ylabel('Percentual das posições obtidas.')
    plt.title(f'Histogramas das normas dos vetores de incertezas da posição ($\sigma_x, \sigma_y, \sigma_z$).')    
    plt.legend()
    plt.savefig(outfilename,  bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    my_app()
