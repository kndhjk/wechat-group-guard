# Architecture

## Flow

1. Watcher polls messages from desktop WeChat UI
2. Detector scores text against ad/spam heuristics
3. Suspicious messages enter review queue
4. Human approves or skips
5. Executor performs kick only after approval
6. Storage keeps audit logs

## MVP order

1. Mock watcher
2. Rule detector
3. Console review
4. Audit log
5. Real desktop WeChat watcher
6. Real kick executor
