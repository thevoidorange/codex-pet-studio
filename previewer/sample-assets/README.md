# Previewer sample assets

These files are project-owned geometric fixtures for exercising the public
Previewer. They are not derived from a contributor's pet, artwork, photographs,
or private project. They are generated deterministically by the checked-in
script without a generative model or third-party artwork.

The bundled `v002` sample uses the approved smooth silhouette and includes:

- one static v2 spritesheet used by Runtime Simulation and frame inspection;
- optional exported GIFs retained only as deterministic QA artifacts.

The public Previewer does not play these GIFs. Runtime Simulation and Endless
Loop both render the source spritesheet at the fixed current-client cadence, so
palette quantization or GIF edge artifacts cannot distort visual review.

Regenerate the assets with the bundled Pillow-capable Python runtime:

```bash
python previewer/sample-assets/generate_sample_assets.py
```

The source and generated fixtures are distributed under the repository license.
