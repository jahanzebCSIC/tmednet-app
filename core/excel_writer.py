import os as _os
import numpy as np
import pandas as pd
import time
from pandas import ExcelWriter
import marineHeatWaves as mhw
import datetime
import mhw_calculations as mhwc

from _paths import OUTPUT_DIR as _OUTPUT_DIR


class ExcelReport:

    def __init__(self, filein):
        self.dfexcel = []
        self.dfmonthly = []
        self.dfseasonal = []
        self.mhwdf = []
        self.filein = filein

    # Converts the data from the historic file to a DataFrame and selects the needed data to create the Excel
    def excel_writer(self):
        start = time.time()
        # Reads the historic file and converts it to a DataFrame. Loads all the DataFrames to make the calculations
        self.read_and_setup()
        # Sorts the final DataFrames that will compose the sheets of the Excel file
        self.dfexcel['depth(m)'] = self.dfexcel['depth(m)'].astype(int)
        self.dfmonthly['depth(m)'] = self.dfmonthly['depth(m)'].astype(int)
        self.dfexcel = self.dfexcel.sort_values(by=['date', 'depth(m)'])
        self.dfmonthly = self.dfmonthly.sort_values(by=['year', 'month', 'depth(m)'])
        self.dfseasonal['depth(m)'] = self.dfseasonal['depth(m)'].astype(int)
        self.dfseasonal = self.dfseasonal.sort_values(by=['year', 'depth(m)'])
        self.dfexcel['year'] = pd.DatetimeIndex(self.dfexcel['date']).year
        self.dfexcel['month'] = pd.DatetimeIndex(self.dfexcel['date']).month
        self.dfexcel['date'] = self.dfexcel['date'].dt.date
        # Drop rows with NA max once; idxmax raises ValueError on all-NA groups in newer pandas
        _nona = self.dfexcel.dropna(subset=['max'])
        dfmaxes = self.dfexcel.loc[_nona.groupby(['year'])['max'].idxmax()][['year', 'date', 'max']]
        dfmaxes.sort_values('max', ascending=False, inplace=True)
        dfmaxesdepth = self.dfexcel.loc[_nona.groupby(['year', 'depth(m)'])['max'].idxmax()][
            ['year', 'depth(m)', 'date', 'max']]
        dfmaxesdepth.sort_values(['depth(m)', 'max'], ascending=False, inplace=True)
        dfmaxes_month = self.dfexcel.loc[_nona.groupby(['year', 'month'])['max'].idxmax()][
            ['year', 'month', 'date', 'max']]
        dfmaxes_month.sort_values('max', ascending=False, inplace=True)
        dfmaxesdepth_month = self.dfexcel.loc[_nona.groupby(['year', 'month', 'depth(m)'])['max'].idxmax()][
            ['year', 'month', 'depth(m)', 'date', 'max']]
        dfmaxesdepth_month.sort_values(['depth(m)', 'max'], ascending=False, inplace=True)
        # Write the Excel file with the given DataFrames as sheets
        filein_split = self.filein.split('_')
        fileout_name = filein_split[3] + '_Stat_Report_' + filein_split[4] + '_' + filein_split[5][:-4]
        writer = ExcelWriter(_os.path.join(_OUTPUT_DIR, fileout_name + '.xlsx'))
        self.dfexcel.to_excel(writer, sheet_name='Daily', index=False)
        self.dfmonthly.to_excel(writer, sheet_name='Monthly', index=False)
        self.dfseasonal.to_excel(writer, sheet_name='Seasonal', index=False)
        dfmaxes.to_excel(writer, sheet_name='Maxes', index=False)
        dfmaxesdepth.to_excel(writer, sheet_name='Maxes depth', index=False)
        dfmaxes_month.to_excel(writer, sheet_name='Maxes month', index=False)
        dfmaxesdepth_month.to_excel(writer, sheet_name='Maxes depth month', index=False)
        df30tmax = self.set_30tmax()
        df30tmax.to_excel(writer, sheet_name='30Tmax', index=False)
        write_mhw = self.__check_year_difference()
        if write_mhw:
            try:
                mhw_sheet = mhwc.create_df_with_mhw(self.mhwdf)
                mhw_sheet.to_excel(writer, sheet_name='MHW', index=False)
                mhw_sheet['year'] = pd.DatetimeIndex(mhw_sheet['Date']).year
                _mhw_nona = mhw_sheet.dropna(subset=['Max Intensity (ºC)'])
                dfmaxesmhw = mhw_sheet.loc[_mhw_nona.groupby(['year', 'Depth (m)'])['Max Intensity (ºC)'].idxmax()]
                dfmaxesmhw.sort_values(['Date'], ascending=True, inplace=True)
                dfmaxesmhw.to_excel(writer, sheet_name='MHW_MAX I', index=False)
            except Exception as _mhw_err:
                print(f'MHW sheets skipped: {_mhw_err}')

        writer.close()
        end = time.time()
        print(end - start)

    def set_30tmax(self):
        df = self.dfexcel.copy()
        result = (
            df.groupby('year')['mean']
            .apply(lambda g: round(float(g.nlargest(30).mean()), 2))
            .reset_index()
        )
        result.columns = ['year', '30tmax']
        result['year'] = result['year'].astype(int)
        return result

    def read_and_setup(self):
        df = pd.read_csv(self.filein, sep='\t')
        self.mhwdf = df.copy()
        depths = df.columns.tolist()
        del depths[0]
        del depths[0]
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
        df['year'] = df['Date'].dt.year
        df['month'] = df['Date'].dt.month

        # Pre-filter seasonal rows once, outside the depth loop
        df_season = df.loc[(df['month'] >= 7) & (df['month'] <= 9)]

        daily_parts = []
        monthly_parts = []
        seasonal_parts = []

        # Iterates for each depth (which is a column on the historic DataFrame)
        for depth in depths:
            col = str(depth)

            # --- Daily: single agg pass instead of 5 separate calls ---
            agg_d = df.groupby('Date')[col].agg(['count', 'mean', 'std', 'max', 'min'])
            agg_d[['mean', 'std', 'max', 'min']] = agg_d[['mean', 'std', 'max', 'min']].round(3)
            agg_d.columns = ['N', 'mean', 'std', 'max', 'min']
            dfinter = agg_d.reset_index().rename(columns={'Date': 'date'})
            dfinter['depth(m)'] = depth
            daily_parts.append(dfinter[['date', 'depth(m)', 'N', 'mean', 'std', 'max', 'min']])

            # --- Monthly: single agg pass + vectorized threshold counts ---
            agg_m = df.groupby(['year', 'month'])[col].agg(['count', 'mean', 'std', 'max', 'min'])
            agg_m[['mean', 'std', 'max', 'min']] = agg_m[['mean', 'std', 'max', 'min']].round(3)
            agg_m.columns = ['N', 'mean', 'std', 'max', 'min']
            dfintermonth = agg_m.reset_index()
            dfintermonth['depth(m)'] = depth
            #TODO consider include June (month 6)
            for thresh in [24, 25, 26]:
                dfintermonth[f'Ndays>={thresh}'] = np.round(
                    (df[col] >= thresh).astype(int)
                    .groupby([df['year'], df['month']]).sum().values / 24
                )
            monthly_parts.append(dfintermonth[['year', 'month', 'depth(m)', 'N', 'mean', 'std', 'max', 'min',
                                                'Ndays>=24', 'Ndays>=25', 'Ndays>=26']])

            # --- Seasonal: single agg pass + vectorized threshold counts ---
            agg_s = df_season.groupby('year')[col].agg(['count', 'mean', 'std', 'max', 'min'])
            agg_s[['mean', 'std', 'max', 'min']] = agg_s[['mean', 'std', 'max', 'min']].round(3)
            agg_s.columns = ['N', 'mean', 'std', 'max', 'min']
            dfinterseason = agg_s.reset_index()
            dfinterseason['season'] = 3
            dfinterseason['depth(m)'] = depth
            for thresh in [23, 24, 25, 26, 27, 28]:
                dfinterseason[f'Ndays>={thresh}'] = np.round(
                    (df_season[col] >= thresh).astype(int)
                    .groupby(df_season['year']).sum().values / 24
                )
            seasonal_parts.append(dfinterseason[['year', 'season', 'depth(m)', 'N', 'mean', 'std', 'max', 'min',
                                                  'Ndays>=23', 'Ndays>=24', 'Ndays>=25',
                                                  'Ndays>=26', 'Ndays>=27', 'Ndays>=28']])

        # Single concat at the end — avoids O(n²) growth from concat in loop
        self.dfexcel = pd.concat(daily_parts, ignore_index=True)
        self.dfmonthly = pd.concat(monthly_parts, ignore_index=True)
        self.dfseasonal = pd.concat(seasonal_parts, ignore_index=True)

    # This method uses the mhw library to return the mhw of a given historic file.
    # TODO SOON TO BE DEPRECATED
    def create_mhw(self):
        del self.mhwdf['Time']
        self.mhwdf['Date'] = pd.to_datetime(self.mhwdf['Date'], format='%d/%m/%Y')
        nufile = self.mhwdf.groupby('Date').mean()
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
             'Mean Temperature (ºC)': [round(sst5[item[0]:item[0]+item[1]].mean(), 2) for item in zip(mhws['index_start'], mhws['duration'])],
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
                     'Mean Temperature (ºC)': [round(sst[item[0]:item[0]+item[1]].mean(), 2) for item in zip(mhws['index_start'], mhws['duration'])],
                     'Category': mhws['category']})
                diff = pd.concat([diff, dfi], ignore_index=True)

        return diff

    def __check_year_difference(self):
        lastyear = self.dfexcel['date'].iloc[-1].year
        firstyear = self.dfexcel['date'].iloc[0].year
        lastmonth = self.dfexcel['date'].iloc[-1].month
        firstmonth = self.dfexcel['date'].iloc[0].month
        if lastmonth < firstmonth:
            years = lastyear - firstyear
        else:
            years = lastyear - firstyear - 1
        if years >= 10:
            write_mhw = True
        else:
            write_mhw = False

        return write_mhw
