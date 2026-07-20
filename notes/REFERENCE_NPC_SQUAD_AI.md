# Reference — NPC Squad Strategy (point-man system)
Source: Instagram, dankfrankest / josephgormley ("NPC Squad Strategy")
Captured: coaching session 2026-07-19

## The core idea to copy
NPCs currently look uncoordinated. Fix with a **point-man / POI system**:
1. At any moment there are usually only **1–3 priority POIs** to check.
2. The **nearest NPC becomes the point-man** for each POI.
3. Additional NPCs **join up to support** a point-man (not scatter).
4. After a POI is cleared, **re-choose point-men** for the next 1–3 POIs.
Result: squads read as coordinated, cover priority spots, avoid predictability.

## Reference environment (for the test room)
Indoor tactical facility: tiled floors/walls, tables & chairs as cover, dim
focused ceiling lighting → tense/stealth mood.

## How this maps to our build
- The **big test room** (in progress: 3000×3000 floor) = the arena to prototype
  this squad AI. Add cover (tables/crates) → define 1–3 POIs → spawn NPCs →
  implement point-man assignment + support + re-selection on clear.
- Next build steps once room is done: (a) place cover objects, (b) mark POIs,
  (c) NPC blueprint with point-man/support state machine.
