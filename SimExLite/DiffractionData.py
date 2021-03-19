"""Diffraction Data API"""

import os
from pathlib import Path
import numpy as np
import h5py
import matplotlib.pylab as plt
import matplotlib.colors as colors
from scipy.sparse import csr_matrix
import argparse


class DiffractionData:
    def __init__(self, input_path) -> None:
        super().__init__()
        self.input_path = input_path
    def getArray(self, )




class PatternsSOne:
    ATTRS = ["ones", "multi", "place_ones", "place_multi", "count_multi"]

    def __init__(
        self,
        num_pix: int,
        ones: np.ndarray,
        multi: np.ndarray,
        place_ones: np.ndarray,
        place_multi: np.ndarray,
        count_multi: np.ndarray,
    ) -> None:
        self.num_pix = num_pix
        self._ones = ones
        self._multi = multi
        self._place_ones = place_ones
        self._place_multi = place_multi
        self._count_multi = count_multi
        self._ones_idx = np.zeros(self.num_data + 1, dtype=self._ones.dtype)
        np.cumsum(self._ones, out=self._ones_idx[1:])
        self._multi_idx = np.zeros(self.num_data + 1, dtype=self._multi.dtype)
        np.cumsum(self._multi, out=self._multi_idx[1:])

    def __len__(self):
        return self.num_data

    @property
    def num_data(self):
        return len(self._ones)

    @property
    def shape(self):
        return self.num_data, self.num_pix

    def write(self, path) -> None:
        with Path(path).open("wb") as fptr:
            header = np.zeros((256), dtype="i4")
            header[:2] = [self.num_data, self.num_pix]
            header.tofile(fptr)
            for g in PatternsSOne.ATTRS:
                self.attrs(g).astype("i4").tofile(fptr)

    def attrs(self, g):
        if g == "ones_idx":
            return self._ones_idx
        if g == "multi_idx":
            return self._multi_idx
        if g == "ones":
            return self._ones
        if g == "multi":
            return self._multi
        if g == "place_ones":
            return self._place_ones
        if g == "place_multi":
            return self._place_multi
        if g == "count_multi":
            return self._count_multi
        raise ValueError(f"What is {g}?")

    def _get_sparse_ones(self) -> csr_matrix:
        _one = np.ones(1, "i4")
        _one = np.lib.stride_tricks.as_strided(  # type: ignore
            _one,
            shape=(self._place_ones.shape[0], ),
            strides=(0, ))
        return csr_matrix((_one, self._place_ones, self._ones_idx),
                          shape=self.shape)

    def _get_sparse_multi(self) -> csr_matrix:
        return csr_matrix(
            (self._count_multi, self._place_multi, self._multi_idx),
            shape=self.shape)

    def todense(self) -> np.ndarray:
        """
        To dense ndarray
        """
        return np.squeeze(self._get_sparse_ones().todense()
                          + self._get_sparse_multi().todense())


def dense_to_PatternsSOne(arr: np.ndarray) -> PatternsSOne:
    mask_one = arr == 1
    mask_multi = arr > 1
    place_ones = np.where(mask_one)[1]
    pmask, place_multi = np.where(mask_multi)  # pmask: pattern mask
    return PatternsSOne(
        arr.shape[1],
        np.sum(mask_one, axis=1, dtype=np.int32),
        np.sum(mask_multi, axis=1, dtype=np.int32),
        place_ones.astype(np.int32),
        place_multi.astype(np.int32),
        arr[pmask, place_multi].astype(np.int32),
    )


def parse_bin_PatternsSOne(fn: str):
    path = Path(fn)
    with path.open("rb") as fin:
        num_data = np.fromfile(fin, dtype=np.int32, count=1)[0]
        start, end = 0, num_data
        num_pix = np.fromfile(fin, dtype=np.int32, count=1)[0]
        fin.seek(1024)
        ones = np.fromfile(fin, dtype=np.int32, count=num_data)
        multi = np.fromfile(fin, dtype=np.int32, count=num_data)
        fin.seek(4 * ones[:start].sum(), os.SEEK_CUR)
        place_ones = np.fromfile(fin,
                                 dtype=np.int32,
                                 count=ones[start:end].sum())
        fin.seek(4 * (ones[end:].sum() + multi[:start].sum()), os.SEEK_CUR)
        sum_multi = multi[start:end].sum()
        place_multi = np.fromfile(fin, dtype=np.int32, count=sum_multi)
        fin.seek(4 * (multi[end:].sum() + multi[:start].sum()), os.SEEK_CUR)
        count_multi = np.fromfile(fin, dtype=np.int32, count=sum_multi)
        fin.seek(4 * multi[end:].sum(), os.SEEK_CUR)
        if fin.read(1):
            raise Exception(f"Error when parsing {path}")
    ones = ones[start:end]
    multi = multi[start:end]
    return PatternsSOne(
        num_pix,
        ones,
        multi,
        place_ones,
        place_multi,
        count_multi,
    )


def plotEMCPhoton(fn, idx=0, shape=None):
    sPattern = parse_bin_PatternsSOne(fn)
    print(sPattern.num_pix)
    data = sPattern.todense()
    if not shape:
        shape = (-1, int(np.sqrt(sPattern.num_pix)))
    plt.imshow(data[idx].reshape(shape), norm=colors.LogNorm())
    plt.colorbar()
    plt.show()


def test():
    data = (np.random.rand(10, 40)**5 * 5).astype(np.int32)
    dense_to_PatternsSOne(data).write("t.bin")


def main(input_file, output_file):
    print('converting', input_file, 'to', output_file)
    data = []
    with h5py.File(input_file, "r") as fp:
        dp = fp['data']
        for fidx in sorted(dp.keys()):  # fidx: frame index
            data.append(dp[fidx]['data'][...].flatten())
        data = np.array(data)
    patterns = dense_to_PatternsSOne(data)
    print(patterns.shape)
    print('writing')
    patterns.write(output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='input file name')
    parser.add_argument('-o',
                        '--output',
                        default='photons.emc',
                        help='output file name (default: %(default)s)')
    args = parser.parse_args()
    main(args.input, args.output)
