# Detection rules

## Signals checked

| Signal | Weight | Notes |
|--------|--------|-------|
| Keyword hit | +30 | Case-insensitive match against configurable keyword list |
| URL | +35 | Any `http://`, `https://`, or `www.` link |
| Blocked domain | +45 | URLs containing blocked domains (e.g. `t.cn`, `bit.ly`, `taobao.com`) |
| Phone number | +35 | NZ-format (`+64` or `0`) or generic 8-11 digit numbers |
| WeChat ID hint | +25 | Contains "微信", "vx", "v信", "wechat" |
| Disguised chars | +40 | Substituted characters (e.g. 微✨信, 加➕V) |
| Repeat offender | +20 | Sender has ≥3 flagged messages in past 24 h |

## Thresholds

- **Suspicious:** score ≥ 30
- **High priority:** score ≥ 60 (multiple strong signals)

## Repeated offense tracking

Tracked per sender within a 24-hour rolling window. A sender with ≥3
suspicious messages in that window gets the `repeat_offender` tag (+20).

## Domain blocklist (default)

`t.cn`, `bit.ly`, `tinyurl.com`, `goo.gl`, `taobao.com`, `1688.com`,
`pinduoduo.com`, `拼多多`

Additional domains can be added via `config.yaml`:

```yaml
blocked_domains:
  - myspammy.site
  - fraud.link
```

## Trusted senders

Users in the `trusted_senders` list bypass detection entirely:

```yaml
trusted_senders:
  - AdminZhang
  - GroupOwnerLi
```

## Future signals

- Repeated message bursts (same text × N accounts)
- OCR on image attachments
- Domain allowlist
- Member join events
- Minimum account age checks
