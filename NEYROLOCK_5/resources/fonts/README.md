# Onest UI fonts

The application bundles Onest Regular 400 and Bold 700 for identical
typography on desktop, PWA, Android, iOS, and the public landing page.

- Upstream variable font: `google/fonts/ofl/onest/Onest[wght].ttf`
- Upstream version: `2.001`
- Upstream SHA-256: `966c5c29b4755da84b6854d5c21dd4eaa2420225d0e9874de602de176d4a9f31`
- Static instances: generated at `wght=400` and `wght=700` with
  `fontTools.varLib.instancer` 4.59.1.
- The Bold instance's standard name/weight metadata was normalized to
  `Onest Bold`, PostScript name `Onest-Bold`, OS/2 weight 700.
- License: SIL Open Font License 1.1; see `OFL.txt`.

The application code must use the family name `Onest` and only weights 400
and 700. Do not rename the files without updating desktop, PWA, Android, iOS,
packaging, deployment, and their focused tests together.
