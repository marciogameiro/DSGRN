### CubicalBlowupGraph.py
### MIT LICENSE 2024 Marcio Gameiro

# TODO: 1) Maybe cache regulation map and cycle decomposition to increase performance
#       2) Level 3 and 4 are allowed in higher dimensions (add restrictions to that?)
#       3) The default value of self_edges is True (change it to False?)
#       4) Add 3D Morse sets plotting cpabilities

import DSGRN
import pychomp

class CubicalBlowupGraph:
    def __init__(self, parameter=None, labelling=None, num_thresholds=None, self_edges=True, level=4):
        # Check if input arguments are valid
        if parameter is None and (labelling is None or num_thresholds is None):
            raise ValueError('Either parameter or labelling and num_thresholds must be provided.')
        if parameter and (labelling or num_thresholds):
            raise ValueError('Only parameter or labelling and num_thresholds should be provided.')
        # Extract info from parameter
        if parameter:
            # Get the parameter index in the original parameter graph
            original_par_graph = DSGRN.ParameterGraph(parameter.network())
            par_index = original_par_graph.index(parameter)
            # Redefine network without self edges blowup
            net_spec = parameter.network().specification()
            network = DSGRN.Network(net_spec, edge_blowup='none')
            # Get the parameter in the new parameter graph
            parameter_graph = DSGRN.ParameterGraph(network)
            parameter = parameter_graph.parameter(par_index)
            # # Set network and parameter
            # self.parameter = parameter
            # self.network = network
            # # Parameter labelling
            # self.labelling = self.parameter.labelling()
            # # Space dimension
            # self.dim = self.network.size()
            # # Number of thresholds (same as number of out edges)
            # self.num_thresholds = [len(self.network.outputs(n)) for n in range(self.dim)]
            # Get parameter labelling
            labelling = parameter.labelling()
            # Number of thresholds (same as number of out edges)
            num_thresholds = [len(network.outputs(n)) for n in range(network.size())]
        # Parameter labelling
        self.labelling = labelling
        # Number of thresholds
        self.num_thresholds = num_thresholds
        # Space dimension
        self.dim = len(self.num_thresholds)
        # Add self edges if True (they are not necessary)
        self.self_edges = self_edges
        # Multivalued map level (level 3 not allowed in higher dims)
        # self.level = level if self.dim <= 3 else min(level, 2)
        self.level = level
        # Max values for the indices of cells in the cubical complex X
        self.limits = [k + 1 for k in self.num_thresholds]
        # Number of boxes per dimension in the cubical complex X
        self.num_boxes = [k + 1 for k in self.num_thresholds]
        # A cubical complex in pychomp has open cells on the right boundary,
        # that is, the right most top cells do not contain the lower dimensional
        # faces on their right boundaries (actually their right boundaries are the
        # lower dimensional cells all the way on the left of the complex - the
        # cell complex has twisted periodic conditions). So to get a "full"
        # cubical complex as a subcomplex we pad with an extra layer of boxes.
        # The cells on the right most boundary are called fringe cells.
        # Define the cubical complex X (add one extra layer for fringe cells)
        self.cubical_complex = pychomp.CubicalComplex([k + 1 for k in self.num_boxes])
        # Blowup cubical complex Xb (double size plus one and add 1 for fringe cells)
        self.blowup_complex = pychomp.CubicalComplex([2 * (k + 1) for k in self.num_boxes])
        # Shape of top dimensional cells
        self.top_shape = 2**self.dim - 1
        # Grid size of the cubical complex X
        self.grid_size = self.cubical_complex.boxes()
        # Grid size of the blowup cubical complex Xb
        self.blowup_grid_size = self.blowup_complex.boxes()
        # Place values (or index offset in each dimension) for
        # actual cubical complex X (without the fringe layer)
        self.pv = [1]
        for k in self.num_boxes:
            self.pv.append(self.pv[-1] * k)
        # Index offset in each dimension for the cubical_complex
        self.jump = [1]
        for k in self.grid_size:
            self.jump.append(self.jump[-1] * k)
        # Index offset in each dimension for the blowup_complex
        self.blowup_jump = [1]
        for k in self.blowup_grid_size:
            self.blowup_jump.append(self.blowup_jump[-1] * k)
        # State Transition Graph (STG) on top cells (including fringe) of Xb
        self.digraph = pychomp.DiGraph()
        # # Add top cells of Xb (including fringe) as vertices
        # # Not necessary (verts are automatically added with edges)
        # for cell in self.blowup_complex(self.dim):
        #     self.digraph.add_vertex(cell)
        # Compute multivalued map (digraph)
        self.compute_multivalued_map()

    def complex(self):
        """Return the cell complex"""
        return self.blowup_complex

    def adjacencies(self):
        """Return a method to compute adjecencies"""
        return self.digraph.adjacencies

    def adjacency_lists(self):
        """Return the digraph adjacency lists"""
        return self.digraph.adjacency_lists

    def digraph_verts(self):
        """Return the digraph vertices"""
        return self.digraph.vertices()

    def digraph_edges(self):
        """Return the digraph edges"""
        return self.digraph.edges()

    def blowup2cubical(self, cell):
        """Return the cubical complex cell corresponding to a blowup complex cell"""
        # Get cell coordinates in the blowup complex
        cell_coords = self.blowup_complex.coordinates(cell)
        # Get cubical complex cell coordinates in the cubical complex
        cc_cell_coords = [k // 2 for k in cell_coords]
        # Get shape bit vector of the cubical complex cell
        cc_cell_shape_vec = [k % 2 for k in cell_coords]
        # Get the integer shape value corresponding to the bit vector
        bit_str = ''.join(str(b) for b in reversed(cc_cell_shape_vec))
        cc_cell_shape = int(bit_str, 2)
        # Get the cubical complex cell index in the cubical complex
        cc_cell = self.cubical_complex.cell_index(cc_cell_coords, cc_cell_shape)
        return cc_cell

    def cubical2blowup(self, cc_cell):
        """Return the blowup complex cell corresponding to a cubical complex cell"""
        # Get cubical complex cell coordinates in the cubical complex
        cc_cell_coords = self.cubical_complex.coordinates(cc_cell)
        # Get the shape of the cubical complex cell
        cc_cell_shape = self.cubical_complex.cell_shape(cc_cell)
        # Get shape bit vector of the cubical complex cell
        cc_cell_shape_vec = [1 if cc_cell_shape & (1 << n) else 0 for n in range(self.dim)]
        # Get the cell coordinates in the blowup complex
        cell_coords = [2 * cc_cell_coords[n] + cc_cell_shape_vec[n] for n in range(self.dim)]
        # Get the cell index in the blowup complex
        cell = self.blowup_complex.cell_index(cell_coords, self.top_shape)
        return cell

    def essential_directions(self, cc_cell):
        """Return the essential (tangent) directions of a cubical cell"""
        shape = self.cubical_complex.cell_shape(cc_cell)
        return [n for n in range(self.dim) if (shape & (1 << n)) != 0]

    def inessential_directions(self, cc_cell):
        """Return the inessential (normal) directions of a cubical cell"""
        shape = self.cubical_complex.cell_shape(cc_cell)
        return [n for n in range(self.dim) if (shape & (1 << n)) == 0]

    def extension_directions(self, cc_face, cc_coface):
        """Return the extension directions of cc_face into cc_coface"""
        # face_inessential = self.inessential_directions(cc_face)
        # coface_essential = self.essential_directions(cc_coface)
        # # Directions essential for cc_coface and inessential for cc_face
        # ext_directions = set(coface_essential).intersection(face_inessential)
        face_shape = self.cubical_complex.cell_shape(cc_face)
        coface_shape = self.cubical_complex.cell_shape(cc_coface)
        # XOR shape (1 where cc_coface is 1 and cc_face is 0)
        xor_shape = coface_shape ^ face_shape
        # Directions essential for cc_coface and inessential for cc_face
        ext_directions = [n for n in range(self.dim) if xor_shape & (1 << n)]
        return ext_directions

    def star(self, cc_cell):
        """Return the list of cells in the star of cc_cell"""
        # Get the star of cc_cell (discard fringe cells)
        cell_star = [cell for cell in self.cubical_complex.star({cc_cell})
                     if not self.cubical_complex.rightfringe(cell)]
        return cell_star

    def top_star(self, cc_cell):
        """Return the list of cells in the top star of cc_cell"""
        # Get the top star of cc_cell (discard fringe cells)
        cell_top_star = [top_cell for top_cell in self.cubical_complex.topstar(cc_cell)
                         if not self.cubical_complex.rightfringe(top_cell)]
        return cell_top_star

    def adjacent_top_cells(self, cc_cell, n):
        """Return the list of (left, right) pairs of n-adjacent top cells of cc_cell"""
        # Get the top star of cc_cell
        cell_top_star = set(self.top_star(cc_cell))
        # Get list of (left, right) pairs of n-adjacent top cells
        adj_top_pairs = [(top_cell, top_cell + self.jump[n]) for top_cell in cell_top_star
                         if top_cell + self.jump[n] in cell_top_star]
        return adj_top_pairs

    def wall_label(self, cc_top_cell, n, side):
        """Return the wall labeling at the given n-wall of the cubical
        complex. The n-wall is represented by a top cell, the wall
        normal (inessential) direction n, and the side of the cell
        containing the wall, where -1 means left n-wall and 1 means
        right n-wall.
        """
        # Get the coordinates of the top cell in the cubical complex
        cc_cell_coords = self.cubical_complex.coordinates(cc_top_cell)
        # Consider all walls of fringe layer cells absorbing
        if any(cc_cell_coords[k] == self.limits[k] for k in range(self.dim)):
            return side
        # The cubical complex cell indexing is not compatible with the labeling
        # indexing due to the extra fringe layer and to the fact that the cubical
        # complex indexes all cells (while labeling indexes only top cells). So we
        # need to compute the labeling index of the top cell.
        label_index = sum(c * self.pv[k] for k, c in enumerate(cc_cell_coords))
        label_bit_mask = 1 << (n + (self.dim if side == 1 else 0))
        # Return side if wall is absorbing
        if self.labelling[label_index] & label_bit_mask:
            return side
        return -side

    def rook_field_component(self, cc_cell, cc_top_cell, n):
        """Return the n-th component of the rook field of cc_cell with respect to cc_top_cell"""
        cell_inessential = self.inessential_directions(cc_cell)
        if n in cell_inessential:
            cell_coords = self.cubical_complex.coordinates(cc_cell)
            top_cell_coords = self.cubical_complex.coordinates(cc_top_cell)
            side = -1 if cell_coords[n] == top_cell_coords[n] else 1
            return self.wall_label(cc_top_cell, n, side)
        left_wall_label = self.wall_label(cc_top_cell, n, -1)
        right_wall_label = self.wall_label(cc_top_cell, n, 1)
        return left_wall_label if left_wall_label == right_wall_label else 0

    def rook_field(self, cc_cell, cc_top_cell):
        """Return the rook field of cc_cell with respect to cc_top_cell"""
        return [self.rook_field_component(cc_cell, cc_top_cell, n) for n in range(self.dim)]

    def gradient_directions(self, cc_cell):
        """Return the list of gradient directions of cc_cell"""
        # Get the top star of cc_cell
        cell_top_star = self.top_star(cc_cell)
        # Get rook field of cc_cell with respect to top cells in the top star
        rook_top_star = [self.rook_field(cc_cell, cc_top_cell) for cc_top_cell in cell_top_star]
        return [n for n, rook in enumerate(zip(*rook_top_star)) if set(rook) == {-1} or set(rook) == {1}]

    def opaque_directions(self, cc_cell):
        """Return the list of opaque directions of cc_cell"""
        # Get the top star of cc_cell
        cell_top_star = self.top_star(cc_cell)
        # Get rook field of cc_cell with respect to top cells in the top star
        rook_top_star = [self.rook_field(cc_cell, cc_top_cell) for cc_top_cell in cell_top_star]
        return [n for n, rook in enumerate(zip(*rook_top_star)) if set(rook) == {-1, 1}]

    def equilibrium_cell(self, cc_cell):
        """Return True if cc_cell is equilibrium cell and False otherwise"""
        # Fringe cells are not equilibrium cells
        if self.cubical_complex.rightfringe(cc_cell):
            return False
        # Get the top star of cc_cell
        cell_top_star = self.top_star(cc_cell)
        for n in range(self.dim):
            # Get the values of the n-th component of the rook field for top cells in the top star
            rook_values = set([self.rook_field_component(cc_cell, cc_top_cell, n) for cc_top_cell in cell_top_star])
            # Check if n is a gradient direction
            if rook_values == {-1} or rook_values == {1}:
                return False
        return True

    def equilibrium_cells(self):
        """Return the list of equilibrium cells"""
        return [cc_cell for cc_cell in self.cubical_complex if self.equilibrium_cell(cc_cell)]

    def active_regulation(self, cc_cell, n, k):
        """Return True if the inessential direction n actively regulates the direction k"""
        # Get list of pairs of n-adjacent top cells
        adjacent_top_pairs = self.adjacent_top_cells(cc_cell, n)
        for top_cell_left, top_cell_right in adjacent_top_pairs:
            # Compute the k-th component of rook field w.r.t. the top cells
            rook_comp_left = self.rook_field_component(cc_cell, top_cell_left, k)
            rook_comp_right = self.rook_field_component(cc_cell, top_cell_right, k)
            if rook_comp_left != rook_comp_right:
                # Regulation is active
                return True
        return False

    def active_regulation_pair(self, cc_face, cc_coface, n, k):
        """Return True if the inessential direction n of cc_coface actively regulates
        the direction k at (cc_face, cc_coface), that is, if there are two n-adjacent
        top cells of cc_coface on which the k-th component of the rook field of cc_face
        disagree. The function active_regulation(cc_cell, n, k) is just a particular
        case: active_regulation_pair(cc_cell, cc_cell, n, k).
        """
        # Get list of pairs of n-adjacent top cells of cc_coface
        adjacent_top_pairs = self.adjacent_top_cells(cc_coface, n)
        for top_cell_left, top_cell_right in adjacent_top_pairs:
            # Compute the k-th component of rook field at cc_face w.r.t. the top cells
            rook_comp_left = self.rook_field_component(cc_face, top_cell_left, k)
            rook_comp_right = self.rook_field_component(cc_face, top_cell_right, k)
            if rook_comp_left != rook_comp_right:
                # Regulation is active
                return True
        return False

    def active_regulation_map(self, cc_cell):
        """Return the active regulation map of cc_cell"""
        coords = self.cubical_complex.coordinates(cc_cell)
        # Get the interior (non-boundary) inessential directions
        iness_inter = [n for n in self.inessential_directions(cc_cell) if coords[n] > 0 and coords[n] < self.limits[n]]
        # # Get regulation map of cc_cell
        # reg_map = {n: self.parameter.regulator(n, coords[n] - 1) for n in iness_inter}
        # # Define active regulation map
        # active_reg_map = {n: reg_map[n] for n in reg_map if self.active_regulation(cc_cell, n, reg_map[n])}
        # Get active regulation map of cc_cell
        active_reg_map = {n: k for n in iness_inter for k in range(self.dim) if self.active_regulation(cc_cell, n, k)}
        return active_reg_map

    def flow_direction_top_cell(self, cc_face, cc_coface, cc_top_cell):
        """Return the flow direction between cc_face and cc_coface
        with respect to the top cell cc_top_cell. The cells are assumed
        to have the following face relations: cc_face < cc_coface <= cc_top_cell.
        The return value is: -1 if the flow cc_coface -> cc_face is transverse
        (cc_face is an exit face of cc_coface with respect to cc_top_cell);
        +1 if the flow cc_face -> cc_coface is transverse (cc_face is an
        entrance face of cc_coface with respect to cc_top_cell); 0 if there
        is not a transverse flow direction with respect to cc_top_cell.
        """
        face_coords = self.cubical_complex.coordinates(cc_face)
        top_cell_coords = self.cubical_complex.coordinates(cc_top_cell)
        # face_inessential = self.inessential_directions(cc_face)
        # coface_essential = self.essential_directions(cc_coface)
        # # Directions essential for cc_coface and inessential for cc_face
        # ext_directions = set(coface_essential).intersection(face_inessential)
        face_shape = self.cubical_complex.cell_shape(cc_face)
        coface_shape = self.cubical_complex.cell_shape(cc_coface)
        # XOR shape (1 where cc_coface is 1 and cc_face is 0)
        xor_shape = coface_shape ^ face_shape
        # Directions essential for cc_coface and inessential for cc_face
        ext_directions = [n for n in range(self.dim) if xor_shape & (1 << n)]
        # Start with both True and update
        exit_face, entrance_face = True, True
        for n in ext_directions:
            # Get side of unique n-wall containing cc_face
            side = -1 if face_coords[n] == top_cell_coords[n] else 1
            if self.wall_label(cc_top_cell, n, side) == side:
                # Exit face for direction n
                entrance_face = False
            else:
                # Entrance face for direction n
                exit_face = False
            if not (exit_face or entrance_face):
                return 0
        if exit_face:
            return -1
        return 1

    def flow_direction(self, cc_cell1, cc_cell2):
        """Return the flow direction between cc_cell1 and cc_cell2. It assumes
        that one cell is a face of the other. The return value is -1 if the flow
        goes cc_cell2 -> cc_cell1 (cc_cell1 is an "exit face" of cc_cell2); it is
        +1 if the flow goes cc_cell1 -> cc_cell2 (cc_cell1 is an "entrance face"
        of cc_cell2); and it is 0 if there is not a transverse flow direction.
        """
        # Set face, coface, and face relation sign
        if cc_cell1 < cc_cell2:
            cc_face, cc_coface = cc_cell1, cc_cell2
            face_sign = 1
        else:
            cc_face, cc_coface = cc_cell2, cc_cell1
            face_sign = -1
        # Get flow directions with respect to cells in the top star
        flow_data = [self.flow_direction_top_cell(cc_face, cc_coface, cc_top_cell) for cc_top_cell in
                     self.cubical_complex.topstar(cc_coface) if not self.cubical_complex.rightfringe(cc_top_cell)]
        # cc_face is an exit face of cc_coface
        if all(k == -1 for k in flow_data):
            return -face_sign
        # cc_face is an entrance face of cc_coface
        if all(k == 1 for k in flow_data):
            return face_sign
        return 0

    def gradient_opaque_pair(self, cc_face, cc_coface):
        """Return a GO-pair for (cc_face, cc_coface) if one exists"""
        # Get the extension directions of cc_face into cc_coface
        ext_directions = self.extension_directions(cc_face, cc_coface)
        # No GO-pair if not a unique extension direction
        if len(ext_directions) != 1:
            return tuple()
        # Get the opaque direction of cc_face
        n_opaque = ext_directions[0]
        # Get the gradient inessential directions of cc_coface
        coface_gradient = self.gradient_directions(cc_coface)
        coface_inessential = self.inessential_directions(cc_coface)
        gradient_inessential = set(coface_gradient).intersection(coface_inessential)
        # No GO-pair if no gradient inessential directions
        if not gradient_inessential:
            return tuple()
        # Search for a direction that actively regulates n_opaque
        for n_grad in gradient_inessential:
            # Check if n_grad actively regulates n_opaque at (cc_face, cc_coface)
            if self.active_regulation_pair(cc_face, cc_coface, n_grad, n_opaque):
                # Found a GO-pair
                return n_grad, n_opaque
        # No GO-pairs found
        return tuple()

    def decision_wall(self, cc_face, cc_coface):
        """Return a decision wall for the pair (cc_face, cc_coface) if one exists"""
        # Compute a GO-pair for (cc_face, cc_coface)
        go_pair = self.gradient_opaque_pair(cc_face, cc_coface)
        # No decision wall if no GO-pair
        if not go_pair:
            return tuple()
        # Get gradient and opaque directions
        n_grad, n_opaque = go_pair
        # Get active regulation map of cc_face
        act_map = self.active_regulation_map(cc_face)
        # Get the opaque inessential directions of cc_face
        face_opaque = self.opaque_directions(cc_face)
        face_inessential = self.inessential_directions(cc_face)
        opaque_inessential = set(face_opaque).intersection(face_inessential)
        # Get the opaque inessential directions other than n_opaque
        opaque_others = opaque_inessential.difference({n_opaque})
        # Check for indecisive drift
        if any(act_map[n] in opaque_others and act_map[n] != n for n in act_map):
            # No indecisive drift
            return tuple()
        # Get one decision wall for cc_face, cc_coface
        face_coords = self.cubical_complex.coordinates(cc_face)
        coface_coords = self.cubical_complex.coordinates(cc_coface)
        # Pick one top cell to get decision wall
        face_top_star = self.top_star(cc_face)
        cc_face_top_cell = face_top_star[0]
        new_coords = coface_coords.copy()
        for n in self.inessential_directions(cc_coface):
            rook_n = self.rook_field_component(cc_face, cc_face_top_cell, n)
            new_coords[n] -= 1 if rook_n == 1 else 0
        # Get the top cell and the wall side defining the (n_opaque-wall) decision wall
        cc_new_top_cell = self.cubical_complex.cell_index(new_coords, self.top_shape)
        # The wall side is determined by cc_face and cc_coface (shift is uniform)
        wall_side = -1 if face_coords[n_opaque] == coface_coords[n_opaque] else 1
        return cc_new_top_cell, n_opaque, wall_side

    def decision_wall_direction(self, cc_cell1, cc_cell2):
        """Return the decision wall (if there is one) flow direction between
        cc_cell1 and cc_cell2. It assumes that one cell is a face of the other.
        The return value is -1 if the flow goes cc_cell2 -> cc_cell1 (cc_cell1
        is an "exit face" of cc_cell2); the return value it is +1 if the flow
        goes cc_cell1 -> cc_cell2 (cc_cell1 is an "entrance face" of cc_cell2);
        and it is 0 if there is no decision wall for cc_cell1, cc_cell2.
        """
        # Set face, coface, and face relation sign
        if cc_cell1 < cc_cell2:
            cc_face, cc_coface = cc_cell1, cc_cell2
            face_sign = 1
        else:
            cc_face, cc_coface = cc_cell2, cc_cell1
            face_sign = -1
        # Get decision wall for cc_face, cc_coface
        dec_wall = self.decision_wall(cc_face, cc_coface)
        if not dec_wall:
            return 0
        # Get decision wall components and check wall label direction
        cc_dec_wall_top_cell, n_opaque, side = dec_wall
        if self.wall_label(cc_dec_wall_top_cell, n_opaque, side) == side:
            # cc_face is an exit face of cc_coface
            return -face_sign
        # If level < 4 check if n_opaque regulates another direction at cc_face
        if self.level < 4:
            # Get active regulation map of cc_face
            act_map = self.active_regulation_map(cc_face)
            if n_opaque in act_map and act_map[n_opaque] != n_opaque:
                return 0
        # cc_face is an entrance face of cc_coface
        return face_sign

    def semi_opaque_cell(self, cc_cell):
        """Return True if cc_cell is semi-opaque"""
        # Get active regulation map of cc_cell
        act_reg_map = self.active_regulation_map(cc_cell)
        # Check if regulation map is a bijection onto its domain
        return set(act_reg_map.keys()) == set(act_reg_map.values())

    def cycle_decomposition(self, reg_map):
        """Return a cycle decomposition of a permutation reg_map"""
        # Make a copy of reg_map
        perm_dict = dict(reg_map)

        def extract_cycle(perm):
            """Extract cycle from permutation"""
            # Pop item as a list [key, value]
            cycle = list(perm.popitem())
            # While last item in perm
            while cycle[-1] in perm:
                # Given key pop item and return value
                cycle.append(perm.pop(cycle[-1]))
            return cycle[:-1]

        # Get a list of cycles
        cycle_decomp = []
        while perm_dict:
            cycle_decomp.append(extract_cycle(perm_dict))
        return cycle_decomp

    def lap_number(self, cc_cell, cc_top_cell, cycle):
        """Compute lap number of cc_cell with respect to cycle at cc_top_cell"""
        cycle_len = len(cycle)
        # Transform cycle into a dictionary
        cycle_dict = {cycle[k]: cycle[(k + 1) % cycle_len] for k in range(cycle_len)}
        # Get cell coords and top cell to evaluate rook field
        cell_coords = self.cubical_complex.coordinates(cc_cell)
        top_cell_coords = self.cubical_complex.coordinates(cc_top_cell)
        top_cell_rook = self.cubical_complex.cell_index(cell_coords, self.top_shape)
        lap_num = 0
        for n in cycle_dict:
            sigma_n = cycle_dict[n]
            # Get left wall label and cell side components n and sigma_n
            left_wall_label = self.wall_label(top_cell_rook, sigma_n, -1)
            side_sigma_n = -1 if cell_coords[sigma_n] == top_cell_coords[sigma_n] else 1
            side_n = -1 if cell_coords[n] == top_cell_coords[n] else 1
            # Count number of negative directions
            if left_wall_label * side_sigma_n * side_n < 0:
                lap_num += 1
        return lap_num

    def unstable_cells(self, cc_cell, non_trivial_cycles):
        """Compute unstable cells of cc_cell with respect to non-trivial cycles"""
        cell_star = self.star(cc_cell)
        cell_dim = self.cubical_complex.cell_dim(cc_cell)
        # Get cofaces of co-dimension 2 or more of cc_cell
        star_codim2 = [cell for cell in cell_star if self.cubical_complex.cell_dim(cell) > cell_dim + 1]
        unst_cells = []
        for cc_coface in star_codim2:
            # Get list of unstable cells
            coface_top_star = self.top_star(cc_coface)
            for cycle in non_trivial_cycles:
                # Check if extension directions are contained in the cycle
                ext_directions = set(self.extension_directions(cc_cell, cc_coface))
                if not ext_directions.issubset(cycle):
                    continue
                cycle_len = len(cycle)
                # Add cell to unstable cell list if lap number condition is valid
                if all(2 * self.lap_number(cc_cell, top_cell, cycle) < cycle_len for top_cell in coface_top_star):
                    unst_cells.append(cc_coface)
        return unst_cells

    def cyclic_extension_direction(self, cc_cell1, cc_cell2):
        """Return the flow direction between cc_cell1 and cc_cell2 if there is one.
        It assumes that one cell is a face of the other. The return value is -1 if
        the flow goes cc_cell2 -> cc_cell1 (cc_cell1 is an "exit face" of cc_cell2);
        the return value it is +1 if the flow goes cc_cell1 -> cc_cell2 (cc_cell1
        is an "entrance face" of cc_cell2); and it is 0 if there is no flow direction
        between cc_cell1 and cc_cell2. If there is a flow direction, the flow always
        goes from cc_coface -> cc_face. It also return a list of unstable cells of
        the target cell, that is, a list of unstable cells of of cc_face.
        """
        # Set face, coface, and face relation sign
        if cc_cell1 < cc_cell2:
            cc_face, cc_coface = cc_cell1, cc_cell2
            face_sign = 1
        else:
            cc_face, cc_coface = cc_cell2, cc_cell1
            face_sign = -1
        # Return 0 if cc_face is not semi-opaque
        if not self.semi_opaque_cell(cc_face):
            return 0, []
        # Get active regulation map and cycle decomposition
        act_reg_map = self.active_regulation_map(cc_face)
        cycle_decomp = self.cycle_decomposition(act_reg_map)
        # Get list of non-trivial cycles
        non_trivial_cycles = [cycle for cycle in cycle_decomp if len(cycle) > 1]
        # Get the unique extension direction (cells have co-dim 1)
        ext_directions = self.extension_directions(cc_face, cc_coface)
        n_ext = ext_directions[0]
        for cycle in non_trivial_cycles:
            if n_ext in cycle:
                # Return flow direction and list of unstable cells of cc_face
                unst_cells = self.unstable_cells(cc_face, non_trivial_cycles)
                # Flow goes from cc_coface to cc_face
                return -face_sign, unst_cells
        return 0, []

    def parallel_neighbors(self, cell):
        """Get the set of left and right neighbors (including fringe) of cell
        in each dimension. Only getting the right neighbors (the left neighbors
        are commented out).
        """
        coords = self.blowup_complex.coordinates(cell)
        # left_right_neighbors = set()
        right_neighbors = set()
        for n in range(self.dim):
            # Get left and right neighbors in direction n
            # cell_left = cell - self.blowup_jump[n]
            cell_right = cell + self.blowup_jump[n]
            # If at boundary the left neighbor is a fringe cell
            # if coords[n] == 0:
            #     # Get the left n-face (left n-wall) of cell
            #     face_left = self.blowup_complex.left(cell, n)
            #     # The (fringe) left neighbor is the unique cell in topstar not equal cell
            #     [cell_left] = [c for c in self.blowup_complex.topstar(face_left) if c != cell]
            # If at boundary the right neighbor is a fringe cell
            # Subtract 1 from blowup_grid_size because of fringe layer
            if coords[n] == self.blowup_grid_size[n] - 1:
                # Get the right n-face (right n-wall) of cell
                face_right = self.blowup_complex.right(cell, n)
                # The (fringe) right neighbor is the unique cell in topstar not equal cell
                [cell_right] = [c for c in self.blowup_complex.topstar(face_right) if c != cell]
            # Add cells to set of neighbors
            # left_right_neighbors.update([cell_left, cell_right])
            right_neighbors.add(cell_right)
        return right_neighbors

    def trivial_multivalued_map(self):
        """Compute the trivial multivalued map (F_0)"""
        # Just need to add edges (vertices are automatically added)
        for cell1 in self.blowup_complex(self.dim):
            # Add self edge if not fringe cell
            if not self.blowup_complex.rightfringe(cell1):
                self.digraph.add_edge(cell1, cell1)
            right_neighbors = self.parallel_neighbors(cell1)
            for cell2 in right_neighbors:
                # Add both edges unless source is non-fringe and target is a fringe cell
                if self.blowup_complex.rightfringe(cell1) or not self.blowup_complex.rightfringe(cell2):
                    self.digraph.add_edge(cell1, cell2)
                if self.blowup_complex.rightfringe(cell2) or not self.blowup_complex.rightfringe(cell1):
                    self.digraph.add_edge(cell2, cell1)

    def compute_multivalued_map(self):
        """Compute the multivalued map (digraph) on top cells of the blowup complex"""
        # Compute trivial map for level 0
        if self.level == 0:
            self.trivial_multivalued_map()
            return
        # Add edges corresponding to level 1 (multivalued map F_1)
        # Just need to add edges (vertices are automatically added)
        for cell1 in self.blowup_complex(self.dim):
            # Get corresponding cubical complex cell
            cc_cell1 = self.blowup2cubical(cell1)
            # Add self edge if equilibrium cell and flag is set
            if self.self_edges and self.equilibrium_cell(cc_cell1):
                self.digraph.add_edge(cell1, cell1)
            right_neighbors = self.parallel_neighbors(cell1)
            for cell2 in right_neighbors:
                # Always add edges from fringe cells
                if self.blowup_complex.rightfringe(cell1):
                    self.digraph.add_edge(cell1, cell2)
                if self.blowup_complex.rightfringe(cell2):
                    self.digraph.add_edge(cell2, cell1)
                if self.blowup_complex.rightfringe(cell1) or self.blowup_complex.rightfringe(cell2):
                    continue
                # Get corresponding cubical complex cell
                cc_cell2 = self.blowup2cubical(cell2)
                # Get flow direction and add edge corresponding to F_1
                flow_dir = self.flow_direction(cc_cell1, cc_cell2)
                if flow_dir == -1:
                    self.digraph.add_edge(cell2, cell1)
                    continue
                if flow_dir == 1:
                    self.digraph.add_edge(cell1, cell2)
                    continue
                # Add edge corresponding to F_2 or F_4 if level >= 2 or level == 4
                if self.level > 1:
                    # Get decision wall flow direction and add edge
                    flow_dir = self.decision_wall_direction(cc_cell1, cc_cell2)
                    if flow_dir == -1:
                        self.digraph.add_edge(cell2, cell1)
                        continue
                    if flow_dir == 1:
                        self.digraph.add_edge(cell1, cell2)
                        continue
                # Add edges corresponding to F_3 if level >= 3
                if self.level > 2:
                    # Get cyclic extension flow direction and unstable cells and add edges
                    flow_dir, unst_cells = self.cyclic_extension_direction(cc_cell1, cc_cell2)
                    if flow_dir == -1:
                        self.digraph.add_edge(cell2, cell1)
                        for cc_cell in unst_cells:
                            cell_unst = self.cubical2blowup(cc_cell)
                            self.digraph.add_edge(cell1, cell_unst)
                        continue
                    if flow_dir == 1:
                        self.digraph.add_edge(cell1, cell2)
                        for cc_cell in unst_cells:
                            cell_unst = self.cubical2blowup(cc_cell)
                            self.digraph.add_edge(cell2, cell_unst)
                        continue
                # Add double edges if get to here
                self.digraph.add_edge(cell1, cell2)
                self.digraph.add_edge(cell2, cell1)
