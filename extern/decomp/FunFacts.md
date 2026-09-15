# Next Level Games & *Super Mario Strikers* — Deep Dive & Developer Insights

##  Next Level Games — Snapshot

- **Founded:** August 22, 2002 in Vancouver by alumni of EA Black Box, known for arcade-style sports work.[^1]  
- **Exclusive Partner:** Since January 2014, the studio has worked exclusively with their main publishing partner.[^1]  
- **Acquisition:** Became a wholly owned subsidiary in March 2021 after internal stakeholders decided it was the right moment for a transition.[^1]  
- **Team Size:** As of 2025, around 175 employees.[^1]  
- **Culture & Recognition:** Known for being among Canada’s and BC’s top employers in previous years and featured in outlets like *Maclean’s*.[^1]

##  *Super Mario Strikers* — Developer Highlights

- **Arcade Roots:** Drawing from their sports development pedigree, they embraced over-the-top, hard-hitting gameplay inspired by titles like *NHL Hitz Pro*.[^2]  
- **Fast Turnaround:** Developed in just **13 months** and revealed at E3 2005.[^2]  
- **No Rules Attached:** Matches featured no referees, power-ups, and electrified fences—emphasizing chaotic fun over simulation.[^2]  
- **GameCube Farewell:** It was the last game in the franchise released on the platform.[^2]  
- **Re-release:** In 2025, it received a re-release on a modern platform's “classics” service.[^2]

##  Decompilation Insights & the Physics Engine

- **Open-Source Physics:** A noteworthy gem uncovered via the decompilation project is the use of the **Open Dynamics Engine (ODE)**—an early, open-source physics engine written in C/C++ (BSD-licensed)—to power the game's physics simulation.[^3]  

## Decompilation Project — KPI Snapshot

Measured from the configured `G4QE01` linked build on August 20, 2026.

| Metric | Value |
|---|---:|
| C/C++ translation units | **730** |
| Unique headers compiled | **788** |
| Total source files | **1,518** |
| Code-only lines | **338,505** |
| Total physical lines | **409,658** |
| Linked functions/methods | **8,605** |
| Code/function match | **100%** |
| `main.elf` size | **5.68 MB** |
| Hash verification | **SHA-1 — passes** |

### Source Breakdown

| Type | Files | Code lines | Physical lines |
|---|---:|---:|---:|
| Headers | 788 | 51,443 | 64,339 |
| C | 206 | 66,441 | 79,569 |
| C++ | 524 | 220,621 | 265,750 |
| **Total** | **1,518** | **338,505** | **409,658** |

The configured assembly translation unit is excluded from these source-file
figures. The functions/methods total includes linked C functions, free C++
functions, and class methods. Generated build headers are excluded.

##  Voice Actor Fun Fact

- **Bowser's Voice:** The game features the debut performance of **Kenny James** as Bowser (and as part of the Super Team). He has since become the series' regular English voice for Bowser across multiple variants and titles.[^4]

---

## Sources

[^1]: [Next Level Games — Wikipedia](https://en.wikipedia.org/wiki/Next_Level_Games)  
[^2]: [Super Mario Strikers — Wikipedia](https://en.wikipedia.org/wiki/Super_Mario_Strikers)  
[^3]: [Open Dynamics Engine — Wikipedia](https://en.wikipedia.org/wiki/Open_Dynamics_Engine)  
[^4]: [Kenny James — Mario Wiki](https://www.mariowiki.com/Kenny_James)  
