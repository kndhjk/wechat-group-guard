# Reading real WeChat groups

## Step 1
Probe the WeChat desktop window and enumerate visible conversation names.

## Step 2
Show these names in the GUI so the user can choose which groups to manage.

## Step 3
Bind watcher logic to the selected groups only.

## Current implementation
A first Windows probe has been added in:
- `watcher/windows_wechat.py`
- `scripts/probe_wechat_groups.py`

This is an early probe, not a fully stable reader yet.
