# Version differences

This repository supports all three Rev 0 releases. They shipped in this order:

| Release | Version | Region and title | Date |
| ---: | --- | --- | --- |
| 1 | `G4QP01` | Europe — *Mario Smash Football* | November 18, 2005 |
| 2 | `G4QE01` | North America — *Super Mario Strikers* | December 5, 2005 |
| 3 | `G4QJ01` | Japan — *Super Mario Strikers* | January 19, 2006 |

> [!NOTE]
> Release dates and regional titles are based on publicly available online
> research. The technical comparisons are based on evidence from the
> byte-matched retail executables and this repository's version-specific
> reconstructed source. This is not recovered development history, so the
> reasons or intent behind a change remain interpretation unless stated
> otherwise.

The chronology matters. The European release is the earliest retail version.
The verified differences below therefore describe code shared by North America
and Japan but absent from Europe as later additions, rather than as removals
from an assumed North American baseline. The three releases still share nearly
all engine, game-mode, rules, physics, and AI code.

## At a glance

| Area | Europe → North America | North America → Japan |
| --- | --- | --- |
| Platform and video | Updates several Dolphin SDK components and expands progressive/interlaced reset handling. | Selects Japanese region behavior and localized disc-error presentation paths. |
| Save/load | Adds defensive file cleanup, card-removal tracking, and more autosave, format, and error handling. | Adds memory-card serial-number checks and Japanese save/load presentation. |
| Audio | Expands audio-setting reload control and makes permanent sound-group loading scene-aware. | Retains the later audio flow; most new work is localization-facing. |
| Gameplay | Revises Shoot to Score timing, goalie grab-ball flow, and full-time draw handling. | Stops action-specific fielder processing while a player is frozen. |
| Presentation | Adds cutscene-load timeouts and several end-of-game, controller, and crowd-loading fixes. | Adds Japanese fonts, text rules, layouts, menu states, graphics, and a localized lesson movie. |

## Europe → North America

The North American release followed 17 days after Europe. Its differences are
mostly small hardening and flow changes rather than a new game revision:

- Several platform components were updated. Europe uses the earlier DVD and VI
  implementations reconstructed under `dvd_2003` and `vi_2003`; embedded OS
  and CARD version strings also identify 2003 components where the later
  releases use 2004 builds. Progressive/interlaced mode and reset-state
  handling were expanded at the same time.
- Memory-card code gained defensive initialization and cleanup, card-removal
  tracking, and a larger save/load state machine. The later flow has additional
  autosave, formatting, retry, and error guards.
- Audio settings gained separate control over mode updates and sample loading.
  DPL2 activation became scene-aware, and some sound shutdown/reload work moved
  to a later point in the transition.
- Gameplay received a few targeted corrections: Shoot to Score uses a shared
  tuning threshold instead of the captain-specific yellow-region width; the
  goalie can leave the grab-ball hold regardless of current ball ownership; and
  full-time statistics check for a draw before recording a winner.
- Cutscene queue entries gained a timeout field and full-queue guard. End-game
  skipping and controller-removal handling were hardened, while crowd animation
  speed moved from state selection to the completed texture-load callback.

These are code-level differences represented by the reconstructed executables.
Some are user-visible fixes; others are internal safety or sequencing changes.

## North America → Japan

The Japanese release followed 45 days after North America. Most of its added
code supports localization and presentation:

- Dedicated Japanese fonts, text measurement, and wrapping accommodate
  Japanese strings. Button labels, highlights, colours, and cup-standing
  buffers are adjusted for the localized layouts.
- Team and captain selection, cup standings and trophies, popups, options,
  save/load, tournament setup, and Strikers 101 select Japanese-specific
  layouts or formatting. The release also includes localized disc-error
  graphics and a Japanese version of the sixth lesson movie.
- Controller-selection screens show additional connected/disconnected
  indicators, and the options menu can display a dedicated message when no
  cheats have been unlocked.
- Save/load operations add memory-card serial-number checks so a changed card
  can be routed through the correct retry, format, or error flow.
- One confirmed gameplay-side change stops a fielder's action-specific
  post-physics processing while that player is frozen. The shared player update
  still runs first.

The reconstructed code does not indicate a broad gameplay or balancing revision
for Japan; it is principally a regional adaptation of the later codebase.

## Binary identity

All three executables use entry point `0x80005240`. Their exact retail sizes
and hashes are:

| Version | `main.dol` size | Change from previous release | SHA-1 |
| --- | ---: | ---: | --- |
| `G4QP01` | 3,202,656 bytes | — | `6dc83dc91d0a5887f0056623498d4cbcd88bc463` |
| `G4QE01` | 3,210,784 bytes | +8,128 bytes | `376d699c99b6b0949abe1b4ceccefdef7828d2b5` |
| `G4QJ01` | 3,224,576 bytes | +13,792 bytes | `d116f02b778a4f69725fd1c00656012d16ebf94a` |

Added code and localization data shift many later addresses, so the project
keeps separate symbol, split, and linker metadata for every release.

This is a compact summary of differences represented by the reconstructed
executables and their version-specific source paths. It is not an exhaustive
comparison of every asset on the three retail discs.
