# Facebook Account Manager

Desktop application for **managing Facebook accounts you own or are authorized to manage**.

Built with Python 3.12+, PySide6, SQLite, and optional Playwright for isolated browser profiles.

## What it does

- Add / edit / delete account profiles (nickname, profile ID, groups, tags, notes)
- Import accounts from CSV or JSON
- Store **user-provided** session cookies only (encrypted at rest with Fernet)
- Never requests or stores Facebook passwords
- Status: Active, Expired, Requires Login, Error
- Clear session immediately from the UI
- Full cookie values never shown in tables or logs
- Content drafts + calendar-style scheduling (reminders for **manual** publishing)
- Task queue and local health checks (no artificial engagement)
- Isolated Playwright browser profile per account for manual login
- Database backups

## What it does **not** do

- Mass friend requests / messaging
- Auto likes, comments, shares, follows
- Fake engagement or account warming
- CAPTCHA / 2FA bypass
- Proxy rotation or fingerprint spoofing
- Auto-extract credentials or tokens from the browser

## Install

```bash
cd facebook_account_manager
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium   # only if you use Open browser / Manual login
```

## Run

```bash
python main.py
```

Data is stored under `~/.facebook_account_manager/` (override with env `FAM_DATA_DIR`).

## Tests

```bash
pip install pytest
pytest tests/ -v
```

## Sample import

See `samples/accounts_example.json` and `samples/accounts_example.csv` — no real credentials.

## Security notes

- Session blobs encrypted with a local Fernet key (`~/.facebook_account_manager/.master.key`, mode 600 when the OS allows)
- Log redaction filter strips cookie-like substrings
- Export metadata intentionally omits sessions
- Delete account removes DB row; clear session zeroes the encrypted blob

## Project layout

```
facebook_account_manager/
├── main.py
├── requirements.txt
├── README.md
├── app/
│   ├── ui/           # PySide6 windows & pages
│   ├── core/         # config, logging
│   ├── accounts/     # import/export service
│   ├── browser/      # Playwright profiles
│   ├── security/     # encryption
│   ├── database/     # SQLite
│   └── scheduler/    # reminders & health
├── samples/
└── tests/
```

## License

MIT — use only on accounts you are authorized to manage. Comply with Meta’s terms and applicable law.
