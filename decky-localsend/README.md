<div align="center">

<img src=".github/assets/send-to-back.svg" width="128" height="128" alt="Decky Localsend" />

# Decky Localsend

![visitors](https://visitor-badge.laobi.icu/badge?page_id=moyoez/Decky-localsend) ![Release](https://img.shields.io/github/v/release/moyoez/decky-localsend) ![License](https://img.shields.io/badge/license-BSD--3--Clause-green) ![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/MoYoez/Decky-Localsend/build.yaml)



<p>
  <img src="https://forthebadge.com/api/badges/generate?panels=2&primaryLabel=Build+With&secondaryLabel=+Go&primaryBGColor=%23f79102&primaryTextColor=%23ffffff&secondaryBGColor=%23389AD5&secondaryTextColor=%23ffffff&primaryFontSize=12&primaryFontWeight=600&primaryLetterSpacing=2&primaryFontFamily=Roboto&primaryTextTransform=uppercase&secondaryFontSize=12&secondaryFontWeight=900&secondaryLetterSpacing=2&secondaryFontFamily=Montserrat&secondaryTextTransform=uppercase&borderRadius=9" alt="Build With Go" style="vertical-align:middle;"/>
  <span style="display:inline-block; width:32px;"></span>
  <img src="https://forthebadge.com/api/badges/generate?panels=2&primaryLabel=Work+On&secondaryLabel=Steam+Deck&primaryBGColor=%23000000&primaryTextColor=%23ffffff&secondaryBGColor=%23389AD5&secondaryTextColor=%23ffffff&primaryFontSize=12&primaryFontWeight=600&primaryLetterSpacing=2&primaryFontFamily=Roboto&primaryTextTransform=uppercase&secondaryFontSize=12&secondaryFontWeight=900&secondaryLetterSpacing=2&secondaryFontFamily=Montserrat&secondaryTextTransform=uppercase&borderRadius=9" style="vertical-align:middle;"/>
</p>

[ENGLISH](README.md) | [简体中文](README-ZH-CN.md)

![preview](https://raw.githubusercontent.com/moyoez/decky-localsend/main/.github/assets/preview.jpg)

A Decky Loader plugin that brings LocalSend functionality to Steam Deck gaming mode.

Related Backend Repo: [MoYoez/localsend-go](https://github.com/MoYoez/localsend-go)

</div>

---

## Features

- Full LocalSend protocol support (except Web LocalSend)
- "Shared Via Link" for one-way file transfer via link
- Upload and browse screenshots
- Some unique LocalSend features (e.g., accepting previous transfer list,  PINs, handling HTTP/HTTPS in certain environments)

## Demo

![preview_en_1](.github/assets/preview_en_1.jpg)
![preview_en_2](.github/assets/preview_en_2.jpg)
![preview_en_3](.github/assets/preview_en_3.jpg)
![preview_en_4](.github/assets/preview_en_4.jpg)

## Usage

> This plugin requires Decky Loader 3.0 or above.

1. On your Steam Deck, install the plugin:
   - Download the latest release from the releases page
   - Or, get the beta version from the Decky test store (Decky Localsend 0.37-1a47753)
   - Or, install using a URL in Decky by entering:

     > https://ba.sh/63Vg

> Decky not installed?｜ Refer to [Decky-Loader](https://github.com/SteamDeckHomebrew/decky-loader) for help | If necessary, search [Youtube](https://www.youtube.com/watch?v=USnS9K0fpQM) for help.

1. Open the plugin from the Quick Access menu
2. The LocalSend server will start automatically when clicking start Backend
3. Your Steam Deck will now be discoverable by other LocalSend clients
4. Send files from any device running LocalSend to your Steam Deck

## Configuration

The plugin uses the following default settings:

- **Port:** 53317
- **Protocol:** HTTPS
- **Upload Directory:** `~/homebrew/data/decky-localsend/uploads`
- **Config File:** `~/homebrew/settings/decky-localsend/localsend.yaml`

You can customize these settings through the plugin interface.

## Project Structure

```
.
├── backend/             # Go backend implementation
│   └── localsend/       # LocalSend protocol implementation
├── src/                 # Frontend React components
│   ├── index.tsx        # Main plugin entry
│   └── utils/           # Utility functions
├── main.py              # Python backend bridge
├── plugin.json          # Plugin metadata
└── package.json         # Node.js dependencies
```

## TODO

- None

## Known Issues

- Sometimes plugin cannot detect other machine ( (30s a time automaticlly , default timeout is 500s, can use **Scan Now** To Detect other client ) .If not found, consider restarting remote localsend client.)

- Plugins can only work in same transfer protocol sometimes, although it has detect method to prevent transfer connection failed.

- When transferring a very large number of files (tested with 3000+ files) to the Deck, the sending side of LocalSend may appear to stutter or become choppy due to multiple running threads. However, this does not affect the actual file transfer.

- HTTP scanning may cause increased latency. HTTP timeout has been set to 60 seconds and runs every 30 seconds by default. Devices are updated via Notify, so you do not need to manually refresh to see remote devices.

- please consider not to transfer too much files(selected), which may cause UI crash,folder dont' effect.

### Compatibility Table

| Communication Method | Decky-Localsend Supported | Discoverable Remote Localsend Devices | Notes                                       |
|---------------------|---------------------------|---------------------------------------|---------------------------------------------|
| UDP Scan            | HTTP/HTTPS                | HTTP, HTTPS                           | UDP can discover devices with any protocol. |
| HTTP Communication  | HTTP                      | HTTP                                  | Only devices with HTTP protocol are supported. |
| HTTPS Communication | HTTPS                     | HTTPS                                 | Only devices with HTTPS protocol are supported. |

> With UDP communication, Decky-Localsend can discover remote devices regardless of whether their protocol is HTTP or HTTPS.

## Development

```bash

# Fork YOURSELF REPO, replace {username} as your "username"

git clone --recurse-submodules git@github.com:{username}/Decky-Localsend.git

cd Decky-Localsend/backend/localsend

# require Golang >= 1.25.7

go mod tidy

cd Decky-Localsend/backend/localsend/web

# require NodeJS > 20

npm i

npm build


```

### Build

Please refer to [Github Action Build](.github/workflows/build.yaml)

## Acknowledgments

- [LocalSend](https://localsend.org)

> This Plugin is based on Localsend Protocol, so pls give a star to this!

- [Decky Loader](https://github.com/SteamDeckHomebrew/decky-loader)

- [ba.sh](https://app.ba.sh/)