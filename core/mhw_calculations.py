import sys, os
sys.path.append(os.path.dirname(__file__))

import marineHeatWaves as mhw
import pandas as pd
import numpy as np

def create_df_with_mhw(df):
    del df['Time']
    nufile = df.groupby('Date').mean()
    if isinstance(nufile.index[0], str):
        nufile.index = pd.to_datetime(nufile.index, dayfirst=True)
    dates = [x.date() for x in nufile.index]
    t = [x.toordinal() for x in dates]
    t = np.array(t)
    depths = nufile.columns
    sst5 = nufile[depths[0]].values
    mhws, clim = mhw.detect(t, sst5)
    diff = pd.DataFrame(
        {'Date': mhws['date_start'], 'Depth (m)': depths[0], 'Duration (Days)': mhws['duration'],
         'Max Intensity (ºC)': [round(num, 2) for num in mhws['intensity_max']],
         'Cumulative Intensity (ºC day)': [round(num, 2) for num in mhws['intensity_cumulative']],
         'Mean Intensity (ºC)': [round(num, 2) for num in mhws['intensity_mean']],
         'Mean Temperature (ºC)': [round(sst5[item[0]:item[0] + item[1]].mean(), 2) for item in
                                   zip(mhws['index_start'], mhws['duration'])],
         'Category': mhws['category']})
    for depth in depths:
        if depth == depths[0]:
            pass
        else:
            sst = nufile[depth].values
            mhws, clim = mhw.detect(t, sst)
            dfi = pd.DataFrame(
                {'Date': mhws['date_start'], 'Depth (m)': depth, 'Duration (Days)': mhws['duration'],
                 'Max Intensity (ºC)': [round(num, 2) for num in mhws['intensity_max']],
                 'Cumulative Intensity (ºC day)': [round(num, 2) for num in mhws['intensity_cumulative']],
                 'Mean Intensity (ºC)': [round(num, 2) for num in mhws['intensity_mean']],
                 'Mean Temperature (ºC)': [round(sst[item[0]:item[0] + item[1]].mean(), 2) for item in
                                           zip(mhws['index_start'], mhws['duration'])],
                 'Category': mhws['category']})
            diff = pd.concat([diff, dfi], ignore_index=True)
    return diff