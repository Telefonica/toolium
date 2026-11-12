# Releasing Toolium

Releases are fully automated. Every merge to `master` is analysed by
[python-semantic-release](https://python-semantic-release.readthedocs.io/) (PSR), which decides the next version,
updates the version and the changelog, commits, tags, and publishes. **There is no manual release step.**

## Versioning rules

The next version is derived from the commit messages, following
[Conventional Commits](https://www.conventionalcommits.org/). Three prefixes are recognised — `feat:`, `fix:` and
`chore:` — with these effects:

| Commit prefix | Effect |
| --- | --- |
| `feat:` | Minor release (`3.9.0` → `3.10.0`) |
| `fix:` | Patch release (`3.9.0` → `3.9.1`) |
| `feat!:` or a `BREAKING CHANGE:` footer | Major release (`3.9.0` → `4.0.0`) |
| `chore:` | No release on its own; it appears in the changelog when something else releases |
| anything else (`docs:`, `ci:`, `test:`, `perf:`, `refactor:`, `style:`, `build:`, …) | **Ignored**: no version bump and no changelog entry |

The prefix list is set in `pyproject.toml` (`minor_tags`, `patch_tags`, `other_allowed_tags`) and is deliberately narrow.
A change worth publishing must use one of the three prefixes above; otherwise it is silently dropped, both from the
version and from the changelog. In particular, a performance improvement is written as `fix:`, not `perf:`, so that it
reaches the patch release and the changelog.

Commits that do not follow the convention are ignored for versioning. A merge that releases nothing simply skips the
whole workflow.

**The pull request title is the commit message.** Pull requests are merged with squash, so the title of the PR becomes
the single commit that lands on `master` — and that is what semantic-release reads. A malformed title is silently
ignored: it will not bump the version and will not appear in the changelog. Note that a prefix with a missing colon is
not recognised: `feat(scope) text` is ignored, `feat(scope): text` is not. Editing the PR title after it has been
merged does **not** fix it, because the commit message is already written and cannot be changed.

Because the version is derived from the commits, `VERSION` is never edited by hand again, and the `X.Y.Z.dev0` scheme
is no longer used: after a release, `VERSION` holds the released version, and the next release is computed from it.

### Postponing a release

To land a change without releasing it, put `[skip release]` in the commit message. The release workflow is skipped, but
the commits it carries stay pending, so the **next** release includes them — with their own entry in the changelog and
their own effect on the version. It only affects the release workflow, not CI, which runs as usual.

```
feat: support python 3.14

[skip release]
```

This is useful to group related changes into a single release: merge the first PR with the marker, and merge the last
one without it. Both `feat:` entries then appear together in the same release.

Two things to bear in mind:

- Put the marker in the **commit message body**, not in the subject. In the subject it would also be copied into the
  changelog entry (`* Support python 3.14 [skip release]`).
- As the marker is read from the message of the commit that triggers the workflow, and a squash merge writes the PR
  title plus the list of its commits, the body of the PR description is not what is read. Set the marker in the
  commits of the PR (or in the squash commit message, when merging from the GitHub UI).

A `chore:` does not release on its own either, but it does appear in the changelog under its own section, so it is the
one to use for maintenance that should be listed. Use `[skip release]` instead when the change must stay out of the
changelog until it is released together with something else — which is the only option for a `feat:` that should not
trigger a release yet.

## What happens on a merge to master

`.github/workflows/release.yml` runs:

1. Checks out `master` and runs python-semantic-release, which calculates the next version from the commits since the
   last tag, rewrites `VERSION`, inserts the new entry in `CHANGELOG.rst`, commits, tags, and builds the distributions.
2. Publishes the distributions on PyPI using Trusted Publishing (OIDC), with PEP 740 attestations enabled.
3. Creates the GitHub release for the tag and attaches the sdist and the wheel.

If the commits since the last tag do not justify a release, the workflow stops after step 1 and nothing is published.

Version commits are named `chore(release): X.Y.Z` and are excluded from the changelog.

## Verifying a release

- PyPI: <https://pypi.org/project/toolium/>
- GitHub releases: <https://github.com/Telefonica/toolium/releases>
- Actions runs: <https://github.com/Telefonica/toolium/actions/workflows/release.yml>
- The attestations of a published file are visible on its PyPI page, under *Provenance*.

To preview the next version locally, without releasing anything:

```bash
pip install python-semantic-release
semantic-release version --print
```

## Rehearsing the flow

`.github/workflows/release-test.yml` builds a prerelease and publishes it on
[TestPyPI](https://test.pypi.org/project/toolium/), so the whole flow can be tried without
publishing anything real:

- It can be started manually from the *Actions* tab, or by pushing to a branch named `test/*`.
  The manual button only appears once the file is on `master`; pushing to a `test/*` branch
  works before that.
- The version is a prerelease (`X.Y.Z-dev.N`). The release commit and tag are created locally
  inside the run to satisfy the action, but nothing is pushed: the remote branches and tags
  are left as they were, and PyPI never sees the rehearsal.
- The changelog entry that the release would generate is shown in the run summary, so it can
  be reviewed before the real release.
- It needs the `testpypi` environment and a trusted publisher on TestPyPI configured the
  same way as the one on PyPI (same repository, workflow `release-test.yml`).

To install a rehearsed build:

```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ toolium==X.Y.Z.devN
```

## The changelog

`CHANGELOG.rst` is no longer edited by hand. When a release happens, semantic-release inserts the section of the new
version right below the document title, and **leaves everything below it untouched**, so the entries written before the
automation are kept exactly as they were.

For uniformity, the historical entries were reformatted once to the format used by semantic-release: each version is
now a heading like `vX.Y.Z (YYYY-MM-DD)` with the date inside the heading, instead of a `vX.Y.Z` heading followed by a
`*Release date: ...*` line. Only the headings and dates were moved; the text of every entry is unchanged.

From `v3.9.0` onwards, the entries of each release are generated from its commits: they summarise the commit subjects
and link to the pull request and the commit of each change. Because of this, **a clear conventional commit message is
what produces a good changelog entry**.

The insertion point is marked by the `..` / `version list` comment block at the top of the file. Do not remove it, or
semantic-release will be unable to insert the notes of the next release.

If a change was missed because its commit message could not be parsed, add its line by hand to the existing changelog,
right below that marker, before the release. semantic-release keeps it and places it inside the new version's section
when inserting the generated entries.

`CHANGELOG.rst` must keep LF line endings: semantic-release looks for that marker using the line separator of the
platform, so the file is pinned to LF in `.gitattributes`. An editor that writes CRLF will break the insertion
silently: the release would publish with the changelog left as it was. Check with
`file CHANGELOG.rst`, or look for `^M$` line endings, if a release's entry is ever missing.