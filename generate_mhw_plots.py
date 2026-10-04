"""
generate_mhw_plots.py
---------------------
Generates Marine Heatwave (MHW) detection plots per year for any T-MEDNet station.
Classification: Moderat / Fort / Sever / Extrem  (Hobday et al. 2016)

Usage:
  Edit the STATION_CONFIGS dict below to add or update stations.
  Set ACTIVE_STATION to the site code you want to run, then execute:
      python generate_mhw_plots.py

One PNG is saved per year in the station's "Grafiques MHW" subfolder.
File naming: {CODE}_MHW_{DEPTH}m_{year}_{site}_{date}.png
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np
from scipy.ndimage import uniform_filter1d
import os
from datetime import date as dt_date

# ── Station configurations ─────────────────────────────────────────
BASE = r'C:\Users\jahan\Desktop\temperatures t-mednet'

STATION_CONFIGS = {
    '05': {
        'db_file': (
            BASE + r'\05 · Cap de Creus Sud  (Costa Brava, ES)'
                   r'\Base de dades'
                   r'\Database_T_5_Cap de Creus-S_200705-202606_2026-06-27.txt'
        ),
        'site_name': 'Cap de Creus Sud',
        'site_folder': '05 · Cap de Creus Sud  (Costa Brava, ES)',
        'clim_start': 2008,
        'clim_end':   2022,
        'gen_date':   '2026-06-27',
        'site_tag':   'Cap_de_Creus_S',
    },
    '06': {
        'db_file': (
            BASE + r'\06 · Illes Medes  (Costa Brava, ES)'
                   r'\Base de dades'
                   r'\6_Database_T_Medes_200207-202605_2026-06-28.txt'
        ),
        'site_name': 'Illes Medes',
        'site_folder': '06 · Illes Medes  (Costa Brava, ES)',
        'clim_start': 2003,
        'clim_end':   2022,
        'gen_date':   '2026-06-28',
        'site_tag':   'Medes',
    },
    '07': {
        'db_file':     BASE + '\07 · Cap de Creus Nord — Portalo  (Costa Brava, ES)\\Base de dades\\7_Database_T_Cap de Creus-N_200705-202605_2026-06-28.txt',
        'site_name':   'Cap de Creus Nord',
        'site_folder': '07 · Cap de Creus Nord — Portalo  (Costa Brava, ES)',
        'depth':       '5',
        'clim_start':  2008,
        'clim_end':    2022,
        'gen_date':    '2026-06-28',
        'site_tag':    'Cap_de_Creus_N',
    },
    '13': {
        'db_file':     BASE + '\\13 · Marsella — Illa de Riou  (FR)\\Base de dades\\13_Database_T_Marseille-Riou_199906-202601_2026-06-28.txt',
        'site_name':   'Marsella — Illa de Riou',
        'site_folder': '13 · Marsella — Illa de Riou  (FR)',
        'depth':       '5',
        'clim_start':  2000,
        'clim_end':    2020,
        'gen_date':    '2026-06-28',
        'site_tag':    'Marseille_Riou',
    },
    '38': {
        'db_file':     BASE + '\\38 · Cap Sicie — Toulon  (FR)\\Base de dades\\38_Database_T_Cap Sicié_201401-202605_2026-06-28.txt',
        'site_name':   'Cap Sicié — Toulon',
        'site_folder': '38 · Cap Sicie — Toulon  (FR)',
        'depth':       '5',
        'clim_start':  2015,
        'clim_end':    2022,
        'gen_date':    '2026-06-28',
        'site_tag':    'Cap_Sicie',
    },
    '150': {
        'db_file':     BASE + '\\150 · Ullastres  (Costa Brava, ES)\\Base de dades\\150_Database_T_Ullastres_202010-202605_2026-06-28.txt',
        'site_name':   'Ullastres',
        'site_folder': '150 · Ullastres  (Costa Brava, ES)',
        'depth':       '5',
        'clim_start':  2021,
        'clim_end':    2024,
        'gen_date':    '2026-06-28',
        'site_tag':    'Ullastres',
    },
    '205': {
        'db_file':     BASE + '\\205 · Capo Caccia — Il Nereo  (Sardenya, IT)\\Base de dades\\205_Database_T_Capo Caccia_202312-202512_2026-06-28.txt',
        'site_name':   'Capo Caccia — Il Nereo',
        'site_folder': '205 · Capo Caccia — Il Nereo  (Sardenya, IT)',
        'depth':       '10',   # no 5m sensor at this station
        'clim_start':  2024,
        'clim_end':    2025,
        'gen_date':    '2026-06-28',
        'site_tag':    'Capo_Caccia',
    },
    # 252 (Capraia): no .txt database available yet (only zip, Sept 2025 - Apr 2026)
}

# ── Select which station to run ───────────────────────────────────
ACTIVE_STATION = '06'

# ── Common parameters (same for all stations) ─────────────────────
DEPTH     = '5'       # depth column name in the database
SMOOTH    = 11        # climatology smoothing window (days)
MON_START = 5         # season start month (May)
MON_END   = 10        # season end month (October)
MIN_DAYS  = 60        # minimum summer days required to plot a year

COLORS = ['#FFE566', '#FFA500', '#E05000', '#8B0000']
LABELS = ['Moderat', 'Fort', 'Sever', 'Extrem']


def wrap_smooth(arr, w):
    ext = np.concatenate([arr[-w:], arr, arr[:w]])
    sm  = uniform_filter1d(ext.astype(float), w)
    return sm[w: w + len(arr)]


def lookup(doy_arr, clim_arr):
    idx = np.clip(np.array(doy_arr, dtype=int) - 1, 0, len(clim_arr) - 1)
    return clim_arr[idx]


def run(code):
    cfg = STATION_CONFIGS[code]
    db_file    = cfg['db_file']
    site_name  = cfg['site_name']
    clim_start = cfg['clim_start']
    clim_end   = cfg['clim_end']
    gen_date   = cfg['gen_date']
    site_tag   = cfg['site_tag']
    out_dir    = os.path.join(BASE, cfg['site_folder'], 'Grafiques MHW')
    os.makedirs(out_dir, exist_ok=True)

    # ── Load database ─────────────────────────────────────────────
    print(f"[{code}] Loading {os.path.basename(db_file)} ...")
    raw = pd.read_csv(db_file, sep='\t', dayfirst=True, na_values=[''],
                      dtype=str, low_memory=False)
    raw['datetime'] = pd.to_datetime(raw['Date'] + ' ' + raw['Time'],
                                     dayfirst=True, errors='coerce')
    raw.set_index('datetime', inplace=True)
    raw.drop(columns=['Date', 'Time'], inplace=True, errors='ignore')
    raw = raw.apply(pd.to_numeric, errors='coerce')

    series = raw[DEPTH].dropna()
    daily  = series.resample('D').mean().dropna()
    print(f"  {len(daily)} daily values  |  "
          f"{daily.index[0].date()} -> {daily.index[-1].date()}")

    # ── Climatology ───────────────────────────────────────────────
    ref      = daily[(daily.index.year >= clim_start) & (daily.index.year <= clim_end)]
    grp_mean = ref.groupby(ref.index.dayofyear).mean()
    grp_p90  = ref.groupby(ref.index.dayofyear).quantile(0.90)

    full_doy = pd.RangeIndex(1, 367)
    grp_mean = grp_mean.reindex(full_doy).interpolate('linear')
    grp_p90  = grp_p90.reindex(full_doy).interpolate('linear')

    clim_mean  = wrap_smooth(grp_mean.values, SMOOTH)
    clim_p90   = wrap_smooth(grp_p90.values,  SMOOTH)
    clim_delta = clim_p90 - clim_mean

    def thresh(n):
        return clim_mean + n * clim_delta

    T = [thresh(1), thresh(2), thresh(3), thresh(4)]

    # ── Year selection ────────────────────────────────────────────
    years = sorted(daily.index.year.unique())
    years = [y for y in years
             if daily[(daily.index.year == y) &
                      (daily.index.month.isin(range(MON_START, MON_END + 1)))
                      ].count() >= MIN_DAYS]
    print(f"  Years to plot: {years}")

    legend_handles = (
        [mpatches.Patch(color=c, label=l) for c, l in zip(COLORS, LABELS)] +
        [plt.Line2D([0], [0], color='#C0392B', lw=1.8, label='Climatologia'),
         plt.Line2D([0], [0], color='#C0392B', lw=1.3, ls='--', label='IT90 (P90)')]
    )

    # ── One figure per year ───────────────────────────────────────
    for year in years:
        mask = ((daily.index.year  == year) &
                (daily.index.month >= MON_START) &
                (daily.index.month <= MON_END))
        yr = daily[mask]
        if yr.empty:
            continue

        dates = yr.index
        temp  = yr.values
        doy   = dates.dayofyear.values

        c_mean = lookup(doy, clim_mean)
        t1 = lookup(doy, T[0])
        t2 = lookup(doy, T[1])
        t3 = lookup(doy, T[2])
        t4 = lookup(doy, T[3])

        fig, ax = plt.subplots(figsize=(12, 5), facecolor='white')

        ax.fill_between(dates, t1, np.minimum(temp, t2),
                        where=temp > t1, color=COLORS[0], lw=0,
                        interpolate=True, zorder=2)
        ax.fill_between(dates, t2, np.minimum(temp, t3),
                        where=temp > t2, color=COLORS[1], lw=0,
                        interpolate=True, zorder=3)
        ax.fill_between(dates, t3, np.minimum(temp, t4),
                        where=temp > t3, color=COLORS[2], lw=0,
                        interpolate=True, zorder=4)
        ax.fill_between(dates, t4, temp,
                        where=temp > t4, color=COLORS[3], lw=0,
                        interpolate=True, zorder=5)

        ax.plot(dates, c_mean, color='#C0392B', lw=1.8, zorder=6)
        ax.plot(dates, t1,     color='#C0392B', lw=1.3, ls='--', zorder=6)
        ax.plot(dates, temp,   color='#1A1A1A', lw=1.1, zorder=7)

        if np.any(temp > t2):
            peak_i = np.argmax(temp - t1)
            if temp[peak_i] > t2[peak_i]:
                ax.annotate(f'{temp[peak_i]:.1f}C',
                            xy=(dates[peak_i], temp[peak_i]),
                            xytext=(0, 8), textcoords='offset points',
                            fontsize=9, ha='center', color='#8B0000',
                            fontweight='bold',
                            arrowprops=dict(arrowstyle='->', color='#8B0000', lw=1))

        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%B'))
        ax.tick_params(axis='x', labelsize=10)
        ax.tick_params(axis='y', labelsize=10)
        ax.set_ylabel('Temperatura (C)', fontsize=11)
        ax.grid(axis='y', lw=0.4, alpha=0.5, color='#AAAAAA')
        ax.spines[['top', 'right']].set_visible(False)
        ax.spines[['left', 'bottom']].set_linewidth(0.8)

        ax.set_title(
            f'{site_name} - Onades de Calor Marines - {DEPTH} m - {year}\n'
            f'Climatologia de referencia: {clim_start}-{clim_end}'
            f'  |  Hobday et al. (2016)',
            fontsize=11, fontweight='bold', color='#1B3A5C', pad=8
        )

        ax.legend(handles=legend_handles, loc='upper left',
                  fontsize=9, frameon=True, edgecolor='#CCCCCC',
                  ncol=3, facecolor='white')

        plt.tight_layout()
        out_file = os.path.join(
            out_dir,
            f'{code}_MHW_{DEPTH}m_{year}_{site_tag}_{gen_date}.png'
        )
        plt.savefig(out_file, dpi=180, bbox_inches='tight', facecolor='white')
        print(f"  Saved {year}")
        plt.close()

    print(f"[{code}] Done. Output: {out_dir}")


if __name__ == '__main__':
    run(ACTIVE_STATION)
