# Copyright (C) 2021 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""Sample Structure Data APIs"""
import h5py
# import ase


class MolecularDynamicsData:
    """Molecular Dynamics Data class

    :param input_path: Path to data file
    :type input_path: str
    """
    def __init__(self, input_path=None):
        self.input_path = input_path
        self.file_format = self.__getFileFormat()

    def __getFileFormat(self) -> str:
        """ Check the file format.
        HDF5:
            openPMD-MD
            XMDYN
        ASCII:
            Handled by ASE

        """
        if h5py.is_hdf5(self.input_path):
            with h5py.File(self.input_path, 'r') as h5:
                try:
                    version = h5['/info/package_version'][()].decode('ascii')
                except KeyError:
                    return "UNKNOWN"
                if version.find('XMDYN') != -1:
                    return "XMDYN"
                else:
                    return "UNKNOWN"


# %%
class xmdynData:
    """xmdyn Data class

    :param input_path: Path to XMDYN hdf5 data
    :type input_path: str
    """
    def __init__(self, input_path=None):
        self.input_path = input_path

    def getSnpGroupList(self, snp_idx=1):
        """Get the dataset list of a snapshot group.

        :param snp_idx: Snapshot index to check, defaults to 1
        :type snp_idx: int

        :return: A list of datasets in the snapshot group
        :rtype: list
        """
        return getItemList(self.input_path, 'data/' + snpName(snp_idx))

    # Softlink seems not working for datasets
    # def softlinkData(self, ref_dset, ref_snp=1):
    #     """Replace a dataset of a snapshot with a softlink of a
    #     reference snapshot.

    #     :param ref_dset: The reference dataset name.
    #     :type ref_dset: str
    #     :param ref_snp: The reference snapshot, defaults to 1.
    #     :type ref_snp: int
    #     """
    #     input_path = self.input_path
    #     ref_snp_name = snpName(ref_snp)

    #     with h5py.File(input_path, "r+") as h5_in:
    #         snp_range = getSnpRange(input_path)
    #         ref_snp_index = ref_snp - 1
    #         snp_range.pop(ref_snp_index)
    #         # for snp_idx in tqdm(snp_range):
    #         for snp_idx in snp_range:
    #             snp = snpName(snp_idx)
    #             try:
    #                 del h5_in['data'][snp][ref_dset]
    #             except KeyError:
    #                 pass
    #             h5_in['data'][snp][ref_dset] = h5py.SoftLink(
    #                 'data/{}/{}'.format(ref_snp_name, ref_dset))

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
