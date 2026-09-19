
Once the build/test/lint commands are known, offer the user a Stop hook in
`.claude/settings.json` that runs lint (and fast tests if cheap) on turn
end, so "done = checks pass" is a hard gate. Add it only with consent.
