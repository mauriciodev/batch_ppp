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
    config_name="plots_hist",
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
        m = np.linalg.norm(df[['X(m)','Y(m)','Z(m)']].to_numpy(), axis=1).flatten()
        if rmin==rmax:
            rmin = int(np.floor(np.percentile(m, 1)))
            rmax = int(np.floor(np.percentile(m, 99)))
            #bins = int(rmax-rmin)
        hist, edges = np.histogram(m.reshape(-1), bins=bins,range=[rmin, rmax], density=True)  
        width = edges[1]-edges[0]
        #plt.plot(edges[:-1]+0.5*width,hist*100, label=model[1]) #, marker='.'
        label = f"{model[0]} $\mu={m.mean():.2f}m$, $\sigma={m.std():.2f}m$"
        if i==0:
            plt.bar(edges[:-1]+0.5*width, hist*100, label=label, alpha=0.5, width=width) #
        else: 
            plt.step(edges, np.concatenate([[hist[0]],hist])*100 , label=label) #*width np.concatenate([[hist[0]],hist])*100
            
        
    #plt.xlabel('Distance to the reference position.')
    #plt.ylabel('Percentage of positions estimated.')
    #plt.title(f'Histogram of the distance to the reference position')
    plt.xlabel('Distância para posição de referência (em metros).')
    plt.ylabel('Percentual das posições obtidas.')
    plt.title(f'Histogramas das distâncias entre as posições obtidas e a referência.')    
    plt.legend()
    plt.savefig(outfilename,  bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    my_app()
