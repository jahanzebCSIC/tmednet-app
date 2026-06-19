"""
gui_plots.py — adapted from the original tMednet GUI_plots.py.

Changes vs original:
 - Removed all Tkinter imports; now backend-agnostic.
 - __init__ takes (fig, canvas, console, reportlogger, dm) directly instead of
   an f2 Tkinter frame.
 - plot_thresholds uses self._add_threshold_btn callback instead of creating
   tk.Button widgets directly on a toolbar.
 - clear_plots uses self._clear_threshold_btns callback instead of btn.destroy().
 - Matplotlib backend is now Qt-based (set globally in main.py).

Version: 04/2023 MJB: Documentation
         2024: Qt port
"""

import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure


class GUIPlot:
    """
    Contains all information necessary to create the different plots shown in
    the GUI.  Attributes and public methods are identical to the original class.
    """

    def __init__(self, fig, canvas, console, reportlogger, dm):
        """
        Parameters
        ----------
        fig : matplotlib.figure.Figure
            The shared figure object created by PlotWidget.
        canvas : FigureCanvasQTAgg
            The Qt-backend canvas; used for canvas.draw() and mpl_connect().
        console : callable
            console_writer(msg, mod, var, liner) — writes to the log console.
        reportlogger : list
            Mutable list shared with DataManager for report generation.
        dm : DataManager
            The application's data manager instance.
        """
        self.fig = fig
        self.canvas = canvas
        self.counter = []
        self.index = []
        self.console_writer = console
        self.reportlogger = reportlogger
        self.dm = dm
        self.savefilename = ""
        self.__cb = ""
        self.__curtab = None
        self.__tabs = {}
        self.__cbexists = False

        # Callbacks set by PlotWidget after construction:
        # add_threshold_btn(label, callback) -> widget reference
        # clear_threshold_btns() -> None
        self._add_threshold_btn = None
        self._clear_threshold_btns = None

        plt.rc('legend', fontsize='medium')
        self.__plot  = self.fig.add_subplot(111)
        self.__plot1 = self.fig.add_subplot(211)
        self.__plot2 = self.fig.add_subplot(212)
        plt.Axes.remove(self.__plot1)
        plt.Axes.remove(self.__plot2)
        plt.Axes.remove(self.__plot)

    def __str__(self):
        return "GUIPlot object"

    # ------------------------------------------------------------------
    # Time-series plot
    # ------------------------------------------------------------------

    def plot_ts(self, mdata, files, index):
        if self.__plot1.axes:
            plt.Axes.remove(self.__plot1)
            plt.Axes.remove(self.__plot2)

        if self.counter[0] in ("Hovmoller", "Cycles", "Thresholds", "Filter",
                                "Difference"):
            self.clear_plots()

        masked_ending_temperatures = np.ma.masked_where(
            np.array(mdata[index]['df']['Temp']) == 999,
            np.array(mdata[index]['df']['Temp'])
        )

        if self.__plot.axes:
            self.__plot.plot(
                mdata[index]['df'].index, masked_ending_temperatures,
                '-', label=str(mdata[index]['depth'])
            )
            self.__plot.set(
                ylabel='Temperature (DEG C)',
                title='Multiple depths  Site: ' + str(mdata[index]['region_name'])
            )
        else:
            self.__plot = self.fig.add_subplot(111)
            self.__plot.plot(
                mdata[index]['df'].index, masked_ending_temperatures,
                '-', label=str(mdata[index]['depth'])
            )
            self.__plot.set(
                ylabel='Temperature (DEG C)',
                title=(files[index] + "\n"
                       + 'Depth:' + str(mdata[index]['depth'])
                       + "  –  Site: " + str(mdata[index]['region_name']))
            )

        self.__plot.legend(title='Depth (m)')
        self.canvas.draw()

    # ------------------------------------------------------------------
    # Zoom plots
    # ------------------------------------------------------------------

    def plot_zoom(self, mdata, files, list_adapter, cut_data_manually,
                  controller=False):
        self.clear_plots()
        index = int(list_adapter.curselection()[0])
        time_series, temperatures, indexes, start_index, valid_start, valid_end = \
            self.dm.zoom_data(mdata[index])

        self.counter.append(index)
        self.counter.append('Zoom')

        if not self.__plot1.axes:
            self.__plot1 = self.fig.add_subplot(211)
            self.__plot2 = self.fig.add_subplot(212)

        masked_temperatures = np.ma.masked_where(
            np.array(mdata[index]['df']['Temp']) == 999,
            np.array(mdata[index]['df']['Temp'])
        )

        self.__plot1.plot(
            time_series[0][int(start_index):],
            masked_temperatures[int(start_index) + int(valid_start):
                                len(time_series[0]) + valid_start],
            '-', color='steelblue', marker='o', label=str(mdata[index]['depth'])
        )
        self.__plot1.legend()
        self.__plot1.plot(
            time_series[0][:int(start_index) + 1],
            masked_temperatures[valid_start:int(start_index) + 1 + int(valid_start)],
            '-', color='red', marker='o', label=str(mdata[index]['depth'])
        )
        self.__plot1.set(
            ylabel='Temperature (DEG C)',
            title=(files[index] + "\n"
                   + 'Depth:' + str(mdata[index]['depth'])
                   + "  –  Region: " + str(mdata[index]['region']))
        )

        if indexes.size != 0:
            if indexes[0] + 1 == len(time_series[0]):
                self.__plot2.plot(
                    time_series[1][:int(indexes[0])],
                    masked_temperatures[-len(time_series[1]):
                                        (int(indexes[0]) - len(time_series[1]))],
                    '-', color='steelblue', marker='o',
                    label=str(mdata[index]['depth'])
                )
            else:
                self.__plot2.plot(
                    time_series[1][:int(indexes[0] + 1)],
                    masked_temperatures[-len(time_series[1]):
                                        (int(indexes[0]) - len(time_series[1]) + 1)],
                    '-', color='steelblue', marker='o',
                    label=str(mdata[index]['depth'])
                )
            self.__plot2.legend()
            self.__plot2.plot(
                time_series[1][int(indexes[0]):],
                masked_temperatures[(int(indexes[0]) - len(time_series[1])):],
                '-', color='red', marker='o', label=str(mdata[index]['depth'])
            )
            self.__plot2.set(
                ylabel='Temperature (DEG C)',
                title=(files[index] + "\n"
                       + 'Depth:' + str(mdata[index]['depth'])
                       + "  –  Region: " + str(mdata[index]['region']))
            )
        else:
            self.__plot2.plot(
                time_series[1], masked_temperatures[-len(time_series[1]):],
                '-', color='steelblue', marker='o', label=str(mdata[index]['depth'])
            )
            self.__plot2.legend()
            self.__plot2.set(
                ylabel='Temperature (DEG C)',
                title=(files[index] + "\n"
                       + 'Depth:' + str(mdata[index]['depth'])
                       + "  –  Region: " + str(mdata[index]['region']))
            )

        if not controller:
            self.fig.canvas.mpl_connect(
                'button_press_event',
                lambda event: cut_data_manually(event, index)
            )

        self.canvas.draw()
        self.console_writer('Plotting zoom of depth: ', 'action', mdata[0]['depth'])
        self.console_writer(' at site ', 'action', mdata[0]['region'], True)

    def plot_all_zoom(self, mdata, list_adapter):
        self.clear_plots()
        index = list_adapter._w.selectedIndexes()
        rows  = [i.row() for i in index]

        for item in rows:
            self.counter.append(item)
        self.counter.append('Zoom')

        depths = ""
        if not self.__plot1.axes:
            self.__plot1 = self.fig.add_subplot(211)
            self.__plot2 = self.fig.add_subplot(212)

        for i in rows:
            time_series, temperatures, _, bad, bad2, bad3 = self.dm.zoom_data(mdata[i])
            depths = depths + " " + str(mdata[i]['depth'])

            masked_temperatures = np.ma.masked_where(
                np.array(mdata[i]['df']['Temp']) == 999,
                np.array(mdata[i]['df']['Temp'])
            )
            self.__plot1.plot(time_series[0], masked_temperatures[:len(time_series[0])],
                              '-', label=str(mdata[i]['depth']))
            self.__plot1.set(
                ylabel='Temperature (DEG C)',
                title='Temperature at depths:' + depths
                      + "  –  Region: " + str(mdata[i]['region'])
            )
            self.__plot1.legend()

            self.__plot2.plot(time_series[1], masked_temperatures[-len(time_series[1]):],
                              '-', label=str(mdata[i]['depth']))
            self.__plot2.set(
                ylabel='Temperature (DEG C)',
                title='Temperature at depths:' + depths
                      + "  –  Region: " + str(mdata[i]['region'])
            )
            self.__plot2.legend()
            self.canvas.draw()

        self.console_writer('Plotting zoom of depths: ', 'action', depths)
        self.console_writer(' at site ', 'action', mdata[0]['region'], True)

    # ------------------------------------------------------------------
    # Difference / filter plots
    # ------------------------------------------------------------------

    def plot_dif(self):
        self.clear_plots()
        depths = ""
        try:
            dfdelta, _ = self.dm.temp_difference()
            self.counter.append('Difference')
            if self.__plot1.axes:
                plt.Axes.remove(self.__plot1)
                plt.Axes.remove(self.__plot2)
            self.__plot = self.fig.add_subplot(111)
            dfdelta.plot(ax=self.__plot)
            self.__plot.set(ylabel='Temperature (DEG C)',
                            title='Temperature differences')
            self.__plot.legend()
            self.canvas.draw()
            self.console_writer('Plotting zoom of depths: ', 'action', depths)
            self.console_writer(' at site ', 'action', self.dm.mdata[0]['region'], True)
        except UnboundLocalError:
            self.console_writer('Load more than a file for plotting the difference',
                                'warning')

    def plot_dif_filter1d(self):
        self.clear_plots()
        depths = ""
        try:
            dfdelta = self.dm.apply_uniform_filter()
            self.counter.append("Filter")
            if self.__plot1.axes:
                plt.Axes.remove(self.__plot1)
                plt.Axes.remove(self.__plot2)
            for _, rows in dfdelta.iterrows():
                for row in rows:
                    if float(row) <= -0.2:
                        self.console_writer('Attention, value under -0.2 threshold',
                                            'warning')
                        self.reportlogger.append('Attention, value under -0.2 threshold')
                        break
                else:
                    continue
                break
            self.__plot = self.fig.add_subplot(111)
            dfdelta.plot(ax=self.__plot)
            self.__plot.set(ylabel='Temperature (DEG C)',
                            title='Temperature differences filtered')
            self.__plot.legend()
            self.canvas.draw()
            self.console_writer('Plotting filter of depths: ', 'action', depths)
            self.console_writer(' at site ', 'action', self.dm.mdata[0]['region'], True)
        except UnboundLocalError:
            self.console_writer('Load more than a file for plotting the difference',
                                'warning')

    # ------------------------------------------------------------------
    # Hovmöller
    # ------------------------------------------------------------------

    def plot_hovmoller(self, mdata):
        try:
            self.clear_plots()
            self.counter.append("Hovmoller")
            df, depths, _ = self.dm.list_to_df()
            depths = np.array(depths)
            if self.__plot1.axes:
                plt.Axes.remove(self.__plot1)
                plt.Axes.remove(self.__plot2)
            self.__plot = self.fig.add_subplot(111)
            levels = np.arange(np.floor(np.nanmin(df.values)),
                               np.ceil(np.nanmax(df.values)), 1)
            cf = self.__plot.contourf(df.index.to_pydatetime(), -depths,
                                     df.values.T, 256, extend='both',
                                     cmap='RdYlBu_r')
            self.__cb = plt.colorbar(cf, ax=self.__plot,
                                     label='Temperature (ºC)', ticks=levels)
            self.__cbexists = True
            self.__plot.set(ylabel='Depth (m)',
                            title='Stratification  Site: ' + mdata[0]['region_name'])
            locator = mdates.MonthLocator()
            self.__plot.xaxis.set_major_locator(locator)
            self.__plot.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
            self.__plot.xaxis.tick_top()
            self.canvas.draw()
            self.console_writer('Plotting HOVMÖLLER at region: ', 'action',
                                mdata[0]['region'], True)
        except IndexError:
            self.console_writer('Load several files before creating a diagram', 'warning')
        except TypeError:
            self.console_writer('Load more than a file for the Hovmöller Diagram',
                                'warning')

    # ------------------------------------------------------------------
    # Stratification
    # ------------------------------------------------------------------

    def plot_stratification(self, historical, year):
        df, hismintemp, hismaxtemp, bad = self.dm.historic_to_df(historical, year)
        try:
            self.clear_plots()
            self.counter.append("Stratification")
            depths = np.array(list(map(float, list(df.columns))))
            if self.__plot1.axes:
                plt.Axes.remove(self.__plot1)
                plt.Axes.remove(self.__plot2)
            self.__plot = self.fig.add_subplot(111)

            if depths[-1] < 40:
                self.__plot.set_ylim(0, -40)
                self.__plot.set_yticks(-np.insert(depths, [0, -1], [0, 40]))
            else:
                self.__plot.set_ylim(0, -depths[-1])
                self.__plot.set_yticks(-np.insert(depths, 0, 0))

            self.__plot.set_xlim(
                datetime.strptime('01/05/' + year + ' 00:00:00', '%d/%m/%Y %H:%M:%S'),
                datetime.strptime('01/12/' + year + ' 00:00:00', '%d/%m/%Y %H:%M:%S')
            )
            self.__plot.invert_yaxis()

            dfcopy = df.copy()
            dfcopy.index = pd.to_datetime(dfcopy.index)
            dfcopy = dfcopy.loc[(dfcopy.index.month >= 5) & (dfcopy.index.month < 12)]
            levels  = np.arange(np.floor(hismintemp), hismaxtemp, 1)
            levels2 = np.arange(np.floor(hismintemp), hismaxtemp, 0.1)

            df_datetime = pd.to_datetime(df.index)
            old = df_datetime[0]
            index_cut = None
            df_cuts = []
            for i in df_datetime[1:]:
                new = i
                diff_d = new - old
                old = new
                if diff_d.days > 0:
                    index_old = 0
                    index_cut = df_datetime.get_loc(i)
                    df_cuts.append(df[index_old:index_cut])
                    index_old = index_cut

            if len(depths) == 1:
                depths = np.insert(depths, 1, depths[0] + 2.5)
                depths = np.insert(depths, 0, depths[0] - 2.5)
                df.insert(0, str(depths[0]), df[str(depths[1])])
                df.insert(2, str(depths[2]), df[str(depths[1])])

            if index_cut:
                df_cuts.append(df[index_cut:])
                cf = []
                for i in range(len(df_cuts)):
                    cf.append(self.__plot.contourf(
                        pd.to_datetime(df_cuts[i].index), -depths,
                        df_cuts[i].values.T, 256, extend='both',
                        cmap='RdYlBu_r', levels=levels2
                    ))
                self.__cb = plt.colorbar(cf[0], ax=self.__plot,
                                         label='Temperature (ºC)', ticks=levels)
            else:
                str_depths = [f'{x:g}' for x in depths]
                vertical_split = []
                for i in range(len(depths)):
                    if i < len(depths) - 1:
                        res = depths[i + 1] - depths[i]
                        if res > 10.:
                            vertical_split.append(i)
                if vertical_split:
                    old_index = 0
                    for i in vertical_split:
                        self.__plot.contourf(
                            df_datetime, -depths[old_index:i + 1],
                            df.filter(items=str_depths[old_index:i + 1]).values.T,
                            256, extend='both', cmap='RdYlBu_r', levels=levels2
                        )
                        old_index = i + 1
                    cf = self.__plot.contourf(
                        df_datetime, -depths[old_index:],
                        df.filter(items=str_depths[old_index:]).values.T,
                        256, extend='both', cmap='RdYlBu_r', levels=levels2
                    )
                else:
                    cf = self.__plot.contourf(
                        df_datetime, -depths, df.values.T, 256,
                        extend='both', cmap='RdYlBu_r', levels=levels2
                    )
                self.__cb = plt.colorbar(cf, ax=self.__plot,
                                         label='Temperature (ºC)', ticks=levels)

            self.__cbexists = True
            self.__plot.set(ylabel='Depth (m)',
                            title=historical.split('_')[4] + '  year ' + year)
            self.savefilename = (historical.split('_')[3] + '_1_' + year
                                 + '_' + historical.split('_')[4])
            locator = mdates.MonthLocator()
            self.__plot.xaxis.set_major_locator(locator)
            self.__plot.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
            self.__plot.xaxis.tick_top()
            tick_depths = [-i for i in depths if i.is_integer()]
            self.__plot.set_yticks(tick_depths)
            self.canvas.draw()
            self.console_writer('Plotting STRATIFICATION at region: ', 'action',
                                historical.split('_')[3], True)
        except IndexError:
            self.console_writer('Load several files before creating a diagram', 'warning')
        except TypeError as e:
            self.console_writer(
                'Load more than a file for the Hovmöller Diagram: ' + str(e), 'warning')

    # ------------------------------------------------------------------
    # Annual T cycle
    # ------------------------------------------------------------------

    def plot_annual_T_cycle(self, historical, year):
        self.clear_plots()
        self.counter.append("Cycles")

        histdf = pd.read_csv(historical, sep='\t')
        depths = histdf.columns[2:]
        histdf.drop(histdf.loc[histdf['Date'].isnull()].index, inplace=True)
        histdf['day']   = pd.DatetimeIndex(histdf['Date'], dayfirst=True).day
        histdf['month'] = pd.DatetimeIndex(histdf['Date'], dayfirst=True).month
        histdf['day_month'] = (histdf['day'].astype(str) + '-'
                               + histdf['month'].astype(str))
        histdf['day_month'] = histdf['day_month'] + '-' + year
        if not pd.to_datetime(year).is_leap_year:
            histdf.drop(
                histdf['day_month'].loc[histdf['day_month']
                                        == '29-2-' + str(year)].index,
                inplace=True
            )
        histdf['day_month'] = pd.DatetimeIndex(histdf['day_month'], dayfirst=True)
        orderedhist_df = histdf.groupby('day_month')[depths].mean()
        orderedhist_df.sort_index(inplace=True)

        year_df, hismintemp, hismaxtemp, minyear = self.dm.historic_to_df(
            historical, year, start_month='01', end_month='01')
        year_df.index = year_df.index.strftime('%Y-%m-%d %H:%M:%S')
        if '0' in year_df.columns:
            year_df.drop('0', axis=1, inplace=True)

        year_df        = self.dm.running_average_special(year_df, running=360)
        orderedhist_df = self.dm.running_average_special(orderedhist_df, running=30)
        orderedhist_df.index = pd.DatetimeIndex(orderedhist_df.index)

        daylist = []
        for time_val in year_df.index:
            if str(time_val) == 'nan':
                pass
            else:
                old = datetime.strftime(time_val, '%Y-%m-%d')
                new = datetime.strptime(old, '%Y-%m-%d')
            daylist.append(new)
        year_df['day'] = daylist

        newdf = None
        for depth in year_df.columns:
            if depth != 'day':
                if newdf is not None:
                    newdf = pd.merge(newdf, year_df.groupby('day')[depth].mean(),
                                     right_index=True, left_index=True)
                else:
                    newdf = pd.DataFrame(year_df.groupby('day')[depth].mean())
        idx = pd.date_range(newdf.index[0], newdf.index[-1])
        newdf = newdf.reindex(idx, fill_value=np.nan)

        if self.__plot1.axes:
            plt.Axes.remove(self.__plot1)
            plt.Axes.remove(self.__plot2)
        self.__plot = self.fig.add_subplot(111)

        color_dict = {
            '5':  '#d4261d', '10': '#f58e6e', '15': '#fca95a', '20': '#fde5a3',
            '25': '#e4f4f8', '30': '#a7d6e7', '35': '#9ec6de', '40': '#3a6daf',
            '45': '#214f8a', '50': '#0a3164',
        }
        for depth in newdf.columns:
            if newdf[depth].isnull().all():
                del newdf[depth]
        newdf.plot(ax=self.__plot, zorder=10,
                   color=[color_dict.get(x, '#333333') for x in newdf.columns])
        self.__plot.legend(title='Depth (m)')

        if str(minyear) != year:
            oldepth = 0
            for depth in orderedhist_df.columns:
                if oldepth != 0:
                    self.__plot.fill_between(
                        np.unique(orderedhist_df.index),
                        orderedhist_df[oldepth], orderedhist_df[depth],
                        facecolor='lightgrey', zorder=0
                    )
                oldepth = depth
                orderedhist_df.plot(kind='line', ax=self.__plot, color='#e9e8e8',
                                    label='_nolegend_', legend=False, zorder=5)

        self.__plot.set(ylabel='Temperature (ºC) smoothed',
                        title=historical.split('_')[4] + '  year ' + year)
        self.__plot.set_yticks(np.arange(10, hismaxtemp, 2))
        self.__plot.set_xlim([year + '-01-01 00:00:00',
                              str(int(year) + 1) + '-01-01 00:00:00'])
        self.savefilename = (historical.split('_')[3] + '_2_' + year
                             + '_' + historical.split('_')[4])
        locator = mdates.MonthLocator()
        self.__plot.xaxis.set_major_locator(locator)
        self.__plot.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        self.__plot.xaxis.set_label_text('foo').set_visible(False)
        self.__plot.text(0.1, 0.1, "multi-year mean", backgroundcolor='grey')
        self.canvas.draw()

    # ------------------------------------------------------------------
    # Thresholds
    # ------------------------------------------------------------------

    def plot_thresholds(self, historical, toolbar_unused, consolescreen_unused,
                        special=False):
        """
        Creates the heat-spike threshold plot.

        The toolbar and consolescreen parameters are accepted for backward
        compatibility but are ignored — threshold buttons are created via
        self._add_threshold_btn callback, and log messages use self.console_writer.
        """
        self.clear_plots()
        self.counter.append("Thresholds")
        df = self.dm.thresholds_df(historical)
        df['year']     = df['year'].astype(str)
        df['depth(m)'] = df['depth(m)'].astype(str)
        df['N'].replace(0, np.nan, inplace=True)

        dfhist_control = pd.read_csv(historical, sep='\t', dayfirst=True)
        dfhist_control['Date']  = pd.to_datetime(dfhist_control['Date'], dayfirst=True)
        dfhist_control['year']  = pd.DatetimeIndex(dfhist_control['Date'], dayfirst=True).year
        dfhist_control['month'] = pd.DatetimeIndex(dfhist_control['Date'], dayfirst=True).month
        dfhist_summer = dfhist_control.loc[
            dfhist_control['month'].isin([7, 8, 9])]

        depths = df['depth(m)'].unique()
        years  = df['year'].unique()
        years  = years[years != 0]

        if special:
            depths = ['10', '15', '20', '25']
            years  = years[[13, 14, 15, 20]]
            df = df[~df['depth(m)'].isin(['5', '30', '35', '40'])]

        for depth in depths:
            depth = str(depth)
            for year in df['year'].unique():
                if (dfhist_summer.loc[dfhist_summer['year'] == int(year)][depth].isnull().all()) or \
                   (dfhist_summer.loc[dfhist_summer['year'] == int(year)][depth].count() / 24 < 30):
                    for i in range(23, 29):
                        df.loc[(df['year'] == str(year)) & (df['depth(m)'] == depth),
                               'Ndays>=' + str(i)] = np.nan

        if self.__plot1.axes:
            plt.Axes.remove(self.__plot1)
            plt.Axes.remove(self.__plot2)
        self.__plot = self.fig.add_subplot(111)

        markers = ['+', 'o', 'x', 's', 'd', '^', 'v', 'p', 'h', '*']
        colors  = ['b', 'b', 'k', 'k']
        lines   = ['solid', 'dotted', 'solid', 'dotted']

        maxdepth = 0
        maxdays  = 0
        temperatures = {23: [], 24: [], 25: [], 26: [], 28: []}
        year_dict    = {}
        legend_years = years.copy()

        for year in years:
            maxndays = np.nanmax(df.loc[df['year'] == year]['N'])
            check = False
            for ni in df.loc[df['year'] == year].index:
                if maxndays - df['N'][ni] > 240:
                    df['N'][ni] = np.nan
                    for j in range(23, 29):
                        df['Ndays>=' + str(j)][ni] = np.nan
                if df['N'][ni] < 2208:
                    check = True
                else:
                    check = False
            if check:
                legend_years[np.where(legend_years == year)[0][0]] = year + '*'
                check = False
            for i in range(23, 29):
                yearly_plot = np.column_stack((
                    df.loc[df['year'] == year, 'Ndays>=' + str(i)],
                    df.loc[df['year'] == year, 'depth(m)']
                ))
                yearly_plot[pd.isnull(yearly_plot)] = -999
                yearly_plot = yearly_plot.astype(int)
                if yearly_plot[-1, -1] > maxdepth:
                    maxdepth = yearly_plot[-1, -1]
                if np.max(yearly_plot[:, 0]) > maxdays:
                    maxdays = np.max(yearly_plot[:, 0])
                temperatures[i] = np.ma.masked_where(yearly_plot == -999, yearly_plot)
            year_dict[year] = temperatures.copy()

            self.__plot.set(ylim=(0, maxdepth + 2))
            ticks = 10 if maxdays >= 30 else (5 if maxdays >= 20 else 2)
            self.__plot.set(xlim=(-2, maxdays + 2),
                            xticks=np.arange(0, maxdays + 2, ticks))

            seq_type = type(year)
            int_year = int(seq_type().join(filter(seq_type.isdigit, year)))

            if int_year < 2000:
                color = 'tab:orange' if year == years[-1] else colors[0]
                self.__plot.plot(year_dict[year][23][:, 0], year_dict[year][23][:, 1],
                                 marker=markers[int_year - 1990],
                                 color=color, linestyle=lines[0])
            elif int_year < 2010:
                color = 'tab:orange' if year == years[-1] else colors[1]
                self.__plot.plot(year_dict[year][23][:, 0], year_dict[year][23][:, 1],
                                 marker=markers[int_year - 2000],
                                 color=color, linestyle=lines[1])
            elif int_year < 2020:
                color = 'tab:orange' if year == years[-1] else colors[2]
                self.__plot.plot(year_dict[year][23][:, 0], year_dict[year][23][:, 1],
                                 marker=markers[int_year - 2010],
                                 color=color, linestyle=lines[2])
            elif int_year < 2030:
                color = 'tab:orange' if year == years[-1] else colors[3]
                self.__plot.plot(year_dict[year][23][:, 0], year_dict[year][23][:, 1],
                                 marker=markers[int_year - 2020],
                                 color=color, linestyle=lines[3])

            self.__plot.invert_yaxis()
            self.__plot.xaxis.tick_top()
            self.canvas.draw()

        box = self.__plot.get_position()
        self.__plot.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        self.__plot.legend(legend_years, title='Year', loc='center left',
                           bbox_to_anchor=(1, 0.5))
        self.__plot.set(ylabel='Depth (m)',
                        title=historical.split('_')[4] + '  Summer (JAS) days ≥ 23ºC')
        self.__plot.xaxis.grid(True, linestyle='dashed')
        p = self.__plot.get_window_extent()
        self.__plot.annotate(
            '*Recorded period not complete', xy=(0.68, 0.03), xycoords=p,
            xytext=(0.1, 0), textcoords="offset points",
            va="center", ha="left", bbox=dict(boxstyle="round", fc="#0E1F33", ec="#1E3050", alpha=0.9)
        )
        self.canvas.draw()

        # Create threshold-temperature buttons via callback (backend-agnostic)
        year_str = year if 'year' in dir() else ""
        for i in range(23, 29):
            tab = {}
            if self._add_threshold_btn:
                btn_ref = self._add_threshold_btn(
                    str(i),
                    lambda i=i: self.__raiseTab(
                        i, maxdepth, year_dict, markers, colors, lines,
                        years, maxdays, historical, legend_years
                    )
                )
            else:
                btn_ref = None
            tab['id']  = i
            tab['btn'] = btn_ref
            self.__tabs[i] = tab
        self.__curtab = 23
        self.savefilename = (historical.split('_')[3] + '_3_23_'
                             + year_str + '_' + historical.split('_')[4])

    def __raiseTab(self, i, maxdepth, year_dict, markers, colors, lines,
                   years, maxdays, historical, legend_years):
        if self.__curtab is not None and self.__curtab != i and len(self.__tabs) > 1:
            self.clear_plots(clear_thresholds=False)
            self.counter.append('Thresholds')
            self.__plot = self.fig.add_subplot(111)
            ticks = 10 if maxdays >= 30 else (5 if maxdays >= 20 else 2)
            self.__plot.set(ylim=(0, maxdepth + 2))
            self.__plot.set(xlim=(-2, maxdays + 2),
                            xticks=np.arange(0, maxdays + 2, ticks))

            for year in years:
                seq_type = type(year)
                int_year = int(seq_type().join(filter(seq_type.isdigit, year)))

                if int_year < 2000:
                    color = 'tab:orange' if year == years[-1] else colors[0]
                    self.__plot.plot(year_dict[year][i][:, 0], year_dict[year][i][:, 1],
                                     marker=markers[int_year - 1990],
                                     color=color, linestyle=lines[0])
                elif int_year < 2010:
                    color = 'tab:orange' if year == years[-1] else colors[1]
                    self.__plot.plot(year_dict[year][i][:, 0], year_dict[year][i][:, 1],
                                     marker=markers[int_year - 2000],
                                     color=color, linestyle=lines[1])
                elif int_year < 2020:
                    color = 'tab:orange' if year == years[-1] else colors[2]
                    self.__plot.plot(year_dict[year][i][:, 0], year_dict[year][i][:, 1],
                                     marker=markers[int_year - 2010],
                                     color=color, linestyle=lines[2])
                elif int_year < 2030:
                    color = 'tab:orange' if year == years[-1] else colors[3]
                    self.__plot.plot(year_dict[year][i][:, 0], year_dict[year][i][:, 1],
                                     marker=markers[int_year - 2020],
                                     color=color, linestyle=lines[3])

            self.__plot.invert_yaxis()
            self.__plot.xaxis.tick_top()
            box = self.__plot.get_position()
            self.__plot.set_position([box.x0, box.y0, box.width * 0.8, box.height])
            self.__plot.legend(legend_years, title='Year', loc='center left',
                               bbox_to_anchor=(1, 0.5))
            self.__plot.set(ylabel='Depth (m)',
                            title=historical.split('_')[4]
                            + '  Summer(JAS) days ≥ ' + str(i) + 'ºC')
            year_str = ""
            self.savefilename = (historical.split('_')[3] + '_3_' + str(i)
                                 + '_' + year_str + '_' + historical.split('_')[4])
            p = self.__plot.get_window_extent()
            self.__plot.annotate(
                '*Recorded period not complete', xy=(0.61, 0.03), xycoords=p,
                xytext=(0.1, 0), textcoords="offset points",
                va="center", ha="left", bbox=dict(boxstyle="round", fc="#0E1F33", ec="#1E3050", alpha=0.9)
            )
            self.__plot.xaxis.grid(True, linestyle='dashed')
            self.canvas.draw()

        self.__curtab = i
        self.console_writer("Plotting for over " + str(i) + " degrees", "action")

    # ------------------------------------------------------------------
    # Clear
    # ------------------------------------------------------------------

    def clear_plots(self, clear_thresholds=True):
        self.console_writer('Clearing Plots', 'action')
        self.index   = []
        self.counter = []
        if self.__plot.axes:
            self.__plot.clear()
            plt.Axes.remove(self.__plot)
        if self.__plot1.axes:
            self.__plot1.clear()
            self.__plot2.clear()
            plt.Axes.remove(self.__plot1)
            plt.Axes.remove(self.__plot2)
        if self.__cbexists:
            if self.__cb is not None:
                try:
                    self.__cb.remove()
                except Exception:
                    pass
            self.__cbexists = False
        if clear_thresholds:
            if self._clear_threshold_btns:
                self._clear_threshold_btns()
            self.__tabs    = {}
            self.__curtab  = None
        self.canvas.draw()
