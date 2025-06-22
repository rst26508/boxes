# Copyright (C) 2013-2016 Florian Festi
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

from boxes import *
from math import pi, sin, cos, ceil
import numpy as np

class Axle(Boxes):
    """An axle, initially for a set of filament spools"""

    description = """
Use small nails to properly align the pieces of the bayonet latch. Glue the parts of the bayonet latch before assembling the "axle". The inner parts go at the side and the outer parts at the inside of the axle.
![opened spool](static/samples/Axle.jpg)"""

    ui_group = "Misc"

    def __init__(self) -> None:
        Boxes.__init__(self)

        self.addSettingsArgs(edges.FingerJointSettings)
     #   self.buildArgParser(h=48)
        
     #   print("edges.FingerJointSettings successfully accessed.")
        self.argparser.add_argument(
            "--outer_diameter", action="store", type=float, default=70.0,
            help="Outer diameter of the axle (mm)"
        )
        self.argparser.add_argument(
            "--total_length", action="store", type=float, default=577.0,
            help="Total length of the axle (mm)"
        )
        self.argparser.add_argument(
            "--material_length", action="store", type=float, default=385.0,
            help="Maximum material length per segment (mm)"
        )
        self.argparser.add_argument(
            "--pass_through_diameter", action="store", type=float, default=48.0,
            help="Inner diameter for mounting or pass-through (mm)"
        )
        self.argparser.add_argument(
            "--sides", action="store", type=int, default=8,
            help="Number of sides for the outer part of the rings"
        )
        self.argparser.add_argument(
            "--recess_depth", action="store", type=float, default=12.0,
            help="Depth of recess for end rings (mm), applied to side panels"
        )
        self.argparser.add_argument(
            "--max_spacing", action="store", type=float, default=150.0,
            help="Maximum spacing between support rings (mm)"
        )
        self.argparser.add_argument(
            "--solid_bottom",  action="store", type=BoolArg(), default=False,
            help="Skips the hole in one support ring to use it as an vertical holder."
        )
        self.argparser.add_argument(
            "--panel_labels",  action="store", type=BoolArg(), default=False,
            help="Prints the side number:panel number on each panel."
        )
        self.argparser.add_argument(
            "--debug_flag",  action="store", type=BoolArg(), default=False,
            help="Turn on/off most console output and some self.text"
        )


    piecelengths = []
    ringpositions = []
    adjustedholepositions = []
    evenholepositions = []
    oddholepositions = []
    numRings = 2   
    numpieces = 1
    

    
    def pieceLengths(self):
        ml = self.material_length
        efml =  self.material_length - self.thickness  # Effective Material length. Finger joints are added to the specified length 
        self.piecelengths = [min(self.material_length - self.thickness, self.total_length)]
        self.numpieces = 1
        while (sum(self.piecelengths) <= self.total_length - ((self.numpieces) * self.thickness)):
            if sum(self.piecelengths) < self.total_length - ((self.numpieces) * self.thickness) - (ml - ( 2 * self.thickness)):
                if self.debug_flag == True: print(f" Appending piece of length {ml - ( 2 * self.thickness):.2f}")
                self.piecelengths.append(ml - ( 2 * self.thickness))
            else:
                self.piecelengths.append(self.total_length - sum(self.piecelengths) - ((self.numpieces) * self.thickness))
            self.numpieces += 1
        if self.debug_flag == True: print(f"Requested total length : {self.total_length:.2f}, Total pieces length : {sum(self.piecelengths):.2f}, join allowance : {(self.numpieces - 1) * self.thickness:.2f} and numpieces of {self.numpieces}")
        
    def ringPositions(self, order="forward"):
        standard_spacing = (self.total_length - (2 * self.recess_depth)) / (self.numRings - 1)
        ringpositions = []
        ringnumber = 0
        if order == "forward": 
            rings = range(self.numRings)
        else: # reverse
          #  rings = reverse(range(self.numRings))  alternatively from itertools import reversed
            rings = range(self.numRings)[::-1]
        for i in rings:
            if self.debug_flag == True: print(f"Ring Number : {i}")
            if sum(ringpositions[:i]) + standard_spacing >= sum(self.piecelengths[:ringnumber]):
                ringnumber += 1
            if i == 0: # Left hand end in forward direction
                if self.debug_flag == True: print(f"  Ring at {self.recess_depth:.2f}")
                ringpositions.append(self.recess_depth)
            else: # 
                if self.debug_flag == True: print(f"  Ring B at {(standard_spacing * i) + self.recess_depth:.2f}")
                ringpositions.append((standard_spacing * i) + self.recess_depth)
        return np.array(ringpositions, dtype=object)
        

    def populate_holes(self, piecelengths, ringpositions, total_length, order="forward"):
        """Generate hole positions for pieces, in forward or reverse order."""
        if self.debug_flag == True: 
            print("")
            print(f"Generating hole positions in the {order} order")
        pieces_holes = []
        max_holes = 0
        piece_indices = range(self.numpieces) if order == "forward" else reversed(range(self.numpieces))
        if self.debug_flag == True: print(f"Piece indices {piece_indices}")
        if order == "forward":
            ring_positions_adjusted = ringpositions.copy()  # Copy to store adjustments
        else:
            ring_positions_adjusted = ringpositions[::-1]
        
        for j in range(self.numpieces):
            piece_length = piecelengths[j]
            if order == "forward":
                subtract_value = sum(piecelengths[:j]) + ( j * self.thickness )
            else:  # reverse
                if self.debug_flag == True: print(f"  Total Length : {total_length:.2f}, sum piecelength : {sum(piecelengths[j:]):.2f}, numpieces : {self.numpieces}, j : {j}, thickness : {self.thickness}, piece length : {piece_length}")
                subtract_value = sum(piecelengths[:j]) + piecelengths[j] + ( j * self.thickness )
                
            if self.debug_flag == True: print(f"  Piece {j}: length = {piece_length:.2f} mm, subtract_value = {subtract_value:.2f}")
            piece_holes = []
            
            for i in range(self.numRings):
                ring_pos = ringpositions[i]
                if self.debug_flag == True: print(f"    Index {i}, ring position = {ring_pos:.2f}")

                # 
                if i == 0:
                    forward_test_value = subtract_value + piece_length + self.thickness
                    reverse_test_value = subtract_value - piece_length + self.thickness
                elif i == self.numRings - 1:
                    forward_test_value = subtract_value + piece_length + self.thickness
                    reverse_test_value = subtract_value - piece_length + self.thickness
                else:
                    forward_test_value = subtract_value + piece_length + (2 * self.thickness)
                    reverse_test_value = subtract_value - piece_length + (2 * self.thickness)
                if self.debug_flag == True: print(f"forward_test_value : {forward_test_value:.2f}, reverse_test_value : {reverse_test_value:.2f}")
                       
                if (ring_pos >= subtract_value and ring_pos <= forward_test_value and order == "forward") or (ring_pos <= subtract_value and ring_pos >= reverse_test_value and order == "reverse"):
                    if order == "forward":
                        relative_pos = ring_pos - subtract_value
                    else:
                        relative_pos = subtract_value - ring_pos
                    if self.debug_flag == True: print(f"      Relative Position : {relative_pos:.2f}")
                    original_relative_pos = relative_pos
                    # Adjustment block. Only used on the forward trace and when a ring position is too close to a joint
                    if order == "forward":
                        if relative_pos < max(self.recess_depth, (3 * self.thickness)):
                            relative_pos = max(self.recess_depth, (3 * self.thickness))
                            new_ring_pos = relative_pos
                        elif relative_pos > min(piece_length - ((3 * self.thickness)), piece_length - self.recess_depth):
                            # This is not working correctly for some situations. Further analysis is needed.
                            # eg tl = 300, ml close to 150 and max ring spacing of 150
                            new_ring_pos = ring_pos + (4 * self.thickness)
                            relative_pos = relative_pos - (4 * self.thickness) 
                        if relative_pos != original_relative_pos and order == "forward":
                            # Update ring_positions_adjusted
                            if self.debug_flag == True: print(f"    Adjusting ring_pos {ring_pos:.2f} to {relative_pos:.2f} and {new_ring_pos:.2f} for Piece {j}")
                            ringpositions[i] = relative_pos
                            ring_positions_adjusted[i] = new_ring_pos
                    piece_holes.append(round(relative_pos, 2))
                    if self.debug_flag == True: print(f"      Ring_Pos : {ring_pos:.2f}, relative_pos : {relative_pos:.2f}")
                else:
                    if self.debug_flag == True: print("      Not on this piece")
            max_holes = max(max_holes, len(piece_holes))
            if order == "forward":
                pieces_holes.append(piece_holes)
            else:
                pieces_holes.append(piece_holes[::-1])
        
        # Pad with None
        for i in range(self.numpieces):
            while len(pieces_holes[i]) < max_holes:
                pieces_holes[i].append(None)
        
        return np.array(pieces_holes, dtype=object), np.array(ring_positions_adjusted, dtype=object)
        
    def create_holes(self, sideno, pieceno, side_width, holepositions):
        hole_diameter = 0 #2 * self.thickness
        hole_y = 0 #- (side_width / 6) # (self.thickness * 2)
        hole_length = side_width + (2 * self.thickness)
        piece_length = self.piecelengths[pieceno]

        # Copied from filamentspool. With some tweaking of the call to fingerHolesAt the side value
        # appears to do well with matching finger holes to the fingers generated on the support rings
        r, h, side = self.regularPolygon(self.sides, radius=(self.outer_diameter - 2 * self.thickness)/2)
        
        label = f"{sideno}:{pieceno}"
        label_x = piece_length / 2
        label_fontsize =  (ceil(side/2))
        # Y positioning is not understood and needs work. This seems like a reasonable compromise for 3 to 10 sides
        label_y = self.thickness * 1.5
        if self.debug_flag == True: print(f"Pieces Matrix {self.piecelengths}, piece no {pieceno}")
        if self.debug_flag == True: print(f"  Hole Positions : {holepositions}")

        if self.debug_flag == False and self.panel_labels == True: self.text(label, label_x, label_y, align="middle center", fontsize=label_fontsize, color=Color.ANNOTATIONS)
        for hole_pos in holepositions:
            if hole_pos is not None:
                x_hole = float(hole_pos)
                    
                if self.debug_flag == True: 
                    print(f"  Hole at {x_hole:.2f}")
                    if self.debug_flag == True: self.text(f"{x_hole:.2f}", x_hole + 8, label_y)
                if x_hole >= self.recess_depth and x_hole <= piece_length - self.recess_depth:
                    self.fingerHolesAt(x_hole, -self.thickness, side + (2 * self.thickness), 90)
                else:
                    if self.debug_flag == True: print("    Failed recess depth, proximity to joint test")

    def print_new_pass_through(self, pass_through_changed):
        if pass_through_changed == True:
            label = f"{self.pass_through_diameter:.2f}"
            label_x = -(self.pass_through_diameter/4)
            label_y = -(self.pass_through_diameter/9)
            label_fontsize =  (ceil(self.pass_through_diameter/5))
            self.text(label,label_x,label_y, fontsize=label_fontsize, color=Color.ANNOTATIONS)
            
    def print_piece_length(self, piecelength):
        if self.debug_flag == True:
            self.text(f"{piecelength:.2f}", 30, 0, color=Color.ANNOTATIONS)

    def render(self):
        t = self.thickness
        # Clearing arrays as some arrays were growing between runs of render
        self.piecelengths.clear()
        self.ringpositions.clear()
        self.adjustedholepositions.clear()
        self.evenholepositions.clear()
        self.oddholepositions.clear()
        pass_through_changed = False
        
        # Check and ajust inner diameter if not a safe distance from the outer edge
        r = (self.outer_diameter / 2) - self.thickness
        min_distance = r * math.cos(math.pi / self.sides)
        safe_inner_diameter = 2 * (min_distance - self.thickness)
        if self.pass_through_diameter > safe_inner_diameter:
            self.pass_through_diameter = safe_inner_diameter
            pass_through_changed = True
        
        self.numRings = max(2, ceil((self.total_length - (2 * self.recess_depth))/ self.max_spacing) + 1)
        if self.debug_flag == True: print(f"Num Rings : {self.numRings}")
        self.pieceLengths ()
        ringpositions = self.ringPositions()
        # Generate hole matrices
        self.evenholepositions, ring_positions_adjusted = self.populate_holes(self.piecelengths, ringpositions, self.total_length, order="forward")

        if self.debug_flag == True: 
            print(f"  Even Hole Positions Matrix")
            print(self.evenholepositions)
        self.oddholepositions = self.populate_holes(self.piecelengths, ring_positions_adjusted, self.total_length, order="reverse")[0]  # Only need holes

        if self.debug_flag == True: 
            print("   Odd Hole Positions Matrix")
            print(self.oddholepositions)
        
        r_outer = (self.outer_diameter / 2) - self.thickness
        side_width = 2 * r_outer * sin(pi / self.sides)
        
        # Create the support rings
        for i in range(self.numRings):
            if self.solid_bottom == True and i == 0:
                self.regularPolygonWall(
                    self.sides, r=self.outer_diameter/2, edges="f",
                    move="down")
            else:
                self.regularPolygonWall(
                    self.sides, r=self.outer_diameter/2, edges="f",hole=self.pass_through_diameter,
                    callback=[lambda:self.print_new_pass_through(pass_through_changed)],
                    move="down")

        self.moveTo(self.outer_diameter + (5 * self.thickness), 0)

        # Create the pieces for the sides
        # Even numbered sides should run left to right
        # Odd numbered sides right to left when assembled
        for j in range(self.numpieces):
            for i in range(self.sides):
                if self.debug_flag == True: print(f"j = {j}")
                
                    
                if i % 2 == 0: # even side
                    order = "forward"
                    holepositions = self.evenholepositions[j].copy()
                    if self.numpieces == 1:
                        edgetype = "eeee"
                    else:
                        edgetype = "eFee" if j == 0 else "eeef" if j == len(self.piecelengths) - 1 else "eFef"
                else: # Odd side
                    order = "reverse"
                    holepositions = self.oddholepositions[j].copy()
                    if self.numpieces == 1:
                        edgetype = "eeee"
                    else:
                        edgetype = "eeeF" if j == 0 else "efee" if j == len(self.piecelengths) - 1 else "efeF"
                if self.debug_flag == True: print(f"Creating {order} Side no {i} edge piece {j} of length {self.piecelengths[j]} with edge type {edgetype}")
                self.rectangularWall(
                    self.piecelengths[j], side_width, edgetype,
                    callback=[lambda:self.create_holes(i, j, side_width, holepositions),
                    self.print_piece_length(self.piecelengths[j])],
                    move="up")
