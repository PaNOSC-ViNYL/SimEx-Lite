""":module SimpleScatteringPMICalculator: Module that holds the SimpleScatteringPMICalculator class."""

import os
import shutil
import sys
import tempfile
from pathlib import Path

import h5py
import numpy

from libpyvinyl import BaseCalculator, CalculatorParameters
from libpyvinyl.BaseData import DataCollection
from SimExLite.PMIData import PMIData, XMDYNFormat
from SimExLite.SampleData import ASEFormat, SampleData
from SimExLite.WavefrontData import WavefrontData, WPGFormat
from .atomic_form_factor import load_ff_database


class SimpleScatteringPMICalculator(BaseCalculator):
    """Class representing simple elastic scattering process."""

    def __init__(
        self,
        name: str,
        input: DataCollection,
        output_keys: str = "PMI",
        output_data_types=PMIData,
        output_filenames: str = "PMI.h5",
        instrument_base_dir="./",
        calculator_base_dir="SimpleScatteringPMICalculator",
        parameters=None,
    ):
        super().__init__(
            name,
            input,
            output_keys,
            output_data_types=output_data_types,
            output_filenames=output_filenames,
            instrument_base_dir=instrument_base_dir,
            calculator_base_dir=calculator_base_dir,
            parameters=parameters,
        )

    def init_parameters(self):
        """Initialize with default parameters"""
        parameters = CalculatorParameters()
        num_steps = parameters.new_parameter(
            "number_of_steps", comment="The number of time steps. Default = 1"
        )
        num_steps.value = 1

        self.parameters = parameters

    def __check_input_type(self):
        # This check can be implemented in the BaseCalculator class
        if not isinstance(self.input.to_list()[0], SampleData):
            raise TypeError(
                f"input[0] should be in SampleData type, instead of {type(self.input.to_list()[0])}"
            )
        if not isinstance(self.input.to_list()[1], WavefrontData):
            raise TypeError(
                f"input[1] should be in WavefrontData type, instead of {type(self.input.to_list[1])}"
            )

    def backengine(self):

        # Prepare input files
        self.__check_input_type()
        Path(self.base_dir).mkdir(parents=True, exist_ok=True)

        if len(self.output_filenames) != 1:
            raise RuntimeError(
                "The number of output_filenames has to be 1 for this calculator."
            )
        output_fn = str(Path(self.base_dir) / self.output_filenames[0])
        sample_data, wavefront_data = self.input.to_list()
        wavefront_fn = prepare_wavefront_file(wavefront_data)

        # Initialize the output HDF5 file with the file structure defined for XMDYN.
        f_h5_out2in(wavefront_fn, output_fn)

        # Miscellaneous parameters to comply with the XMDYN format.
        pmi_scattering = PMIScattering()
        pmi_scattering.g_s2e["prj"] = ""
        pmi_scattering.g_s2e["id"] = "0000001"
        pmi_scattering.g_s2e["prop_out"] = wavefront_fn
        pmi_scattering.g_s2e["setup"] = dict()
        pmi_scattering.g_s2e["sys"] = dict()
        pmi_scattering.g_s2e["setup"]["num_digits"] = 7
        pmi_scattering.g_s2e["steps"] = self.parameters["number_of_steps"].value
        # The maximum atomic number considered in the simulation
        pmi_scattering.g_s2e["maxZ"] = 100
        pmi_scattering.g_s2e["random_rotation"] = False
        pmi_scattering.g_s2e["setup"]["pmi_out"] = output_fn


        pmi_scattering.f_dbase_setup()
        pmi_scattering.f_save_info()
        pmi_scattering.f_load_pulse(pmi_scattering.g_s2e["prop_out"])

        pmi_scattering.g_s2e["sample"] = SampleData_to_atoms_dict(sample_data)
        pmi_scattering.f_rotate_sample()
        pmi_scattering.f_system_setup()
        pmi_scattering.f_time_evolution()

        assert len(self.output_keys) == 1
        key = self.output_keys[0]
        output_data = self.output[key]
        output_data.set_file(output_fn, XMDYNFormat)

        return self.output


def prepare_wavefront_file(wavefront_data: WavefrontData):
    """Prepare the wavefront file for the backengine"""

    if wavefront_data.mapping_type == WPGFormat:
        wavefront_fn = wavefront_data.filename
    else:
        temp_name = next(tempfile._get_candidate_names())
        wavefront_fn = "input_wavefront_" + temp_name + ".h5"
        wavefront_data.write(wavefront_fn, WPGFormat)

    return wavefront_fn


def SampleData_to_atoms_dict(sample_data: SampleData) -> dict:
    """Read the sampleData object into an atoms_dict for the backengine"""

    atoms_dict = {
        "Z": [],  # Atomic number.
        "r": [],  # Cartesian coordinates.
        "selZ": {},  # Abundance of each element.
        "N": 0,  # Number of atoms.
    }
    input_dict = sample_data.get_data()
    atoms_dict["Z"] = input_dict["atomic_numbers"]
    atoms_dict["r"] = input_dict["positions"] * 1e-10
    atoms_dict["N"] = len(input_dict["atomic_numbers"])
    for sel_Z in numpy.unique(atoms_dict["Z"]):
        atoms_dict["selZ"][sel_Z] = numpy.nonzero(atoms_dict["Z"] == sel_Z)[0]

    # empty line before return is recommended to enhance readability
    return atoms_dict


class PMIScattering(object):
    """The core of the elastic scattering simulation."""

    def __init__(self):
        """Initialize the simulation parameter and database dictionary."""
        self.g_s2e = {}
        self.g_dbase = {}

        self.f_s2e_setup()

    def f_s2e_setup(self):
        """Set initial parameters of the simulation."""
        self.g_s2e["setup"] = dict()
        self.g_s2e["sys"] = dict()
        self.g_s2e["setup"]["num_digits"] = 7
        self.g_s2e["steps"] = 100
        self.g_s2e["maxZ"] = 100

    def f_save_info(self):
        """Create info group in the output h5 file."""

        pmi_file = self.g_s2e["setup"]["pmi_out"]

        grp = "/info"
        xfp = h5py.File(pmi_file, "a")
        try:
            grp_hist_parent = xfp.create_group(grp)
        except:
            1
        xfp.close()

    def f_dbase_Zq2id(self, a_Z, a_q):
        # This is not clear.
        return (a_Z * (a_Z + 1)) // 2 - 1 * 1 + a_q

    def f_dbase_setup(self):
        """Set initial parameters of the structure factor ff."""
        xdbase = load_ff_database()

        g_dbase = dict()

        #   q               ->   sin(theta/2)/lambda
        #   au, exp(i*q*r)  ->   1/Angstrom, exp( 2*pi*q*r)
        g_dbase["halfQ"] = xdbase[:, 0] = xdbase[:, 0] / (
            2.0 * numpy.pi * 0.529177206 * 2.0
        )
        maxZ = self.g_s2e["maxZ"]  # 99
        numQ = len(g_dbase["halfQ"])
        g_dbase["ff"] = numpy.zeros((self.f_dbase_Zq2id(maxZ, maxZ) + 1, numQ))
        ii = 0
        for ZZ in range(1, maxZ + 1):
            for qq in range(ZZ + 1):
                g_dbase["ff"][ii, :] = xdbase[:, ZZ] * (ZZ - qq) / (ZZ * 1.0)
                ii += 1

        g_dbase["Sq_halfQ"] = g_dbase["halfQ"]
        g_dbase["Sq_bound"] = numpy.zeros((numQ,))
        g_dbase["Sq_free"] = numpy.zeros((numQ,))

        self.g_dbase = g_dbase

    def f_load_snp_content(self, a_fp, a_snp):
        """Load a snapshot from a H5 file pointer.

        Args:
            a_fp (h5py.File): The H5 file containing snapshot information.
            a_snp (int): The snapshot index.

        Returns:
            dict: A dictionary of the snapshot data.
        """
        dbase_root = (
            "/data/snp_" + str(a_snp).zfill(self.g_s2e["setup"]["num_digits"]) + "/"
        )
        xsnp = dict()
        xsnp["Z"] = a_fp.get(dbase_root + "Z")[()]
        xsnp["T"] = a_fp.get(dbase_root + "T")[()]
        xsnp["ff"] = a_fp.get(dbase_root + "ff")[()]
        xsnp["xyz"] = a_fp.get(dbase_root + "xyz")[()]
        xsnp["r"] = a_fp.get(dbase_root + "r")[()]
        N = xsnp["Z"].size
        xsnp["q"] = numpy.array(
            [xsnp["ff"][numpy.nonzero(xsnp["T"] == x)[0], 0] for x in xsnp["xyz"]]
        ).reshape(
            N,
        )
        xsnp["snp"] = a_snp

        return xsnp

    def f_load_snp_xxx(self, a_real, a_snp):
        """Load a snapshot from a specific PMI file.

        Args:
            a_real (int): PMI file index.
            a_snp (int): The snapshot index.

        Returns:
            dict: A dictionary of the snapshot data.
        """
        xfp = h5py.File(
            self.g_s2e["prj"]
            + "/pmi/pmi_out_"
            + str(a_real).zfill(self.g_s2e["setup"]["num_digits"])
            + ".h5",
            "r",
        )
        xsnp = self.f_load_snp_content(xfp, a_snp)
        xfp.close()
        return xsnp

    def f_load_snp_from_dir(self, path_to_snapshot):
        """
        Loads xmdyn output from an xmdyn directory.

        Args:
            path (str): The directory path to xmdyn output.
            snapshot_index (int): Which snapshot to load.

        Returns:
            dict: The snapshot data.
        """

        xsnp = dict()
        xsnp["Z"] = numpy.loadtxt(
            os.path.join(path_to_snapshot, "Z.dat")
        )  # Atom numbers
        xsnp["T"] = numpy.loadtxt(os.path.join(path_to_snapshot, "T.dat"))  # Atom type
        xsnp["uid"] = numpy.loadtxt(
            os.path.join(path_to_snapshot, "uid.dat")
        )  # Unique atom ID.
        xsnp["r"] = numpy.loadtxt(
            os.path.join(path_to_snapshot, "r.dat")
        )  # Cartesian coordinates.
        xsnp["v"] = numpy.loadtxt(
            os.path.join(path_to_snapshot, "v.dat")
        )  # Cartesian velocities.
        xsnp["m"] = numpy.loadtxt(os.path.join(path_to_snapshot, "m.dat"))  # Masses.
        xsnp["q"] = numpy.loadtxt(os.path.join(path_to_snapshot, "q.dat"))  # Ion charge
        xsnp["ff"] = numpy.loadtxt(
            os.path.join(path_to_snapshot, "f0.dat")
        )  # Form factors of each atom type.
        xsnp["Q"] = numpy.loadtxt(
            os.path.join(path_to_snapshot, "Q.dat")
        )  # Wavenumber grid for form factors.

        return xsnp

    def f_load_sample(self, sample_path):
        """Load the sample data from a sample H5 file.

        Args:
            sample_path (str): Sample H5 file.
        """
        sample = dict()
        xfp = h5py.File(sample_path, "r")
        xxx = xfp.get("Z")
        sample["Z"] = xxx[()]
        xxx = xfp.get("r")
        sample["r"] = xxx[()]
        xfp.close()
        sample["selZ"] = dict()
        for sel_Z in numpy.unique(sample["Z"]):
            sample["selZ"][sel_Z] = numpy.nonzero(sample["Z"] == sel_Z)
        sample["N"] = len(sample["Z"])

        self.g_s2e["sample"] = sample

    def f_save_data(self, dset, data):
        """Save the data to a specific H5 dataset.

        Args:
            dset (str): The name of the H5 dataset.
            data (ndarray): The data to save.
        """
        xfp = h5py.File(self.g_s2e["setup"]["pmi_out"], "a")
        try:
            xfp.create_group(os.path.dirname(dset))
        except:
            1

        xfp[dset] = data
        xfp.close()

    def f_rotate_sample(self):
        """Rotate the sample with the rot_quaternion parameter."""
        # Init quaternion for rotation.
        self.g_s2e["sample"]["rot_quaternion"] = numpy.array([0, 0, 0, 0])

        # Set to random if desired.
        if self.g_s2e["random_rotation"] is True:
            self.g_s2e["sample"]["rot_quaternion"] = numpy.random.rand(4)
            self.g_s2e["sample"]["rotmat"] = numpy.zeros((9,))
            s2e_gen_randrot_quat(
                self.g_s2e["sample"]["rot_quaternion"], self.g_s2e["sample"]["rotmat"]
            )
            s2e_rand_orient(self.g_s2e["sample"]["r"], self.g_s2e["sample"]["rotmat"])

        self.f_save_data(
            "/data/angle", self.g_s2e["sample"]["rot_quaternion"].reshape((1, 4))
        )

    def f_system_setup(self):
        """Setup the system parameters."""
        self.g_s2e["sys"]["r"] = self.g_s2e["sample"]["r"].copy()
        self.g_s2e["sys"]["q"] = numpy.zeros(self.g_s2e["sample"]["Z"].shape)
        self.g_s2e["sys"]["NE"] = self.g_s2e["sample"]["Z"].copy()
        self.g_s2e["sys"]["Z"] = self.g_s2e["sample"]["Z"]
        self.g_s2e["sys"]["Nph"] = 1e99

    def f_save_snp(self, a_snp):
        """Save a snapshot.

        Args:
            a_snp (int): The index of the snapshot to save.
        """
        self.g_s2e["sys"]["xyz"] = self.f_dbase_Zq2id(
            self.g_s2e["sys"]["Z"], self.g_s2e["sys"]["q"]
        )
        self.g_s2e["sys"]["T"] = numpy.sort(numpy.unique(self.g_s2e["sys"]["xyz"]))
        ff = numpy.zeros((len(self.g_s2e["sys"]["T"]), len(self.g_dbase["halfQ"])))
        for ii in range(len(self.g_s2e["sys"]["T"])):
            ff[ii, :] = self.g_dbase["ff"][
                self.g_s2e["sys"]["T"][ii].astype(int), :
            ].copy()

        pmi_file = self.g_s2e["setup"]["pmi_out"]
        grp = "/data/snp_" + str(a_snp).zfill(self.g_s2e["setup"]["num_digits"])
        xfp = h5py.File(pmi_file, "a")
        try:
            grp_hist_parent = xfp.create_group("/data")
        except:
            1
        grp_hist_parent = xfp.create_group(grp)
        dt = 1e-15  # s

        xfp["misc/time/snp_" + str(a_snp).zfill(self.g_s2e["setup"]["num_digits"])] = (
            a_snp * dt
        )
        xfp[grp + "/charge"] = numpy.zeros_like(self.g_s2e["sys"]["Z"])
        xfp[grp + "/Z"] = self.g_s2e["sys"]["Z"]
        xfp[grp + "/T"] = self.g_s2e["sys"]["T"].astype(numpy.int32)
        xfp[grp + "/xyz"] = self.g_s2e["sys"]["xyz"].astype(numpy.int32)
        xfp[grp + "/r"] = self.g_s2e["sys"]["r"].astype(numpy.float32)
        xfp[grp + "/Nph"] = numpy.array([self.g_s2e["pulse"]["sel_int"][a_snp - 1]])
        xfp[grp + "/halfQ"] = self.g_dbase["halfQ"].astype(numpy.float32)
        xfp[grp + "/ff"] = ff.astype(numpy.float32)
        xfp[grp + "/Sq_halfQ"] = self.g_dbase["Sq_halfQ"].astype(numpy.float32)
        xfp[grp + "/Sq_bound"] = self.g_dbase["Sq_bound"].astype(numpy.float32)
        xfp[grp + "/Sq_free"] = self.g_dbase["Sq_free"].astype(numpy.float32)

        xfp.close()

    def f_num_snp_xxx(self, all_real):
        """Get the number of snapshots in a PMI file.

        Args:
            all_real (int): The PMI file index.

        Returns:
            int: The number of snapshots in the PMI file.
        """
        xfp = h5py.File(
            self.g_s2e["prj"]
            + "/pmi/pmi_out_"
            + str(all_real[0]).zfill(self.g_s2e["setup"]["num_digits"])
            + ".h5",
            "r",
        )
        cc = 1
        while 1:
            if not xfp.get(
                "/data/snp_" + str(cc).zfill(self.g_s2e["setup"]["num_digits"])
            ):
                xfp.close()
                return cc - 1
            cc = cc + 1

    def f_load_pulse(self, a_prop_out):
        """Load the propogated beam.

        Args:
            a_prop_out (str): The file name of the propogated beam.
        """

        xfp = h5py.File(a_prop_out, "r")
        self.g_s2e["pulse"] = dict()
        self.g_s2e["pulse"]["xFWHM"] = xfp.get("/misc/xFWHM")[()]
        self.g_s2e["pulse"]["yFWHM"] = xfp.get("/misc/yFWHM")[()]
        self.g_s2e["pulse"]["nSlices"] = xfp.get("params/Mesh/nSlices")[()]
        self.g_s2e["pulse"]["nx"] = xfp.get("params/Mesh/nx")[()]
        self.g_s2e["pulse"]["ny"] = xfp.get("params/Mesh/ny")[()]
        self.g_s2e["pulse"]["sliceMax"] = xfp.get("params/Mesh/sliceMax")[()]
        self.g_s2e["pulse"]["sliceMin"] = xfp.get("params/Mesh/sliceMin")[()]
        self.g_s2e["pulse"]["xMax"] = xfp.get("params/Mesh/xMax")[()]
        self.g_s2e["pulse"]["xMin"] = xfp.get("params/Mesh/xMin")[()]
        self.g_s2e["pulse"]["yMax"] = xfp.get("params/Mesh/yMax")[()]
        self.g_s2e["pulse"]["yMin"] = xfp.get("params/Mesh/yMin")[()]
        self.g_s2e["pulse"]["photonEnergy"] = xfp.get("params/photonEnergy")[()]
        self.g_s2e["pulse"]["arrEver"] = xfp.get("data/arrEver")[()]
        self.g_s2e["pulse"]["arrEhor"] = xfp.get("data/arrEhor")[()]
        xfp.close()

        # Take central pixel values.
        sel_x = self.g_s2e["pulse"]["nx"] // 2
        sel_y = self.g_s2e["pulse"]["ny"] // 2
        # note: the data order in the HDF5 file is not x,y but y,x
        sel_pixV = self.g_s2e["pulse"]["arrEver"][sel_y, sel_x, :, :]
        sel_pixH = self.g_s2e["pulse"]["arrEhor"][sel_y, sel_x, :, :]
        dt = (self.g_s2e["pulse"]["sliceMax"] - self.g_s2e["pulse"]["sliceMin"]) / (
            self.g_s2e["pulse"]["nSlices"] * 1.0
        )
        dx = (self.g_s2e["pulse"]["xMax"] - self.g_s2e["pulse"]["xMin"]) / (
            self.g_s2e["pulse"]["nx"] * 1.0
        )
        dy = (self.g_s2e["pulse"]["yMax"] - self.g_s2e["pulse"]["yMin"]) / (
            self.g_s2e["pulse"]["ny"] * 1.0
        )
        Eph = self.g_s2e["pulse"]["photonEnergy"] * 1.0

        NPH = 0
        for tt in range(self.g_s2e["pulse"]["nSlices"]):
            NPH += (
                sel_pixV[tt, 0] ** 2
                + sel_pixV[tt, 1] ** 2
                + sel_pixH[tt, 0] ** 2
                + sel_pixH[tt, 1] ** 2
            )

        NPH *= (
            1e6
            * dt
            * self.g_s2e["pulse"]["xFWHM"]
            * self.g_s2e["pulse"]["yFWHM"]
            / (Eph * 1.6022e-19)
        )

        # Distribute the number of photons evenly among the steps
        self.g_s2e["pulse"]["sel_int"] = numpy.ones((self.g_s2e["steps"],)) * (
            NPH / (1.0 * self.g_s2e["steps"])
        )

        return

    def f_time_evolution(self):
        for step in range(1, self.g_s2e["steps"] + 1):
            self.f_save_snp(step)


def s2e_gen_randrot_quat(quat, rotmat):
    """Generate a quaternion with random orientation and set the rotation matrix.

    Args:
        quat (ndarray): The quaternion array.
        rotmat (ndarray): The output rotation matrix.
    """

    if (
        0
        == quat[0] * quat[0] + quat[1] * quat[1] + quat[2] * quat[2] + quat[3] * quat[3]
    ):
        u0, u1, u2 = numpy.random.random(3)
        q0 = numpy.sqrt(1.0 - u0) * numpy.sin(2 * numpy.pi * u1)
        q1 = numpy.sqrt(1.0 - u0) * numpy.cos(2 * numpy.pi * u1)
        q2 = numpy.sqrt(u0) * numpy.sin(2 * numpy.pi * u2)
        q3 = numpy.sqrt(u0) * numpy.cos(2 * numpy.pi * u2)

        quat[0] = q0
        quat[1] = q1
        quat[2] = q2
        quat[3] = q3

    else:
        q0 = quat[0]
        q1 = quat[1]
        q2 = quat[2]
        q3 = quat[3]

    rotmat[0] = q0 * q0 + q1 * q1 - q2 * q2 - q3 * q3
    # // M[0][0]
    rotmat[1] = 2 * (q1 * q2 - q0 * q3)
    # // M[0][1]
    rotmat[2] = 2 * (q1 * q3 + q0 * q2)
    # // M[0][2]
    rotmat[3] = 2 * (q1 * q2 + q0 * q3)
    # // M[1][0]
    rotmat[4] = q0 * q0 - q1 * q1 + q2 * q2 - q3 * q3
    # // M[1][1]
    rotmat[5] = 2 * (q2 * q3 - q0 * q1)
    # // M[1][2]
    rotmat[6] = 2 * (q1 * q3 - q0 * q2)
    # // M[2][0]
    rotmat[7] = 2 * (q2 * q3 + q0 * q1)
    # // M[2][1]
    rotmat[8] = q0 * q0 - q1 * q1 - q2 * q2 + q3 * q3
    # // M[2][2]


def s2e_rand_orient(r, mat):
    """Apply the rotation matrix to the sample coordinate.

    Args:
        r (ndarray): The sample coordinate to rotate.
        mat (ndarray): The rotation matrix.
    """
    N = r.shape[0]
    vv = numpy.zeros((3, 0))
    for ii in range(N):
        vv = r[ii, :]
        ###        print vv , vv.shape , mat.shape
        r[ii, 0] = mat[0] * vv[0] + mat[1] * vv[1] + mat[2] * vv[2]
        r[ii, 1] = mat[3] * vv[0] + mat[4] * vv[1] + mat[5] * vv[2]
        r[ii, 2] = mat[6] * vv[0] + mat[7] * vv[1] + mat[8] * vv[2]


def f_h5_out2in(src, dest, *args):
    """Import the input data.

    Args:
        src (str): The input file name.
        dest (str): The output file name.
    """
    file_in = h5py.File(src, "r")
    file_out = h5py.File(dest, "w")

    grp_hist = file_out.create_group("history")
    grp_hist_parent = file_out.create_group("history/parent")
    grp_hist_parent_detail = file_out.create_group("history/parent/detail")

    pre_s2e_module = os.path.basename(os.path.dirname(os.path.abspath(src)))
    print("Previous module: ", pre_s2e_module)

    # Add attribute to history/parent
    grp_hist_parent.attrs["name"] = "_" + pre_s2e_module

    grp_srchist = file_in.get("history/parent")
    file_out.copy(grp_srchist, grp_hist_parent)

    # Copy everything to history except "data" & "history"
    for objname in list(file_in.keys()):
        if objname != "data" and objname != "history":
            x = file_in.get(objname)
            if isinstance(x, h5py.Dataset):
                mygroup = file_in["/"]
                file_out["history/parent/detail/" + objname] = mygroup[objname][...]
            elif isinstance(x, h5py.Group):
                file_out.copy(x, "history/parent/detail/" + objname)
            else:
                print(objname, " has been SKIPPED!!")
            print(objname)
        else:
            print("  NOT:", objname)

    print(list(file_in["data"].keys()))
    print(list(file_in["data"].items()))

    # Create external link to parent's data
    # file_out['history/parent/detail/data'] = h5py.ExternalLink( src ,'/data')
    parent_module = os.path.basename(src)[: os.path.basename(src).find("_out")]
    file_out["history/parent/detail/data"] = h5py.ExternalLink(
        "../" + parent_module + "/" + os.path.basename(src), "/data"
    )

    # Create your own groups
    grp_data = file_out.create_group("data")
    grp_param = file_out.create_group("params")
    grp_param = file_out.create_group("misc")
    grp_param = file_out.create_group("info")

    # Create s2e interface version
    interface = file_out.create_dataset("info/interface_version", (1,), dtype="f")
    interface[0] = 1.0

    file_out.close()
    file_in.close()
