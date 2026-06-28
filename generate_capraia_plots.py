"""
Generates 4 T-MEDNet website-style plots for Capraia (site 252), one set per year.
  Desktop\Capraia_2025\  →  4 plots with 2025 data  (Sep–Dec 2025)
  Desktop\Capraia_2026\  →  4 plots with 2026 data  (Jan–Apr 2026)

Format matches gui_plots.py and surface_temperature.py exactly.
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core'))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from scipy.ndimage import uniform_filter1d

# ── Config ────────────────────────────────────────────────────────────────────
TXT_DIR   = r"C:\Users\jahan\AppData\Local\Temp\hobo_export"
DESKTOP   = os.path.join(os.path.expanduser("~"), "Desktop")
SITE_NAME = "Capraia"
SITE_CODE = 252
DPI       = 150

plt.rc('legend', fontsize='medium')

# ── Load data ─────────────────────────────────────────────────────────────────
from data_manager import DataManager

class _Console:
    def __call__(self, msg, mode='info', *a): print(f"[{mode}] {msg}")

dm = DataManager(_Console(), [])

txts = sorted([
    os.path.join(TXT_DIR, f).replace("\\", "/")
    for f in os.listdir(TXT_DIR) if f.endswith(".txt")
])
print(f"Loading {len(txts)} files...")

class _TextBox:
    def insert(self, *a): pass
    def delete(self, *a): pass
    def get(self, *a): return ""

class _Lister:
    def __init__(self): self._items = []
    def size(self): return len(self._items)
    def insert(self, i, item): self._items.append(item)

lister = _Lister()
dm.openfile(tuple(txts), _TextBox(), lister)
dm.files = lister._items
dm.newfiles = len(dm.files)
dm.load_data()
print(f"Loaded {len(dm.mdata)} depths")

# Trim each depth to the deployment window encoded in the filename.
# datainici/datafin are parsed from the filename (e.g. 252_20250925-09_20260410-12_05.txt)
# and represent when the diver placed/retrieved the sensor at the correct depth.
# Data outside that window is recorded while the sensor was at the surface or mid-water.
for dat in dm.mdata:
    t0 = dat['datainici']
    t1 = dat['datafin']
    before = len(dat['df'])
    dat['df'] = dat['df'].loc[(dat['df'].index >= t0) & (dat['df'].index <= t1)]
    trimmed = before - len(dat['df'])
    if trimmed:
        print(f"  Depth {dat['depth']}m: trimmed {trimmed} rows outside [{t0} – {t1}]")

df_all, depths_int, _ = dm.list_to_df()
depths_insitu = np.array(depths_int, dtype=float)
depth_strs_insitu = [str(int(d)) for d in depths_insitu]
df_all.columns = depth_strs_insitu
df_all.index = pd.to_datetime(df_all.index)
df_all = df_all.sort_index()

# ── Integrate Copernicus SST as depth 0m ──────────────────────────────────────
SST_CSV = r"C:\Users\jahan\AppData\Local\Temp\hobo_export\capraia_sst_copernicus.csv"
if os.path.exists(SST_CSV):
    sst_daily = pd.read_csv(SST_CSV, index_col=0, parse_dates=True)
    sst_daily.index = pd.to_datetime(sst_daily.index).tz_localize(None)
    sst_daily.columns = ['0']
    # Interpolate daily SST to hourly to match in-situ resolution
    sst_hourly = sst_daily.resample('h').interpolate(method='linear')
    # Align to df_all index and prepend as column '0'
    sst_aligned = sst_hourly.reindex(df_all.index, method='nearest', tolerance=pd.Timedelta('2h'))
    df_all.insert(0, '0', sst_aligned['0'])
    print(f"Copernicus SST loaded: {sst_aligned['0'].notna().sum()} hourly values at 0m")

# Depths now include 0m from Copernicus + 5–40m from sensors
depth_strs = [c for c in df_all.columns]
depths = np.array([float(d) for d in depth_strs])

print(f"Full range: {df_all.index[0]} to {df_all.index[-1]}")
print(f"Depths: {depth_strs}")


# ═════════════════════════════════════════════════════════════════════════════
# Plot functions — each receives the year-filtered DataFrame
# ═════════════════════════════════════════════════════════════════════════════

def plot_stratification(df, year, out_dir):
    from datetime import datetime as dt

    yr = int(year)
    t_may = dt(yr, 5, 1)
    t_dec = dt(yr, 12, 1)

    # Only contourf where there is data inside May–Dec window
    df_window = df[(df.index >= pd.Timestamp(t_may)) & (df.index < pd.Timestamp(t_dec))]

    fig = plt.figure(figsize=(10, 5))
    ax = fig.add_subplot(111)

    # Y-axis: same setup as plot_stratification in gui_plots.py
    max_depth = depths[-1]
    if max_depth < 40:
        ax.set_ylim(0, -40)
    else:
        ax.set_ylim(0, -max_depth)
    ax.invert_yaxis()
    tick_depths = [-d for d in depths if d == int(d)]
    ax.set_yticks(tick_depths)

    # X-axis: always May 1 – Dec 1 of the year
    ax.set_xlim(t_may, t_dec)

    if not df_window.empty:
        hismintemp = np.nanmin(df_window.values)
        hismaxtemp = np.nanmax(df_window.values)
        levels  = np.arange(np.floor(hismintemp), hismaxtemp, 1)
        levels2 = np.arange(np.floor(hismintemp), hismaxtemp, 0.1)
        cf = ax.contourf(df_window.index.to_pydatetime(), -depths,
                         df_window.values.T, 256, extend='both',
                         cmap='RdYlBu_r', levels=levels2)
        plt.colorbar(cf, ax=ax, label='Temperature (ºC)', ticks=levels)

    ax.set(ylabel='Depth (m)',
           title=f'{SITE_NAME} {year}')

    locator = mdates.MonthLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax.xaxis.tick_top()

    t0, t1 = df.index[0], df.index[-1]
    out = os.path.join(out_dir,
        f"capraia_{SITE_CODE}_stratification_{t0.strftime('%Y%m%d')}_{t1.strftime('%Y%m%d')}.png")
    fig.savefig(out, dpi=DPI, bbox_inches='tight')
    plt.close(fig)
    print(f"  [strat]     {os.path.basename(out)}  ({os.path.getsize(out)//1024} KB)")


def plot_annual_T_cycle(df, year, out_dir):
    color_dict = {
        '5':  '#d4261d', '10': '#f58e6e', '15': '#fca95a', '20': '#fde5a3',
        '25': '#e4f4f8', '30': '#a7d6e7', '35': '#9ec6de', '40': '#3a6daf',
        '45': '#214f8a', '50': '#0a3164',
    }

    # Running average (size=360) then daily mean — same as app
    df_smooth = df[depth_strs].copy()
    for col in depth_strs:
        valid = df_smooth[col].dropna()
        if len(valid) >= 2:
            df_smooth.loc[valid.index, col] = uniform_filter1d(
                valid.values, size=min(360, len(valid)))

    daylist = [ts.normalize() for ts in df_smooth.index]
    df_smooth['day'] = daylist

    newdf = None
    for depth in depth_strs:
        grp = df_smooth.groupby('day')[depth].mean()
        newdf = pd.DataFrame(grp) if newdf is None else pd.merge(
            newdf, grp, left_index=True, right_index=True)

    idx = pd.date_range(newdf.index[0], newdf.index[-1])
    newdf = newdf.reindex(idx, fill_value=np.nan)

    fig = plt.figure(figsize=(10, 5))
    ax = fig.add_subplot(111)

    newdf.plot(ax=ax, zorder=10,
               color=[color_dict.get(x, '#333333') for x in newdf.columns])
    ax.legend(title='Depth (m)')

    hismaxtemp = np.nanmax(df.values) + 1
    ax.set(ylabel='Temperature (ºC) smoothed',
           title=f'{SITE_NAME}  year {year}')
    ax.set_yticks(np.arange(10, int(hismaxtemp) + 1, 2))
    ax.set_xlim([f'{year}-01-01 00:00:00', f'{int(year)+1}-01-01 00:00:00'])

    locator = mdates.MonthLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax.xaxis.set_label_text('').set_visible(False)

    t0, t1 = df.index[0], df.index[-1]
    out = os.path.join(out_dir,
        f"capraia_{SITE_CODE}_annual_T_cycle_{t0.strftime('%Y%m%d')}_{t1.strftime('%Y%m%d')}.png")
    fig.savefig(out, dpi=DPI, bbox_inches='tight')
    plt.close(fig)
    print(f"  [T cycle]   {os.path.basename(out)}  ({os.path.getsize(out)//1024} KB)")


def plot_thresholds(df, year, out_dir):
    df_jas = df[(df.index.month >= 7) & (df.index.month <= 9)][depth_strs].copy()

    if df_jas.empty:
        print(f"  [thresh]    No JAS data for {year} — skipped")
        return

    df_jas['year'] = df_jas.index.year.astype(str)
    years = sorted(df_jas['year'].unique())
    markers = ['+', 'o', 'x', 's', 'd', '^', 'v', 'p', 'h', '*']
    colors  = ['b', 'b', 'k', 'k']
    lines   = ['solid', 'dotted', 'solid', 'dotted']

    maxdepth = int(max(depths))
    year_dict = {}
    legend_years = list(years)

    for yr in years:
        yr_daily = df_jas[df_jas['year'] == yr][depth_strs].resample('D').max()
        temps = {}
        for thr in range(23, 28):
            ndays   = np.array([(yr_daily[d] >= thr).sum() for d in depth_strs])
            dep_arr = np.array([int(d) for d in depth_strs])
            temps[thr] = np.column_stack((ndays, dep_arr))
        year_dict[yr] = temps

    t0, t1 = df.index[0], df.index[-1]

    for thr in range(23, 28):
        maxdays = max(
            int(np.max(year_dict[yr][thr][:, 0])) for yr in years
        )

        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        ax.set(ylim=(0, maxdepth + 2))
        ticks = 10 if maxdays >= 30 else (5 if maxdays >= 20 else 2)
        ax.set(xlim=(-2, max(maxdays + 2, 5)),
               xticks=np.arange(0, max(maxdays + 2, 5), ticks))

        for i, yr in enumerate(years):
            int_yr = int(yr)
            color  = 'tab:orange' if yr == years[-1] else colors[min(i, len(colors)-1)]
            ls     = lines[min(i, len(lines)-1)]
            if int_yr < 2000:
                mk = markers[int_yr - 1990]
            elif int_yr < 2010:
                mk = markers[int_yr - 2000]
            elif int_yr < 2020:
                mk = markers[int_yr - 2010]
            else:
                mk = markers[int_yr - 2020]

            arr = year_dict[yr][thr]
            ax.plot(arr[:, 0], arr[:, 1], marker=mk, color=color, linestyle=ls)

        ax.invert_yaxis()
        ax.xaxis.tick_top()
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        ax.legend(legend_years, title='Year', loc='center left', bbox_to_anchor=(1, 0.5))
        ax.set(ylabel='Depth (m)',
               title=f'{SITE_NAME}  Summer (JAS) days ≥ {thr}ºC  {year}')
        ax.xaxis.grid(True, linestyle='dashed')

        out = os.path.join(out_dir,
            f"capraia_{SITE_CODE}_thresholds_{thr}C_{t0.strftime('%Y%m%d')}_{t1.strftime('%Y%m%d')}.png")
        fig.savefig(out, dpi=DPI, bbox_inches='tight')
        plt.close(fig)
        print(f"  [thresh {thr}C]  {os.path.basename(out)}  ({os.path.getsize(out)//1024} KB)")


def plot_anomaly(df, year, out_dir):
    depths_to_use = [d for d in depth_strs if d in ['10', '25', '40']]
    if not depths_to_use:
        depths_to_use = [depth_strs[1], depth_strs[len(depth_strs)//2], depth_strs[-1]]

    target_year = int(year)
    first_year  = target_year

    data = df[depths_to_use].copy()
    data.insert(0, 'day',   data.index.day)
    data.insert(1, 'month', data.index.month)
    data.insert(2, 'year',  data.index.year)

    last_legend_dict = {}
    this_legend_dict = {}
    concated = None

    for depth in depths_to_use:
        last_years_legend = f"{first_year}-{target_year-1} Climatology ({depth}m)"
        this_year_legend  = f"{target_year} ({depth}m)"
        last_legend_dict[depth] = last_years_legend
        this_legend_dict[depth] = this_year_legend

        depth_data = data[['day', 'month', 'year', depth]].dropna(subset=[depth])
        filtered   = uniform_filter1d(depth_data[depth].values,
                                      size=min(360, len(depth_data)))
        df_filt = depth_data.copy()
        df_filt[depth] = filtered

        last_means = (df_filt
                      .groupby(['day', 'month'], as_index=False)
                      .mean(numeric_only=True)
                      .rename(columns={depth: last_years_legend})
                      .drop('year', axis=1))
        last_means.sort_values(['month', 'day'], inplace=True)
        last_means['date'] = pd.to_datetime(
            '2020/' + last_means['month'].astype(int).astype(str)
            + '/' + last_means['day'].astype(int).astype(str))
        last_means.set_index('date', inplace=True)
        last_means.drop(['month', 'day'], axis=1, inplace=True)

        this_yr = (df_filt[df_filt['year'] == target_year]
                   .groupby(['day', 'month'], as_index=False)
                   .mean(numeric_only=True)
                   .rename(columns={depth: this_year_legend})
                   .drop('year', axis=1))
        this_yr.sort_values(['month', 'day'], inplace=True)
        this_yr['date'] = pd.to_datetime(
            '2020/' + this_yr['month'].astype(int).astype(str)
            + '/' + this_yr['day'].astype(int).astype(str))
        this_yr.set_index('date', inplace=True)
        this_yr.drop(['month', 'day'], axis=1, inplace=True)

        if concated is None:
            concated = pd.concat([last_means, this_yr], axis=1)
            prop = concated.index.strftime('%b')
        else:
            concated = pd.concat([concated, last_means, this_yr], axis=1)

    concated.index = concated.index.strftime('%m-%d')

    # Reindex to a full Jan–Dec year so the x-axis always spans the whole year
    full_year_idx = pd.date_range('2020-01-01', '2020-12-31', freq='D').strftime('%m-%d').tolist()
    concated = concated.reindex(full_year_idx)

    fig = plt.figure(figsize=(10, 5))
    ax = plt.axes()
    cycler = plt.cycler(linestyle=['-', '-'], color=['black', 'grey'],
                        alpha=[1., 0.7], linewidth=[0.7, 0.7])
    ax.set_prop_cycle(cycler)
    concated.plot(ax=ax)

    x_pos = range(len(concated))
    for depth in depths_to_use:
        y1 = concated[last_legend_dict[depth]].values
        y2 = concated[this_legend_dict[depth]].values
        ax.fill_between(x_pos, y1, y2, where=(y2 > y1), color='#fa5a5a')
        ax.fill_between(x_pos, y1, y2, where=(y2 < y1), color='#5aaaff')

    plt.xlabel('')
    month_ticks_str = ['01-01', '02-01', '03-01', '04-01', '05-01', '06-01',
                       '07-01', '08-01', '09-01', '10-01', '11-01', '12-01']
    idx_list = list(concated.index)
    tick_pos    = [idx_list.index(t) for t in month_ticks_str if t in idx_list]
    tick_labels = [pd.to_datetime('2020/' + t.replace('-', '/')).strftime('%b')
                   for t in month_ticks_str if t in idx_list]
    if tick_pos:
        plt.xticks(tick_pos, tick_labels)

    plt.xlim((0, len(concated) - 1))
    plt.title(f'Anomalies in {SITE_NAME} in {target_year}')
    handles, _ = plt.gca().get_legend_handles_labels()
    red_patch  = mpatches.Patch(color='#fa5a5a', label='[+] anomaly')
    blue_patch = mpatches.Patch(color='#5aaaff', label='[-] anomaly')
    plt.legend(handles=[handles[0], red_patch, blue_patch],
               labels=['Multi-Year Mean', '[+] anomaly', '[-] anomaly'])

    t0, t1 = df.index[0], df.index[-1]
    out = os.path.join(out_dir,
        f"capraia_{SITE_CODE}_anomaly_{t0.strftime('%Y%m%d')}_{t1.strftime('%Y%m%d')}.png")
    fig.savefig(out, dpi=DPI, bbox_inches='tight')
    plt.close(fig)
    print(f"  [anomaly]   {os.path.basename(out)}  ({os.path.getsize(out)//1024} KB)")


# ═════════════════════════════════════════════════════════════════════════════
# Generate one set of 4 plots per year
# ═════════════════════════════════════════════════════════════════════════════

for year in [2025, 2026]:
    df_year = df_all[df_all.index.year == year][depth_strs].copy()

    if df_year.empty:
        print(f"\nYear {year}: no data — skipped")
        continue

    t0, t1 = df_year.index[0], df_year.index[-1]
    print(f"\nYear {year}: {t0.strftime('%d %b %Y')} to {t1.strftime('%d %b %Y')} "
          f"({len(df_year)} rows)")

    out_dir = os.path.join(DESKTOP, f"Capraia_{year}")
    os.makedirs(out_dir, exist_ok=True)

    plot_stratification(df_year, str(year), out_dir)
    plot_annual_T_cycle(df_year, str(year), out_dir)
    plot_thresholds(df_year, str(year), out_dir)
    plot_anomaly(df_year, str(year), out_dir)

# ═════════════════════════════════════════════════════════════════════════════
# Database_T  (matriu de dades) — full deployment, in-situ sensors only
# ═════════════════════════════════════════════════════════════════════════════

insitu_cols = [c for c in depth_strs if c != '0']   # exclude Copernicus SST
df_insitu = df_all[insitu_cols].copy()

t0_all = df_insitu.index[0]
t1_all = df_insitu.index[-1]
date_range = f"{t0_all.strftime('%Y%m')}-{t1_all.strftime('%Y%m')}"
today_str  = pd.Timestamp.now().strftime('%Y-%m-%d')

db_filename = f"{SITE_CODE}_Database_T_{SITE_NAME}_{date_range}_{today_str}.txt"
db_path     = os.path.join(DESKTOP, db_filename)

df_db = df_insitu.copy()
df_db.insert(0, 'Date', df_insitu.index.strftime('%d/%m/%Y'))
df_db.insert(1, 'Time', df_insitu.index.strftime('%H:%M:%S'))
df_db.to_csv(db_path, sep='\t', index=False, float_format='%.3f')
print(f"\n[Database_T]  {db_filename}  ({os.path.getsize(db_path)//1024} KB)")

# ═════════════════════════════════════════════════════════════════════════════
# Excel Stat Report — generated from the Database_T
# ═════════════════════════════════════════════════════════════════════════════

from pandas import ExcelWriter as _ExcelWriter

df_ex = df_insitu.copy()
df_ex['Date']  = df_insitu.index.strftime('%d/%m/%Y')
df_ex['month'] = df_insitu.index.month
df_ex['year']  = df_insitu.index.year
df_ex_date = pd.to_datetime(df_insitu.index.strftime('%Y-%m-%d'))

daily_parts    = []
monthly_parts  = []
seasonal_parts = []

df_season = df_ex[df_ex['month'].isin([7, 8, 9])]

for col in insitu_cols:
    depth = int(col)

    # Daily
    agg_d = df_insitu.groupby(df_ex_date)[col].agg(['count','mean','std','max','min']).round(3)
    agg_d.columns = ['N','mean','std','max','min']
    agg_d = agg_d.reset_index().rename(columns={'index':'date'})
    agg_d['depth(m)'] = depth
    daily_parts.append(agg_d[['date','depth(m)','N','mean','std','max','min']])

    # Monthly
    agg_m = df_insitu.groupby([df_ex['year'], df_ex['month']])[col]\
                     .agg(['count','mean','std','max','min']).round(3)
    agg_m.columns = ['N','mean','std','max','min']
    agg_m = agg_m.reset_index()
    agg_m.columns = ['year','month','N','mean','std','max','min']
    agg_m['depth(m)'] = depth
    for thr in [24, 25, 26]:
        agg_m[f'Ndays>={thr}'] = np.round(
            (df_insitu[col] >= thr).astype(int)
            .groupby([df_ex['year'], df_ex['month']]).sum().values / 24)
    monthly_parts.append(agg_m[['year','month','depth(m)','N','mean','std','max','min',
                                 'Ndays>=24','Ndays>=25','Ndays>=26']])

    # Seasonal (JAS)
    agg_s = df_season.groupby(df_season['year'])[col]\
                     .agg(['count','mean','std','max','min']).round(3)
    agg_s.columns = ['N','mean','std','max','min']
    agg_s = agg_s.reset_index()
    agg_s.columns = ['year','N','mean','std','max','min']
    agg_s['season'] = 3
    agg_s['depth(m)'] = depth
    for thr in [23, 24, 25, 26, 27, 28]:
        vals = (df_season[col] >= thr).astype(int).groupby(df_season['year']).sum()
        agg_s[f'Ndays>={thr}'] = np.round(vals.reindex(agg_s['year']).fillna(0).values / 24)
    seasonal_parts.append(agg_s[['year','season','depth(m)','N','mean','std','max','min',
                                  'Ndays>=23','Ndays>=24','Ndays>=25',
                                  'Ndays>=26','Ndays>=27','Ndays>=28']])

dfexcel   = pd.concat(daily_parts,    ignore_index=True).sort_values(['date','depth(m)'])
dfmonthly = pd.concat(monthly_parts,  ignore_index=True).sort_values(['year','month','depth(m)'])
dfseasonal= pd.concat(seasonal_parts, ignore_index=True).sort_values(['year','depth(m)'])

dfexcel['year']  = pd.DatetimeIndex(dfexcel['date']).year
dfexcel['month'] = pd.DatetimeIndex(dfexcel['date']).month
dfexcel['date']  = dfexcel['date'].apply(lambda d: d.date())

_nona = dfexcel.dropna(subset=['max'])
dfmaxes = dfexcel.loc[_nona.groupby('year')['max'].idxmax()][['year','date','max']]\
                  .sort_values('max', ascending=False)
dfmaxes_depth = dfexcel.loc[_nona.groupby(['year','depth(m)'])['max'].idxmax()]\
                        [['year','depth(m)','date','max']]\
                        .sort_values(['depth(m)','max'], ascending=False)
dfmaxes_month = dfexcel.loc[_nona.groupby(['year','month'])['max'].idxmax()]\
                        [['year','month','date','max']]\
                        .sort_values('max', ascending=False)
dfmaxes_dm    = dfexcel.loc[_nona.groupby(['year','month','depth(m)'])['max'].idxmax()]\
                        [['year','month','depth(m)','date','max']]\
                        .sort_values(['depth(m)','max'], ascending=False)

df30 = dfexcel.groupby('year')['mean']\
              .apply(lambda g: round(float(g.nlargest(30).mean()), 2))\
              .reset_index()
df30.columns = ['year', '30tmax']

xl_filename = f"{SITE_CODE}_Stat_Report_{SITE_NAME}_{date_range}_{today_str}.xlsx"
xl_path     = os.path.join(DESKTOP, xl_filename)

with _ExcelWriter(xl_path, engine='openpyxl') as writer:
    dfexcel.to_excel(writer,       sheet_name='Daily',            index=False)
    dfmonthly.to_excel(writer,     sheet_name='Monthly',          index=False)
    dfseasonal.to_excel(writer,    sheet_name='Seasonal',         index=False)
    dfmaxes.to_excel(writer,       sheet_name='Maxes',            index=False)
    dfmaxes_depth.to_excel(writer, sheet_name='Maxes depth',      index=False)
    dfmaxes_month.to_excel(writer, sheet_name='Maxes month',      index=False)
    dfmaxes_dm.to_excel(writer,    sheet_name='Maxes depth month',index=False)
    df30.to_excel(writer,          sheet_name='30Tmax',           index=False)

print(f"[Excel]       {xl_filename}  ({os.path.getsize(xl_path)//1024} KB)")

print("\nDone. Check Desktop\\Capraia_2025 and Desktop\\Capraia_2026.")
