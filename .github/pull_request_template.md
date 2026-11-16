<!--
The pull request title decides the release: it is the only thing semantic-release reads.
Use a conventional commit prefix.

    feat: ...            -> minor release   (3.9.0 -> 3.10.0)
    fix: ...             -> patch release   (3.9.0 -> 3.9.1)
    feat!: ...           -> major release   (3.9.0 -> 4.0.0)
    chore: ...           -> no release; listed in the changelog when something else releases

Any other prefix (docs:, ci:, test:, perf:, refactor:, style:, build:) is ignored: no
version bump, no changelog entry. A performance improvement is written as fix:.

Releases are cut on the 1st of each month, so a merge does not publish on its own. See
RELEASING.md for the details.
-->

## What does this change?

<!-- A short description of the change, and why it is needed. -->

## How was it tested?

<!-- Unit tests added, or the manual steps followed. -->

## Checklist

- [ ] The **title of this pull request** follows the convention above
- [ ] `ruff check .` and `ruff format --check .` pass
- [ ] `python -m pytest` passes
