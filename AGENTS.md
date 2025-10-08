# Agent Guidelines

## Mission
This repository hosts an open source Blender add-on that generates three-view renders for the currently selected collection.

## Communication Rules
- Agents must reason in English while composing responses.
- Agents must deliver all user-facing responses in Japanese.
- All repository documentation must be written in English.

## Rendering Requirements
- Produce orthographic front, side, and top views for the active collection.
- Render with a transparent background to simplify downstream compositing.
- Use the Eevee engine to prioritize fast turnaround over path-traced accuracy.
- Configure lighting for a flat, neutral look that preserves surface color without directional shadows.

## Engineering Practices
- Keep the add-on modular with responsibilities separated across well-named files.
- Favor readable, maintainable code with clear function boundaries and minimal duplication.
- Document public APIs and non-obvious decisions directly in English within the source.
- Validate behavior with automated checks when feasible before publishing changes.

## Release Discipline
- Ensure new features do not degrade render speed or lighting neutrality benchmarks.
- Review contributions for adherence to the communication and rendering rules prior to merge.
