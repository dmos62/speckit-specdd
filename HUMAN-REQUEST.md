# Published Boundary archive evidence needed

P10 requires two distinct, publicly retrievable immutable Boundary commit archives. Repository code cannot create valid publication evidence for commits that have not been published.

At the latest captured check:

- origin is `https://github.com/dmos62/speckit-specdd.git`;
- published remote HEAD is `a016187ce6107d7b1abc1e108669d463a104cb82`;
- local HEAD is `6d3a0c658c5c2c7097b95e1571c7f5abea8318fd`;
- no remote branch contains that local HEAD.

Publish the current implementation to the intended origin branch according to the repository's normal policy. The published history needs at least two distinct commits that contain the current downstream consumer and `tests/test_consumer_release.py`.

Suggested bash checks before and after publication:

    git status --short
    git branch --show-current
    git push origin HEAD
    git fetch --prune origin
    git branch -r --contains HEAD
    git ls-remote origin HEAD 'refs/heads/*'

After publication, rerun the harness. `dev-scripts.include` will identify two suitable remote commits and attempt to calculate the SHA-256 of each anonymous GitHub commit archive.

Do not create release lock fixtures from unpublished commits, authenticated-only archive downloads, mutable branch/tag archives, or synthetic archive bytes.

Delete this file once two usable published archive identities have been obtained.
