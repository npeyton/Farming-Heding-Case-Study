"""
Off-Season Rain Analysis: Planting & Harvest Window Wet-Spell Study
====================================================================
Tests whether rain patterns OUTSIDE peak summer (April-June planting window
and Sep-Nov harvest window) affect Illinois corn and soybean outcomes, and
whether Kalshi rain contracts could hedge those effects.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

BASE = Path(__file__).parent
DATA = BASE / "data" / "offseason"
CHARTS = BASE / "charts" / "offseason"
CHARTS.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "figure.figsize": (14, 7), "figure.dpi": 150, "font.size": 11,
    "axes.titlesize": 14, "axes.labelsize": 12, "lines.linewidth": 2,
    "figure.facecolor": "white",
})

# Windows
PLANT_START, PLANT_END = "04-01", "06-15"   # April 1 – June 15
HARVEST_START, HARVEST_END = "09-15", "11-30"  # Sep 15 – Nov 30

STATIONS = ["KMDW", "KORD", "KRFD", "KPIA", "KSPI"]
STATION_NAMES = {
    "KMDW": "Midway", "KORD": "O'Hare", "KRFD": "Rockford",
    "KPIA": "Peoria", "KSPI": "Springfield",
}

COUNTIES_NORTH = ["DEKALB", "KANE", "KENDALL", "WILL", "GRUNDY", "LA SALLE", "KANKAKEE"]
COUNTIES_CENTRAL = ["SANGAMON", "MCLEAN", "CHAMPAIGN"]
ALL_COUNTIES = COUNTIES_NORTH + COUNTIES_CENTRAL

# Station-county mapping (which station is closest proxy for which counties)
STATION_COUNTY_MAP = {
    "KMDW": ["KANE", "WILL", "KENDALL", "GRUNDY", "KANKAKEE"],
    "KORD": ["KANE", "DEKALB", "WILL"],
    "KRFD": ["DEKALB"],
    "KPIA": ["LA SALLE", "MCLEAN"],
    "KSPI": ["SANGAMON", "CHAMPAIGN", "MCLEAN"],
}


# ===========================================================================
# SECTION 1: Load Data
# ===========================================================================

def load_station_data():
    """Load all station daily data."""
    frames = {}
    for sid in STATIONS:
        path = DATA / f"station_{sid}_daily.csv"
        if path.exists():
            df = pd.read_csv(path)
            df["date"] = pd.to_datetime(df["date"])
            df["precip_in"] = pd.to_numeric(df["precip_in"], errors="coerce")
            frames[sid] = df
    print(f"  Loaded {len(frames)} stations")
    return frames


def load_county_precip():
    """Load county daily precipitation."""
    path = DATA / "county_daily_precip.csv"
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df["precip_in"] = pd.to_numeric(df["precip_in"], errors="coerce")
    print(f"  Loaded county precip: {len(df)} records, "
          f"{df['county'].nunique()} counties")
    return df


def load_yields():
    """Load and detrend county yields."""
    path = DATA / "county_yields.csv"
    df = pd.read_csv(path)
    df["yield_bu_acre"] = pd.to_numeric(df["yield_bu_acre"], errors="coerce")

    results = []
    for (county, commodity), grp in df.groupby(["county", "commodity"]):
        g = grp.sort_values("year").copy()
        if len(g) < 10:
            continue
        slope, intercept, r, p, se = stats.linregress(g["year"], g["yield_bu_acre"])
        g["trend"] = intercept + slope * g["year"]
        g["yield_dev_pct"] = ((g["yield_bu_acre"] - g["trend"]) / g["trend"]) * 100
        results.append(g)

    out = pd.concat(results)
    print(f"  Loaded yields: {len(out)} records")
    return out


# ===========================================================================
# SECTION 2: Wet-Spell Metrics
# ===========================================================================

def compute_wet_spell_metrics(precip_series, threshold=0.01):
    """
    Given a daily precipitation series for one window/year, compute:
    - rain_days: count of days >= threshold
    - longest_wet_run: longest consecutive run of wet days
    - spells_3plus: number of separate wet spells of 3+ consecutive days
    - workable_days_v1: days with precip < 0.10 AND preceded by at least
                        1 day with precip < 0.25 (simple "dry enough" rule)
    - workable_days_v2: days with precip < 0.10 AND preceded by at least
                        2 days averaging < 0.25 (stricter "field dried out")
    - longest_dry_window: longest streak of days below threshold
    - total_rainfall: sum of precipitation
    - heavy_rain_days: days with >= 1.0"
    """
    vals = precip_series.values
    n = len(vals)

    # Rain days at multiple thresholds
    rain_days_001 = int(np.nansum(vals >= 0.01))
    rain_days_010 = int(np.nansum(vals >= 0.10))
    rain_days_025 = int(np.nansum(vals >= 0.25))
    heavy_rain_days = int(np.nansum(vals >= 1.0))

    # Consecutive wet/dry runs
    wet = (vals >= threshold).astype(int)
    dry = (vals < threshold).astype(int)

    def max_run(arr):
        if len(arr) == 0:
            return 0
        max_r = 0
        current = 0
        for v in arr:
            if v:
                current += 1
                max_r = max(max_r, current)
            else:
                current = 0
        return max_r

    longest_wet_run = max_run(wet)
    longest_dry_window = max_run(dry)

    # Count separate spells of 3+ wet days
    spells_3plus = 0
    current_run = 0
    for w in wet:
        if w:
            current_run += 1
        else:
            if current_run >= 3:
                spells_3plus += 1
            current_run = 0
    if current_run >= 3:
        spells_3plus += 1

    # Workable days (Version 1: dry today + yesterday was dryish)
    workable_v1 = 0
    for i in range(1, n):
        today_dry = vals[i] < 0.10 if not np.isnan(vals[i]) else False
        yesterday_dry = vals[i-1] < 0.25 if not np.isnan(vals[i-1]) else False
        if today_dry and yesterday_dry:
            workable_v1 += 1

    # Workable days (Version 2: dry today + 2-day rolling avg < 0.25)
    workable_v2 = 0
    for i in range(2, n):
        today_dry = vals[i] < 0.10 if not np.isnan(vals[i]) else False
        prev_avg = np.nanmean(vals[max(0, i-2):i])
        if today_dry and prev_avg < 0.25:
            workable_v2 += 1

    total_rainfall = float(np.nansum(vals))

    return {
        "rain_days_001": rain_days_001,
        "rain_days_010": rain_days_010,
        "rain_days_025": rain_days_025,
        "heavy_rain_days": heavy_rain_days,
        "longest_wet_run": longest_wet_run,
        "spells_3plus": spells_3plus,
        "workable_days_v1": workable_v1,
        "workable_days_v2": workable_v2,
        "longest_dry_window": longest_dry_window,
        "total_rainfall": round(total_rainfall, 2),
    }


def build_station_metrics(station_data):
    """Build wet-spell metrics for each station, window, year."""
    all_rows = []

    for sid, df in station_data.items():
        df = df.set_index("date").sort_index()

        for year in range(1980, 2026):
            for window, (ws, we) in [
                ("planting", (PLANT_START, PLANT_END)),
                ("harvest", (HARVEST_START, HARVEST_END)),
            ]:
                start = pd.Timestamp(f"{year}-{ws}")
                end = pd.Timestamp(f"{year}-{we}")
                subset = df.loc[start:end, "precip_in"].dropna()

                if len(subset) < 30:  # Need at least 30 days
                    continue

                metrics = compute_wet_spell_metrics(subset)
                metrics["station"] = sid
                metrics["year"] = year
                metrics["window"] = window
                all_rows.append(metrics)

    result = pd.DataFrame(all_rows)
    print(f"  Built {len(result)} station-window-year metric rows")
    return result


def build_county_metrics(county_precip):
    """Build wet-spell metrics for each county, window, year."""
    all_rows = []

    for county in ALL_COUNTIES:
        cdf = county_precip[county_precip["county"] == county].copy()
        cdf = cdf.set_index("date").sort_index()

        for year in range(1980, 2026):
            for window, (ws, we) in [
                ("planting", (PLANT_START, PLANT_END)),
                ("harvest", (HARVEST_START, HARVEST_END)),
            ]:
                start = pd.Timestamp(f"{year}-{ws}")
                end = pd.Timestamp(f"{year}-{we}")
                subset = cdf.loc[start:end, "precip_in"].dropna()

                if len(subset) < 30:
                    continue

                metrics = compute_wet_spell_metrics(subset)
                metrics["county"] = county
                metrics["year"] = year
                metrics["window"] = window
                all_rows.append(metrics)

    result = pd.DataFrame(all_rows)
    print(f"  Built {len(result)} county-window-year metric rows")
    return result


# ===========================================================================
# SECTION 3: Build Outcome Proxies
# ===========================================================================

def build_crop_progress_proxy(station_metrics):
    """
    Approximate IL crop planting pace from spring weather.
    Real NASS Crop Progress data is unavailable via API, so we model:
    - Days suitable for fieldwork ~ workable_days
    - Planting delay ~ inverse of workable days
    Known wet springs: 2019, 1993, 2008, 2009, 2015
    """
    # Use the IL-wide average of station metrics for planting window
    plant = station_metrics[station_metrics["window"] == "planting"]
    plant_avg = plant.groupby("year").agg(
        avg_workable_v1=("workable_days_v1", "mean"),
        avg_workable_v2=("workable_days_v2", "mean"),
        avg_rain_days=("rain_days_010", "mean"),
        avg_total_rain=("total_rainfall", "mean"),
        avg_longest_wet=("longest_wet_run", "mean"),
        avg_spells_3plus=("spells_3plus", "mean"),
        avg_heavy_days=("heavy_rain_days", "mean"),
    ).reset_index()

    # Normal planting window is 76 days (Apr 1 - Jun 15)
    # "Days suitable" is roughly the workable days
    # Planting delay: how many fewer workable days than the long-run average
    avg_workable = plant_avg["avg_workable_v1"].mean()
    plant_avg["workable_deficit"] = avg_workable - plant_avg["avg_workable_v1"]
    plant_avg["pct_workable"] = (plant_avg["avg_workable_v1"] / 76) * 100

    # Harvest window metrics
    harv = station_metrics[station_metrics["window"] == "harvest"]
    harv_avg = harv.groupby("year").agg(
        harv_workable_v1=("workable_days_v1", "mean"),
        harv_rain_days=("rain_days_010", "mean"),
        harv_total_rain=("total_rainfall", "mean"),
        harv_longest_wet=("longest_wet_run", "mean"),
        harv_spells_3plus=("spells_3plus", "mean"),
    ).reset_index()

    combined = plant_avg.merge(harv_avg, on="year", how="outer")
    return combined


def build_rma_proxy():
    """
    Build RMA excess-moisture loss proxy.
    Real RMA data is coded: cause 31 = excess moisture/precipitation.
    We model losses based on published patterns for IL corn/soybeans.
    """
    np.random.seed(321)

    # Known big excess-moisture loss years for IL
    # Source: published RMA summary reports
    wet_loss_years = {
        1993: 3.0,  # Great Flood
        2008: 1.8,
        2009: 1.5,
        2010: 1.3,
        2011: 1.2,
        2015: 1.5,
        2019: 4.0,  # Record prevented planting
    }

    rows = []
    for year in range(1989, 2025):
        mult = wet_loss_years.get(year, 1.0)
        base_loss = np.random.exponential(5) * mult  # million $
        rows.append({
            "year": year,
            "cause": "EXCESS_MOISTURE",
            "indemnity_millions": round(base_loss, 2),
            "is_major_wet_year": year in wet_loss_years,
        })

    return pd.DataFrame(rows)


# ===========================================================================
# SECTION 4: Correlation Analysis
# ===========================================================================

def analyze_weather_outcome_correlations(station_metrics, county_metrics,
                                          yield_df, progress):
    """
    Which wet-spell measures best explain farm outcomes?
    Compare all measures against yield deviations and workable-day deficits.
    Use train/test split to avoid overfitting.
    """
    print("\n  === PLANTING WINDOW: Wet-Spell Measures vs Outcomes ===")
    print("  " + "=" * 55)

    # Merge station planting metrics with yield deviations
    plant_stn = station_metrics[station_metrics["window"] == "planting"]
    plant_avg = plant_stn.groupby("year").mean(numeric_only=True).reset_index()

    # Average yield deviation across all counties for corn
    corn_dev = yield_df[yield_df["commodity"] == "CORN"].groupby("year")[
        "yield_dev_pct"].mean().reset_index()
    corn_dev.columns = ["year", "corn_yield_dev"]

    soy_dev = yield_df[yield_df["commodity"] == "SOYBEANS"].groupby("year")[
        "yield_dev_pct"].mean().reset_index()
    soy_dev.columns = ["year", "soy_yield_dev"]

    merged = plant_avg.merge(corn_dev, on="year").merge(soy_dev, on="year")

    # Metrics to test
    metrics_to_test = [
        "rain_days_001", "rain_days_010", "rain_days_025",
        "longest_wet_run", "spells_3plus",
        "workable_days_v1", "workable_days_v2",
        "longest_dry_window", "total_rainfall", "heavy_rain_days",
    ]

    results_plant = {}

    # Train on even years, test on odd (simple split)
    train = merged[merged["year"] % 2 == 0]
    test = merged[merged["year"] % 2 == 1]

    print(f"\n  Train: {len(train)} years | Test: {len(test)} years")
    print(f"\n  {'Metric':<22s} {'r(corn)':<10s} {'p-val':<10s} "
          f"{'r(test)':<10s} {'r(soy)':<10s}")
    print("  " + "-" * 65)

    for metric in metrics_to_test:
        if metric not in merged.columns:
            continue

        # Train correlation
        valid_train = train.dropna(subset=[metric, "corn_yield_dev"])
        if len(valid_train) < 8:
            continue

        r_train, p_train = stats.pearsonr(
            valid_train[metric], valid_train["corn_yield_dev"])

        # Test correlation
        valid_test = test.dropna(subset=[metric, "corn_yield_dev"])
        r_test = np.nan
        if len(valid_test) > 5:
            r_test, _ = stats.pearsonr(
                valid_test[metric], valid_test["corn_yield_dev"])

        # Soybean correlation (full sample)
        valid_all = merged.dropna(subset=[metric, "soy_yield_dev"])
        r_soy, p_soy = stats.pearsonr(
            valid_all[metric], valid_all["soy_yield_dev"])

        # Full-sample correlation
        valid_full = merged.dropna(subset=[metric, "corn_yield_dev"])
        r_full, p_full = stats.pearsonr(
            valid_full[metric], valid_full["corn_yield_dev"])

        sig = "***" if p_full < 0.01 else "**" if p_full < 0.05 else "*" if p_full < 0.1 else ""

        results_plant[metric] = {
            "r_corn_full": r_full,
            "r_corn_train": r_train,
            "r_corn_test": r_test,
            "r_soy": r_soy,
            "p_corn": p_full,
            "n": len(valid_full),
        }

        print(f"  {metric:<22s} {r_full:>+7.3f}{sig:<3s} {p_full:<10.4f} "
              f"{r_test:>+7.3f}    {r_soy:>+7.3f}")

    # Harvest window
    print("\n\n  === HARVEST WINDOW: Wet-Spell Measures vs Outcomes ===")
    print("  " + "=" * 55)

    harv_stn = station_metrics[station_metrics["window"] == "harvest"]
    harv_avg = harv_stn.groupby("year").mean(numeric_only=True).reset_index()
    harv_merged = harv_avg.merge(corn_dev, on="year").merge(soy_dev, on="year")

    results_harv = {}

    h_train = harv_merged[harv_merged["year"] % 2 == 0]
    h_test = harv_merged[harv_merged["year"] % 2 == 1]

    print(f"\n  Train: {len(h_train)} years | Test: {len(h_test)} years")
    print(f"\n  {'Metric':<22s} {'r(corn)':<10s} {'p-val':<10s} "
          f"{'r(test)':<10s} {'r(soy)':<10s}")
    print("  " + "-" * 65)

    for metric in metrics_to_test:
        if metric not in harv_merged.columns:
            continue

        valid_full = harv_merged.dropna(subset=[metric, "corn_yield_dev"])
        if len(valid_full) < 8:
            continue

        r_full, p_full = stats.pearsonr(
            valid_full[metric], valid_full["corn_yield_dev"])

        valid_test = h_test.dropna(subset=[metric, "corn_yield_dev"])
        r_test = np.nan
        if len(valid_test) > 5:
            r_test, _ = stats.pearsonr(
                valid_test[metric], valid_test["corn_yield_dev"])

        valid_soy = harv_merged.dropna(subset=[metric, "soy_yield_dev"])
        r_soy, p_soy = stats.pearsonr(
            valid_soy[metric], valid_soy["soy_yield_dev"])

        sig = "***" if p_full < 0.01 else "**" if p_full < 0.05 else "*" if p_full < 0.1 else ""

        results_harv[metric] = {
            "r_corn_full": r_full, "r_corn_test": r_test,
            "r_soy": r_soy, "p_corn": p_full,
        }

        print(f"  {metric:<22s} {r_full:>+7.3f}{sig:<3s} {p_full:<10.4f} "
              f"{r_test:>+7.3f}    {r_soy:>+7.3f}")

    return results_plant, results_harv, merged, harv_merged


# ===========================================================================
# SECTION 5: Basis Risk
# ===========================================================================

def analyze_basis_risk(station_metrics, county_metrics):
    """
    How well does rain at Midway/Springfield track county-average rain?
    """
    print("\n\n  === BASIS RISK: Station Rain vs County-Average Rain ===")
    print("  " + "=" * 55)

    results = {}

    for window in ["planting", "harvest"]:
        print(f"\n  --- {window.upper()} WINDOW ---")
        print(f"  {'Station':<10s} {'County':<12s} {'r':<8s} {'RMSE':<8s} "
              f"{'Bias':<10s} {'Years':<6s}")
        print("  " + "-" * 60)

        stn_w = station_metrics[station_metrics["window"] == window]
        cty_w = county_metrics[county_metrics["window"] == window]

        for sid in STATIONS:
            stn_data = stn_w[stn_w["station"] == sid][
                ["year", "total_rainfall", "rain_days_010", "longest_wet_run"]
            ].copy()

            proxied_counties = STATION_COUNTY_MAP.get(sid, [])

            for county in proxied_counties:
                cty_data = cty_w[cty_w["county"] == county][
                    ["year", "total_rainfall", "rain_days_010"]
                ].copy()

                merged = stn_data.merge(cty_data, on="year",
                                        suffixes=("_stn", "_cty"))

                if len(merged) < 10:
                    continue

                r, p = stats.pearsonr(
                    merged["total_rainfall_stn"],
                    merged["total_rainfall_cty"])
                rmse = np.sqrt(np.mean(
                    (merged["total_rainfall_stn"] -
                     merged["total_rainfall_cty"])**2))
                bias = (merged["total_rainfall_stn"] -
                        merged["total_rainfall_cty"]).mean()

                key = f"{sid}_{county}_{window}"
                results[key] = {
                    "station": sid, "county": county, "window": window,
                    "r": r, "rmse": rmse, "bias": bias, "n": len(merged),
                }

                quality = "GOOD" if r > 0.7 else "FAIR" if r > 0.5 else "POOR"
                print(f"  {STATION_NAMES[sid]:<10s} {county:<12s} "
                      f"{r:<8.3f} {rmse:<8.2f} {bias:>+8.2f}\"  "
                      f"{len(merged):<6d} {quality}")

    # Find divergence years
    print("\n  --- BIGGEST DIVERGENCES (station said wet, farm was dry or vice versa) ---")
    stn_w = station_metrics[station_metrics["window"] == "planting"]
    cty_w = county_metrics[county_metrics["window"] == "planting"]

    # Midway vs average of north IL counties
    mdw = stn_w[stn_w["station"] == "KMDW"][["year", "total_rainfall"]].copy()
    mdw.columns = ["year", "mdw_rain"]

    north_avg = cty_w[cty_w["county"].isin(COUNTIES_NORTH)].groupby("year")[
        "total_rainfall"].mean().reset_index()
    north_avg.columns = ["year", "county_rain"]

    comp = mdw.merge(north_avg, on="year")
    comp["diff"] = comp["mdw_rain"] - comp["county_rain"]

    print("\n  Midway vs North IL county average (planting window):")
    print("  Years where Midway was much wetter than farms:")
    for _, row in comp.nlargest(3, "diff").iterrows():
        print(f"    {int(row['year'])}: Midway {row['mdw_rain']:.1f}\" vs "
              f"counties {row['county_rain']:.1f}\" (diff: {row['diff']:+.1f}\")")

    print("  Years where Midway was much drier than farms:")
    for _, row in comp.nsmallest(3, "diff").iterrows():
        print(f"    {int(row['year'])}: Midway {row['mdw_rain']:.1f}\" vs "
              f"counties {row['county_rain']:.1f}\" (diff: {row['diff']:+.1f}\")")

    return results


# ===========================================================================
# SECTION 6: Charts
# ===========================================================================

def chart_wet_spell_vs_yield(merged, harv_merged):
    """Chart: Key wet-spell measures vs yield deviations."""

    fig, axes = plt.subplots(2, 3, figsize=(20, 12))

    # Planting window charts
    datasets = [
        (merged, "workable_days_v1", "corn_yield_dev",
         "Planting: Workable Days vs Corn Yield", "steelblue", "Workable Days"),
        (merged, "longest_wet_run", "corn_yield_dev",
         "Planting: Longest Wet Run vs Corn Yield", "crimson", "Longest Wet Run (days)"),
        (merged, "total_rainfall", "corn_yield_dev",
         "Planting: Total Rainfall vs Corn Yield", "darkorange", "Total Rainfall (inches)"),
        (harv_merged, "workable_days_v1", "corn_yield_dev",
         "Harvest: Workable Days vs Corn Yield", "steelblue", "Workable Days"),
        (harv_merged, "longest_wet_run", "corn_yield_dev",
         "Harvest: Longest Wet Run vs Corn Yield", "crimson", "Longest Wet Run (days)"),
        (harv_merged, "total_rainfall", "soy_yield_dev",
         "Harvest: Total Rainfall vs Soy Yield", "seagreen", "Total Rainfall (inches)"),
    ]

    for i, (data, x_col, y_col, title, color, xlabel) in enumerate(datasets):
        ax = axes[i // 3, i % 3]
        valid = data.dropna(subset=[x_col, y_col])

        ax.scatter(valid[x_col], valid[y_col], alpha=0.7, s=50,
                   color=color, edgecolors="gray", linewidth=0.5)

        if len(valid) > 5:
            z = np.polyfit(valid[x_col], valid[y_col], 1)
            p = np.poly1d(z)
            xr = np.linspace(valid[x_col].min(), valid[x_col].max(), 100)
            ax.plot(xr, p(xr), "k--", alpha=0.5, linewidth=1.5)
            r, pval = stats.pearsonr(valid[x_col], valid[y_col])
            ax.text(0.05, 0.95, f"r = {r:.2f}\np = {pval:.3f}",
                    transform=ax.transAxes, fontsize=10, va="top",
                    bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))

        # Label 2019 and 2009
        for yr in [2019, 2009, 1993]:
            row = valid[valid["year"] == yr]
            if len(row) > 0:
                ax.annotate(str(yr), xy=(row[x_col].iloc[0], row[y_col].iloc[0]),
                             xytext=(5, 5), textcoords="offset points",
                             fontsize=9, fontweight="bold", color="red")

        ax.axhline(y=0, color="gray", linewidth=0.5)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Yield Deviation (%)")
        ax.set_title(title)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig.savefig(CHARTS / "01_wetspell_vs_yield.png", bbox_inches="tight")
    plt.close()
    print("    Saved: 01_wetspell_vs_yield.png")


def chart_workable_days_timeseries(station_metrics):
    """Chart: Workable days over time."""
    fig, axes = plt.subplots(2, 1, figsize=(16, 10), sharex=True)

    for i, window in enumerate(["planting", "harvest"]):
        ax = axes[i]
        wdf = station_metrics[station_metrics["window"] == window]
        avg = wdf.groupby("year")["workable_days_v1"].mean()

        colors = ["#c62828" if v < avg.quantile(0.2) else
                  "#1565c0" if v > avg.quantile(0.8) else "#757575"
                  for v in avg.values]
        ax.bar(avg.index, avg.values, color=colors, alpha=0.8)
        ax.axhline(avg.mean(), color="black", linestyle="--", linewidth=1,
                    label=f"Average: {avg.mean():.0f} days")

        # Label worst years
        worst = avg.nsmallest(5)
        for yr, val in worst.items():
            ax.annotate(str(yr), xy=(yr, val), xytext=(0, -12),
                         textcoords="offset points", ha="center",
                         fontsize=9, fontweight="bold", color="red")

        window_label = "Planting (Apr 1 – Jun 15)" if window == "planting" \
            else "Harvest (Sep 15 – Nov 30)"
        ax.set_title(f"Workable Days During {window_label}")
        ax.set_ylabel("Workable Days")
        ax.legend()
        ax.grid(True, alpha=0.3, axis="y")

    axes[-1].set_xlabel("Year")
    plt.tight_layout()
    fig.savefig(CHARTS / "02_workable_days_timeline.png", bbox_inches="tight")
    plt.close()
    print("    Saved: 02_workable_days_timeline.png")


def chart_metric_comparison(results_plant):
    """Chart: Which metric best predicts yield impact?"""
    fig, ax = plt.subplots(figsize=(12, 7))

    metrics = []
    r_values = []
    for metric, res in sorted(results_plant.items(),
                               key=lambda x: abs(x[1]["r_corn_full"]),
                               reverse=True):
        label = metric.replace("_", " ").title()
        metrics.append(label)
        r_values.append(res["r_corn_full"])

    colors = ["#c62828" if r < -0.2 else "#1565c0" if r > 0.2 else "#757575"
              for r in r_values]
    bars = ax.barh(range(len(metrics)), r_values, color=colors, alpha=0.8)
    ax.set_yticks(range(len(metrics)))
    ax.set_yticklabels(metrics)
    ax.set_xlabel("Correlation with Corn Yield Deviation")
    ax.set_title("Which Planting-Season Rain Metric Best Predicts Yield Impact?\n"
                 "(Negative = more rain/wet days -> lower yields)")
    ax.axvline(x=0, color="black", linewidth=0.5)
    ax.grid(True, alpha=0.3, axis="x")
    ax.invert_yaxis()

    for i, (m, r) in enumerate(zip(metrics, r_values)):
        sig = ""
        p = results_plant.get(m.replace(" ", "_").lower(), {}).get("p_corn", 1)
        if p < 0.01: sig = "***"
        elif p < 0.05: sig = "**"
        elif p < 0.1: sig = "*"
        ax.text(r + (0.01 if r >= 0 else -0.01), i,
                f"{r:.2f}{sig}", va="center",
                ha="left" if r >= 0 else "right", fontsize=10)

    plt.tight_layout()
    fig.savefig(CHARTS / "03_metric_ranking.png", bbox_inches="tight")
    plt.close()
    print("    Saved: 03_metric_ranking.png")


def chart_basis_risk_precip(station_metrics, county_metrics):
    """Chart: Station vs county rainfall scatter plots."""
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    pairs = [
        ("KMDW", "KANE", "Midway vs Kane"),
        ("KMDW", "WILL", "Midway vs Will"),
        ("KMDW", "DEKALB", "Midway vs DeKalb"),
        ("KSPI", "SANGAMON", "Springfield vs Sangamon"),
        ("KPIA", "MCLEAN", "Peoria vs McLean"),
        ("KSPI", "CHAMPAIGN", "Springfield vs Champaign"),
    ]

    for idx, (sid, county, title) in enumerate(pairs):
        ax = axes[idx // 3, idx % 3]

        stn_plant = station_metrics[
            (station_metrics["station"] == sid) &
            (station_metrics["window"] == "planting")
        ][["year", "total_rainfall"]].rename(columns={"total_rainfall": "stn_rain"})

        cty_plant = county_metrics[
            (county_metrics["county"] == county) &
            (county_metrics["window"] == "planting")
        ][["year", "total_rainfall"]].rename(columns={"total_rainfall": "cty_rain"})

        m = stn_plant.merge(cty_plant, on="year")
        if len(m) < 5:
            ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center",
                    transform=ax.transAxes)
            continue

        ax.scatter(m["stn_rain"], m["cty_rain"], alpha=0.7, s=40, color="steelblue")

        # 1:1 line
        lims = [min(m["stn_rain"].min(), m["cty_rain"].min()) - 1,
                max(m["stn_rain"].max(), m["cty_rain"].max()) + 1]
        ax.plot(lims, lims, "k--", alpha=0.3, linewidth=1)

        r, p = stats.pearsonr(m["stn_rain"], m["cty_rain"])
        ax.text(0.05, 0.95, f"r = {r:.2f}", transform=ax.transAxes,
                fontsize=11, va="top",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))

        # Label 2019
        yr19 = m[m["year"] == 2019]
        if len(yr19) > 0:
            ax.annotate("2019",
                         xy=(yr19["stn_rain"].iloc[0], yr19["cty_rain"].iloc[0]),
                         xytext=(5, 5), textcoords="offset points",
                         fontsize=9, fontweight="bold", color="red")

        ax.set_xlabel(f"{STATION_NAMES[sid]} Rain (inches)")
        ax.set_ylabel(f"{county} Avg Rain (inches)")
        ax.set_title(title)
        ax.grid(True, alpha=0.3)

    fig.suptitle("Basis Risk: Station Rainfall vs County Average (Planting Window)",
                 fontsize=14, y=1.02)
    plt.tight_layout()
    fig.savefig(CHARTS / "04_basis_risk_rain.png", bbox_inches="tight")
    plt.close()
    print("    Saved: 04_basis_risk_rain.png")


def chart_tipping_point(merged):
    """Chart: Is there a tipping point in longest wet run?"""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Binned analysis of longest_wet_run vs yield
    valid = merged.dropna(subset=["longest_wet_run", "corn_yield_dev"])

    ax = axes[0]
    bins = [0, 3, 5, 7, 10, 25]
    labels = ["0-3", "4-5", "6-7", "8-10", "11+"]
    valid["wet_run_bin"] = pd.cut(valid["longest_wet_run"], bins=bins,
                                   labels=labels, right=True)

    bin_means = valid.groupby("wet_run_bin", observed=True)["corn_yield_dev"].agg(
        ["mean", "std", "count"])

    colors = ["#4caf50", "#8bc34a", "#ffeb3b", "#ff9800", "#f44336"]
    ax.bar(range(len(bin_means)), bin_means["mean"], color=colors[:len(bin_means)],
           alpha=0.8, edgecolor="gray")
    ax.set_xticks(range(len(bin_means)))
    ax.set_xticklabels(bin_means.index)
    ax.set_xlabel("Longest Wet Run (days)")
    ax.set_ylabel("Avg Corn Yield Deviation (%)")
    ax.set_title("Yield Impact by Longest Wet Spell\n(Planting Window)")
    ax.axhline(y=0, color="black", linewidth=0.5)
    ax.grid(True, alpha=0.3, axis="y")

    for i, (idx, row) in enumerate(bin_means.iterrows()):
        ax.text(i, row["mean"] + (0.5 if row["mean"] >= 0 else -1.5),
                f"n={int(row['count'])}", ha="center", fontsize=9)

    # Rain days binned
    ax = axes[1]
    valid2 = merged.dropna(subset=["rain_days_010", "corn_yield_dev"])
    bins2 = [0, 15, 20, 25, 30, 50]
    labels2 = ["0-15", "16-20", "21-25", "26-30", "31+"]
    valid2["rain_bin"] = pd.cut(valid2["rain_days_010"], bins=bins2,
                                 labels=labels2, right=True)

    bin_means2 = valid2.groupby("rain_bin", observed=True)["corn_yield_dev"].agg(
        ["mean", "std", "count"])

    ax.bar(range(len(bin_means2)), bin_means2["mean"],
           color=colors[:len(bin_means2)], alpha=0.8, edgecolor="gray")
    ax.set_xticks(range(len(bin_means2)))
    ax.set_xticklabels(bin_means2.index)
    ax.set_xlabel("Rain Days (>= 0.10\") in Planting Window")
    ax.set_ylabel("Avg Corn Yield Deviation (%)")
    ax.set_title("Yield Impact by Number of Rain Days\n(Planting Window)")
    ax.axhline(y=0, color="black", linewidth=0.5)
    ax.grid(True, alpha=0.3, axis="y")

    for i, (idx, row) in enumerate(bin_means2.iterrows()):
        ax.text(i, row["mean"] + (0.5 if row["mean"] >= 0 else -1.5),
                f"n={int(row['count'])}", ha="center", fontsize=9)

    plt.tight_layout()
    fig.savefig(CHARTS / "05_tipping_points.png", bbox_inches="tight")
    plt.close()
    print("    Saved: 05_tipping_points.png")


# ===========================================================================
# SECTION 7: Kalshi Hedge Backtest
# ===========================================================================

def backtest_kalshi_rain_hedge(station_metrics, merged, harv_merged):
    """
    Backtest Kalshi rain hedge strategies.

    Strategy A: Buy "rain YES" every day in the planting window.
    Strategy B: Buy "rain YES" only after 2+ wet days (betting spell continues).
    Strategy C: Buy monthly rain contracts for Apr, May, Sep, Oct.
    """
    print("\n\n  === KALSHI RAIN HEDGE BACKTEST ===")
    print("  " + "=" * 45)

    # Historical rain frequencies at Midway
    mdw_plant = station_metrics[
        (station_metrics["station"] == "KMDW") &
        (station_metrics["window"] == "planting")
    ].copy()

    # Daily rain probability (across all planting window days)
    mdw_all = pd.read_csv(DATA / "station_KMDW_daily.csv")
    mdw_all["date"] = pd.to_datetime(mdw_all["date"])
    mdw_all["month"] = mdw_all["date"].dt.month
    mdw_all["day"] = mdw_all["date"].dt.day
    mdw_all["year"] = mdw_all["date"].dt.year

    # Planting window days
    plant_days = mdw_all[
        ((mdw_all["month"] >= 4) & (mdw_all["month"] <= 5)) |
        ((mdw_all["month"] == 6) & (mdw_all["day"] <= 15))
    ].copy()

    prob_rain_001 = (plant_days["precip_in"] >= 0.01).mean()
    prob_rain_010 = (plant_days["precip_in"] >= 0.10).mean()
    prob_rain_025 = (plant_days["precip_in"] >= 0.25).mean()

    print(f"\n  Historical rain probabilities (planting window, Midway):")
    print(f"    P(>= 0.01\"): {prob_rain_001:.1%}")
    print(f"    P(>= 0.10\"): {prob_rain_010:.1%}")
    print(f"    P(>= 0.25\"): {prob_rain_025:.1%}")
    print(f"    Fair price for 'rain today' (>= 0.01\"): ${prob_rain_001:.2f}")

    # Model farm
    farm_acres = 1000  # Corn + soy
    corn_acres = 600
    soy_acres = 400
    corn_trend_yield = 200
    soy_trend_yield = 55
    corn_price = 4.50
    soy_price = 11.00
    gross_rev = corn_acres * corn_trend_yield * corn_price + \
                soy_acres * soy_trend_yield * soy_price
    print(f"\n  Model farm: {corn_acres} acres corn, {soy_acres} acres soybeans")
    print(f"  Gross revenue at trend: ${gross_rev:,.0f}")

    # --- STRATEGY A: Buy "rain YES" every planting day ---
    print(f"\n  --- STRATEGY A: Buy 'rain YES' every planting day ---")
    strat_a_results = []
    window_days = 76  # Apr 1 - Jun 15
    contracts_per_day = 200
    fair_price = prob_rain_001  # ~42%

    for _, row in mdw_plant.iterrows():
        year = row["year"]
        rain_days = row["rain_days_001"]
        # Payout: $1 per contract on each rain day
        payout = rain_days * contracts_per_day
        cost = window_days * contracts_per_day * fair_price
        net = payout - cost

        # Get yield deviation
        yr_data = merged[merged["year"] == year]
        yield_dev = yr_data["corn_yield_dev"].iloc[0] if len(yr_data) > 0 else 0
        yield_loss = min(0, yield_dev) * gross_rev / 100

        strat_a_results.append({
            "year": int(year), "rain_days": rain_days,
            "payout": payout, "cost": cost, "net_hedge": net,
            "yield_loss": yield_loss,
            "net_with_hedge": yield_loss + net,
            "strategy": "A",
        })

    df_a = pd.DataFrame(strat_a_results)
    print(f"  Avg annual cost: ${df_a['cost'].mean():,.0f}")
    print(f"  Avg annual payout: ${df_a['payout'].mean():,.0f}")
    print(f"  Avg net: ${df_a['net_hedge'].mean():,.0f}")

    # --- STRATEGY B: Buy "rain YES" only after 2+ consecutive wet days ---
    print(f"\n  --- STRATEGY B: Buy 'rain YES' after 2+ wet days ---")
    strat_b_results = []

    # Need daily data to simulate this
    for year in range(1980, 2025):
        start = pd.Timestamp(f"{year}-04-01")
        end = pd.Timestamp(f"{year}-06-15")
        daily = mdw_all[(mdw_all["date"] >= start) & (mdw_all["date"] <= end)].copy()

        if len(daily) < 50:
            continue

        # Simulate: after 2 consecutive wet days, buy "rain YES" for next day
        bets = 0
        wins = 0
        consecutive_wet = 0

        for idx, drow in daily.iterrows():
            pcpn = drow["precip_in"]
            is_wet = pcpn >= 0.01 if pd.notna(pcpn) else False

            if consecutive_wet >= 2:
                bets += 1
                if is_wet:
                    wins += 1

            if is_wet:
                consecutive_wet += 1
            else:
                consecutive_wet = 0

        # After 2 wet days, P(3rd day wet) is higher than unconditional
        conditional_prob = wins / bets if bets > 0 else prob_rain_001
        payout = wins * contracts_per_day
        cost = bets * contracts_per_day * fair_price  # Still pay fair unconditional price
        net = payout - cost

        yr_data = merged[merged["year"] == year]
        yield_dev = yr_data["corn_yield_dev"].iloc[0] if len(yr_data) > 0 else 0
        yield_loss = min(0, yield_dev) * gross_rev / 100

        strat_b_results.append({
            "year": year, "bets": bets, "wins": wins,
            "payout": payout, "cost": cost, "net_hedge": net,
            "yield_loss": yield_loss, "net_with_hedge": yield_loss + net,
            "conditional_prob": conditional_prob,
            "strategy": "B",
        })

    df_b = pd.DataFrame(strat_b_results)
    if len(df_b) > 0:
        avg_cond = df_b["conditional_prob"].mean()
        print(f"  P(rain | 2+ wet days): {avg_cond:.1%} vs unconditional {prob_rain_001:.1%}")
        print(f"  Avg bets/year: {df_b['bets'].mean():.0f}")
        print(f"  Avg annual cost: ${df_b['cost'].mean():,.0f}")
        print(f"  Avg annual payout: ${df_b['payout'].mean():,.0f}")
        print(f"  Avg net: ${df_b['net_hedge'].mean():,.0f}")

    # --- STRATEGY C: Monthly rain total contracts ---
    print(f"\n  --- STRATEGY C: Monthly total rain contracts ---")
    strat_c_results = []

    for year in range(1980, 2025):
        monthly_payouts = 0
        monthly_costs = 0

        for month in [4, 5, 9, 10]:
            mdata = mdw_all[(mdw_all["year"] == year) & (mdw_all["month"] == month)]
            if len(mdata) == 0:
                continue

            monthly_total = mdata["precip_in"].sum()

            # Buy "above 4 inches" (typical threshold)
            # Historical freq of monthly total > 4"
            all_months = mdw_all[mdw_all["month"] == month].groupby("year")[
                "precip_in"].sum()
            prob_above_4 = (all_months > 4.0).mean()

            contracts = 500
            cost = contracts * prob_above_4
            payout = contracts if monthly_total > 4.0 else 0

            monthly_costs += cost
            monthly_payouts += payout

        yr_data = merged[merged["year"] == year]
        yield_dev = yr_data["corn_yield_dev"].iloc[0] if len(yr_data) > 0 else 0
        yield_loss = min(0, yield_dev) * gross_rev / 100

        strat_c_results.append({
            "year": year, "payout": monthly_payouts,
            "cost": monthly_costs, "net_hedge": monthly_payouts - monthly_costs,
            "yield_loss": yield_loss,
            "net_with_hedge": yield_loss + (monthly_payouts - monthly_costs),
            "strategy": "C",
        })

    df_c = pd.DataFrame(strat_c_results)
    if len(df_c) > 0:
        print(f"  Avg annual cost: ${df_c['cost'].mean():,.0f}")
        print(f"  Avg annual payout: ${df_c['payout'].mean():,.0f}")
        print(f"  Avg net: ${df_c['net_hedge'].mean():,.0f}")

    # Compare worst years
    print(f"\n  --- WORST YEAR COMPARISON ---")
    for yr in [2019, 1993, 2009, 2008]:
        print(f"\n  Year {yr}:")
        for label, df_s in [("A", df_a), ("B", df_b), ("C", df_c)]:
            row = df_s[df_s["year"] == yr]
            if len(row) > 0:
                r = row.iloc[0]
                print(f"    Strategy {label}: Cost ${r['cost']:,.0f} | "
                      f"Payout ${r['payout']:,.0f} | "
                      f"Net ${r['net_hedge']:+,.0f}")

    all_bt = pd.concat([df_a, df_b, df_c], ignore_index=True)
    return all_bt, df_a, df_b, df_c


def chart_hedge_backtest(df_a, df_b, df_c):
    """Chart: Hedge backtest comparison."""
    fig, axes = plt.subplots(2, 2, figsize=(18, 12))

    # Panel 1: Strategy comparison - net hedge P&L over time
    ax = axes[0, 0]
    for label, df_s, color in [
        ("A: Every day", df_a, "steelblue"),
        ("B: After 2+ wet", df_b, "darkorange"),
        ("C: Monthly >4\"", df_c, "seagreen"),
    ]:
        s = df_s.sort_values("year")
        cum = s["net_hedge"].cumsum() / 1000
        ax.plot(s["year"], cum, linewidth=2, label=label, color=color)

    ax.axhline(y=0, color="black", linewidth=0.5)
    ax.set_xlabel("Year")
    ax.set_ylabel("Cumulative Hedge-Only P&L ($000s)")
    ax.set_title("Cumulative Hedge P&L by Strategy")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel 2: Worst years — bar chart
    ax = axes[0, 1]
    worst_years = [1993, 2008, 2009, 2015, 2019]
    x = np.arange(len(worst_years))
    width = 0.25

    for i, (label, df_s, color) in enumerate([
        ("A", df_a, "steelblue"),
        ("B", df_b, "darkorange"),
        ("C", df_c, "seagreen"),
    ]):
        vals = []
        for yr in worst_years:
            row = df_s[df_s["year"] == yr]
            vals.append(row["net_hedge"].iloc[0] / 1000 if len(row) > 0 else 0)
        ax.bar(x + i * width, vals, width, label=f"Strategy {label}",
               color=color, alpha=0.8)

    ax.set_xticks(x + width)
    ax.set_xticklabels(worst_years)
    ax.set_ylabel("Net Hedge P&L ($000s)")
    ax.set_title("Hedge Performance in Wet Years")
    ax.legend()
    ax.axhline(y=0, color="black", linewidth=0.5)
    ax.grid(True, alpha=0.3, axis="y")

    # Panel 3: Annual cost vs payout for Strategy A
    ax = axes[1, 0]
    s = df_a.sort_values("year")
    ax.bar(s["year"], s["payout"] / 1000, alpha=0.6, color="steelblue",
           label="Payout")
    ax.axhline(y=s["cost"].mean() / 1000, color="red", linestyle="--",
               linewidth=2, label=f"Avg Cost: ${s['cost'].mean():,.0f}")
    ax.set_xlabel("Year")
    ax.set_ylabel("$000s")
    ax.set_title("Strategy A: Annual Payouts vs Average Cost")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    # Panel 4: Rain days distribution
    ax = axes[1, 1]
    rain = df_a["rain_days"].dropna()
    ax.hist(rain, bins=15, color="steelblue", alpha=0.7, edgecolor="navy")
    ax.axvline(rain.mean(), color="red", linestyle="--", linewidth=2,
               label=f"Mean: {rain.mean():.0f} days")
    ax.set_xlabel("Rain Days in Planting Window (Midway, >= 0.01\")")
    ax.set_ylabel("Number of Years")
    ax.set_title("Distribution of Planting-Season Rain Days")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    fig.suptitle("Kalshi Rain Contract Hedge Backtest", fontsize=15, y=1.02)
    plt.tight_layout()
    fig.savefig(CHARTS / "06_hedge_backtest.png", bbox_inches="tight")
    plt.close()
    print("    Saved: 06_hedge_backtest.png")


def chart_year_profiles(station_metrics):
    """Chart: Profile of notable wet years."""
    fig, axes = plt.subplots(2, 3, figsize=(20, 10))

    notable_years = [2019, 1993, 2009, 2015, 2008, 2024]

    plant = station_metrics[
        (station_metrics["station"] == "KMDW") &
        (station_metrics["window"] == "planting")
    ]

    metrics_to_show = ["rain_days_010", "longest_wet_run", "spells_3plus",
                        "workable_days_v1", "total_rainfall", "heavy_rain_days"]
    metric_labels = ["Rain Days\n(>=0.10\")", "Longest\nWet Run", "Wet Spells\n(3+ days)",
                     "Workable\nDays", "Total\nRain (in)", "Heavy Days\n(>=1\")"]

    for i, year in enumerate(notable_years):
        ax = axes[i // 3, i % 3]
        yr_data = plant[plant["year"] == year]

        if len(yr_data) == 0:
            ax.text(0.5, 0.5, f"{year}: no data", ha="center", va="center",
                    transform=ax.transAxes)
            continue

        vals = [yr_data[m].iloc[0] for m in metrics_to_show]
        avgs = [plant[m].mean() for m in metrics_to_show]

        x = np.arange(len(metrics_to_show))
        ax.bar(x - 0.15, vals, 0.3, label=str(year), color="crimson", alpha=0.8)
        ax.bar(x + 0.15, avgs, 0.3, label="Average", color="steelblue", alpha=0.6)

        ax.set_xticks(x)
        ax.set_xticklabels(metric_labels, fontsize=8)
        ax.set_title(f"{year}")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3, axis="y")

    fig.suptitle("Planting Season Weather Profiles: Notable Wet Years vs Average (Midway)",
                 fontsize=14, y=1.02)
    plt.tight_layout()
    fig.savefig(CHARTS / "07_year_profiles.png", bbox_inches="tight")
    plt.close()
    print("    Saved: 07_year_profiles.png")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    print("=" * 70)
    print("  OFF-SEASON RAIN ANALYSIS — FULL PIPELINE")
    print("=" * 70)

    print("\n[1/8] Loading data...")
    station_data = load_station_data()
    county_precip = load_county_precip()
    yield_df = load_yields()

    print("\n[2/8] Computing wet-spell metrics (stations)...")
    station_metrics = build_station_metrics(station_data)
    station_metrics.to_csv(DATA / "station_wetspell_metrics.csv", index=False)

    print("\n[3/8] Computing wet-spell metrics (counties)...")
    county_metrics = build_county_metrics(county_precip)
    county_metrics.to_csv(DATA / "county_wetspell_metrics.csv", index=False)

    print("\n[4/8] Building outcome proxies...")
    progress = build_crop_progress_proxy(station_metrics)
    rma_proxy = build_rma_proxy()

    print("\n[5/8] Analyzing weather-outcome correlations...")
    results_plant, results_harv, merged, harv_merged = \
        analyze_weather_outcome_correlations(
            station_metrics, county_metrics, yield_df, progress)

    print("\n[6/8] Analyzing basis risk...")
    basis_results = analyze_basis_risk(station_metrics, county_metrics)

    print("\n[7/8] Generating charts...")
    chart_wet_spell_vs_yield(merged, harv_merged)
    chart_workable_days_timeseries(station_metrics)
    chart_metric_comparison(results_plant)
    chart_basis_risk_precip(station_metrics, county_metrics)
    chart_tipping_point(merged)
    chart_year_profiles(station_metrics)

    print("\n[8/8] Running Kalshi hedge backtest...")
    all_bt, df_a, df_b, df_c = backtest_kalshi_rain_hedge(
        station_metrics, merged, harv_merged)
    chart_hedge_backtest(df_a, df_b, df_c)

    # Save all results
    all_bt.to_csv(DATA / "hedge_backtest_results.csv", index=False)

    print("\n" + "=" * 70)
    print("  ANALYSIS COMPLETE!")
    print("=" * 70)

    return (station_metrics, county_metrics, yield_df, results_plant,
            results_harv, basis_results, all_bt, df_a, df_b, df_c,
            merged, harv_merged)


if __name__ == "__main__":
    main()
