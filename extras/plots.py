import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

def plot(file_list, label_list, fname='plot.png'):
    fig, axs = plt.subplots(4)
    #fig.suptitle('Vertically stacked subplots')
    for ax in axs:
        #ax.grid(True, which='both')
        ax.axhline(y=0, color='k')
    for file_name, label in zip(file_list, label_list):
        series = np.load(file_name)
        
        axs[0].plot(np.linalg.norm(series, axis=-1), label=label, marker='.')
        axs[1].plot(series[:,0], label=label, marker='.')
        axs[2].plot(series[:,1], label=label, marker='.')
        axs[3].plot(series[:,2], label=label, marker='.')
    
    axs[0].set(ylabel='Norm deviation')
    axs[1].set(ylabel='X deviation')
    axs[2].set(ylabel='Y deviation')
    axs[3].set(ylabel='Z deviation')
    plt.legend()
    plt.tight_layout()
    plt.savefig(fname)
    plt.close()
    """df = pd.DataFrame()
    df['date'] = pd.date_range(d0,d1,freq='D')
    df['CODG_ex'] = codgError[:,0]
    df['CODG_ey'] = codgError[:,1]
    df['CODG_ez'] = codgError[:,2]
    df['CODG_norm'] = np.linalg.norm(codgError,axis=1)
    df['Klobuchar_ex'] = brdcError[:,0]
    df['Klobuchar_ey'] = brdcError[:,1]
    df['Klobuchar_ez'] = brdcError[:,2]
    df['Klobuchar_norm'] = np.linalg.norm(brdcError,axis=1)
    csvFileName = f'output/data_{d0}_to_{d1}.csv'
    print(f"Saving the errors to {csvFileName}")
    df.to_csv(csvFileName)
    df.plot(x='date', y=['CODG_ex', 'CODG_ey', 'CODG_ez'], figsize=(10, 10))
    df.plot(x='date', y=['Klobuchar_ex', 'Klobuchar_ey', 'Klobuchar_ez'], figsize=(10, 10))
    df.plot(x='date', y=['CODG_norm', 'Klobuchar_norm'], figsize=(10, 10))"""
   # pos_mean = [df['X(m)'].mean(), df['Y(m)'].mean(), df['Z(m)'].mean()]


def save_csv(file_list, label_list):
    

    df['err_X'] = df['X(m)']-df['X(m)'].mean()
    df['err_Y'] = df['Y(m)']-df['Y(m)'].mean()
    df['err_Z'] = df['Z(m)']-df['Z(m)'].mean()

    df['err_norm'] = np.linalg.norm(df[['err_X', 'err_Y', 'err_Z']],axis=1)


    df.plot(x='GPS_TIME', y = ['err_X', 'err_Y', 'err_Z', 'err_norm'])

    df.plot(x='GPS_TIME', y = 'err_norm')

if __name__=="__main__":
    #parser = argparse.ArgumentParser()

    #parser.add_argument('-c' '-config',  type=argparse.FileType('r'), default='config.yml')
    #parsed_args = parser.parse_args()
    #config = yaml.safe_load(parsed_args.c_config)
    plot(['data/rtklib_brdc/onrj.npy', 
          'data/spp_rtklib_ionex/onrj.npy',
          'data/spp_rtklib_c1pg/onrj.npy'
          ],[
          'rtklib_brdc', 
          'spp_rtklib_ionex',
          'spp_rtklib_c1pg'
         ], 'plot3.png')
    plot([
      'data/spp_rtklib_ionex/onrj.npy',
      'data/spp_rtklib_c1pg/onrj.npy'
      ],[
      'spp_rtklib_ionex',
      'spp_rtklib_c1pg'
     ], 'plot_igs.png')