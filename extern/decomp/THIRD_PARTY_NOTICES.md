# Third-party notices

This repository contains or reconstructs material with multiple origins. This
file records third-party notices identified during the licensing review; it is
not exhaustive and does not replace complete license texts or file-level
notices. When this summary conflicts with a component's license or preserved
header, the component-specific terms control.

## Open Dynamics Engine

- **Component:** Open Dynamics Engine (ODE)
- **Historical release compared:** ODE 0.5, released 29 May 2004
- **Historical copyright:** Copyright (c) 2001–2004, Russell L. Smith
- **License used here for upstream ODE portions:** Historical ODE BSD-style
  alternative
- **Complete license:** [`LICENSE-BSD.TXT`](LICENSE-BSD.TXT)
- **Affected locations:** Primarily `src/ode/`, `include/ode/`, and files that
  copy, adapt, include, or closely derive from those sources or headers
- **Historical release:** [ODE version 0.5 on SourceForge](https://sourceforge.net/projects/opende/files/ODE/ODE%20version%200.5/)
- **ODE project and license:** <https://www.ode.org/>
- **Preserved archive collection:** <https://archive.org/details/OpenDynamicsEngine>

ODE 0.5 was offered under a choice that included LGPL terms and the historical
BSD-style license. This repository uses the BSD-style alternative for
redistribution of upstream ODE material. Existing ODE copyright, authorship,
and license headers must be preserved.

Comparison with the preserved ODE 0.5 archive confirms substantial direct
correspondence, including byte-identical files as well as modified files. The
retail game appears to incorporate a modified ODE version. The ODE BSD license
applies to upstream ODE expression; it does not, by itself, establish the
licensing status of independently copyrightable modifications or additions
authored by the game developer or another party.

The ODE 0.5 release archive also contains a separately attributed OPCODE
source tree, and some ODE TriMesh sources refer to or interface with OPCODE.
The standalone OPCODE tree is not tracked in this repository at that upstream
path. No blanket licensing claim about separately obtained OPCODE material is
made here; copied OPCODE expression, if identified, requires its own provenance
and licensing review.

See [`docs/ode-provenance.md`](docs/ode-provenance.md) for the archive hashes,
comparison record, and classification policy.

## Ninja Python helper

- **Component:** `tools/ninja_syntax.py`
- **Copyright notice:** Copyright 2011 Google Inc. All Rights Reserved.
- **License:** Apache License 2.0
- **Complete license:** [`LICENSE-APACHE-2.0.txt`](LICENSE-APACHE-2.0.txt)

Preserve the file's copyright and license header when redistributing it.

## eCos-derived mathematical code

The following files contain eCos notices offering the code under GNU General
Public License version 2 or, at the recipient's option, a later version, with
a special linking exception stated in each file:

- `src/PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/e_pow.c`
- `src/PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/k_tan.c`

The GPL version 2 text is included in
[`LICENSE-GPL-2.0.txt`](LICENSE-GPL-2.0.txt). The additional exception is part
of each source file's preserved header and must be read together with the GPL.
This repository does not represent those files as CC0.

## Sun fdlibm material

Files under `src/PowerPC_EABI_Support/` and `include/PowerPC_EABI_Support/`
contain fdlibm code and headers bearing Sun Microsystems copyright and
permission notices. Those notices require preservation and remain the
applicable terms for the covered material. See the individual file headers;
this repository does not relicense that material under CC0.

## Git submodules

Repositories checked out below `extern/` are separate works governed by their
own licenses and notices. A license in this parent repository does not
relicense submodule contents. Consult each checked-out submodule before use or
redistribution.

## Game-derived and proprietary material

This repository is an independently produced reconstruction of code from the
retail releases of *Mario Smash Football* and *Super Mario Strikers*. It is not
an official source release.

Some reconstructed material, including runtime or SDK-related material, may
remain subject to rights held by Nintendo, Next Level Games, Metrowerks or its
successors, or other parties. Project contributors do not grant rights they do
not own. The project's CC0 dedication applies only to qualifying
project-original contributions, not to third-party game-derived expression.

## Trademarks and affiliation

Nintendo, Super Mario Strikers, Mario Smash Football, GameCube, and associated
names and marks are the property of their respective owners. The project is
not affiliated with, sponsored by, authorized by, or endorsed by Nintendo,
Next Level Games, Russell L. Smith, or the Open Dynamics Engine project.
