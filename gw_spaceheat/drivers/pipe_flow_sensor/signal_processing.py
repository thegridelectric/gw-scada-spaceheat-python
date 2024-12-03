import numpy as np

def butter_lowpass(N=5, Wn=2, fs=250):
    Wn = np.asarray(Wn)
    Wn = 2*Wn/fs
    # Get analog lowpass prototype
    z = np.array([])
    m = np.arange(-N+1, N, 2)
    p = -np.exp(1j * np.pi * m / (2 * N))
    k = 1
    # Pre-warp frequencies for digital filter design
    fs = 2.0
    warped = 2 * fs * np.tan(np.pi * Wn / fs)
    # transform to lowpass
    wo = float(warped)
    degree = len(p) - len(z)
    z = wo * z
    p = wo * p
    k = k * wo**degree
    # Find discrete equivalent
    degree = len(p) - len(z)
    fs2 = 2.0*fs
    z_z = (fs2 + z) / (fs2 - z)
    p_z = (fs2 + p) / (fs2 - p)
    z_z = np.append(z_z, -np.ones(degree))
    k_z = k * np.real(np.prod(fs2 - z) / np.prod(fs2 - p))
    z, p, k = z_z, p_z, k_z
    # Transform for output
    b = k * np.poly(z)
    a = np.atleast_1d(np.poly(p))
    return b, a


def lfilter_zi(b, a):
    b = np.atleast_1d(b)
    a = np.atleast_1d(a)
    # Remove leading zeros from the numerator (b) and denominator (a)
    while len(a) > 1 and a[0] == 0.0:
        a = a[1:]
    # Normalize the coefficients so that a[0] == 1.0
    if a[0] != 1.0:
        b = b / a[0]
        a = a / a[0]
    n = max(len(a), len(b))
    # Pad a and b to make their lengths equal to n
    if len(a) < n:
        a = np.r_[a, np.zeros(n - len(a), dtype=a.dtype)]
    elif len(b) < n:
        b = np.r_[b, np.zeros(n - len(b), dtype=b.dtype)]
    # Construct the companion matrix: I - A^-1 (where A^-1 is represented in a column form)
    companion_matrix = np.eye(n - 1, dtype=np.result_type(a, b))
    # Create the last column as a column vector
    last_column = np.zeros((n - 1, 1)) 
    last_column[:] = (-a[1:] / a[0]).reshape(-1, 1)
    IminusA = companion_matrix - last_column.T 
    # Vector B, adjusting the first element of b
    B = b[1:] - a[1:] * b[0]
    # Solve the linear system
    zi = np.linalg.solve(IminusA, B)
    return zi


def axis_slice(a, start=None, stop=None, step=None, axis=-1):
    a_slice = [slice(None)] * a.ndim
    a_slice[axis] = slice(start, stop, step)
    b = a[tuple(a_slice)]
    return b


def simple_linear_filter(b, a, x, axis=-1, initial=None):
    b = np.asarray(b)
    a = np.asarray(a)
    x = np.asarray(x)
    if initial is None:
        initial = np.zeros(len(a) - 1)
    y = np.zeros_like(x)
    z = initial.copy()
    if axis == -1:
        axis = x.ndim - 1
    for i in range(len(x)):
        output = 0
        for j in range(len(b)):
            if i - j >= 0:
                output += b[j] * x[i - j]
        for k in range(1, len(a)):
            if i - k >= 0:
                output -= a[k] * y[i - k]
        y[i] = output
        z = np.roll(z, 1)
        z[0] = output
    return y, z


def odd_ext(x, n, axis=-1):
    if n < 1:
        return x
    left_end = axis_slice(x, start=0, stop=1, axis=axis)
    left_ext = axis_slice(x, start=n, stop=0, step=-1, axis=axis)
    right_end = axis_slice(x, start=-1, axis=axis)
    right_ext = axis_slice(x, start=-2, stop=-(n + 2), step=-1, axis=axis)
    ext = np.concatenate((2 * left_end - left_ext,
                          x,
                          2 * right_end - right_ext),
                          axis=axis)
    return ext


def filtering(b, a, x, axis=-1, padtype='odd', padlen=None, method='pad',
             irlen=None):
    b = np.atleast_1d(b)
    a = np.atleast_1d(a)
    x = np.asarray(x)
    # Padding
    ntaps = 10 * max(len(a), len(b)) #default: 3 instead of 10
    edge = ntaps * 3
    ext = odd_ext(x, edge, axis=axis)
    # Get the steady state of the filter's step response.
    zi = lfilter_zi(b, a)
    # Reshape zi and create x0 so that zi*x0 broadcasts appropriately.
    zi_shape = [1] * x.ndim
    zi_shape[axis] = zi.size
    zi = np.reshape(zi, zi_shape)
    x0 = axis_slice(ext, stop=1, axis=axis)
    # Forward filter.
    (y, zf) = simple_linear_filter(b, a, ext, axis=axis, initial=zi * x0)
    # Backward filter.
    # Create y0 so zi*y0 broadcasts appropriately.
    y0 = axis_slice(y, start=-1, axis=axis)
    (y, zf) = simple_linear_filter(b, a, axis_slice(y, step=-1, axis=axis), axis=axis, initial=zi * y0)
    # Reverse y.
    y = axis_slice(y, step=-1, axis=axis)
    if edge > 0:
        # Slice the actual signal from the extended signal.
        y = axis_slice(y, start=edge, stop=-edge, axis=axis)
    return y