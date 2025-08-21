Here is a sceleton for the three-screens frontend for this app to implement, with reasonable edit and re-work.

Screen 1 — Scenario Builder (“enter then calculate”)

┌──────────────────────────────────────────────────────────────────────────────┐
│ Clinical Service Planning – Scenario Builder                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│ [Scenario Name]: ______________________     [Preset]: (• Baseline ○ Target   │
│                                             ○ Stress ○ Best)                 │
│ [Baseline Year]: (2022/23 ▼)  [Horizon]: (3 yrs ▼)   [Compute Mode]: On-demand│
├──────────────────────────────────────────────────────────────────────────────┤
│ LEFT FILTERS                                                                  │
│ ┌────────────────────────────┐   PARAMETERS                                   │
│ │ Sites (multi-select)       │   ┌──────────────────────────────────────────┐ │
│ │ [ ] Snowberry General      │   │ Occupancy target:  [ 0.90 ▼ ]            │
│ │ [ ] Blue Heron Medical     │   │ LOS delta (%):    [  -3  ▼ ]             │
│ │ [ ] Salmon Run Hospital    │   │ ALC target (%):   [  12  ▼ ]             │
│ │ [ ] Mossy Cedar Community  │   │ Demand growth %:  [   2  ▼ ] (global)    │
│ │ [ ] Otter Bay Medical Ctr  │   │ Transfer policy:  [ ON  ▼ ]              │
│ │ [ ] Bear Creek Hospital    │   │ Capacity schedule: [ Sched-A ▼ ]          │
│ │ [ ] Driftwood Regional     │   │ Seasonality:      [ OFF ▼ ]               │
│ │ [ ] Stargazer Hlth Ctr     │   │ ED boarding model:[ Lookup ▼ ]            │
│ │ [ ] Sunrise Coast Hosp     │   └──────────────────────────────────────────┘ │
│ │ [ ] Grouse Ridge Medical   │   OVERRIDES (optional)                         │
│ │ [ ] Foggy Harbor Hosp      │   ┌──────────────────────────────────────────┐ │
│ │ [ ] Granite Peak Medical   │   │ Program: (Medicine ▼) Sub: (ACE ▼)       │
│ └────────────────────────────┘   │ Demand growth % override: [  4  ]        │
│                                  │ LOS delta % override:     [  -5 ]        │
│ PROGRAMS (pick 1–3)               │ ALC target % override:    [  10 ]        │
│ ┌────────────────────────────┐   └──────────────────────────────────────────┘ │
│ │ ( ) Medicine               │                                                │
│ │ ( ) Inpatient MHSU         │   VALIDATION                                   │
│ │ ( ) MICY                   │   ┌──────────────────────────────────────────┐ │
│ │ ( ) Critical Care          │   │ ✓ Parameters consistent                   │
│ │ ( ) Surgery / Periop       │   │ ✓ Coverage matrix valid at selected sites │
│ │ ( ) Emergency              │   │ ✓ Bounds: occ ≥ 0.80; Eff LOS ≥ 0.25 d    │
│ │ ( ) …                      │   └──────────────────────────────────────────┘ │
│ └────────────────────────────┘                                                │
├──────────────────────────────────────────────────────────────────────────────┤
│ [ C ] Calculate     [ S ] Save Scenario     [ R ] Reset      [ → ] Go to Results │
└──────────────────────────────────────────────────────────────────────────────┘


Screen 2 — Results Dashboard (for a single scenario)

┌──────────────────────────────────────────────────────────────────────────────┐
│ Results — Scenario: “Med-ACE FY22/23 Target-0.90”   (Baseline: 2022/23)      │
├──────────────────────────────────────────────────────────────────────────────┤
│ KPI CARDS (aggregate of current filters)                                     │
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐      │
│ │ RequiredBeds  │ │ StaffedBeds   │ │ CapacityGap   │ │ Nursing FTE   │      │
│ │      842      │ │      790      │ │     +52       │ │     126.4     │      │
│ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘      │
│ Filters: Sites[All 12]  Program[Medicine]  Subprogram[ACE]                    │
├──────────────────────────────────────────────────────────────────────────────┤
│ BY-SITE TABLE (sorted by gap)                                                 │
│ ┌────┬──────────────────────┬──────────┬──────────┬──────────┬──────────────┐ │
│ │ #  │ Site                 │ ReqBeds  │ Staffed  │ Gap      │ Gap Bar      │ │
│ ├────┼──────────────────────┼──────────┼──────────┼──────────┼──────────────┤ │
│ │ 1  │ Sunrise Coast Hosp   │    98    │   80     │  +18     │ ████████▌    │ │
│ │ 2  │ Grouse Ridge Medical │    82    │   70     │  +12     │ █████▌       │ │
│ │ 3  │ Driftwood Regional   │    66    │   62     │  +4      │ ██▌          │ │
│ │ …  │ …                    │   …      │  …       │  …       │ …            │ │
│ └────┴──────────────────────┴──────────┴──────────┴──────────┴──────────────┘ │
│                                                                             │
│ ED METRICS (informing inpatient flow)                                        │
│ ┌──────────────────────────────────────────────────────────────────────────┐ │
│ │ Adult ED arrivals:  +3.1%   Pediatric: +0.8%   UCC: +1.2%                 │
│ │ Estimated boarding hours (95th):  ↑ 6% (occ @ 0.90; LOSΔ −3%; ALC 12%)    │
│ └──────────────────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────────────────┤
│ [ A ] Adjust Parameters    [ S ] Save Scenario    [ E ] Export to Power BI    │
└──────────────────────────────────────────────────────────────────────────────┘

Screen 3 — Scenario Compare (A vs B side-by-side + delta)

┌──────────────────────────────────────────────────────────────────────────────┐
│ Compare Scenarios                                                             │
├──────────────────────────────────────────────────────────────────────────────┤
│ A: “Target-0.90 / LOS −3% / ALC 12% / Growth 2%”    vs                        │
│ B: “Baseline-0.85 / LOS 0%  / ALC 14% / Growth 0%”                             │
├──────────────────────────────────────────────────────────────────────────────┤
│ GLOBAL KPIs                                                                   │
│ ┌───────────────────────────────┬───────────────────────────────┬───────────┐ │
│ │           Metric              │       Scenario A              │    Δ(A-B) │ │
│ ├───────────────────────────────┼───────────────────────────────┼───────────┤ │
│ │ Required Beds (all sites)     │ 842                           │  +36      │ │
│ │ Staffed Beds (sched-A)        │ 790                           │   0       │ │
│ │ Capacity Gap                  │ +52                           │ +36       │ │
│ │ Nursing FTE                   │ 126.4                         │  +5.7     │ │
│ │ ED Boarding (95th, hours)     │  +6%                          │  +9 pp    │ │
│ └───────────────────────────────┴───────────────────────────────┴───────────┘ │
│ BY-SITE SNAPSHOT (top 5 by absolute gap delta)                                │
│ ┌────┬──────────────────────┬─────────┬─────────┬──────────┬───────────────┐ │
│ │ #  │ Site                 │ Gap A   │ Gap B   │ Δ(A-B)   │ ASCII Bars    │ │
│ ├────┼──────────────────────┼─────────┼─────────┼──────────┼───────────────┤ │
│ │ 1  │ Sunrise Coast Hosp   │  +18    │   +9    │   +9     │ A: ████████   │ │
│ │    │                      │         │         │          │ B: ████▌      │ │
│ │ 2  │ Grouse Ridge Medical │  +12    │   +6    │   +6     │ A: █████▌     │ │
│ │ 3  │ Driftwood Regional   │   +4    │   +1    │   +3     │ A: ██▌        │ │
│ │ 4  │ Blue Heron Medical   │   +3    │   +2    │   +1     │ A: ██         │ │
│ │ 5  │ Snowberry General    │   +1    │   +0    │   +1     │ A: ▌          │ │
│ └────┴──────────────────────┴─────────┴─────────┴──────────┴───────────────┘ │
├──────────────────────────────────────────────────────────────────────────────┤
│ [ ← ] Back to Results   [ D ] Duplicate A→New    [ X ] Export Comparison CSV │
└──────────────────────────────────────────────────────────────────────────────┘
