"""
add_mhw_sheets.py
-----------------
Adds MHW (Marine Heat Wave) and MHW_MAX sheets to all T-MEDNet
Stat_Report Excel files, using Hobday et al. (2016) detection via
core/marineHeatWaves.py.

Run once to patch existing files; generate_*.py scripts call
_compute_mhw_sheets() directly from their own copy of the function.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core'))

import numpy as np
import pandas as pd
from pandas import ExcelWriter
from openpyxl import load_workbook
import marineHeatWaves as _mhw_lib

BASE = r'C:\Users\jahan\Desktop\temperatures t-mednet'

# Hobday climatology reference period per site code
_MHW_PARAMS = {
    5:   (2008, 2022),   # Cap de Creus-S  (only 2026 data → will return empty)
    6:   (2003, 2022),   # Medes
    7:   (2008, 2022),   # Cap de Creus-N / Portalo
    8:   (2007, 2022),   # Banyuls
    35:  (2014, 2022),   # Sa Foradada
    38:  (2015, 2022),   # Cap Sicié / Toulon
    150: (2021, 2024),   # Ullastres
}

_CAT_NAMES = {
    'Moderate': 'Moderat', 'Strong': 'Fort',
    'Severe':   'Sever',   'Extreme': 'Extrem',
    1: 'Moderat', 2: 'Fort', 3: 'Sever', 4: 'Extrem',
}


def _compute_mhw_sheets(dfexcel, clim_start, clim_end):
    """
    Detect MHW events per depth from the 'Daily' tab DataFrame.

    Parameters
    ----------
    dfexcel      : DataFrame with columns date, depth(m), mean, ...
    clim_start/end : reference period years (inclusive)

    Returns
    -------
    df_mhw     : one row per detected event   → 'MHW' sheet
    df_mhw_max : one row per year × depth     → 'MHW_MAX' sheet
    """
    all_events = []
    depths = sorted(dfexcel['depth(m)'].unique())

    for depth in depths:
        sub = dfexcel[dfexcel['depth(m)'] == depth][['date', 'mean']].copy()
        sub['date'] = pd.to_datetime(sub['date'])
        sub = sub.dropna(subset=['mean']).sort_values('date')
        if sub.empty:
            continue

        # Clamp climatology period to actual data range (library fails if
        # clim_start < first year or clim_end > last year in series)
        first_yr = int(sub['date'].dt.year.min())
        last_yr  = int(sub['date'].dt.year.max())
        eff_start = max(clim_start, first_yr)
        eff_end   = min(clim_end,   last_yr)

        ref_count = ((sub['date'].dt.year >= eff_start) &
                     (sub['date'].dt.year <= eff_end)).sum()
        if ref_count < 365 or eff_start >= eff_end:
            continue

        t    = np.array([d.toordinal() for d in sub['date'].dt.date])
        temp = sub['mean'].values

        try:
            mhws, _ = _mhw_lib.detect(
                t, temp,
                climatologyPeriod=[eff_start, eff_end],
                maxPadLength=10,
            )
        except Exception as exc:
            print(f"    [MHW] depth {depth}m — detection error: {exc}")
            continue

        n = mhws.get('n_events', 0)
        if n == 0:
            continue

        for i in range(n):
            raw_cat = mhws['category'][i]
            cat_str = _CAT_NAMES.get(raw_cat, _CAT_NAMES.get(str(raw_cat), str(raw_cat)))
            all_events.append({
                'year':                   mhws['date_start'][i].year,
                'depth(m)':              depth,
                'start':                  mhws['date_start'][i],
                'end':                    mhws['date_end'][i],
                'peak_date':              mhws['date_peak'][i],
                'duration_days':          int(mhws['duration'][i]),
                'max_temp(ºC)':           round(float(mhws['intensity_max_abs'][i]),  2),
                'max_intensity(ºC)':      round(float(mhws['intensity_max'][i]),       2),
                'mean_intensity(ºC)':     round(float(mhws['intensity_mean'][i]),      2),
                'cum_intensity(ºC·day)':  round(float(mhws['intensity_cumulative'][i]),2),
                'category':               cat_str,
                'clim_period':            f'{eff_start}-{eff_end}',
            })

    _empty_mhw = pd.DataFrame(columns=[
        'year', 'depth(m)', 'start', 'end', 'peak_date', 'duration_days',
        'max_temp(ºC)', 'max_intensity(ºC)', 'mean_intensity(ºC)',
        'cum_intensity(ºC·day)', 'category', 'clim_period'])
    _empty_max = pd.DataFrame(columns=[
        'year', 'depth(m)', 'n_events', 'total_days', 'max_temp(ºC)',
        'max_intensity(ºC)', 'max_duration_days', 'cum_intensity(ºC·day)',
        'worst_category', 'clim_period'])

    if not all_events:
        return _empty_mhw, _empty_max

    df_mhw = pd.DataFrame(all_events).sort_values(['depth(m)', 'start'])

    # Order categories for "worst" comparison
    _cat_order = {'Moderat': 1, 'Fort': 2, 'Sever': 3, 'Extrem': 4}
    summary = []
    for (yr, dep), g in df_mhw.groupby(['year', 'depth(m)']):
        worst_cat = max(g['category'], key=lambda c: _cat_order.get(c, 0))
        summary.append({
            'year':                   yr,
            'depth(m)':              dep,
            'n_events':              len(g),
            'total_days':            int(g['duration_days'].sum()),
            'max_temp(ºC)':          round(float(g['max_temp(ºC)'].max()),        2),
            'max_intensity(ºC)':     round(float(g['max_intensity(ºC)'].max()),   2),
            'max_duration_days':     int(g['duration_days'].max()),
            'cum_intensity(ºC·day)': round(float(g['cum_intensity(ºC·day)'].sum()), 2),
            'worst_category':        worst_cat,
            'clim_period':           g['clim_period'].iloc[0],
        })

    df_mhw_max = pd.DataFrame(summary).sort_values(['depth(m)', 'year'])
    return df_mhw, df_mhw_max


def patch_excel(xl_path, site_code):
    """Add/replace MHW and MHW_MAX sheets in an existing Stat_Report Excel."""
    clim = _MHW_PARAMS.get(site_code)
    if clim is None:
        print(f"  [skip] no MHW params for site {site_code}")
        return

    clim_start, clim_end = clim
    print(f"  Reading Daily tab … ", end='', flush=True)
    dfexcel = pd.read_excel(xl_path, sheet_name='Daily')
    print(f"{len(dfexcel)} rows | clim {clim_start}-{clim_end}")

    print(f"  Computing MHW events … ", end='', flush=True)
    df_mhw, df_mhw_max = _compute_mhw_sheets(dfexcel, clim_start, clim_end)
    print(f"{len(df_mhw)} events detected")

    # Load workbook and remove old MHW sheets if present
    wb = load_workbook(xl_path)
    for sheet in ('MHW', 'MHW_MAX'):
        if sheet in wb.sheetnames:
            del wb[sheet]
    wb.save(xl_path)

    # Append the new sheets with ExcelWriter in overlay mode
    with pd.ExcelWriter(xl_path, engine='openpyxl', mode='a',
                        if_sheet_exists='replace') as writer:
        df_mhw.to_excel(writer,     sheet_name='MHW',     index=False)
        df_mhw_max.to_excel(writer, sheet_name='MHW_MAX', index=False)

    print(f"  → Sheets MHW + MHW_MAX added to {os.path.basename(xl_path)}")


# ── Sites to patch ────────────────────────────────────────────────────────────
EXCEL_FILES = {
    5:   r'C:\Users\jahan\Desktop\temperatures t-mednet\Cap de Creus-S\5_Stat_Report_Cap de Creus-S_202606-202609_2026-10-01.xlsx',
    6:   r'C:\Users\jahan\Desktop\temperatures t-mednet\Medes\6_Stat_Report_Medes_200207-202609_2026-10-01.xlsx',
    7:   r'C:\Users\jahan\Desktop\temperatures t-mednet\Cap de Creus-N\7_Stat_Report_Cap de Creus-N_200705-202609_2026-10-01.xlsx',
    8:   r'C:\Users\jahan\Desktop\temperatures t-mednet\Banyuls\8_Stat_Report_Banyuls_200603-202607_2026-10-02.xlsx',
    35:  r'C:\Users\jahan\Desktop\temperatures t-mednet\Sa Foradada\35_Stat_Report_Sa Foradada_201301-202607_2026-10-02.xlsx',
    38:  None,   # filled below from glob
    150: r'C:\Users\jahan\Desktop\temperatures t-mednet\Ullastres\150_Stat_Report_Ullastres_202010-202609_2026-10-01.xlsx',
}

# Cap Sicié filename varies slightly; find it dynamically
import glob as _glob
_cs = _glob.glob(r'C:\Users\jahan\Desktop\temperatures t-mednet\Cap Sicie\*.xlsx')
if _cs:
    EXCEL_FILES[38] = _cs[0]


if __name__ == '__main__':
    print("=" * 60)
    print("  Adding MHW + MHW_MAX sheets to all Stat_Report files")
    print("=" * 60)
    for code, path in EXCEL_FILES.items():
        if path is None or not os.path.exists(path):
            print(f"\nSite {code}: file not found — skipped")
            continue
        print(f"\nSite {code}  {os.path.basename(path)}")
        try:
            patch_excel(path, code)
        except Exception as exc:
            print(f"  ERROR: {exc}")
    print("\nDone.")
