# StockTickerDashboard

This repo is a small **Dash** web app that simulates a “stock ticker game” with two main experiences:

- **Dashboard**: roll a dice to randomly move stock prices and visualize them.
- **User portfolio**: manage a simple portfolio (buy/sell shares and add cash) and see net value update based on the current dashboard prices.

## What’s in the project

Key files:

- `main.py`: creates the Dash app shell and handles top-level routing (`dcc.Location`) updates.
- `constants.py`: shared configuration (available commodities, starting user balance).
- `pages/`
  - `sign_in.py`: the landing page (`/`) where you enter your name.
  - `dashboard.py`: the stock-price game (`/dashboard`).
  - `user.py`: the portfolio UI (`/user`).
- `callbacks/`
  - `sign_in_callbacks.py`: navigation logic from the landing page into user mode.
  - `dashboard_callbacks.py`: “roll dice” logic and updating the dashboard graph + table.
  - `user_callbacks.py`: hydrating user state and handling buy/sell/add-cash actions.

## Routes (pages)

1. `/` (`pages/sign_in.py`)
   - Input: `username-input`
   - Buttons: `Enter User Mode` and `Go to Dashboard`
   - The username becomes a query parameter like `/user?name=Alex`.

2. `/dashboard` (`pages/dashboard.py`)
   - Shows a table of stock prices (one row per commodity).
   - Shows a bar chart of the same prices.
   - Has a `Roll Dice` button that randomly:
     - picks a stock,
     - chooses an action: `Up`, `Down`, or `Dividend`,
     - changes the stock price by `0.05`, `0.10`, or `0.20`.

3. `/user` (`pages/user.py`)
   - Shows:
     - balance,
     - net value,
     - share holdings per commodity.
   - Lets you:
     - select a commodity from `stock-select`,
     - buy or sell a fixed number of shares (buttons for `100`, `500`, `1000`, `5000`),
     - add cash via `cash-input` + `Add Cash`.

## How navigation works

`main.py` creates a top-level layout with:

- `dcc.Location(id="url", refresh="callback-nav")`
- `dcc.Store(id="nav-store", storage_type="memory")`
- a `page_container` that renders the registered pages.

Flow:

- `callbacks/sign_in_callbacks.py` updates `nav-store` when you click navigation buttons on `/`.
- `main.py` has a callback that listens to `nav-store` and sets `url.pathname` to switch pages.

The result is:

- “Enter User Mode” navigates to `/user?name=<username>`
- “Go to Dashboard” navigates to `/dashboard`

## How stock prices are stored and shared

The dashboard uses a module-level dictionary in `callbacks/dashboard_callbacks.py`:

- `stock_prices = {commodity: 1.00, ...}`

When you roll the dice, that dictionary is updated and then persisted on the server via:

- `dash.get_app().server.config['STOCK_PRICES']`

Why this matters:

- The **user** page calculates net value using the **current dashboard prices**.
- User page callbacks read from the server config (`STOCK_PRICES`), so they reflect dashboard rolls without needing a real database.

Persistence behavior:

- Prices persist **for as long as the Dash server process is running**.
- Restarting the server resets prices back to `1.00` per commodity (unless you change the code to persist them elsewhere).

When a roll moves a stock’s price to **2.00 or higher**, that commodity’s price is reset to **1.00** and **every user’s shares** of that commodity are **doubled** (see `callbacks/dashboard_callbacks.py` and `USER_STATE`). When a roll moves a price to **0 or below**, the price resets to **1.00** and **everyone’s shares** of that commodity are set to **0**.

**Dividends:** If the dice show **Dividend** for a stock, that stock’s **price at the time of the roll** must be **at or above par ($1.00)** or no dividend is paid. If it is at/above par, each player’s **cash balance** increases by **shares held × value**, where `value` is the same dice amount used for Up/Down moves (`0.05`, `0.10`, or `0.20`). A Dividend roll does **not** change the stock price.

## How user portfolio state works

Portfolios are stored **on the server** in Flask `server.config["USER_STATE"]` (see `callbacks/user_callbacks.py`):

- `username -> { balance: float, stocks: {commodity: int} }`

The username comes from the `name` query parameter on `/user` (e.g. `/user?name=Alex`). If no name is given, the key `__anonymous__` is used.

- **Same name, same portfolio everywhere**: any device that opens `/user?name=<same>` talks to the same in-memory record on that server.
- **Restart clears everyone**: stopping the Python process removes `USER_STATE` (and in-memory stock prices). After a restart, each user starts from the default balance and zero shares until they trade again.

Hydration runs when the user page loads (URL change or initial load). Buy/sell/add-cash actions update the server-side map via `handle_user_actions`. The app also polls server stock prices on a short interval (`main.py`) so balance, share counts, and net value refresh automatically when the dashboard dice (or dividends/splits) change server state—no manual page refresh required.

## Running locally

1. Create/activate a virtual environment (optional but recommended).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the server (uses **Waitress**, a threaded WSGI server suitable for several phones on the same Wi‑Fi):

```bash
python main.py
```

4. Open the app:

- On the host machine: `http://127.0.0.1:8050/`
- On other devices on the LAN: `http://<host-ip>:8050/` (same port; firewall must allow inbound TCP 8050).

**Important:** Game state lives in **one Python process** (`server.config`). Use **one** server process only (do not run multiple `python main.py` or multiple copies of the executable expecting a shared game). For many concurrent clients, use **one** Waitress process with multiple **threads** (defaults are set in `constants.py`: `WAITRESS_THREADS`, `PRICE_POLL_INTERVAL_MS`).

**Linux / macOS (alternative):** you can serve the same app with Gunicorn using a **single worker** and multiple threads, for example:

```bash
gunicorn -w 1 -k gthread --threads 16 -b 0.0.0.0:8050 main:server
```

(Requires `pip install gunicorn` and a `main:server` export — see `main.py`.)

## Build Windows executable (portable folder)

This project includes a PowerShell build script for a Windows `onedir` bundle. The executable runs the same entry point as `python main.py` (Waitress on port 8050); PyInstaller bundles `waitress` from `requirements.txt`.

```powershell
.\build_exe.ps1
```

Build output:

- Executable folder: `dist/StockTickerDashboard/`
- Executable: `dist/StockTickerDashboard/StockTickerDashboard.exe`

Run:

```powershell
.\dist\StockTickerDashboard\StockTickerDashboard.exe
```

Then open (same as a source run):

- On the host: `http://127.0.0.1:8050/`
- Other devices: `http://<host-ip>:8050/`

Session persistence location for the executable build:

- `dist/StockTickerDashboard/data/session_state.json`
- Crash snapshots: `dist/StockTickerDashboard/data/session_crash_*.json`

To run on another Windows computer, copy the entire `dist/StockTickerDashboard` folder and run `StockTickerDashboard.exe` there.

## GitHub Actions release build

This repo now supports automated Windows executable releases via GitHub Actions.

- Workflow file: `.github/workflows/release.yml`
- Trigger options:
  - Push a tag that starts with `v` (example: `v1.0.0`)
  - Manually run workflow (`workflow_dispatch`) and provide a tag
- Output release asset:
  - `StockTickerDashboard-windows.zip` (contents of `dist/StockTickerDashboard`)

Tag example:

```bash
git tag v1.0.0
git push origin v1.0.0
```

## Notes / limitations

- App state is kept in server memory during runtime (`server.config`) and saved to JSON on shutdown and after trades (buy/sell/add cash writes are **debounced** briefly to reduce disk contention when many players trade at once).
- For source runs (`python main.py`), session data is written under `data/session_state.json` in the project directory.
- For executable runs, session data is written under the executable folder (`dist/StockTickerDashboard/data/session_state.json`).
- If you run multiple **worker** processes (e.g. Gunicorn `workers > 1`), each worker has separate in-memory state; this app expects **one** process. Use a shared database if you ever shard workers.
