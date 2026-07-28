# Previewer sample assets

These files are project-owned geometric fixtures for exercising the public
Previewer. They are not derived from a contributor's pet, artwork, photographs,
or private project. They are generated deterministically by the checked-in
script without a generative model or third-party artwork.

The bundled `v002` sample uses the approved smooth silhouette and includes:

- one static v2 spritesheet used by Runtime Simulation and frame inspection;
- one native exported GIF for every standard state used by GIF Loop.

Regenerate the assets with the bundled Pillow-capable Python runtime:

```bash
python previewer/sample-assets/generate_sample_assets.py
```

The source and generated fixtures are distributed under the repository license.
