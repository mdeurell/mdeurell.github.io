# Jekyll + Tailwind starter

Dette er et minimalt GitHub Pages/Jekyll-setup med:

- `_includes/head.html`
- `_includes/nav.html`
- `_includes/header.html`
- `_includes/content.html`
- `_includes/footer.html`
- `assets/css/styles.css`
- `_config.yml`

## Struktur

```text
.
├─ _config.yml
├─ _includes/
│  ├─ content.html
│  ├─ footer.html
│  ├─ head.html
│  ├─ header.html
│  └─ nav.html
├─ assets/
│  └─ css/
│     └─ styles.css
└─ index.html
```

## Bemærkning om Tailwind

Denne starter bruger Tailwind via browser/CDN-script for at holde setup simpelt på GitHub Pages.
Hvis du senere vil bygge Tailwind lokalt med CLI eller Vite, kan strukturen stadig bruges som udgangspunkt.
