"""
src/app.py
----------
Streamlit storyboard: "Are We Going to Reach Our Goals?"
Run: streamlit run src/app.py
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os

# ── Path setup ────────────────────────────────────────────────────────────────
_SRC     = os.path.dirname(os.path.abspath(__file__))
_ARCHIVE = os.path.abspath(os.path.join(_SRC, '..'))
for _p in [_ARCHIVE, os.path.join(_ARCHIVE, 'target')]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Are We Going to Reach Our Goals?",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Load data (heavy chain — cached once) ─────────────────────────────────────
@st.cache_resource(show_spinner="Loading forecast chain 2014→2017 ...")
def load():
    from suggestTarget import (
        BASELINES, ACTUALS, SUGGESTED_RANGES, TIERS,
        Q1_ACTUALS, Q1_WEIGHTS,
    )
    from monthlyForecast2014 import FORECAST_2014
    from monthlyForecast2015 import FORECAST_2015
    from monthlyForecast2016 import FORECAST_2016
    from monthlyForecast2017 import FORECAST_2017
    from target import (
        SALES_TARGET, PROFIT_TARGET,
        CUSTOMER_TARGET, ORDER_TARGET, TIER_BY_YEAR,
    )
    HUMAN_KPI = {
        yr: {
            'Sales'    : SALES_TARGET[yr],
            'Profit'   : PROFIT_TARGET[yr],
            'Customers': CUSTOMER_TARGET[yr],
            'Orders'   : ORDER_TARGET[yr],
        }
        for yr in [2014, 2015, 2016, 2017]
    }
    return dict(
        B  = BASELINES,
        A  = ACTUALS,
        SR = SUGGESTED_RANGES,
        T  = TIERS,
        KPI= HUMAN_KPI,
        TY = TIER_BY_YEAR,
        F  = {2014: FORECAST_2014, 2015: FORECAST_2015,
              2016: FORECAST_2016, 2017: FORECAST_2017},
        Q1A= Q1_ACTUALS,
        Q1W= Q1_WEIGHTS,
    )

d = load()

# ── Constants ─────────────────────────────────────────────────────────────────
METRICS  = ['Sales', 'Profit', 'Customers', 'Orders']
UNIT     = {'Sales': '$', 'Profit': '$', 'Customers': '', 'Orders': ''}
YEARS    = [2014, 2015, 2016, 2017]
MONTHS   = ['Jan','Feb','Mar','Apr','May','Jun',
            'Jul','Aug','Sep','Oct','Nov','Dec']

TIER_COLOR = {
    'Below baseline': '#e74c3c',
    'Baseline'      : '#95a5a6',
    'Achievable'    : '#3498db',
    'Challenging'   : '#27ae60',
    'Stretch'       : '#f39c12',
    'Moonshot'      : '#9b59b6',
}
BAND_COLOR = {          # tier band fills
    'Achievable' : 'rgba(52,152,219,0.15)',
    'Challenging': 'rgba(39,174,96,0.15)',
    'Stretch'    : 'rgba(243,156,18,0.15)',
    'Moonshot'   : 'rgba(155,89,182,0.15)',
}

def classify(actual, baseline):
    if not baseline: return 'Baseline'
    r = actual / baseline
    if r < 0.95:  return 'Below baseline'
    if r < 1.05:  return 'Baseline'
    if r < 1.15:  return 'Achievable'
    if r < 1.275: return 'Challenging'
    if r < 1.425: return 'Stretch'
    return 'Moonshot'

def vfmt(v, metric, short=False):
    u = UNIT[metric]
    if short:
        if u == '$': return f'${v/1000:.0f}K'
        return f'{v:,.0f}'
    if u == '$': return f'${v:,.0f}'
    return f'{v:,.0f}'

def achieve_pct(actual, target):
    if not target: return 0
    return round(actual / target * 100, 1)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🎯 Are We Going to Reach Our Goals?")
st.caption("4-Year KPI Storyboard  |  2014–2017 Actuals  +  2018 Projection  |  Powered by XGBoost Rolling Forecast")
st.divider()

# ── Top summary cards (all metrics, all years) ────────────────────────────────
cols = st.columns(4)
for col, metric in zip(cols, METRICS):
    total_actual = sum(d['A'][yr][metric] for yr in YEARS)
    total_kpi    = sum(d['KPI'][yr][metric] for yr in YEARS)
    pct          = achieve_pct(total_actual, total_kpi)
    delta_val    = total_actual - total_kpi
    delta_str    = f"{'+' if delta_val>=0 else ''}{vfmt(delta_val, metric, short=True)} vs KPI"
    col.metric(
        label  = metric,
        value  = vfmt(total_actual, metric, short=True),
        delta  = delta_str,
        delta_color = "normal" if delta_val >= 0 else "inverse",
    )

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 4-Year Overview",
    "🎯 KPI Tier Ranges",
    "📅 Monthly Tracking",
    "🔭 2018 Projection",
])

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1 — 4-Year Overview
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    metric1 = st.selectbox("Metric", METRICS, key="t1_metric")
    u       = UNIT[metric1]

    baselines = [d['B'][yr][metric1] for yr in YEARS]
    actuals   = [d['A'][yr][metric1] for yr in YEARS]
    kpis      = [d['KPI'][yr][metric1] for yr in YEARS]
    tiers     = [classify(a, b) for a, b in zip(actuals, baselines)]
    bar_colors= [TIER_COLOR.get(t, '#888') for t in tiers]

    fig = go.Figure()

    # Baseline bars (ghost)
    fig.add_trace(go.Bar(
        name='Baseline (model predict)', x=YEARS, y=baselines,
        marker_color='rgba(149,165,166,0.35)',
        marker_line_color='#95a5a6', marker_line_width=1,
        text=[vfmt(v, metric1, short=True) for v in baselines],
        textposition='outside', textfont_size=11,
    ))

    # KPI target bars
    fig.add_trace(go.Bar(
        name='KPI Target (human-set)', x=YEARS, y=kpis,
        marker_color='rgba(52,73,94,0.5)',
        marker_line_color='#2c3e50', marker_line_width=1.5,
        text=[vfmt(v, metric1, short=True) for v in kpis],
        textposition='outside', textfont_size=11,
    ))

    # Actual bars (colored by tier)
    fig.add_trace(go.Bar(
        name='Actual', x=YEARS, y=actuals,
        marker_color=bar_colors,
        text=[vfmt(v, metric1, short=True) for v in actuals],
        textposition='outside', textfont_size=11, textfont_color='white',
    ))

    fig.update_layout(
        barmode='group', height=450,
        title=f'{metric1} — Baseline vs KPI Target vs Actual (2014–2017)',
        xaxis=dict(tickvals=YEARS, ticktext=[str(y) for y in YEARS]),
        yaxis=dict(title=f'{metric1} ({u if u else "count"})'),
        legend=dict(orientation='h', y=-0.15),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    if u == '$':
        fig.update_yaxes(tickprefix='$', tickformat=',.0f')

    st.plotly_chart(fig, use_container_width=True)

    # Tier achievement table
    st.subheader("Tier Achievement by Year")
    rows = []
    for yr in YEARS:
        base = d['B'][yr][metric1]
        act  = d['A'][yr][metric1]
        kpi  = d['KPI'][yr][metric1]
        tier = classify(act, base)
        rows.append({
            'Year'        : yr,
            'KPI Target'  : vfmt(kpi, metric1),
            'Baseline'    : vfmt(base, metric1),
            'Actual'      : vfmt(act, metric1),
            'vs KPI'      : f"{achieve_pct(act,kpi):+.1f}%",
            'vs Baseline' : f"{achieve_pct(act,base)-100:+.1f}%",
            'Tier'        : tier,
            'KPI Tier Set': d['TY'].get(yr, '—'),
        })
    df_table = pd.DataFrame(rows).set_index('Year')

    def color_tier(val):
        c = TIER_COLOR.get(val, '#ffffff')
        return f'background-color: {c}22; color: {c}; font-weight: bold'

    st.dataframe(
        df_table.style.map(color_tier, subset=['Tier', 'KPI Tier Set']),
        use_container_width=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2 — KPI Tier Ranges
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    metric2 = st.selectbox("Metric", METRICS, key="t2_metric")
    u2      = UNIT[metric2]

    YEARS_ALL = [2014, 2015, 2016, 2017, 2018]
    x_labels  = ['2014\n(Q1 proj)', '2015', '2016', '2017', '2018\n(proj)']
    tiers_order = ['Achievable', 'Challenging', 'Stretch', 'Moonshot']

    fig2 = go.Figure()

    # Tier bands (stacked area)
    prev = [d['B'][yr][metric2] for yr in YEARS_ALL]
    for tier in tiers_order:
        mult = {'Achievable':1.10,'Challenging':1.20,'Stretch':1.35,'Moonshot':1.50}[tier]
        curr = [d['B'][yr][metric2] * mult for yr in YEARS_ALL]
        fig2.add_trace(go.Scatter(
            x=x_labels, y=curr,
            fill='tonexty', fillcolor=BAND_COLOR[tier],
            line=dict(color=BAND_COLOR[tier].replace('0.15','0.5'), width=1),
            name=tier, mode='lines',
            hovertemplate=f'{tier}: %{{y:,.0f}}<extra></extra>',
        ))
        # First iteration needs a base trace
        if tier == 'Achievable':
            fig2.add_trace(go.Scatter(
                x=x_labels, y=prev,
                fill=None, line=dict(color='rgba(149,165,166,0.5)', width=1.5, dash='dash'),
                name='Baseline', mode='lines',
                hovertemplate='Baseline: %{y:,.0f}<extra></extra>',
            ))
        prev = curr

    # Actual bars (2014-2017)
    act_vals   = [d['A'][yr][metric2] for yr in YEARS]
    act_colors = [TIER_COLOR.get(classify(a, d['B'][yr][metric2]), '#888')
                  for a, yr in zip(act_vals, YEARS)]
    fig2.add_trace(go.Bar(
        x=x_labels[:4], y=act_vals,
        marker_color=act_colors, opacity=0.85,
        name='Actual', width=0.4,
        text=[vfmt(v, metric2, short=True) for v in act_vals],
        textposition='outside', textfont_size=11,
    ))

    # 2018 recommendation diamonds
    r18 = d['SR'][2018][metric2]
    for tier, sym, color in [('Achievable','diamond','#3498db'),
                              ('Challenging','diamond','#27ae60')]:
        fig2.add_trace(go.Scatter(
            x=['2018\n(proj)'], y=[r18[tier]],
            mode='markers+text',
            marker=dict(symbol=sym, size=14, color=color,
                        line=dict(color='white', width=1.5)),
            text=[f"{tier}<br>{vfmt(r18[tier], metric2, short=True)}"],
            textposition='top center', textfont_size=9,
            name=f'2018 {tier}',
        ))

    fig2.update_layout(
        height=480,
        title=f'{metric2} — KPI Tier Ranges 2014–2018  (Prospective)',
        yaxis=dict(title=metric2),
        legend=dict(orientation='h', y=-0.18),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        barmode='overlay',
    )
    if u2 == '$':
        fig2.update_yaxes(tickprefix='$', tickformat=',.0f')

    st.plotly_chart(fig2, use_container_width=True)

    # Range table
    st.subheader("Suggested KPI Ranges")
    rows2 = []
    for yr in YEARS_ALL:
        base = d['B'][yr][metric2]
        r    = d['SR'][yr][metric2]
        act  = d['A'].get(yr, {}).get(metric2)
        rows2.append({
            'Year'       : str(yr) + (' *' if yr in [2014,2018] else ''),
            'Baseline'   : vfmt(base, metric2),
            'Achievable' : vfmt(r['Achievable'], metric2),
            'Challenging': vfmt(r['Challenging'], metric2),
            'Stretch'    : vfmt(r['Stretch'], metric2),
            'Actual'     : vfmt(act, metric2) if act else '—',
        })
    st.dataframe(pd.DataFrame(rows2).set_index('Year'), use_container_width=True)
    st.caption("* 2014 baseline = Q1 projection  |  2018 baseline = 2017 momentum forecast")

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3 — Monthly Tracking
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    c1, c2 = st.columns(2)
    year3   = c1.selectbox("Year", YEARS, key="t3_year")
    metric3 = c2.selectbox("Metric", METRICS, key="t3_metric")
    u3      = UNIT[metric3]

    forecast = d['F'][year3]
    months_x = MONTHS
    targets  = [forecast[metric3][m]['target'] for m in range(1, 13)]
    actuals3 = [forecast[metric3][m]['actual'] for m in range(1, 13)]
    errors   = [forecast[metric3][m]['error_pct'] for m in range(1, 13)]
    ann_ests = [forecast[metric3][m]['annual_est'] for m in range(1, 13)]
    bar_cols = ['#27ae60' if a >= t else '#e74c3c'
                for a, t in zip(actuals3, targets)]

    fig3 = go.Figure()

    # Target line
    fig3.add_trace(go.Scatter(
        x=months_x, y=targets,
        mode='lines+markers',
        line=dict(color='#2c3e50', width=2, dash='dash'),
        marker=dict(size=6, color='#2c3e50'),
        name='Target', yaxis='y1',
        hovertemplate='Target: %{y:,.0f}<extra></extra>',
    ))

    # Actual bars
    fig3.add_trace(go.Bar(
        x=months_x, y=actuals3,
        marker_color=bar_cols, opacity=0.8,
        name='Actual', yaxis='y1',
        text=[f"{e:+.0f}%" for e in errors],
        textposition='outside', textfont_size=9,
        hovertemplate='Actual: %{y:,.0f}<extra></extra>',
    ))

    # Annual estimate line (secondary axis)
    fig3.add_trace(go.Scatter(
        x=months_x, y=ann_ests,
        mode='lines', line=dict(color='#f39c12', width=1.5, dash='dot'),
        name='Annual Est. (rolling)', yaxis='y2',
        hovertemplate='Annual Est: %{y:,.0f}<extra></extra>',
    ))

    fig3.update_layout(
        height=450,
        title=f'{metric3} {year3} — Monthly Target vs Actual (green=beat, red=missed)',
        yaxis =dict(title=f'{metric3}', side='left'),
        yaxis2=dict(title='Annual Estimate', side='right', overlaying='y',
                    showgrid=False, tickformat=',.0f'),
        legend=dict(orientation='h', y=-0.18),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        barmode='overlay',
    )
    if u3 == '$':
        fig3.update_yaxes(tickprefix='$', tickformat=',.0f')

    st.plotly_chart(fig3, use_container_width=True)

    # Monthly table
    rows3 = [{
        'Month' : MONTHS[m-1],
        'Target': vfmt(forecast[metric3][m]['target'], metric3),
        'Actual': vfmt(forecast[metric3][m]['actual'], metric3),
        'Error%': f"{forecast[metric3][m]['error_pct']:+.1f}%",
        'Ann.Est.': vfmt(forecast[metric3][m]['annual_est'], metric3),
    } for m in range(1, 13)]
    st.dataframe(pd.DataFrame(rows3).set_index('Month'), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 4 — 2018 Projection
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("2018 KPI Recommendation")
    st.caption("Baseline = model prediction from 2017 H2/H1 momentum × 10% base growth")

    cols4 = st.columns(4)
    for col, metric in zip(cols4, METRICS):
        u4  = UNIT[metric]
        r18 = d['SR'][2018][metric]
        base= d['B'][2018][metric]
        col.markdown(f"**{metric}**")
        col.metric("Baseline",    vfmt(base,           metric))
        col.metric("✅ Achievable", vfmt(r18['Achievable'], metric),
                   delta="+10% vs baseline")
        col.metric("🎯 Challenging", vfmt(r18['Challenging'], metric),
                   delta="+20% vs baseline")
        col.metric("💪 Stretch",    vfmt(r18['Stretch'],    metric),
                   delta="+35% vs baseline")

    st.divider()

    # Progression chart: 2014-2017 actual + 2018 range
    metric4 = st.selectbox("Metric", METRICS, key="t4_metric")
    u4 = UNIT[metric4]

    fig4 = go.Figure()

    # Historical actuals
    fig4.add_trace(go.Scatter(
        x=[str(y) for y in YEARS],
        y=[d['A'][yr][metric4] for yr in YEARS],
        mode='lines+markers+text',
        line=dict(color='#3498db', width=3),
        marker=dict(size=10, color=[TIER_COLOR.get(
            classify(d['A'][yr][metric4], d['B'][yr][metric4]),'#888')
            for yr in YEARS], line=dict(color='white',width=2)),
        text=[vfmt(d['A'][yr][metric4], metric4, short=True) for yr in YEARS],
        textposition='top center', textfont_size=10,
        name='Actual',
    ))

    # 2018 range bar
    r18     = d['SR'][2018][metric4]
    base18  = d['B'][2018][metric4]
    tiers18 = ['Achievable', 'Challenging', 'Stretch']
    for i, (lo, hi, color, label) in enumerate([
        (base18,           r18['Achievable'],  '#3498db', 'Baseline→Achievable'),
        (r18['Achievable'],r18['Challenging'], '#27ae60', 'Achievable→Challenging'),
        (r18['Challenging'],r18['Stretch'],    '#f39c12', 'Challenging→Stretch'),
    ]):
        fig4.add_trace(go.Bar(
            x=['2018'],
            y=[hi - lo], base=[lo],
            marker_color=color, opacity=0.6,
            name=label, width=0.4,
        ))

    # 2018 baseline dot
    fig4.add_trace(go.Scatter(
        x=['2018'], y=[base18],
        mode='markers+text',
        marker=dict(size=10, color='#95a5a6', symbol='circle'),
        text=[f"Base<br>{vfmt(base18, metric4, short=True)}"],
        textposition='bottom center', textfont_size=9,
        name='2018 Baseline',
    ))

    fig4.update_layout(
        height=450,
        title=f'{metric4} — 4-Year Actuals + 2018 Target Range',
        barmode='stack',
        yaxis=dict(title=metric4),
        legend=dict(orientation='h', y=-0.2),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    if u4 == '$':
        fig4.update_yaxes(tickprefix='$', tickformat=',.0f')

    st.plotly_chart(fig4, use_container_width=True)

    # 2014 Q1 projection note
    with st.expander("ℹ️  How was the 2014 baseline derived?"):
        st.markdown("""
**2014** là năm đầu tiên — không có prior year data để dự báo.
Sau Q1 (3 tháng thử nghiệm), model dùng actual Jan–Mar + XGBoost seasonal weights để project cả năm:

> `baseline_2014 = sum(actual[Jan-Mar]) / sum(w_xgb[Jan-Mar])`
        """)
        q1_rows = []
        for metric in METRICS:
            q1a = d['Q1A'][metric]
            q1w = d['Q1W'][metric]
            tot = sum(q1a.values())
            wtot= sum(q1w.values())
            proj= d['B'][2014][metric]
            q1_rows.append({
                'Metric': metric,
                'Jan': vfmt(q1a[1], metric),
                'Feb': vfmt(q1a[2], metric),
                'Mar': vfmt(q1a[3], metric),
                'Q1 Total': vfmt(tot, metric),
                'Q1 Weight': f'{wtot:.2%}',
                'Projected Annual': vfmt(proj, metric),
            })
        st.dataframe(pd.DataFrame(q1_rows).set_index('Metric'), use_container_width=True)
