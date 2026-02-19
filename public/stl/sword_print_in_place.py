import cadquery as cq

# ==========================================
# Telescopic Sword - Print-in-Place
# ==========================================
# All 3 parts printed nested inside each other.
# After printing, wiggle/twist to break free.
#
# Cross-section (looking from top):
#
#   ╭──────────────────────╮  Handle (outer)
#   │ ╭──────────────────╮ │
#   │ │ ╭──────────────╮ │ │
#   │ │ │   Tip (core)  │ │ │  Middle
#   │ │ ╰──────────────╯ │ │
#   │ ╰──────────────────╯ │
#   ╰──────────────────────╯
#
# Side view (collapsed, print orientation):
#
#   ┌─lip──┐
#   │┌lip─┐│
#   ││┌──┐││
#   │││  │││  ← all nested, standing upright
#   │││  │││
#   ││├══┤││  ← tip ridge (inside middle)
#   │├╪══╪┤│  ← middle ridge (inside handle)
#   ├┤│  │├┤
#   ╚═╧══╧═╝  ← handle closed bottom

# --- Parameters ---
TOLERANCE = 0.35         # Slightly more gap for print-in-place
WALL = 1.5
SECTION_LENGTH = 170.0
OVERLAP = 30.0
RIDGE_HEIGHT = 1.2       # Slightly smaller for print-in-place
RIDGE_LENGTH = 3.0

# --- Crossguard ---
CROSSGUARD_WIDTH = 70.0    # Total width of crossguard (side to side)
CROSSGUARD_THICK = 8.0     # Thickness of crossguard bar
CROSSGUARD_CURVE = 15.0    # How much the ends curve upward

# --- Diameters ---
HANDLE_OD = 22.0
HANDLE_ID = HANDLE_OD - 2 * WALL

MID_OD = HANDLE_ID - 2 * TOLERANCE
MID_ID = MID_OD - 2 * WALL

TIP_OD = MID_ID - 2 * TOLERANCE


def create_handle():
    """Handle: hollow cylinder, closed bottom, inward lip at top."""
    # Main tube
    handle = (
        cq.Workplane("XY")
        .circle(HANDLE_OD / 2)
        .circle(HANDLE_ID / 2)
        .extrude(SECTION_LENGTH)
    )

    # Closed bottom
    cap = (
        cq.Workplane("XY")
        .circle(HANDLE_OD / 2)
        .extrude(WALL)
        .translate((0, 0, -WALL))
    )
    handle = handle.union(cap)

    # Grip grooves
    for i in range(6):
        z = 10.0 + i * 8.0
        groove = (
            cq.Workplane("XY")
            .workplane(offset=z)
            .circle(HANDLE_OD / 2 + 1)
            .circle(HANDLE_OD / 2 - 0.8)
            .extrude(2.0)
        )
        handle = handle.cut(groove)

    # Inward lip at top (catches middle's ridge)
    lip = (
        cq.Workplane("XY")
        .workplane(offset=SECTION_LENGTH - RIDGE_LENGTH)
        .circle(HANDLE_ID / 2)
        .circle(HANDLE_ID / 2 - RIDGE_HEIGHT)
        .extrude(RIDGE_LENGTH)
    )
    handle = handle.union(lip)

    # Curved crossguard at the top of the grip area
    guard_z = SECTION_LENGTH * 0.55
    half_w = CROSSGUARD_WIDTH / 2

    # Sweep an oval cross-section along a curved path
    # Path: arc from left tip, through center, to right tip
    guard_path = (
        cq.Workplane("XZ")
        .moveTo(-half_w, guard_z + CROSSGUARD_CURVE)
        .threePointArc(
            (0, guard_z),                          # middle point (lowest)
            (half_w, guard_z + CROSSGUARD_CURVE)   # right end (curves up)
        )
    )

    # Sweep an elliptical cross-section along the path
    guard = (
        cq.Workplane("YZ")
        .workplane(offset=-half_w)
        .transformed(offset=(0, guard_z + CROSSGUARD_CURVE, 0))
        .ellipse(CROSSGUARD_THICK / 2, CROSSGUARD_THICK / 2)
        .sweep(guard_path)
    )

    handle = handle.union(guard)

    return handle


def create_middle():
    """Middle: hollow cylinder, outward ridge at bottom, inward lip at top."""
    middle = (
        cq.Workplane("XY")
        .circle(MID_OD / 2)
        .circle(MID_ID / 2)
        .extrude(SECTION_LENGTH)
    )

    # Outward stop ridge at bottom
    ridge = (
        cq.Workplane("XY")
        .circle(MID_OD / 2 + RIDGE_HEIGHT)
        .circle(MID_ID / 2)
        .extrude(RIDGE_LENGTH)
    )
    middle = middle.union(ridge)

    # Inward lip at top (catches tip's ridge)
    lip = (
        cq.Workplane("XY")
        .workplane(offset=SECTION_LENGTH - RIDGE_LENGTH)
        .circle(MID_ID / 2)
        .circle(MID_ID / 2 - RIDGE_HEIGHT)
        .extrude(RIDGE_LENGTH)
    )
    middle = middle.union(lip)

    return middle


def create_tip():
    """Tip: solid rod, outward ridge at bottom, pointed top."""
    tip = (
        cq.Workplane("XY")
        .circle(TIP_OD / 2)
        .extrude(SECTION_LENGTH)
    )

    # Pointed cone
    point_length = 30.0
    point = (
        cq.Workplane("XY")
        .workplane(offset=SECTION_LENGTH)
        .circle(TIP_OD / 2)
        .workplane(offset=point_length)
        .circle(1.0)
        .loft()
    )
    tip = tip.union(point)
    tip = tip.edges(">Z").fillet(0.8)

    # Outward stop ridge at bottom
    ridge = (
        cq.Workplane("XY")
        .circle(TIP_OD / 2 + RIDGE_HEIGHT)
        .extrude(RIDGE_LENGTH)
    )
    tip = tip.union(ridge)

    return tip


def create_print_in_place():
    """
    All parts nested in collapsed position.

    The ridges sit inside the tolerance gaps:
    - Middle's bottom ridge sits just above handle's bottom cap
    - Tip's bottom ridge sits just above middle's bottom
    - Handle's top lip is above middle's top lip
    - Middle's top lip is above tip's top

    The key: ridges are BETWEEN the lips, so parts can
    slide but not fall out.
    """
    print(f"  Handle: OD={HANDLE_OD}, ID={HANDLE_ID}")
    print(f"  Middle: OD={MID_OD}, ID={MID_ID}")
    print(f"  Tip:    OD={TIP_OD}")
    print(f"  Tolerance: {TOLERANCE}mm per side")

    # Handle sits at Z=0 (bottom cap at Z=-WALL)
    handle = create_handle()
    handle = handle.translate((0, 0, WALL))  # Move so bottom cap is at Z=0

    # Middle nested inside handle
    # Position so its bottom ridge is just above handle's bottom cap
    # Leave a small gap (1mm) above the bottom
    middle = create_middle()
    middle = middle.translate((0, 0, WALL + 1.0))

    # Tip nested inside middle
    # Position similarly
    tip = create_tip()
    tip = tip.translate((0, 0, WALL + 2.0))

    # Combine all parts into one STL (they're separate bodies with gaps)
    result = cq.Workplane().add(handle.objects).add(middle.objects).add(tip.objects)
    return result


def create_exploded_view():
    """Side-by-side exploded view showing all parts."""
    spacing = HANDLE_OD + 15

    handle = create_handle()
    handle = handle.translate((-spacing, 0, WALL))

    middle = create_middle()

    tip = create_tip()
    tip = tip.translate((spacing, 0, 0))

    result = cq.Workplane().add(handle.objects).add(middle.objects).add(tip.objects)
    return result


if __name__ == "__main__":
    print("Creating Telescopic Sword - Print-in-Place\n")

    # Print-in-place version (nested)
    print("Nested (print-in-place):")
    nested = create_print_in_place()
    cq.exporters.export(nested, "sword_nested.stl")
    print("  Exported: sword_nested.stl\n")

    # Exploded view for reference
    print("Exploded view:")
    exploded = create_exploded_view()
    cq.exporters.export(exploded, "sword_exploded.stl")
    print("  Exported: sword_exploded.stl\n")

    print("Print-in-place tips:")
    print("  - Print upright (standing)")
    print("  - Layer height: 0.2mm")
    print("  - Infill: 15-20%")
    print("  - NO supports (the gaps are the tolerance)")
    print("  - After printing, twist & wiggle to free the parts")
    print("  - If stuck, run warm water over it to soften slightly")
    print("Done!")
