# Contributing to smstrikers-decomp

Thanks for your interest in contributing! This is a community-driven decompilation of *Super Mario Strikers* (GameCube), aimed at producing source code that compiles to a **byte-for-byte identical** match of the original binary.

Whether you're an experienced decomp veteran or just curious about reverse engineering, you're welcome here.

- Discord: [join the server](https://discord.gg/hKx3FJJgrV) — the fastest way to ask questions, coordinate work, or get unstuck.
- Issues / PRs: please use GitHub.

## Table of contents

- [Where the project stands](#where-the-project-stands)
- [Before you start](#before-you-start)
- [Development setup](#development-setup)
- [How to contribute](#how-to-contribute)
- [Pull request guidelines](#pull-request-guidelines)
- [Code style](#code-style)
- [Working on matches](#working-on-matches)
- [Header and module reorganisation](#header-and-module-reorganisation)
- [Use of AI tools](#use-of-ai-tools)
- [Helpful tooling](#helpful-tooling)
- [Licensing and provenance of contributions](#licensing-and-provenance-of-contributions)
- [Code of conduct](#code-of-conduct)

## Where the project stands

The skeleton of the codebase is by now reasonably well defined — most of the core C++ classes are in place, and a large number of methods already match at 95%+. What's left is mostly the hard part:

- Closing the last few percent on tricky functions.
- Untangling subtle ABI / register-allocation / scheduling quirks.
- Tightening up details that only show up once the surrounding code is in shape.
- Reorganising headers and module boundaries as the puzzle pieces start to interlock.

In other words: from here on, **attention to detail and patient iteration matter much more than raw volume**. Improvements that unlock matches elsewhere — even small ones — are extremely valuable.

## Before you start

- Read the [README](README.md) for project overview, supported versions, and a quick orientation.
- Make sure you can produce a clean build locally before sending a PR (see [Development setup](#development-setup)).
- For non-trivial changes, it's usually a good idea to mention what you're working on in Discord first, so we don't duplicate effort.
- Never commit game assets, ROMs, original assembly, extracted DOL/REL files, or anything else copyrighted by Nintendo / Next Level Games. The repository must remain clean of original game data.

## Development setup

Full setup, dependencies, and build instructions live in the [README](README.md). At minimum you'll need:

- Python 3
- Ninja
- A legally obtained copy of the game (disc image), placed at `orig/G4QE01/`
- On Linux/macOS: `wibo` (auto-downloaded on x86_64) or Wine

Quick build:

```sh
git clone --recursive https://github.com/yannicksuter/smstrikers-decomp
cd smstrikers-decomp
python configure.py
ninja
```

After the first successful build, an `objdiff.json` will be present at the project root — see [Diffing](README.md#diffing) for how to wire it up.

## How to contribute

There are many useful ways to contribute, not just writing C++:

- **Improve matches** on functions that aren't yet 100%.
- **Fix structures, types, or signatures** so that surrounding code becomes easier to match.
- **Reorganise headers** to better reflect actual ownership and dependencies.
- **Document discoveries** (`FunFacts.md` is a good home for interesting findings).
- **Improve tooling and scripts** under `tools/`.
- **File issues** with reproducible repro steps when something is wrong with the build, scripts, or repo configuration.

If you're new and looking for a starting point, ask in Discord — there are usually some "good first" candidates around.

## Pull request guidelines

Please keep PRs **small, focused, and reviewable**:

- One logical change per PR. If you fix a function and reorganise a header, that's two PRs.
- Title should clearly state the scope (e.g. `glModel: match glModel::draw`, `headers: split feBasic3dModel`).
- In the description, explain the *why*: what was the issue, what did you change, and how did you verify it. Link to relevant `objdiff` results or screenshots when useful.
- Make sure `ninja` builds cleanly.
- If something is **not yet matching**, say so explicitly. Don't gloss over it — partial progress is fine and welcome, but it has to be honest.
- Avoid drive-by formatting or unrelated cleanup; that just makes review harder.
- If your change touches a public-ish header or a struct layout, mention which other modules you've sanity-checked.

Force-pushes during review are fine; please don't rewrite history once a PR has been approved unless asked.

## Code style

- Run [`clang-format`](https://clang.llvm.org/docs/ClangFormat.html) before committing. The repo's `.clang-format` is the source of truth — please don't fight it.
- Match the existing conventions in the surrounding files (naming, header order, indentation, etc.). Decomp work means the *shape* of the code matters; please don't refactor for personal taste in unrelated places.
- Keep comments meaningful. Comments that just narrate what the code does add noise; comments that explain *why* something is unusual (compiler quirk, ABI detail, scheduling artefact) are gold.
- Prefer reorganising headers and types over `#include` shuffling band-aids when the underlying structure is wrong.

## Working on matches

A few practical notes that will save you time:

- **Use `objdiff` actively.** Most matching work is read-the-diff, change, rebuild, read-the-diff again. Trying to reason without looking at the actual diff is almost always slower.
- **Don't chase 100% blindly.** If a function is at 95% with a single weird scheduling difference, it's often worth pausing to check whether a surrounding type or inline is wrong — the real fix may live elsewhere.
- **Watch out for inlines and templates.** Many "mysterious" mismatches are actually caused by an incorrect inline definition in a header that's included by many translation units.
- **Be skeptical of suspiciously easy matches.** If something matches with no effort but the code looks nothing like the disasm, you may be matching by accident; double-check.
- **Partial matches are welcome** when they capture real structure. Mark them clearly (in the PR description and/or with a `// NONMATCHING:` comment if appropriate).

## Header and module reorganisation

As more code lands, the include layout and module boundaries are increasingly important. PRs that:

- Move types into the header where they actually belong,
- Split overstuffed headers,
- Remove circular or transitive include dependencies,
- Or correct visibility (public vs internal) of declarations

are very welcome — these often unlock matches in unrelated files. When doing this kind of work, please keep it surgical and isolated from match changes; mixing the two makes review painful.

## Use of AI tools

I use modern AI tools myself and have honestly learned a lot from them. They've surfaced solutions I would never have thought of on my own, and their ability to look at the code holistically has repeatedly helped me spot improvements in completely unrelated areas. As an *assisting* tool to converge on a matching result, they have a fair place in this project.

That said:

- **PRs consisting of uncurated, AI-generated output are explicitly low priority.** They will not be reviewed with urgency, and may be closed if there's no evidence the author has actually engaged with the code.
- The phase where it made sense to generate code purely to fill gaps is over. What this project needs now is **attention to detail** — understanding *why* something matches (or doesn't), reading the disassembly, and verifying against the diff.
- If you use AI assistance, treat its output as a *starting point*, not a deliverable. Review it, test it, diff it, and only submit what you actually understand and can defend in review.
- Be honest about AI involvement when it's relevant (e.g. "I used an LLM to draft this, then verified X and Y manually"). That context helps reviewers focus.

In short: AI is welcome as a tool, not as an author.

## Helpful tooling

- **`objdiff`** — primary tool for verifying matches; see [Diffing](README.md#diffing).
- **`decomp.me`** — useful for iterating on a single function in isolation.
- **DWARF dump** — if you have legally acquired the game and placed the original debug ELF at `orig/G4QE01/MarioSoccerR.elf`, you can dump its DWARF debug info into a human-readable `dwarf.txt`:

  ```sh
  ./tools/scripts/dump_dwarf.sh
  ```

  The script writes `dwarf.txt` to the project root. Run `python configure.py && ninja` at least once beforehand so that `build/tools/dtk` is available.

## Licensing and provenance of contributions

By submitting a contribution, you confirm that you have the right to submit
it and agree that your original contribution is offered under CC0 1.0, except
where maintainers explicitly accept another license that is clearly identified
in the contribution. CC0 applies only to rights you hold and does not change
the status of third-party material.

Do not submit:

- leaked, stolen, confidential, or improperly obtained source code;
- game assets, disc images, SDK files, proprietary compiler files, or other
  material that the repository is not authorized to distribute;
- code copied from an unrelated proprietary source release; or
- third-party code with a license incompatible with its proposed use here.

When a contribution is based on publicly available third-party source,
identify its origin and license in the pull request. Preserve existing
copyright, authorship, and license notices.

For ODE-related contributions:

- state whether the change is based on historical upstream ODE source, retail
  binary analysis, or original project work;
- identify the relevant upstream ODE file where possible;
- preserve ODE copyright, authorship, and license headers;
- do not describe game-developer modifications as CC0 unless reliable
  evidence establishes that the relevant rightsholder released them under
  CC0; and
- follow the classifications in
  [`docs/ode-provenance.md`](docs/ode-provenance.md).

A matching or byte-identical build does not by itself establish that all
reconstructed expression is owned by the contributor or available under CC0.
Maintainers may request additional provenance information or decline material
whose origin or licensing cannot be documented adequately.

## Code of conduct

Be kind, be patient, and assume good faith. This is a hobby project; people contribute in their spare time. We're here to learn, share, and have fun reverse-engineering a great game — keep the discussion technical and respectful, both in PRs and on Discord.

If something feels off, ping a maintainer on Discord rather than escalating publicly.

---

Thanks for taking the time to contribute — every small improvement gets us closer to a fully matching decompilation.
