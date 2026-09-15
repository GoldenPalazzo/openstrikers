# Open Dynamics Engine provenance

## Purpose

This document records the origin and licensing treatment of Open Dynamics
Engine material used in this source-reconstruction project. It is a technical
provenance record, not a legal opinion.

## Upstream component

The repository contains code corresponding to Open Dynamics Engine (ODE)
version 0.5. ODE 0.5 source identifies Russell L. Smith as the copyright owner
and offers a choice of licenses that includes a BSD-style alternative.

For upstream ODE portions, this repository uses the historical BSD-style
alternative reproduced verbatim in
[`../LICENSE-BSD.TXT`](../LICENSE-BSD.TXT).

Historical references:

- ODE project and historical license: <https://www.ode.org/>
- ODE 0.5 release: <https://sourceforge.net/projects/opende/files/ODE/ODE%20version%200.5/>
- Preserved archive collection: <https://archive.org/details/OpenDynamicsEngine>

## Preserved archive record

The comparison performed for this review used the archive supplied to the
project maintainer outside the repository:

| Field | Value |
|---|---|
| Upstream published filename | `ode-0.5.tgz` |
| Locally preserved filename | `ode-0.5.tar.gz` |
| Release date | 29 May 2004 |
| Archive SHA-256 | `6e0dc1314aa6be78f1d9fb76ebda19b7a44551f044082dc808a3e3de7759ff51` |
| Extracted top-level directory | `ode-040529/` |
| Extracted `LICENSE-BSD.TXT` SHA-256 | `e205c5c9a1a0cd0ae6d59de258bf76d00edec15ef4779bc37e5e74c2747c565a` |

The stored filename differs from the historical published filename, so the
hash above identifies the exact local archive examined rather than purporting
to be an independently published upstream checksum.

## Initial comparison record

The 25 August 2026 review compared repository files with the extracted ODE 0.5
tree by relative basename and then used byte-for-byte comparisons:

| Repository area | Same-name upstream files | Byte-identical | Different |
|---|---:|---:|---:|
| `src/ode/` vs. `ode/src/` | 54 | 23 | 31 |
| `include/ode/` vs. `include/ode/` | 21 | 12 | 9 |

Three additional renamed repository files are byte-identical to their
upstream counterparts:

- `src/ode/_array.cpp` corresponds to upstream `ode/src/array.cpp`;
- `src/ode/_collision_quadtreespace.cpp` corresponds to upstream
  `ode/src/collision_quadtreespace.cpp`; and
- `src/ode/joint_orig.cpp` corresponds to upstream `ode/src/joint.cpp`.

This is a high-level provenance check, not a completed expression-level audit.
Filename correspondence or a non-identical diff does not establish who wrote
each changed region. Conversely, byte identity supports an upstream match but
does not determine the status of material elsewhere in the same directory.

## Affected repository areas

Known ODE-related material is primarily located in:

- `src/ode/`;
- `include/ode/`; and
- files elsewhere in the repository that copy, adapt, include, or closely
  derive from ODE source or headers.

The list is descriptive rather than exhaustive. File history and an upstream
comparison should be consulted when the origin of a particular file is
unclear.

## Modified ODE in the retail game

The ODE version incorporated into the retail game was modified. Relevant
files may therefore contain a mixture of:

1. unchanged upstream ODE code;
2. mechanically adapted upstream ODE code;
3. substantive modifications to ODE;
4. developer-specific additions;
5. source reconstructed by this project from the retail executable; and
6. project annotations, build metadata, or other contributor-created
   material.

The historical ODE BSD license authorizes redistribution and modification of
the upstream ODE code subject to its conditions. It does not, by itself,
establish that independently copyrightable developer modifications were
licensed under BSD or CC0 by their rightsholder.

Accordingly, the project does not represent all files under `src/ode/` or
`include/ode/` as wholly CC0 or wholly BSD material. CC0 applies only to rights
held by project contributors and intentionally offered under CC0.

## OPCODE boundary

The ODE 0.5 archive contains a separate `OPCODE/` tree attributed to Pierre
Terdiman. That standalone tree is not present at a corresponding tracked path
in this repository, although some upstream ODE TriMesh files refer to or
interface with OPCODE. The ODE BSD file should not be assumed, without further
evidence, to license separately copied OPCODE expression. Any such material
identified in a future comparison should receive a separate provenance and
license classification.

In particular, `src/ode/collision_trimesh_sphere.cpp` is byte-identical to the
ODE 0.5 file but retains an upstream comment stating that code was taken from
OPCODE 1.1. For this project's conservative policy, that file remains
`mixed-or-uncertain` pending an OPCODE-specific provenance review; byte
identity with the ODE release is not enough to resolve the nested provenance.

## Classification policy

When comparing reconstructed files with preserved ODE 0.5 source, use these
classifications:

| Classification | Meaning | Licensing treatment |
|---|---|---|
| `upstream-identical` | Substantively identical to historical ODE source | Historical ODE BSD terms; preserve notices |
| `upstream-mechanical` | Formatting, compiler, platform, naming, or similarly mechanical adaptation | Preserve ODE notices and document the adaptation |
| `upstream-modified` | ODE-derived code containing substantive changes | Preserve ODE notices; do not claim third-party changes are CC0 |
| `developer-addition` | Game-specific addition not found in upstream ODE | Treat as game-derived unless reliable evidence establishes another license |
| `project-original` | New material authored by project contributors without copying third-party expression | CC0 only where the contributor owns the rights and applied CC0 |
| `mixed-or-uncertain` | Authorship or derivation cannot be separated with confidence | Preserve all applicable notices and avoid a blanket licensing claim |

## Required preservation

Do not remove or rewrite historical ODE copyright, authorship, or licensing
headers merely to make files appear uniformly licensed.

For source redistribution, retain:

- the ODE copyright notice;
- all BSD license conditions; and
- the complete BSD disclaimer.

For binary redistribution, reproduce the same notice, conditions, and
disclaimer in accompanying documentation and/or other distributed materials.
Do not use the names of ODE's copyright owner or contributors to imply
endorsement.

## Future file-level audit

A complete audit should record, for every ODE-related file:

- repository path;
- closest upstream ODE 0.5 path;
- upstream archive filename and SHA-256;
- file-level similarity or diff result;
- classification from the table above; and
- notes identifying reconstructed or game-specific regions where possible.

Until that audit is complete, ambiguous material should be classified as
`mixed-or-uncertain` rather than assumed to be CC0 or wholly BSD.
