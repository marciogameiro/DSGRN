# EquilibriumCells.py
# Marcio Gameiro
# MIT LICENSE
# 2024-05-21

import DSGRN
import pychomp

__all__ = ['EquilibriumCells']

def EquilibriumCells(parameter, eqtype='all', eqformat='coords'):
    """Return the DSGRN equilibrium cells for the given parameter.
    """
    # Check if equilibrium cell type is valid
    eqtype_vals = ['all', 'a', 'topdim', 't', 'nontop', 'n']
    if eqtype not in eqtype_vals:
        raise ValueError(f"Invalid value '{eqtype}' for eqtype. Supported values are: {', '.join(map(repr,eqtype_vals))}.")
    # Check if equilibrium output format is valid
    eqformat_vals = ['coords', 'c', 'index', 'i']
    if eqformat not in eqformat_vals:
        raise ValueError(f"Invalid value '{eqformat}' for eqformat. Supported values are: {', '.join(map(repr,eqformat_vals))}.")
    # Get the parameter index in the original parameter graph
    original_par_graph = DSGRN.ParameterGraph(parameter.network())
    par_index = original_par_graph.index(parameter)
    # Redefine network without self edges blowup
    net_spec = parameter.network().specification()
    network = DSGRN.Network(net_spec, edge_blowup='none')
    # Get the parameter in the new parameter graph
    parameter_graph = DSGRN.ParameterGraph(network)
    parameter = parameter_graph.parameter(par_index)
    D = network.size()
    limits = [len(network.outputs(d)) + 1 for d in range(D)]
    # Use a cubical complex to access lower dimensional cells
    cc = pychomp.CubicalComplex([n + 1 for n in limits])
    labelling = parameter.labelling()
    pv = [1]
    for k in limits:
        pv.append(pv[-1] * k)

    def closedrightfringe(c):
        return any(cc.rightfringe(k) for k in cc.star({c}))

    def Absorbing(kappa, d, direction):
        """Return True if the codim 1 face of top cell kappa collapsed
        in dimension d in direction "direction" is absorbing. Here
        direction = -1 means left wall and direction = 1 means right wall.
        """
        coords = cc.coordinates(kappa)
        # The "wrap layer" boxes have all walls absorbing
        if any(coords[d] == limits[d] for d in range(D)):
            return True
        # The cc kappa indexing is not compatible with labelling indexing
        # due to the extra wrapped layer, so we compute the index idx
        idx = sum(c * pv[k] for (k, c) in enumerate(coords))
        labelbit = 1 << (d + (D if direction == 1 else 0))
        return labelling[idx] & labelbit != 0

    def RookField(kappa):
        """Return the rook field of a cubical top-cell kappa as a list
        of tuples, where each tuple gives the sign of the flow at the
        lef and right walls, respectively.
        """
        sign = lambda kappa, d, direc: direc if Absorbing(kappa, d, direc) else -direc
        return [(sign(kappa, d, -1), sign(kappa, d, 1)) for d in range(D)]

    def NormalVariables(sigma):
        # Inessential directions
        shape = cc.cell_shape(sigma)
        return [d for d in range(D) if shape & (1 << d) == 0]

    def TangentVariables(sigma):
        # Essential directions
        shape = cc.cell_shape(sigma)
        return [d for d in range(D) if shape & (1 << d) != 0]

    def Shape(sigma):
        """Return shape of sigma as a tuple.
        """
        shape = cc.cell_shape(sigma)
        return [1 if (shape & (1 << d) != 0) else 0 for d in range(D)]

    def RelativePositionVector(sigma, tau):
        """Return the relative position vector of sigma with respect to tau. This is
        equal to the difference of combinatorial position of two cells, regarding
        vertices to be at (even, even, ...) integer coordinates and higher dimensional
        cells to have odd coordinates for their dimensions with extent.
        """
        # Matches the definiton in the paper if sigma is a face of tau
        return [x-y for (x, y) in zip(cc.barycenter(sigma), cc.barycenter(tau))]

    def Phi(sigma, kappa):
        """Return the rook field extension from a top-cell kappa to
        a lower dimensionl cell sigma.
        """
        rf = RookField(kappa)        # Rook field of top cell
        J_i = NormalVariables(sigma) # Inessential directions
        p = RelativePositionVector(sigma, kappa)
        # Set flow to zero if essential direction and opposite signs at walls
        phi = lambda left, right, d: (left if p[d] == -1 else right) if d in J_i else 0
        return [left if left == right else phi(left, right, d) for d, (left, right) in enumerate(rf)]

    def Opaque(sigma):
        """Return True if sigma is an opaque cubical cell.
        """
        J_i = NormalVariables(sigma) # Inessential directions
        # Compute Phi(sigma, kappa) for kappa in the top star of sigma
        phi_tstar = [Phi(sigma, kappa) for kappa in cc.topstar(sigma) if not cc.rightfringe(sigma)]
        return all(n not in J_i or set(phi) == {-1, 1} for (n, phi) in enumerate(zip(*phi_tstar)))

    def isEquilibriumCell(sigma):
        """Return True if sigma is an equilibrium cubical cell.
        """
        if closedrightfringe(sigma):
            return False
        if not Opaque(sigma):
            return False
        for kappa in cc.topstar(sigma):
            rf = RookField(kappa)
            if any(rf[d][0] == rf[d][1] for d in TangentVariables(sigma)):
                return False
        return True

    # Get equilibrium cells
    if eqtype in ['all', 'a']:
        # Get all equilibrium cells
        eq_cells = [sigma for sigma in cc if isEquilibriumCell(sigma)]
    elif eqtype in ['topdim', 't']:
        # Get only the top-dimensional equilibrium cells
        eq_cells = [sigma for sigma in cc if isEquilibriumCell(sigma) if cc.cell_dim(sigma) == D]
    elif eqtype in ['nontop', 'n']:
        # Get only the lower-dimensional equilibrium cells
        eq_cells = [sigma for sigma in cc if isEquilibriumCell(sigma) if cc.cell_dim(sigma) < D]
    # else: # Unreachable

    # Return the indices if eqformat is index
    if eqformat in ['index', 'i']:
        return eq_cells

    # Return coordinates (eqformat is coords)
    if eqtype in ['topdim', 't']:
        # Return only the coordinates of lowest vertex
        equilibrium_cells = [tuple(cc.coordinates(sigma)) for sigma in eq_cells]
    else:
        # Return coordinates of lowest vertex and shape of cell
        equilibrium_cells = [[tuple(cc.coordinates(sigma)), tuple(Shape(sigma))] for sigma in eq_cells]
    return equilibrium_cells
