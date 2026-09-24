# Published Boundary archive evidence needed

P10 requires two distinct, publicly retrievable immutable Boundary commit archives. Repository code cannot manufacture valid publication evidence for revisions that have not been published.

The configured origin is:

    https://github.com/dmos62/speckit-specdd.git

The latest captured remote state did not contain two published commits with the complete downstream consumer and release-proof implementation.

Publish the current branch to the intended origin branch according to the repository's normal policy. The resulting published history must contain at least two distinct genuine commits that include the current downstream consumer and `tests/test_consumer_release.py`.

Suggested bash checks:

    git status --short
    git branch --show-current
    git push origin HEAD
    git fetch --prune origin
    git branch -r --contains HEAD
    git ls-remote origin HEAD 'refs/heads/*'

After publication, rerun the harness. `dev-scripts.include` will search published history, anonymously download the two newest usable GitHub commit archives, and report their exact revisions, URLs, and SHA-256 values.

If the harness still reports fewer than two usable published candidates, another genuine implementation revision must be published before P10 can complete.

Do not create release lock fixtures from unpublished commits, mutable branch or tag archives, authenticated-only archive downloads, synthetic archive bytes, fabricated checksums, or empty evidence-only commits.

Delete this file once two usable published archive identities have been obtained and the release fixtures can be committed.
