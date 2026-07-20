# Dankfrankest reference — design spec for ProjectEmergence
Source: 39 clips (dankfrankest devlogs), analyzed with qwen2.5vl:7b + OCR of his
on-screen commentary. Raw per-clip breakdowns in `clip_analysis/`.
His game = a stealth/tactical shooter; his devlogs directly model what we want.

## 1. LEVEL DESIGN (what to build in the test level)
- **Greybox facilities**: indoor utilitarian/industrial spaces — labs, warehouses,
  offices. **Checkered/tiled floors** = the greybox test-room look (matches our
  current build). Warm-tiled walls.
- **Cover language**: columns/pillars, crates/boxes, low walls, platforms, furniture.
  Cover is placed to create sightline breaks, not just decoration.
- **Verticality**: multiple levels connected by stairs/platforms; mantling to climb.
- **Layout**: rooms connected by corridors + open arena sections; mix of tight
  (corridors, corners) and open (arenas) so stealth AND firefights both work.
- **Also seen**: night urban / Middle-Eastern exteriors (flat-roof low buildings,
  minimal cover, string lights) and his own open desert w/ solar panels (like ours).
- **Takeaway for our room**: don't leave it empty — add columns + crates for cover,
  a second level with stairs, and 1-2 corridors feeding a central open space.

## 2. LIGHTING & STEALTH (core pillar)
- **Breakable lights**: "Lights can now be broken — but weigh your options carefully."
  Shooting out lights creates darkness = player-created stealth. KEY mechanic.
- **Flashlights**: both player and **NPC flashlights** with directional cones that
  drive detection; flashlight has on/off state tied to gameplay.
- **Dark maps / hiding spots**: "pick your hiding spots", "model in the dark maps".
  Light vs shadow is the stealth playing field — lit = exposed, dark = safe.
- **Takeaway**: light placement IS level design. Build lit patrol lanes + dark
  pockets of cover. Make lights breakable.

## 3. STEALTH / TRAVERSAL MECHANICS
- **Crouch / sneak** (player movement states).
- **Mantle** (Space Bar) to climb ledges/cover.
- **Throw items to distract**: NPCs investigate where an item was thrown from /
  landed ("where the item was thrown from", disturbance location).
- **Cover & corners**: objects obstruct sightlines; corners break line of sight.

## 4. NPC AI BEHAVIOR (the standout — his main focus)
- **Vision-based detection**: NPCs detect via actual line-of-sight; **obstructions
  and corners block vision** ("object is obstructing the character's [view]").
  Detection is NOT omniscient — "disabled for targets that have not been seen."
- **Search / last-known-position**: when they lose a target they **estimate its
  location** and **path to investigate** ("he will estimate location", "path
  creation system"). "How do NPCs know where to look — searches for a lost [target]."
- **Squad coordination (point-man/POI)**: nearest NPC = point-man per POI, others
  support; after **a squad completely clears an area**, they re-target and go
  **investigate disturbances**. (See [[REFERENCE_NPC_SQUAD_AI]].)
- **Investigate disturbances**: thrown items, noises, broken lights → NPCs converge
  on the disturbance location.
- **VIP system**: designate a protect/priority NPC target.
- **Detection tuning**: longer on-screen "spotted" flashes before locations reveal.

## 5. COMBAT / PHYSICS (supporting)
- Realistic **bullet drop** + per-weapon **projectile speed** (must lead targets).
- **Ragdoll / collapsing** physics for downed NPCs.
- Health **regen** system.

## BUILD PRIORITY for ProjectEmergence (test level first)
1. **Finish the greybox room** → add cover (columns + crates), a second level w/
   stairs, 1-2 corridors into a central arena. (In progress now.)
2. **Lighting pass**: place lit patrol lanes + dark cover pockets; make key lights
   breakable.
3. **NPC AI v1**: line-of-sight detection with obstruction, last-known-position
   search + investigate, then squad point-man/POI clearing.
4. **Player stealth kit**: crouch, mantle, throwable distraction.
5. Layer in combat/physics (bullet drop, ragdoll) after the stealth loop works.
