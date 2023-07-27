# Copyright (C) 2023 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""Basic utility module"""

import numpy as np


def rebin_sum(arr:np.ndarray, new_shape):
    n_dim = [arr.shape[0] // new_shape[0], arr.shape[1] // new_shape[1]]
    shape = (new_shape[0], n_dim[0], new_shape[1], n_dim[1])
    # extra_rows = arr[new_shape[0] * n_dim[0]:, :]
    # extra_cols = arr[:, new_shape[1] * n_dim[1]:]
    # if len(extra_rows) > 0:
    #     arr[new_shape[0] * n_dim[0] - 1, :] += extra_rows.sum(axis=0)
    # if len(extra_cols) > 0:
    #     arr[:, new_shape[1] * n_dim[1] - 1] += extra_cols.sum(axis=1)
    return (
        arr[: new_shape[0] * n_dim[0], : new_shape[1] * n_dim[1]]
        .reshape(shape)
        .sum(-1)
        .sum(-2)
    )
