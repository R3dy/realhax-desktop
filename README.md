# realhax-desktop

![realhax wallpaper](assets/wallpaper.png)

One script that turns a Linux machine into the **realhax Linux** desktop: dark XFCE, neon red ring wallpaper, top panel, bottom dock, conky "System" / "Lab Info" widgets, alacritty + fish, and a fastfetch card.

## One-shot install

```bash
curl -fsSL https://raw.githubusercontent.com/R3dy/realhax-desktop/main/install.sh | bash
```

Run it as your normal user. It asks for your sudo password once, to install packages. When it finishes, log out, pick **Xfce Session** on the login screen, and log in.

Options go after `bash -s --`:

```bash
curl -fsSL https://raw.githubusercontent.com/R3dy/realhax-desktop/main/install.sh | bash -s -- --no-apps
```

| Option | Effect |
|---|---|
| `--no-apps` | skip VS Code and Wireshark (VS Code needs Microsoft's package repository) |
| `--keep-session` | don't make XFCE the default login session |
| `--skip-packages` | user-level config only, no sudo |
| `--restore` | put back every file the installer replaced |

To read the script before running it:

```bash
git clone https://github.com/R3dy/realhax-desktop && cd realhax-desktop
less install.sh && bash install.sh
```

Primary target: Ubuntu 24.04. The script also has package maps for Debian/Ubuntu derivatives (apt), Fedora (dnf), Arch (pacman) and openSUSE (zypper).

## What it does

| Step | Result |
|---|---|
| Packages (apt / dnf / pacman / zypper) | XFCE 4.18, whiskermenu, plank, conky, Papirus, Inter, alacritty, fish, rsvg, sassc (+ VS Code and Wireshark). Packages a distro doesn't have are skipped with a warning. On apt it uses `--no-install-recommends`, so your display manager stays as it is. |
| Fonts | JetBrainsMono Nerd Font v3.4.0 (sha256-pinned) if missing |
| fastfetch | pinned 2.40.4 static build if missing; `neofetch` maps to it |
| GTK + xfwm4 theme | Orchis `2025-04-25` (sha256-pinned), red, black tweak, installed as **RealHax-Dark** |
| Icons | **RealHax** theme: inherits Papirus-Dark, adds red folders, red home, realhax logo, terminal icon |
| Wallpaper | `assets/wallpaper.png` (sha256-pinned), set on every monitor |
| Panel | top bar: logo + "Applications" menu, tray, notifications, volume, `Mon Oct 26  21:39` clock, power |
| Desktop | Home, Terminal, Tools, Recon, Reports, Trash |
| Dock | plank, RealHax theme: Terminal, Files, Firefox, VS Code, Editor, Wireshark, app grid |
| Widgets | conky System (CPU, memory, disk, network graphs) and Lab Info (Attacker turns green when `tun0` is up, IP, OS, uptime) |
| Terminal | alacritty RealHax palette; prompt `user@host ~` with a blue path tag and a `❯` line (fish function, or starship via `STARSHIP_CONFIG` inside alacritty) |

## Determinism

- Every download is pinned to a version and checked against a sha256. A mismatch aborts the install.
- XFCE settings are written straight to the xfconf XML files, so the first login always looks the same.
- At each XFCE login, `realhax-session-init` points the wallpaper at whatever monitor names that machine has.
- Re-running is safe. Originals are backed up once, the first time a file is replaced, under `~/.local/share/realhax/backup`, and listed in `manifest.txt`.

## Rebuilding

`install.sh` is generated. Edit `tools/install.sh.in`, then run `tools/build.sh`. If you replace `assets/wallpaper.png`, update `WALLPAPER_SHA256` to match.

## Known gaps vs. the mockup

- Plank sits flush on the screen edge, not floating.
- Conky boxes have square corners.
- "Open Lab Guide" is a label, not a button.
- The "M" shield app in the mock dock isn't included.
- The user and host name stay your own (the mock shows `student@realhax`).
