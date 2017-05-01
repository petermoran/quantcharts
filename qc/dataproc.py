import numpy as np
from PyQt5.QtGui import QPolygonF


def to_polyline(xbar, ybar):
    """Convert plot data to QPolygon(F) polyline.
    
    This code is derived from plotpy qtcharts example. 
    
    """
    # TODO support multiple dims
    nx = len(xbar)
    if nx != len(ybar):
        raise ValueError("x and y must have the same len")

    polyline = QPolygonF(nx)
    pointer = polyline.data()

    # TODO support different dtypes
    dtype, tinfo = np.float, np.finfo  # integers: = np.int, np.iinfo
    pointer.setsize(2*polyline.size()*tinfo(dtype).dtype.itemsize)
    memory = np.frombuffer(pointer, dtype)
    memory[:(nx-1)*2+1:2] = xbar
    memory[1:(nx-1)*2+2:2] = ybar
    return polyline
