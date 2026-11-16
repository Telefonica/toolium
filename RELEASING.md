# Releasing Toolium

Releases are fully automated and cut **once a month**. On the 1st,
[python-semantic-release](https://python-semantic-release.readthedocs.io/) (PSR) looks at everything merged into
`master` since the last release, decides the next version, updates the version and the changelog, commits, tags, and
publishes. **There is no manual release step**, beyond starting the workflow by hand for a hotfix.

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

The prefix list is set in `pyproject.toml` (`minor_tags`, `patch_tags`, `other_allowed_tags` and `allowed_tags`) and is
deliberately narrow. A change worth publishing must use one of the three prefixes above; otherwise it is silently
dropped, both from the version and from the changelog. In particular, a performance improvement is written as `fix:`,
not `perf:`, so that it reaches the patch release and the changelog.

Commits that do not follow the convention are ignored for versioning, and are left out of the release.

**The pull request title is the commit message.** Pull requests are merged with squash, so the title of the PR becomes
the single commit that lands on `master` — and that is what semantic-release reads. A malformed title is silently
ignored: it will not bump the version and will not appear in the changelog. Note that a prefix with a missing colon is
not recognised: `feat(scope) text` is ignored, `feat(scope): text` is not. Editing the PR title after it has been
merged does **not** fix it, because the commit message is already written and cannot be changed.

**Only the title is read**, not the list of commits that GitHub writes below it (`parse_squash_commits = false` in
`pyproject.toml`). That list holds the individual commits of the branch, which are often written without this
convention in mind, and it would let a change slip into the version and the changelog unnoticed. The title, on the
other hand, is reviewed before merging and can be corrected at any point while the PR is open, so it is the only thing
that decides the release. A consequence worth knowing: a `feat!:` buried in the branch whose PR is titled `chore:` will
not raise the major version.

Because the version is derived from the commits, `VERSION` is never edited by hand again, and the `X.Y.Z.dev0` scheme
is no longer used: after a release, `VERSION` holds the released version, and the next release is computed from it.

## When a release happens

Releases are cut **once a month**: on the 1st, the workflow picks up everything merged into `master` since the last
tag and publishes it as a single release. Changes therefore accumulate during the month, instead of going out one by
one, which keeps the number of versions published on PyPI close to what it used to be before the automation.

For anything that cannot wait for the monthly release, such as a hotfix, the workflow can also be started by hand from
the *Actions* tab (*release → Run workflow*). It will publish whatever is pending at that moment.

There is no way to hold back a single change: whatever is merged into `master` goes into the next release.

## What the release workflow does

`.github/workflows/release.yml` runs:

1. Checks out `master` and runs python-semantic-release, which calculates the next version from the commits since the
   last tag, rewrites `VERSION`, inserts the new entry in `CHANGELOG.rst`, commits, tags, and builds the distributions.
2. Publishes the distributions on PyPI using Trusted Publishing (OIDC), with PEP 740 attestations enabled.
3. Creates the GitHub release for the tag and attaches the sdist and the wheel.

If the commits since the last tag do not justify a release, the workflow stops after step 1 and nothing is published.

Version commits are named `chore(release): X.Y.Z` and are excluded from the changelog.

### The GitHub App token

The workflow does not push with the built-in `GITHUB_TOKEN`, but with a token generated from the
**`cross-cutting-devex` GitHub App** (`vars.GH_CI_APP_CLIENT_ID` and `secrets.GH_CI_APP_PRIVATE_KEY`). This is needed
because the version commit and the tag are pushed straight to `master`, which is protected: the app is the identity
allowed to do it, instead of having to exempt the `github-actions` bot from the rule.

One consequence: a push made with an app token **does** trigger workflows, unlike one made with `GITHUB_TOKEN`. So the
version commit starts a run of CI, which is what we want (the released commit gets tested), and no run of this workflow,
since it no longer listens to pushes.

If the app is renamed or replaced, update the two values above and the workflow, and note that the workflow pushes on
behalf of that app.

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
