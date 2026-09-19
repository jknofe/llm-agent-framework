Once the build/test/lint commands are known, offer the user a `pre_verify`
hook (a script under `.agents/hooks/`, declared in `~/.hermes/config.yaml`
next to the framework's entries) that runs lint (and fast tests if cheap)
before the turn ends, so "done = checks pass" is a hard gate. Add it only
with consent.
