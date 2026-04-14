# MVP Roadmap

## ✅ Phase 1 — Core engine
- [x] Rule detector (keyword / URL / phone / WeChat ID / domain blocklist)
- [x] Disguised-character detection
- [x] Score weights and suspicious threshold
- [x] Repeat-offender tracker (24h rolling window)
- [x] Time-window deduplication
- [x] Mock watcher (demo)
- [x] Console review (k/i/s actions)
- [x] Audit logging (append-only JSONL)

## ✅ Phase 2 — GUI
- [x] Tkinter review panel
- [x] Color-coded score rows (🔴🟡⚪)
- [x] Approve / Skip / Ignore buttons
- [x] Manage ignored users dialog
- [x] Group selection sidebar
- [x] Auto-refresh (5-second polling)
- [x] Shared data file with console watcher

## ✅ Phase 3 — Windows integration (foundation)
- [x] WeChatWindowProbe — enumerate conversation names
- [x] WeChatWatcher — continuous watcher stub
- [x] DesktopWeChatKickExecutor — executor stub (dry_run)
- [x] config.yaml — dry_run safety flag

## 🛠 Phase 4 — Windows integration (field testing)
- [ ] Test WeChatWatcher on real Windows + WeChat 3.x
- [ ] Tune UI element selectors for WeChat version differences
- [ ] Add screenshot-based error reporting when group not found
- [ ] Real kick flow: confirm it works on Windows

## 🛠 Phase 5 — Packaging
- [ ] Test PyInstaller spec on Windows
- [ ] Build EXE with `scripts/build_spec.spec`
- [ ] Test EXE on clean Windows machine (no Python installed)
- [ ] Create GitHub Release ZIP

## 📋 Future ideas
- OCR for image ads
- Web-based review dashboard
- Alert notification (email / Telegram) for high-priority items
- Minimum account age check (new accounts = higher risk)
- Group admin webhook integration
