# Review flow

## Current flow

1. Watcher yields messages
2. Detector scores each message
3. Suspicious messages are written to pending review storage
4. Reviewer approves or skips in console
5. Decision is written to audit storage
6. Approved actions can later be passed to desktop executor

## Future flow

- Replace console review with web panel or message approval channel
- Add explicit action IDs
- Support `approve`, `skip`, `ban`, `mute`, `ignore-user`
