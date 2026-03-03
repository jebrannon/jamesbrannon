# James Brannon

Personal portfolio site — [jebrannon.github.io](https://jebrannon.github.io)

## Stack

- **Vite** — dev server and build tool
- **LESS** — CSS preprocessing
- **Vanilla JS** — no framework dependencies

## Requirements

- Node 20+ (use [nvm](https://github.com/nvm-sh/nvm))

## Installation

```bash
nvm use
npm install
```

## Development

```bash
npm run dev
```

Starts a local dev server at `http://localhost:3000` with hot module replacement.

## Build

```bash
npm run build
```

Outputs a production-ready bundle to `dist/`.

## Preview build

```bash
npm run preview
```

Serves the `dist/` build locally for final checks before deploying.

## Project structure

```
├── index.html
├── public/
│   └── images/
├── src/
│   ├── js/
│   │   └── main.js
│   └── less/
│       ├── _base/
│       ├── _layout/
│       ├── _mixins/
│       ├── _theme/
│       └── main.less
└── vite.config.js
```
