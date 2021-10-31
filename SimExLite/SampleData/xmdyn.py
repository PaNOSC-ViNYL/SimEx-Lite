# Copyright (C) 2021 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.

import h5py
import numpy as np
import matplotlib.pyplot as plt
from pysingfel import radiationDamage


class xmdynData:
    """xmdyn Data class

    :param input_path: Path to XMDYN HDF5 data
    :type input_path: str
    """
    def __init__(self, input_path=None):
        self.input_path = input_path

    @property
    def diam(self):
        try:
            return self._diam
        except AttributeError:
            return self.getDiam()

    @property
    def focus_area(self):
        return np.pi / 4 * self.diam**2

    @property
    def n_photons(self):
        """The n_photons property."""
        try:
            return self._n_photons
        except AttributeError:
            return self.get_n_photons()

    def get_n_photons(self):
        """Get the number of photons of each time frame"""
        fname = self.input_path
        n_photons = []
        with h5py.File(fname, 'r') as f:
            n_frame = len(f['data']) - 1
            for i in range(n_frame):
                datasetname = '/data/snp_' + '{0:07}'.format(i + 1) + '/Nph'
                n_photons.append(f[datasetname][()][0])
        self._n_photons = np.array(n_photons)
        return self.n_photons

    def plot_n_photons(self):
        n_photons = self.n_photons
        #     plt.figure(figsize=(8,6))
        plt.figure()
        plt.plot(n_photons)
        n_phontons_idx = np.indices(n_photons.shape)
        plt.plot(n_phontons_idx[0][::10], n_photons[::10], 'o')
        plt.xlabel('time slice #')
        plt.ylabel('number of photons')

    def plot_n_photons_time(self):
        n_photons = self.n_photons
        #     plt.figure(figsize=(8,6))
        times = self.getTime() * 1e15
        plt.figure()
        plt.plot(times, n_photons)
        plt.plot(times[::10], n_photons[::10], 'o')
        plt.xlabel('time (fs)')
        plt.ylabel('number of photons')

    def getTime(self, *snapshots, is_print=False):
        file = self.input_path
        with h5py.File(file, 'r') as f:
            times = []
            g_time = f['misc/time']
            for i in g_time:
                times.append(g_time[i][0])
            times = np.array(times)
            t_step = times[1] - times[0]

            if (is_print):
                print(f"n_frame = {times.shape[0]}")
                print(f"time start = {times[0]*1e15:.3g} fs")
                print(f"time end = {times[-1]*1e15:.3g} fs")
                print(f"time step = {t_step*1e15:.3g} fs")
                print("Returned time in unit of second")

                if (snapshots):
                    for step in snapshots:
                        print(
                            f"time at step {step} = {times[step]*1e15:.3g} fs")

            return np.array(times)

    def getDiam(self):
        """The diameter (m) of the beam"""
        with h5py.File(self.input_path, 'r') as h5:
            lines = [
                l.split(' ')
                for l in h5['params/xparams'][()].decode('utf-8').split("\n")
            ]
            xparams = radiationDamage.get_dict_from_lines(lines)
            diam = xparams['DIAM']
            self._diam = diam
        return self._diam

    def getN_phot_slice(self, timeSlice, sliceInterval):
        """Get the photons in one time slice"""
        fname = self.input_path
        n_phot = 0
        for i in range(sliceInterval):
            with h5py.File(fname, 'r') as f:
                datasetname = '/data/snp_' + '{0:07}'.format(
                    timeSlice - i) + '/Nph'
                n_phot += f[datasetname][0]
        return n_phot

    def getSnpGroupList(self, snp_idx=1):
        """Get the dataset list of a snapshot group.

        :param snp_idx: Snapshot index to check, defaults to 1
        :type snp_idx: int

        :return: A list of datasets in the snapshot group
        :rtype: list
        """
        return getItemList(self.input_path, 'data/' + snpName(snp_idx))

    def replaceWithExternal(self,
                            ref_path,
                            ref_dsets,
                            ref_snp=1,
                            snp_range=None):
        """Replace a dataset in a snapshot range with that in another referece .h5 file.

        :param input_path: The input .h5 file name
        :type input_path: str
        :param ref_path: The reference .h5 file name
        :type ref_path: str
        :param ref_dsets: The reference dataset name.
        :type ref_dsets: str
        :param ref_snp: The reference snapshot, defaults to 1.
        :type ref_snp: int
        :param snp_range: The snapshot range to replace, defaults to ``None``, which takes
            the snapshot range in the reference .h5 file.
        :type snp_range: list-like
        """

        try:
            iter(ref_dsets)
        except TypeError:
            ref_dsets = [ref_dsets]

        if not snp_range:
            snp_range = getSnpRange(ref_path)

        try:
            iter(snp_range)
        except TypeError:
            raise TypeError('snp_range ({}) is not iterable'.format(
                type(snp_range)))

        with h5py.File(self.input_path, "r+") as h5_in:
            for snp_idx in snp_range:
                snp = snpName(snp_idx)
                for ref_dset in ref_dsets:
                    try:
                        del h5_in['data'][snp][ref_dset]
                    except KeyError:
                        pass
                    h5_in['data'][snp][ref_dset] = h5py.ExternalLink(
                        ref_path, 'data/{}/{}'.format(snpName(ref_snp),
                                                      ref_dset))


def snpName(idx):
    """Get the snapshot group name from an int index"""
    return 'snp_{0:07}'.format(idx)


def getItemList(input_path, group):
    """Get a list of items in one group in a hdf5 file.

    :param input_path: The hdf5 file of to check.
    :type input_path: str
    :param group: The group path to check.
    :type group: str

    :return: (item name, data shape) in the group
    :rtype: list
    """
    with h5py.File(input_path, 'r') as h5:
        h5group = h5[group]
        items = []

        for dname, ds in h5group.items():
            try:
                items.append((dname, ds.shape))
            except AttributeError:
                items.append((dname, 'group'))

    return items


def createLinkedData(input_path,
                     link_path,
                     snp_range=None,
                     ref_dsets=None,
                     ref_snp=1):
    """Create a hdf5 data with all items linked to an input data. A
        certain dataset can be replaced with that in a reference snapshot,
        if ``ref_snp`` and ``ref_dsets`` are provided.

    :param input_path: The input hdf5 file name
    :type input_path: str
    :param link_path: The hdf5 file name holding the links
    :type link_path: str
    :param snp_range: The snapshot range to replace, defaults to ``None``, which takes
        the snapshot range in the reference .h5 file.
    :type snp_range: list-like
    :param ref_dsets: The reference dataset name.
    :type ref_dsets: str
    :param ref_snp: The reference snapshot, defaults to 1.
    :type ref_snp: int
    """

    # Set it iterable
    try:
        iter(ref_dsets)
    except TypeError:
        ref_dsets = [ref_dsets]

    if not snp_range:
        snp_range = getSnpRange(input_path)

    try:
        iter(snp_range)
    except TypeError:
        raise TypeError('snp_range ({}) is not iterable'.format(
            type(snp_range)))

    with h5py.File(link_path, "w") as h5_out:
        h5_out_data = h5_out.create_group('data')

        with h5py.File(input_path, 'r') as h5_in:
            for key in h5_in:
                if key != 'data':
                    h5_out[key] = h5py.ExternalLink(input_path, key)

            key = 'data/angle'
            h5_out[key] = h5py.ExternalLink(input_path, key)

            for snp_idx in snp_range:
                snp = snpName(snp_idx)
                h5_out_data.create_group(snp)
                for item in h5_in['data'][snp]:
                    if item in ref_dsets:
                        h5_out_data[snp][item] = h5py.ExternalLink(
                            input_path,
                            'data/{}/{}'.format(snpName(ref_snp), item))
                    else:
                        h5_out_data[snp][item] = h5py.ExternalLink(
                            input_path, 'data/{}/{}'.format(snp, item))


def getSnpRange(input_path):
    """Get the snapshot range of a .h5 file"""
    with h5py.File(input_path, "r") as h5_in:
        snp_range = []
        for i in h5_in['data'].items():
            group_name = i[0]
            if group_name != 'angle':
                snp_range.append(int(group_name.split('_')[1]))
    return snp_range


def getTimeSlices(slice_interval, number_of_slices):
    done = False
    time_slice = 0
    time_slices = []
    while not done:
        # set time slice to calculate diffraction pattern
        if time_slice + slice_interval >= number_of_slices:
            slice_interval = number_of_slices - time_slice
            done = True
        time_slice += slice_interval
        time_slices.append(time_slice)
    return time_slices


def replaceDset(input_path, ref_path, ref_dsets):
    """Replace/Add dataset with that in another referece .h5 file.

    """
    try:
        iter(ref_dsets)
    except TypeError:
        ref_dsets = [ref_dsets]

    with h5py.File(input_path, "r+") as h5_in:
        for ref_dset in ref_dsets:
            try:
                del h5_in[ref_dset]
            except KeyError:
                pass
            h5_in[ref_dset] = h5py.ExternalLink(ref_path, ref_dset)