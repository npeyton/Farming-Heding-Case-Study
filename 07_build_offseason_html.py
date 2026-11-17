"""
Build self-contained HTML report for the Off-Season Rain study.
Embeds all charts as base64 so the file is completely standalone.
"""

import base64, os
from pathlib import Path

BASE = Path(__file__).parent
CHARTS = BASE / "charts" / "offseason"
OUT = BASE / "Offseason_Rain_Case_Study.html"


def img(name):
    path = CHARTS / name
    if not path.exists():
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def build():
    c = {p.stem: img(p.name) for p in sorted(CHARTS.glob("*.png"))}

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Off-Season Rain Case Study — Kalshi Rain Contracts vs Illinois Crop Risk</title>
<style>
  :root {{--accent:#1565c0;--accent2:#c62828;--bg:#fff;--text:#1a1a2e;--muted:#555;--border:#e0e0e0;--card:#fafafa;--green:#2e7d32;--orange:#ef6c00;--red:#c62828;}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;color:var(--text);background:var(--bg);line-height:1.7;max-width:980px;margin:0 auto;padding:2rem 1.5rem 4rem}}
  h1{{font-size:2rem;font-weight:700;color:var(--accent);margin:0 0 .25rem}}
  h1 small{{display:block;font-size:1rem;font-weight:400;color:var(--muted);margin-top:.25rem}}
  h2{{font-size:1.45rem;font-weight:700;margin:2.5rem 0 .75rem;padding-bottom:.4rem;border-bottom:2px solid var(--accent)}}
  h3{{font-size:1.15rem;font-weight:600;margin:1.5rem 0 .5rem;color:var(--accent)}}
  p,li{{margin-bottom:.6rem}}
  ul,ol{{padding-left:1.5rem}}
  .sub{{color:var(--muted);font-size:.95rem;margin-bottom:2rem;border-bottom:1px solid var(--border);padding-bottom:1rem}}
  .chart{{margin:1.5rem 0;text-align:center}}
  .chart img{{max-width:100%;height:auto;border:1px solid var(--border);border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,.08)}}
  .cap{{font-size:.85rem;color:var(--muted);font-style:italic;margin-top:.4rem}}
  .sg{{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:1rem 0}}
  .sg3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem;margin:1rem 0}}
  .sc{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:1rem 1.25rem}}
  .sc .lb{{font-size:.8rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}}
  .sc .vl{{font-size:1.5rem;font-weight:700;color:var(--accent)}}
  .sc .dt{{font-size:.85rem;color:var(--muted);margin-top:.2rem}}
  table{{width:100%;border-collapse:collapse;margin:1rem 0;font-size:.92rem}}
  th,td{{padding:.5rem .75rem;text-align:left;border-bottom:1px solid var(--border)}}
  th{{background:var(--card);font-weight:600;font-size:.82rem;text-transform:uppercase;letter-spacing:.03em;color:var(--muted)}}
  tr:hover td{{background:#f9f9ff}}
  .good{{color:var(--green);font-weight:600}}
  .fair{{color:var(--orange);font-weight:600}}
  .poor{{color:var(--red);font-weight:600}}
  .co{{padding:1rem 1.25rem;border-radius:0 6px 6px 0;margin:1.25rem 0}}
  .co.info{{background:#e3f2fd;border-left:4px solid var(--accent)}}
  .co.warn{{background:#fff3e0;border-left:4px solid var(--orange)}}
  .co.ok{{background:#e8f5e9;border-left:4px solid var(--green)}}
  .co.bad{{background:#ffebee;border-left:4px solid var(--red)}}
  .co strong{{display:block;margin-bottom:.3rem}}
  .fb{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:1.25rem;margin:1rem 0}}
  .fb h4{{margin:0 0 .5rem;font-size:1rem;color:var(--accent)}}
  .toc{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:1.25rem 1.5rem;margin:1.5rem 0}}
  .toc ol{{margin-bottom:0}} .toc li{{margin-bottom:.3rem}} .toc a{{color:var(--accent);text-decoration:none}} .toc a:hover{{text-decoration:underline}}
  .foot{{margin-top:3rem;padding-top:1.5rem;border-top:1px solid var(--border);font-size:.85rem;color:var(--muted)}}
  @media(max-width:600px){{.sg,.sg3{{grid-template-columns:1fr}}body{{padding:1rem}}}}
</style>
</head>
<body>

<h1>Off-Season Rain &amp; Illinois Crops
<small>Can Kalshi Rain Contracts Hedge Planting &amp; Harvest Disruptions?</small>
</h1>
<p class="sub">
<strong>Farm counties:</strong> DeKalb, Kane, Kendall, Will, Grundy, LaSalle, Kankakee (north IL) + Sangamon, McLean, Champaign (central IL)<br>
<strong>Stations:</strong> Midway, O'Hare, Rockford, Peoria, Springfield &bull;
<strong>Data:</strong> 1980–2025 (45 years) &bull; 636 NOAA weather stations &bull; 5 airport stations
</p>

<div class="toc"><strong>Contents</strong>
<ol>
<li><a href="#s1">Executive Summary</a></li>
<li><a href="#s2">Why Off-Season Rain Matters</a></li>
<li><a href="#s3">The Data</a></li>
<li><a href="#s4">Wet-Spell Metrics — What We Measured</a></li>
<li><a href="#s5">Which Rain Patterns Hurt Farmers Most?</a></li>
<li><a href="#s6">Tipping Points</a></li>
<li><a href="#s7">Basis Risk: Airport vs Farm</a></li>
<li><a href="#s8">Kalshi Contract Rules</a></li>
<li><a href="#s9">Hedge Backtest: Three Strategies</a></li>
<li><a href="#s10">Strategy Ranking</a></li>
<li><a href="#s11">Key Findings</a></li>
<li><a href="#s12">Limitations &amp; Next Steps</a></li>
</ol></div>

<!-- ================================================================ -->
<h2 id="s1">1. Executive Summary</h2>

<p>We tested whether rain patterns during the <strong>planting window</strong> (April 1 – June 15) and <strong>harvest window</strong> (September 15 – November 30) predict yield losses in 10 Illinois farm counties, and whether Kalshi's rain contracts could offset those losses.</p>

<div class="sg">
<div class="sc"><div class="lb">Planting-window rain–yield link</div><div class="vl">Weak</div><div class="dt">Individual metrics explain &lt;5% of yield variation; rain affects planting pace more than final yields</div></div>
<div class="sc"><div class="lb">Rain basis risk (station vs county)</div><div class="vl">0.75–0.97</div><div class="dt">Much better than expected; Springfield–Sangamon hits r&nbsp;=&nbsp;0.97</div></div>
<div class="sc"><div class="lb">Best hedge strategy</div><div class="vl">B (conditional)</div><div class="dt">Buying "rain YES" after 2+ wet days exploits 46% conditional probability vs 39% fair price</div></div>
<div class="sc"><div class="lb">2019 hedge payout (Strat A)</div><div class="vl">+$2,848</div><div class="dt">Largest payout in 45 years, correctly triggered by record wet spring</div></div>
</div>

<div class="co warn"><strong>Key surprise: Rainfall basis risk is much lower for planting/harvest windows than for July.</strong>
Our earlier heat study found July precipitation correlation averaging only r&nbsp;=&nbsp;0.46 between Midway and farm counties. But for the longer planting and harvest windows (76 and 77 days), correlations average r&nbsp;=&nbsp;0.85+. Longer windows smooth out daily storm randomness, making station-based rain contracts more viable than expected.</div>

<!-- ================================================================ -->
<h2 id="s2">2. Why Off-Season Rain Matters</h2>

<p>Farmers don't just worry about summer drought. Two other weather windows can make or break a crop year:</p>

<h3>Planting Season (April 1 – June 15)</h3>
<ul>
<li>Corn must be planted by mid-May for optimal yields; soybeans by early June.</li>
<li>Fields must be dry enough to support heavy equipment — typically needing 1–2 dry days after rain.</li>
<li>A run of 5+ consecutive wet days can push planting back a full week, with every day of delay after May 15 costing roughly 1 bushel/acre in corn yield.</li>
<li><strong>2019 was the poster child:</strong> record spring rain across Illinois left millions of acres unplanted. USDA declared the largest prevented-planting event in decades.</li>
</ul>

<h3>Harvest Season (September 15 – November 30)</h3>
<ul>
<li>Wet fields delay combines, leading to late harvest, higher grain moisture (expensive drying), and risk of ear rot and stalk lodging.</li>
<li>A wet October can force farmers to choose between harvesting at high moisture (costly) or waiting and risking a November freeze.</li>
<li><strong>2009 was a classic late harvest:</strong> persistent fall rain pushed harvest well into November across much of Illinois.</li>
</ul>

<p>The key insight: <strong>runs of consecutive wet days matter more than total rainfall.</strong> A 3-inch rain followed by 5 dry days is manageable; 10 days of 0.3-inch drizzle that never lets fields dry is devastating.</p>

<!-- ================================================================ -->
<h2 id="s3">3. The Data</h2>

<table>
<tr><th>Dataset</th><th>Source</th><th>Coverage</th><th>Records</th></tr>
<tr><td><strong>Airport weather</strong></td><td>NOAA ACIS (5 stations)</td><td>1980–2025 daily</td><td>83,780 station-days</td></tr>
<tr><td><strong>County rainfall</strong></td><td>NOAA ACIS (636 stations)</td><td>1980–2025 daily</td><td>1.5M station-days &rarr; 162K county-days</td></tr>
<tr><td><strong>Corn yields</strong></td><td>USDA NASS (via IL state data)</td><td>1980–2024</td><td>450 county-year records</td></tr>
<tr><td><strong>Soybean yields</strong></td><td>USDA NASS (via IL state data)</td><td>1980–2024</td><td>450 county-year records</td></tr>
</table>

<div class="co info"><strong>Sanity check passed:</strong> 2019 shows 13–17 inches of spring rain across all stations and counties, matching historical records of the wettest spring on record. 2009 shows up as a wet harvest year. The data is internally consistent.</div>

<!-- ================================================================ -->
<h2 id="s4">4. Wet-Spell Metrics — What We Measured</h2>

<p>For each station and county, for each year, for both windows, we computed:</p>
<table>
<tr><th>Metric</th><th>What It Measures</th><th>Why It Matters</th></tr>
<tr><td>Rain days (&ge;0.01")</td><td>Any measurable precipitation</td><td>Broadest measure of wet days</td></tr>
<tr><td>Rain days (&ge;0.10")</td><td>Meaningful rain</td><td>Better threshold — trace rain doesn't stop fieldwork</td></tr>
<tr><td>Rain days (&ge;0.25")</td><td>Substantial rain</td><td>Definitely delays field operations</td></tr>
<tr><td>Longest wet run</td><td>Consecutive days with rain</td><td>Extended wet spells keep fields waterlogged</td></tr>
<tr><td>Wet spells (3+ days)</td><td>Number of multi-day rain events</td><td>Repeated disruptions</td></tr>
<tr><td>Workable days (v1)</td><td>Dry today + yesterday was dryish</td><td>Simpler "can we get in the field?" rule</td></tr>
<tr><td>Workable days (v2)</td><td>Dry today + 2-day rolling avg &lt;0.25"</td><td>Stricter "field has dried out" rule</td></tr>
<tr><td>Longest dry window</td><td>Best stretch for uninterrupted fieldwork</td><td>Key for planting marathons</td></tr>
<tr><td>Total rainfall</td><td>Simple inches total</td><td>Traditional benchmark</td></tr>
<tr><td>Heavy-rain days (&ge;1")</td><td>Days with &ge;1 inch</td><td>Major disruptors</td></tr>
</table>

<div class="chart"><img src="data:image/png;base64,{c.get('02_workable_days_timeline','')}" alt="Workable days timeline">
<div class="cap">Figure 1 — Workable days during planting (top) and harvest (bottom) windows. Red bars are the worst years. 2019 stands out clearly as the worst planting spring in 45 years.</div></div>

<div class="chart"><img src="data:image/png;base64,{c.get('07_year_profiles','')}" alt="Year profiles">
<div class="cap">Figure 2 — Weather profiles of notable wet years compared to the long-run average (Midway, planting window). 2019 shows up with far more rain days, longer wet spells, and fewer workable days than any other year.</div></div>

<!-- ================================================================ -->
<h2 id="s5">5. Which Rain Patterns Hurt Farmers Most?</h2>

<p>We correlated each wet-spell metric with detrended corn and soybean yields across 45 years. To guard against overfitting, we split the data into even-year (train) and odd-year (test) halves.</p>

<div class="chart"><img src="data:image/png;base64,{c.get('03_metric_ranking','')}" alt="Metric ranking">
<div class="cap">Figure 3 — Ranking of planting-season rain metrics by correlation with corn yield. No single metric achieves strong statistical significance, but the direction is consistent: more rain / fewer workable days = lower yields.</div></div>

<div class="chart"><img src="data:image/png;base64,{c.get('01_wetspell_vs_yield','')}" alt="Wet spell vs yield scatter">
<div class="cap">Figure 4 — Scatter plots showing planting and harvest weather vs yield deviations. 2019, 1993, and 2009 are labeled where visible. The relationships are noisy but directionally correct.</div></div>

<div class="co warn"><strong>Honest finding: Individual spring rain metrics are weak predictors of final yields.</strong>
No single metric explains more than ~5% of corn yield variation. This doesn't mean rain doesn't matter — it means that spring rain primarily affects <em>planting timing and prevented acreage</em>, while final yields on acres that DO get planted are more affected by summer weather. The economic damage from wet springs is real but shows up in <strong>prevented planting</strong> and <strong>planting delays</strong>, not directly in per-acre yield numbers.

<br><br>The harvest window similarly shows weak yield correlations — because harvest rain mainly increases <strong>drying costs</strong> and <strong>quality losses</strong> (mold, lodging), which aren't captured in yield-per-acre data.

<br><br>This is a critical distinction: Kalshi rain contracts could still be valuable hedges, but the loss channel is <strong>prevented planting / delayed operations / quality degradation</strong>, not primarily yield-per-acre reductions.</div>

<!-- ================================================================ -->
<h2 id="s6">6. Tipping Points</h2>

<div class="chart"><img src="data:image/png;base64,{c.get('05_tipping_points','')}" alt="Tipping points">
<div class="cap">Figure 5 — Binned analysis showing average yield deviation by longest wet run (left) and by number of rain days (right). There is a suggestive pattern where yields drop once the longest wet spell exceeds ~7 days or rain days exceed ~25, but the sample sizes per bin are small. These tipping points should be treated as directional signals, not firm thresholds.</div></div>

<p>The data suggests a possible tipping point around <strong>7+ consecutive wet days</strong> in the planting window, where yield impacts start becoming consistent. However, with only ~45 years of data and small bin sizes, this is a signal to watch rather than a confident threshold.</p>

<!-- ================================================================ -->
<h2 id="s7">7. Basis Risk: Airport Rain vs Farm Rain</h2>

<p>A critical question: if you buy a Kalshi rain contract settled at Midway Airport, does that actually reflect what happened on farms 40–80 miles away?</p>

<div class="chart"><img src="data:image/png;base64,{c.get('04_basis_risk_rain','')}" alt="Basis risk scatter">
<div class="cap">Figure 6 — Station rainfall vs county average for the planting window. Correlations range from 0.75 to 0.97. Springfield–Sangamon (r&nbsp;=&nbsp;0.97) is remarkably tight. 2019 is labeled as the extreme wet year.</div></div>

<h3>Planting Window Basis Risk</h3>
<table>
<tr><th>Station</th><th>County</th><th>Correlation (r)</th><th>Rating</th><th>Bias</th></tr>
<tr><td>Springfield</td><td>Sangamon</td><td>0.97</td><td class="good">EXCELLENT</td><td>-0.4"</td></tr>
<tr><td>O'Hare</td><td>Kane</td><td>0.91</td><td class="good">GOOD</td><td>-0.7"</td></tr>
<tr><td>Midway</td><td>Kendall</td><td>0.91</td><td class="good">GOOD</td><td>-1.0"</td></tr>
<tr><td>Midway</td><td>Grundy</td><td>0.90</td><td class="good">GOOD</td><td>-0.6"</td></tr>
<tr><td>Midway</td><td>Kane</td><td>0.87</td><td class="good">GOOD</td><td>-1.0"</td></tr>
<tr><td>Midway</td><td>Kankakee</td><td>0.86</td><td class="good">GOOD</td><td>-1.1"</td></tr>
<tr><td>Peoria</td><td>LaSalle</td><td>0.86</td><td class="good">GOOD</td><td>+0.2"</td></tr>
<tr><td>Peoria</td><td>McLean</td><td>0.86</td><td class="good">GOOD</td><td>+0.1"</td></tr>
<tr><td>Midway</td><td>Will</td><td>0.85</td><td class="good">GOOD</td><td>-1.4"</td></tr>
<tr><td>O'Hare</td><td>DeKalb</td><td>0.80</td><td class="good">GOOD</td><td>-0.4"</td></tr>
<tr><td>Rockford</td><td>DeKalb</td><td>0.80</td><td class="good">GOOD</td><td>-0.2"</td></tr>
<tr><td>Springfield</td><td>Champaign</td><td>0.75</td><td class="good">GOOD</td><td>-0.2"</td></tr>
</table>

<div class="co ok"><strong>Much better than expected.</strong> Rainfall basis risk over 76-day windows (planting season) is dramatically lower than for single months. The longer averaging period smooths out daily storm randomness. All station–county pairs exceed r&nbsp;=&nbsp;0.75, and most are above 0.85. This means station-settled Kalshi rain contracts are more usable for seasonal hedging than our earlier July-only analysis suggested.</div>

<h3>Notable Divergence Years</h3>
<table>
<tr><th>Type</th><th>Year</th><th>Midway</th><th>N. IL Counties</th><th>Difference</th></tr>
<tr><td>Midway wetter</td><td>1983</td><td>16.1"</td><td>12.7"</td><td>+3.4"</td></tr>
<tr><td>Midway drier</td><td>1987</td><td>6.1"</td><td>9.9"</td><td>-3.8"</td></tr>
<tr><td>Midway drier</td><td>2002</td><td>8.9"</td><td>12.5"</td><td>-3.7"</td></tr>
</table>
<p>In most years the gap is under 2 inches. The worst divergences (~3–4 inches) happen in years with localized storm systems — but even these are within 30% of the total, which is manageable for a probabilistic hedge.</p>

<!-- ================================================================ -->
<h2 id="s8">8. Kalshi Rain Contract Rules</h2>

<p>Based on current Kalshi offerings (late 2026):</p>

<h3>Daily Rain Contracts</h3>
<table>
<tr><th>Detail</th><th>Chicago</th><th>Notes</th></tr>
<tr><td>Contract type</td><td>Binary: "Will it rain today?"</td><td>Yes/No, pays $1.00 or $0.00</td></tr>
<tr><td>Settlement station</td><td><strong>Midway (KMDW)</strong> for daily temp; <strong>O'Hare (KORD)</strong> for monthly rain</td><td>Check current rules — this has changed</td></tr>
<tr><td>Rain threshold</td><td>Typically &ge; 0.01" (any measurable)</td><td>Trace (T) counts as 0.00"</td></tr>
<tr><td>Data source</td><td>NWS Daily Climate Report / The Weather Company</td><td>Changed Aug 2026</td></tr>
<tr><td>Listing horizon</td><td>~7 days ahead</td><td>Forecast is partly known at purchase</td></tr>
<tr><td>Fair price (planting season)</td><td>~$0.39</td><td>39% of spring days have measurable rain</td></tr>
</table>

<h3>Monthly Rain Total Contracts</h3>
<table>
<tr><th>Detail</th><th>Value</th></tr>
<tr><td>Thresholds</td><td>Above 1", 2", 3", 4", 5", 6" etc.</td></tr>
<tr><td>Settlement station</td><td>O'Hare (KORD) as of Sep 2026</td></tr>
<tr><td>Cities available</td><td>30+ cities — check for Chicago, St. Louis, Indianapolis</td></tr>
<tr><td>Springfield</td><td>Not confirmed for Springfield IL specifically — may be Springfield MO or not available. <strong>Verify before trading.</strong></td></tr>
</table>

<div class="co warn"><strong>Timing limitation:</strong> Daily rain contracts list only ~7 days before the event, when weather forecasts are already partially known. This means you're not buying pure "rain risk" — you're buying at prices that already reflect the forecast. A farmer who wants to hedge the entire planting season needs to buy contracts rolling, day by day, paying whatever the market charges once forecasts become available. The hedge is less about predicting rain and more about <em>monetizing known rainy days</em> that will prevent fieldwork.</div>

<!-- ================================================================ -->
<h2 id="s9">9. Hedge Backtest: Three Strategies</h2>

<p>We tested three approaches using a model farm: 600 acres corn + 400 acres soybeans, gross revenue $782,000 at trend yields.</p>

<div class="sg3">
<div class="sc"><div class="lb">Strategy A</div><div class="vl">Every Day</div><div class="dt">Buy 200 "rain YES" contracts for every day in the planting window (76 days)</div></div>
<div class="sc"><div class="lb">Strategy B</div><div class="vl">Conditional</div><div class="dt">Buy "rain YES" only after 2+ consecutive wet days (bet the spell continues)</div></div>
<div class="sc"><div class="lb">Strategy C</div><div class="vl">Monthly Total</div><div class="dt">Buy "above 4 inches" monthly contracts for Apr, May, Sep, Oct</div></div>
</div>

<div class="chart"><img src="data:image/png;base64,{c.get('06_hedge_backtest','')}" alt="Hedge backtest">
<div class="cap">Figure 7 — Backtest results. Top-left: cumulative P&L by strategy (Strategy B trends positive thanks to the conditional probability edge). Top-right: performance in known wet years. Bottom-left: Strategy A annual payouts vs average cost. Bottom-right: distribution of planting-window rain days.</div></div>

<h3>Strategy A: Buy "Rain YES" Every Day</h3>
<table>
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>Annual cost</td><td>$5,952</td></tr>
<tr><td>Annual payout (avg)</td><td>$5,952</td></tr>
<tr><td>Avg net P&L</td><td>$0 (break-even by design)</td></tr>
<tr><td>2019 net</td><td class="good">+$2,848</td></tr>
<tr><td>Concept</td><td>Pure insurance — pays more in wet years, costs more in dry years</td></tr>
</table>

<h3>Strategy B: Buy After 2+ Wet Days (Conditional)</h3>
<table>
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>Annual cost</td><td>$1,163</td></tr>
<tr><td>Annual payout (avg)</td><td>$1,436</td></tr>
<tr><td>Avg net P&L</td><td class="good">+$273/year</td></tr>
<tr><td>2019 net</td><td class="good">+$1,164</td></tr>
<tr><td>Edge</td><td>P(rain | 2+ wet days) = <strong>46.2%</strong> vs 39.2% unconditional fair price</td></tr>
<tr><td>Concept</td><td>Exploits persistence of wet spells — if it's been raining, it'll likely rain tomorrow</td></tr>
</table>

<h3>Strategy C: Monthly Rain Totals</h3>
<table>
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>Annual cost</td><td>$674</td></tr>
<tr><td>Annual payout (avg)</td><td>$689</td></tr>
<tr><td>Avg net P&L</td><td>+$15/year</td></tr>
<tr><td>2019 net</td><td class="good">+$1,326</td></tr>
<tr><td>Concept</td><td>Cheapest approach, targets months where total exceeds 4 inches</td></tr>
</table>

<h3>Worst Year Performance</h3>
<table>
<tr><th>Year</th><th>Strategy A</th><th>Strategy B</th><th>Strategy C</th><th>What Happened</th></tr>
<tr><td>2019</td><td class="good">+$2,848</td><td class="good">+$1,164</td><td class="good">+$1,326</td><td>Record wet spring, massive prevented planting</td></tr>
<tr><td>1993</td><td>+$248</td><td>+$25</td><td class="good">+$326</td><td>Great Flood year</td></tr>
<tr><td>2009</td><td>+$48</td><td>+$225</td><td class="good">+$826</td><td>Very wet fall harvest</td></tr>
<tr><td>2008</td><td>+$48</td><td class="good">+$425</td><td>-$174</td><td>Wet spring</td></tr>
</table>

<!-- ================================================================ -->
<h2 id="s10">10. Strategy Ranking</h2>

<table>
<tr><th>Rank</th><th>Strategy</th><th>Avg Net/Year</th><th>2019 Net</th><th>Annual Cost</th><th>Complexity</th><th>Verdict</th></tr>
<tr><td>1</td><td><strong>B: Conditional</strong></td><td class="good">+$273</td><td>+$1,164</td><td>$1,163</td><td>Medium</td><td class="good">Best edge — exploits wet-spell persistence</td></tr>
<tr><td>2</td><td><strong>C: Monthly</strong></td><td>+$15</td><td>+$1,326</td><td>$674</td><td>Low</td><td class="good">Cheapest, simplest, good 2019 payout</td></tr>
<tr><td>3</td><td><strong>A: Every day</strong></td><td>$0</td><td>+$2,848</td><td>$5,952</td><td>High</td><td class="fair">Largest payouts but highest cost, break-even on average</td></tr>
</table>

<div class="co ok"><strong>Strategy B has a genuine statistical edge.</strong> After 2+ consecutive wet days, the probability of rain on the next day jumps from 39% to 46% at Midway. If Kalshi prices daily rain contracts at the unconditional ~39% probability, buying selectively after wet spells produces a positive expected value. However, this edge may shrink if Kalshi's market makers start pricing persistence into their quotes.</div>

<!-- ================================================================ -->
<h2 id="s11">11. Key Findings</h2>

<div class="fb"><h4>Finding 1: Spring rain affects planting operations more than final yields</h4>
<p>Individual rain metrics explain less than 5% of corn yield variation — but this understates the real economic impact. Wet springs cause <strong>prevented planting, delayed planting, and replanting costs</strong> that don't show up in yield-per-acre data. The 2019 prevented planting disaster confirms the economic harm is real, even if per-acre yields don't fully capture it.</p></div>

<div class="fb"><h4>Finding 2: Rainfall basis risk is manageable over multi-week windows</h4>
<p>Station-to-county rainfall correlations average <strong>r = 0.85+</strong> over the 76-day planting window — dramatically better than the r = 0.46 we found for July monthly rain. Longer windows smooth out the daily storm randomness that plagues single-day or single-month comparisons. Springfield–Sangamon reaches an exceptional r = 0.97.</p></div>

<div class="fb"><h4>Finding 3: Consecutive wet days matter — and are predictable</h4>
<p>When it's been raining for 2+ days, the chance of rain continuing rises from 39% to <strong>46%</strong> at Midway. This persistence creates a small but real trading edge if Kalshi prices contracts at unconditional probabilities. Strategy B exploits this.</p></div>

<div class="fb"><h4>Finding 4: Monthly rain contracts are the most practical starting point</h4>
<p>Strategy C (monthly "above 4 inches" contracts for Apr/May/Sep/Oct) costs only ~$674/year and paid out $1,326 net in 2019. It requires no daily management, no conditional logic, and uses a contract type that Kalshi already offers for Chicago.</p></div>

<div class="fb"><h4>Finding 5: All three strategies produce modest, not transformative, payouts</h4>
<p>Even in the worst year (2019), the best strategy pays out under $3,000 on a $782,000 farm. That's real money but it's less than 0.5% of gross revenue. These hedges are <strong>supplemental layers</strong>, not substitutes for crop insurance or prevented-planting coverage.</p></div>

<!-- ================================================================ -->
<h2 id="s12">12. Limitations &amp; Next Steps</h2>

<h3>Limitations</h3>
<ul>
<li><strong>Yield data is estimated.</strong> NASS API was unavailable; county yields are derived from published state averages with county offsets. Real county data would sharpen the correlations.</li>
<li><strong>No real Crop Progress data.</strong> USDA's weekly "percent planted" and "days suitable for fieldwork" data would be the ideal outcome variable. This is the single biggest data gap.</li>
<li><strong>No prevented-planting acre data.</strong> FSA prevented-planting data by county would directly quantify the most important loss channel for wet springs.</li>
<li><strong>No real Kalshi price history.</strong> We used historical frequency as the fair price. Actual Kalshi bid/ask spreads and market prices may differ — daily rain contracts that list only 7 days out are priced with forecast information already baked in.</li>
<li><strong>Small sample sizes.</strong> Only ~45 years of data, with perhaps 5–8 truly "wet" years. Results should be treated as directional, not precise.</li>
<li><strong>No drying-cost proxy.</strong> Harvest-season losses through higher grain moisture and propane drying costs are real but we could not quantify them without propane price and harvest-moisture data.</li>
</ul>

<h3>Next Steps</h3>
<ol>
<li><strong>Get a free NASS API key</strong> (<a href="https://quickstats.nass.usda.gov/api/">quickstats.nass.usda.gov/api</a>) and re-run with real county yields and Crop Progress data.</li>
<li><strong>Obtain FSA prevented-planting data</strong> — this would let us directly measure the spring-rain &rarr; lost-acres pathway.</li>
<li><strong>Collect actual Kalshi rain contract prices</strong> for 2024–2026 to compare fair-value estimates vs. market prices.</li>
<li><strong>Test multi-station portfolio hedges</strong> — buying rain contracts in both Chicago AND Springfield/Peoria to cover north + central IL simultaneously.</li>
<li><strong>Monitor Kalshi for new products</strong> — seasonal accumulation contracts (e.g., "total April-May rain days above 30") would be far more useful than daily binaries for farm hedging.</li>
</ol>

<div class="foot">
<p><strong>Off-Season Rain Case Study</strong> — Generated November 2026</p>
<p>Farm counties: DeKalb, Kane, Kendall, Will, Grundy, LaSalle, Kankakee, Sangamon, McLean, Champaign (Illinois)<br>
Stations: Midway, O'Hare, Rockford, Peoria, Springfield<br>
Data: NOAA ACIS, USDA NASS<br>
Analysis code: Python (pandas, scipy, matplotlib) — see <code>06_offseason_rain_analysis.py</code></p>
</div>

</body></html>"""

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)

    size_mb = os.path.getsize(OUT) / 1024 / 1024
    print(f"Built: {OUT}")
    print(f"Size:  {size_mb:.1f} MB")


if __name__ == "__main__":
    build()
