from boxes import *
from boxes import edges
from math import pi, sin, ceil
import numpy as np

class Axle(Boxes):
    """Axle generator for filament spools with hexagonal rings and side panels."""
    def __init__(self):
        super().__init__()
        self.addSettingsArgs(edges.FingerJointSettings)
        self.axle_debug = True
        self.debug_labels = True
        if self.axle_debug: print("FingerJointSettings accessed.")
        self.argparser.add_argument("--axle_outer_diameter", type=float, default=70.0, help="Outer diameter (mm)")
        self.argparser.add_argument("--total_length", type=float, default=575.0, help="Total length (mm)")
        self.argparser.add_argument("--material_length", type=float, default=410.0, help="Max segment length (mm)")
        self.argparser.add_argument("--pass_through_diameter", type=float, default=48.0, help="Inner diameter (mm)")
        self.argparser.add_argument("--sides", type=int, default=6, help="Number of sides")
        self.argparser.add_argument("--recess_depth", type=float, default=12.0, help="Recess depth (mm)")
        self.argparser.add_argument("--max_spacing", type=float, default=150.0, help="Max ring spacing (mm)")

    def set_text_engrave(self): self.ctx.save(); self.ctx.set_source_rgb(0, 0, 1)
    def reset_cut(self): self.ctx.set_source_rgb(0, 0, 0); self.ctx.restore()

    def populate_holes(self, piece_lengths, ring_positions, total_length, order="forward"):
        """Generate hole positions, adjusting rings to avoid joints."""
        if self.axle_debug: print(f"Generating holes in {order} order")
        t, num_pieces = self.thickness, len(piece_lengths)
        pieces_holes, max_holes = [], 0
        piece_indices = range(num_pieces) if order == "forward" else range(num_pieces - 1, -1, -1)
        ring_positions_adjusted, adjustments = ring_positions.copy(), {}

        safety_zone = (2 * t) + t
        for j in piece_indices:
            piece_length = piece_lengths[j]
            subtract_value = sum(piece_lengths[:j]) - (j * t) if order == "forward" else total_length - sum(piece_lengths[j + 1:]) - (j * t)
            if self.axle_debug: print(f"Piece {j}: length = {piece_length:.2f} mm, subtract_value = {subtract_value:.2f}")
            piece_holes = []
            start_pos, end_pos = subtract_value if order == "forward" else subtract_value - piece_length, subtract_value + piece_length
            for idx, ring_pos in enumerate(ring_positions):
                if start_pos <= ring_pos < end_pos:
                    relative_pos = ring_pos - start_pos
                    if order == "forward":
                        min_pos, max_pos = max(self.recess_depth, safety_zone), piece_length - max(safety_zone, self.recess_depth)
                        if not (min_pos <= relative_pos <= max_pos):
                            relative_pos = max(min_pos, min(max_pos, relative_pos))
                            new_ring_pos = round(start_pos + relative_pos, 2)
                            if ring_pos not in adjustments or min(abs(ring_pos - start_pos), abs(ring_pos - end_pos)) < adjustments[ring_pos][1]:
                                adjustments[ring_pos] = (new_ring_pos, min(abs(ring_pos - start_pos), abs(ring_pos - end_pos)))
                    elif order == "reverse" and ring_pos in adjustments:
                        offset = adjustments[ring_pos][0] - ring_pos
                        new_ring_pos = ring_pos + offset
                        safe = all(max(self.recess_depth, safety_zone) > (new_ring_pos - adj_start_pos) or (new_ring_pos - adj_start_pos) > piece_lengths[adj_j] - max(safety_zone, self.recess_depth)
                                  for adj_j in range(num_pieces)
                                  for adj_start_pos in [sum(piece_lengths[:adj_j]) - (adj_j * t) if adj_j <= j else total_length - sum(piece_lengths[adj_j + 1:]) - (adj_j * t) + piece_lengths[adj_j]])
                        relative_pos = new_ring_pos - start_pos if safe else relative_pos
                    if self.axle_debug: print(f"Ring_Pos : {ring_pos:.2f}, relative_pos : {relative_pos:.2f}")
                    piece_holes.append(round(relative_pos, 2))
            max_holes = max(max_holes, len(piece_holes))
            pieces_holes.append(piece_holes) if order == "forward" else pieces_holes.insert(0, piece_holes)
        
        for i in range(num_pieces): pieces_holes[i].extend([None] * (max_holes - len(pieces_holes[i])))
        if self.axle_debug and order == "forward":
            for idx, ring_pos in enumerate(ring_positions):
                if ring_pos in adjustments: print(f"Final adjustment: {ring_pos:.2f} to {ring_positions_adjusted[idx]:.2f}")
        return pieces_holes, ring_positions_adjusted

    def render(self):
        """Render axle with panels and rings."""
        od, tl, ml, pd, s, rd, ms = self.axle_outer_diameter, self.total_length, self.material_length, self.pass_through_diameter, self.sides, self.recess_depth, self.max_spacing
        t = self.thickness
        if self.axle_debug: print(f"Render started - Parameters: od={od}, tl={tl}, ml={ml}, pd={pd}, s={s}, rd={rd}, ms={ms}, t={t}")

        self.ctx.save()
        if self.axle_debug: print("Context saved")
        current_y = od + 10  # Initialize current_y here

        # Calculate number of support rings
        if self.axle_debug: print("Before num_rings calculation")
        base_rings = max(2, ceil((tl - 2 * rd) / ms) + 1)
        if self.axle_debug: print(f"Base rings: {base_rings}")
        num_rings = base_rings
        if (num_rings - 1) * ms < (tl - 2 * rd):
            num_rings += 1
        if self.axle_debug: print(f"Num_rings after adjustment: {num_rings}")
        ring_spacing = (tl - 2 * rd) / (num_rings - 1) if num_rings > 1 else (tl - 2 * rd)
        if self.axle_debug: print(f"Ring spacing: {ring_spacing:.2f}")

        # Compute side panel dimensions
        r_outer = (od / 2) - t
        side_length = 2 * r_outer * sin(pi / s)
        num_pieces = ceil(tl / ml)
        total_joint_loss = (num_pieces - 1) * t
        piece_lengths = [ml] * (num_pieces - 1) + [tl - ((num_pieces - 1) * ml) + total_joint_loss]
        if self.axle_debug: print(f"Side width: {side_length:.2f} mm, Lengths: {piece_lengths}")

        # Calculate absolute ring positions and add parameter info rectangle
        ring_positions = [round(rd, 2)]
        for i in range(1, num_rings - 1):
            ring_positions.append(round(ring_positions[-1] + ring_spacing, 2))
        ring_positions.append(round(tl - rd, 2))
        if self.axle_debug: print(f"Ring Positions: {ring_positions}")
        self.moveTo(10, current_y + (num_pieces * self.sides * (side_length + 10)) + 100)  # Position below panels
        self.rectangularWall(200, 100, "e", callback=[], move="")
        params_text = f"od={od:.1f}, tl={tl:.1f}, ml={ml:.1f}, pd={pd:.1f}, s={s}, rd={rd:.1f}, ms={ms:.1f}, t={t:.1f}"
        self.set_text_engrave()
        self.text(params_text, 100, 50, align="center")

        # Generate hole positions for even and odd sides
        even_holes, ring_positions_adjusted = self.populate_holes(piece_lengths, ring_positions, tl, "forward")
        odd_holes = self.populate_holes(piece_lengths, ring_positions_adjusted, tl, "reverse")[0]

        even_holes_matrix, odd_holes_matrix = np.array(even_holes, dtype=object), np.array(odd_holes, dtype=object)
        if self.axle_debug:
            print("Even Holes:", [f"{h:.2f}" if h else None for h in even_holes])
            print("Odd Holes:", [f"{h:.2f}" if h else None for h in odd_holes])

        x_panel_start, y_panel_base = 10.0, od + 10
        for j in range(num_pieces):
            piece_length = piece_lengths[j]
            for i in range(self.sides):
                holes = odd_holes_matrix[j][::-1] if i % 2 else even_holes_matrix[j]
                def create_holes(pos):
                    self.reset_cut()
                    hole_length = 32
                    hole_diameter = 8
                    hole_y = (side_length / 2) - (hole_length / 2)
                    self.set_text_engrave()
                    label, label_x, label_y = f"{i}:{j}", piece_length / 2, side_length / 2 - t
                    self.text(label, label_x, label_y)
                    if self.debug_labels:
                        for h in holes:
                            if h is not None and rd <= h <= piece_length - rd:
                                self.text(f"{h:.2f}", h + 8, label_y)
                    self.reset_cut()
                    if self.axle_debug: print(f"Piece {j}, Side {i}: Holes={holes}, y={hole_y:.2f}, length={hole_length:.2f}")
                    for h in holes:
                        if h and rd <= h <= piece_length - rd:
                            self.fingerHolesAt(h, hole_y, hole_length, 90)
                is_even = i % 2 == 0
                edge_type = edge_types[(is_even, j if j in (0, num_pieces - 1) else None)]
                self.reset_cut()
                self.rectangularWall(piece_length, side_length, edge_type,
                                     callback=[lambda i: create_holes(x_panel_start + i * (piece_length + 10))],
                                     move="down")
            current_y += side_length + 10

        x_ring_start, y_ring_start = x_panel_start, (num_pieces * self.sides * (side_length + 2)) + 3
        self.moveTo(x_ring_start, y_ring_start)
        if self.axle_debug: print(f"Starting ring loop with num_rings={num_rings}")
        for i in range(num_rings):
            self.current_pos = (x_ring_start + i * (od + 10.0), y_ring_start)
            if self.axle_debug: print(f"Ring {i} at x={self.current_pos[0]}, y={self.current_pos[1]}")
            try:
                with self.saved_context():
                    self.reset_cut()
                    self.moveTo(0, 0)
                    self.moveTo(-od, 0)
                    self.regularPolygonWall(s, r=r_outer, edges="f", move="", hole=pd)
                    if self.axle_debug: print(f"Ring {i} drawn")
            except Exception as e:
                if self.axle_debug: print(f"Ring error: {e}")
            if i < num_rings - 1: self.moveTo(od + 10.0, 0)

        self.ctx.restore()
        if self.axle_debug: print("Render complete")