# Monthly-Tracker-App

## Data storage

- Streamlit Cloud cannot write directly back to files on your Mac.
- When Supabase is configured, the app uses Supabase as the source of truth.
- Your local `monthly_tracker_data.json` only updates when you explicitly pull the latest cloud data down to your machine.

## Automatic commit protection

- This repo uses a Git pre-commit hook to pull the latest Supabase data into `monthly_tracker_data.json` before each commit.
- If sync fails, the commit is blocked so you do not accidentally commit stale local data over newer app data.

## Manual fallback

- You can still pull the latest app data manually at any time:
	- `python sync_supabase_to_json.py`
- This is useful if you want to review the JSON before committing.

## One-time upload from local to cloud

- If you make intentional local edits and want Supabase to match your local file, run:
	- `python sync_json_to_supabase.py`
- Use this carefully: it pushes your local `monthly_tracker_data.json` up to Supabase and replaces the cloud payload.
- Normal day-to-day workflow should still rely on the automatic pre-commit pull from Supabase.

## Hook setup

- Run this once in the repo:
	- `git config core.hooksPath .githooks`
- After that, every `git commit` will auto-run the sync first.

## Credentials

- The sync script reads credentials from environment variables first:
	- `SUPABASE_URL`
	- `SUPABASE_KEY`
- If those are not set, it falls back to `.streamlit/secrets.toml`.
