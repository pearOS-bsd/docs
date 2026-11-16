# Solarium (Liquid Glass)

Repository: github.com/pearOS-bsd/Solarium (layer 3, above QuartzCore, below AppKit; BSD-2).

What is established (evidence in the repository, `docs/`):
- Architecture: `CASDFLayer` + effects (`CASDFGlassDisplacementEffect`, `CASDFGlassHighlightEffect` ...), defaults read from the real classes (`tools/sdf-defaults.m`).
- `CA::OGL::GlassBackgroundFilter::render` (QuartzCore): ~50 numeric filter keys with Apple's defaults, packed into the shader constants.
- 18 of 18 glass Metal shaders (`glass_background*`, `glass_foreground*`, `displacement_map`, `sdf_gen_*`) translate to valid SPIR-V with metal2vulkan (GPL-2+/LGPL-3+ tool, used only as a tool).

How the evidence was obtained (repeatable): dyld cache copied from the Mac VM to `~/.pear/dsc`, `ipsw dyld extract <cache> QuartzCore`, opened in REA; metallib files copied from the Mac (never committed); `metal2vulkan` built with nightly-2026-11-03; SPIRV-Tools v2026.4 for `spirv-val` (the distro one is too old for the FMA capability).

Not done: key names, `GlassForegroundFilter`, run on a GPU, pixel comparison with the Mac, AppKit `NSGlassEffectView` / `GlassMaterialProvider` mapping.
