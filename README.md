# FunnelIQ
### Marketing Attribution & Funnel ROI Dashboard

## 🚀 Live Dashboard

**[Open the FunnelIQ live Streamlit dashboard ↗](https://harsha-funneliq.streamlit.app)**

Try the interactive dashboard directly in your browser. The GitHub repository contains the complete source code, while the Streamlit deployment is the live, interactive version for portfolio reviewers and hiring managers.

> **How to use this document:** Paste this whole file into ChatGPT as your
> first message and ask it to build the project exactly as specified below,
> file by file, in the order given in Section 11.

## 1. Business Problem
Marketing budget gets split across paid social, search, email, and referral
with no reliable answer to "which channel actually drives revenue?"
Last-click reporting over-credits bottom-funnel channels and under-credits
the channels that started the journey. Growth/marketing teams need a
side-by-side attribution comparison and a concrete reallocation
recommendation.

**Business questions this project answers:**
- Where do users drop off in the funnel, and which channel brings people who
  convert vs. bounce?
- How does channel ROI change under last-touch vs. linear attribution?
- If we move $X from a low-ROI channel to a high-ROI one, what's the
  estimated revenue lift?

## 2. Business Impact
Reframes a marketing report as a budget-reallocation recommendation with an
estimated dollar outcome — the exact "so what" a BA is expected to add to a
dashboard.

## 3. Solution Overview
Synthetic multi-touch user journeys stored in SQLite; SQL funnel-stage
conversion views; a Python attribution engine computing both last-touch and
linear models; a Streamlit dashboard with a channel-reallocation
recommendation and a one-click Excel export.

## 4. Tech Stack
| Layer | Tool | Purpose |
|---|---|---|
| Language | Python 3.11+ | Core logic |
| Database | SQLite | Local relational store |
| Query layer | SQL | Funnel-stage conversion views |
| Data handling | pandas, numpy | Transformation, attribution math |
| App/dashboard | Streamlit | Interactive UI |
| Charts | Plotly | Funnel chart, ROI bar chart |
| Export | openpyxl (via pandas `.to_excel`) | 1-page exec summary export |
| Testing | pytest | Unit tests |
| Version control | Git + GitHub | Source control |

## 5. Architecture / Pipeline
```
[generate_synthetic_data.py] --> [SQLite: funneliq.db]
        v
[queries/funnel_conversion.sql] --> stage-by-stage conversion rates
        v
[attribution.py] -- last-touch + linear models --> revenue-per-channel
        v
[metrics.py] --> ROI, CAC per channel; reallocation suggestion
        v
[app.py: Streamlit] --> funnel viz, ROI chart, reallocation panel, Excel export
```
**Ingest (synthetic generator) → Store (SQLite) → Transform (SQL funnel
views) → Model (attribution engine) → Visualize (Streamlit) → Recommend
(reallocation panel + export)**

## 6. Data Model
**`touchpoints`**
| Column | Type |
|---|---|
| user_id | INTEGER |
| timestamp | DATETIME |
| channel | TEXT (paid_social/search/email/referral/organic) |
| campaign_id | TEXT |
| cost_attributed | REAL |

**`funnel_events`**
| Column | Type |
|---|---|
| user_id | INTEGER |
| timestamp | DATETIME |
| stage | TEXT (visit/signup/trial/purchase) |

**`purchases`**
| Column | Type |
|---|---|
| user_id | INTEGER |
| purchase_date | DATE |
| revenue | REAL |

## 7. Synthetic Data Generation Rules
- ~5,000 users over a 90-day window
- 1–5 touchpoints per user, channel mix weighted so each channel has a
  distinct, realistic cost and conversion-rate profile (e.g., paid_social =
  high volume/low conversion, email = low volume/high conversion)
- Funnel progression is monotonic (visit → signup → trial → purchase) with a
  drop-off probability at each stage that differs by entry channel
- Purchases only exist for users who reach the `purchase` stage; revenue
  drawn from a realistic distribution per plan/segment

## 8. Modeling Details (Attribution Engine)
- **Last-touch:** 100% of a purchase's revenue credited to the final
  touchpoint's channel before purchase
- **Linear:** revenue split evenly across every touchpoint's channel in that
  user's journey
- For each channel under each model, compute `revenue_attributed`,
  `cost_attributed` (from touchpoints), `ROI = revenue_attributed /
  cost_attributed`, `CAC = cost_attributed / conversions`
- **Reallocation logic:** identify the lowest-ROI and highest-ROI channel;
  simulate moving a configurable % of the low-ROI channel's spend to the
  high-ROI channel at that channel's current ROI, and report the estimated
  incremental revenue at the same total spend

## 9. Dashboard Specification
- **Sidebar:** attribution-model toggle (last-touch / linear),
  reallocation-% slider
- **KPI row:** total spend, total revenue, blended ROI, total conversions
- **Chart 1:** funnel chart — user counts at each stage with drop-off %
  annotated
- **Chart 2:** bar chart — ROI per channel (updates on model toggle)
- **Panel:** plain-language reallocation recommendation with the estimated
  revenue lift
- **Button:** "Export 1-page summary to Excel" (creates the `exports/`
  folder if missing)

## 10. File & Folder Structure
```
funneliq/
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── data/
│   └── generate_synthetic_data.py
├── tests/
│   ├── test_attribution.py
│   └── test_metrics.py
├── queries/
│   └── funnel_conversion.sql
├── exports/            (generated at runtime, not committed)
└── src/
    ├── __init__.py
    ├── db.py
    ├── attribution.py
    └── metrics.py
```

## 11. Step-by-Step Build Order
1. Scaffold folders; `.gitignore` (include `exports/`), `LICENSE`.
2. Write `data/generate_synthetic_data.py` per Section 7; populates
   `funneliq.db`.
3. Write `src/db.py`: connection + query helpers.
4. Write `queries/funnel_conversion.sql`: stage counts and stage-to-stage
   conversion %.
5. Write `src/attribution.py`: `last_touch(df) -> DataFrame`, `linear(df) ->
   DataFrame`, and `recommend_reallocation(roi_df, pct) -> dict`.
6. Write `src/metrics.py`: ROI/CAC roll-ups and KPI dict.
7. Write `tests/`: assert last-touch and linear attribution both sum to
   total revenue exactly (no revenue created or lost), and that reallocation
   only ever suggests moving from a lower-ROI to a higher-ROI channel.
8. Write `app.py` wiring it all together per Section 9, including the Excel
   export button.
9. Run locally, fix all exceptions in both attribution modes.
10. Write final `README.md` per Section 14.
11. `git init`, commit, push.

## 12. Production-Quality Bar
- [ ] Type hints + docstrings
- [ ] No bare `except:`
- [ ] Attribution functions are pure (no side effects) and unit-tested for
  the revenue-conservation property above
- [ ] `logging` on data generation and export steps
- [ ] `pytest` passes
- [ ] `requirements.txt` pinned
- [ ] Export button creates its target folder if missing, and shows a
  success/failure message in the UI

## 13. Roadmap / Future Enhancements
- Add a third attribution model (time-decay) for a 3-way comparison
- Connect to a real ad-platform export (Google Ads/Meta CSV) instead of
  synthetic touchpoints
- Recreate the ROI chart in Power BI/Tableau connected to the same SQLite
  file
- Add confidence intervals on the reallocation estimate via bootstrap
  resampling

## 14. Required Contents of Final `README.md`
Business problem → what attribution models are compared and why it matters →
tech stack → setup steps → schema summary → how to read the reallocation
recommendation → limitations (synthetic data, attribution is illustrative
not causal).

## 15. Definition of Done
- [ ] Both attribution models run and sum to the same total revenue
- [ ] Funnel chart, ROI chart, and reallocation panel all update together on
  toggle
- [ ] Excel export produces a valid, openable file
- [ ] Tests pass
- [ ] README complete

## 16. Resume Bullet Template
"Built a marketing attribution dashboard (SQL, Python, Streamlit) comparing
last-touch vs. linear models across 5 channels, identifying a [X]%
budget-reallocation opportunity with an exec-ready Excel export."