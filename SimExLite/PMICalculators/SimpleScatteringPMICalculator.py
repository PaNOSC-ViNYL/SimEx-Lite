""":module SimpleScatteringPMICalculator: Module that holds the SimpleScatteringPMICalculator class."""

import h5py
import numpy
from pathlib import Path
import shutil
import sys
import os
import tempfile


from libpyvinyl import BaseCalculator, CalculatorParameters
from libpyvinyl.BaseData import DataCollection
from SimExLite.SampleData import SampleData, ASEFormat
from SimExLite.WavefrontData import WavefrontData, WPGFormat
from SimExLite.PMIData import PMIData, XMDYNFormat


class SimpleScatteringPMICalculator(BaseCalculator):
    """:class SimpleScatteringPMICalculator: Class representing simple elastic scattering process."""

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
        assert len(self.output_filenames) == 1
        output_fn = str(Path(self.base_dir) / self.output_filenames[0])
        sample_data, wavefront_data = self.input.to_list()
        wavefront_fn = prepare_wavefront_file(wavefront_data)

        f_h5_out2in(wavefront_fn, output_fn)

        pmi_scattering = PMIScattering()
        pmi_scattering.g_s2e["prj"] = ""
        pmi_scattering.g_s2e["id"] = "0000001"
        pmi_scattering.g_s2e["prop_out"] = wavefront_fn
        pmi_scattering.g_s2e["setup"] = dict()
        pmi_scattering.g_s2e["sys"] = dict()
        pmi_scattering.g_s2e["setup"]["num_digits"] = 7
        pmi_scattering.g_s2e["steps"] = self.parameters["number_of_steps"].value
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
    return atoms_dict


class PMIScattering(object):
    def __init__(self):
        self.g_s2e = {}
        self.g_dbase = {}

        self.f_s2e_setup()

    def f_s2e_setup(self):
        self.g_s2e["setup"] = dict()
        self.g_s2e["sys"] = dict()
        self.g_s2e["setup"]["num_digits"] = 7
        self.g_s2e["steps"] = 100
        self.g_s2e["maxZ"] = 100

    ##############################################################################

    def f_save_info(self):
        pmi_file = self.g_s2e["setup"]["pmi_out"]

        grp = "/info"
        ###    print pmi_file , grp
        xfp = h5py.File(pmi_file, "a")
        try:
            grp_hist_parent = xfp.create_group(grp)
        except:
            1

        #    xfp[ grp + '/Sq_free' ] = g_dbase['Sq_free']
        xfp.close()

    ##############################################################################

    # def f_init_random(self):
    #     random.seed(self.g_s2e["id"])

    ##############################################################################

    def f_dbase_Zq2id(self, a_Z, a_q):
        return (a_Z * (a_Z + 1)) // 2 - 1 * 1 + a_q

    ##############################################################################

    def f_dbase_setup(self):
        # print '   Update database!!!'
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

    #    g_dbase['ph_sigma'] ;

    ##    g_dbase['halfQ'] = numpy.array( [ 0 , 1 , 2 ] ) ;
    ##    maxZ = g_s2e['maxZ']  #99
    ##    g_dbase['ff'] = numpy.zeros( ( f_dbase_Zq2id( maxZ , maxZ ) + 1 , len( g_dbase['halfQ'] ) ) )
    ##    ii = 0
    ##    for ZZ in range( 1 , maxZ+1 ) :
    ##        for qq in range( ZZ+1 ) :
    ##            g_dbase['ff'][ ii , : ] = numpy.array( [ 1.0 , 0.5 , 0.25 ] ) * ( ZZ - qq ) ;
    #####            print ZZ,  qq, ii
    #####            print  g_dbase['ff'][ ii , : ]
    ##            ii = ii + 1
    ##    g_dbase['Sq_halfQ'] = numpy.array( [ 0 , 0 , 0 ] ) ;
    ##    g_dbase['Sq_bound'] = numpy.array( [ 0 , 0 , 0 ] ) ;
    ##    g_dbase['Sq_free']  = numpy.array( [ 0 , 0 , 0 ] ) ;
    ###    g_dbase['ph_sigma'] ;

    def f_load_snp_content(self, a_fp, a_snp):
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
        """Load xmdyn output from an xmdyn directory.

        :param path: The directory path to xmdyn output.
        :type path: str

        :param snapshot_index: Which snapshot to load.
        :type snapshot_index: int

        :returns: The snapshot data.
        :rtype: dict

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
        xfp = h5py.File(self.g_s2e["setup"]["pmi_out"], "a")
        try:
            xfp.create_group(os.path.dirname(dset))
        except:
            1

        xfp[dset] = data
        xfp.close()

    def f_rotate_sample(self):
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
        self.g_s2e["sys"]["r"] = self.g_s2e["sample"]["r"].copy()
        self.g_s2e["sys"]["q"] = numpy.zeros(self.g_s2e["sample"]["Z"].shape)
        self.g_s2e["sys"]["NE"] = self.g_s2e["sample"]["Z"].copy()
        self.g_s2e["sys"]["Z"] = self.g_s2e["sample"]["Z"]
        self.g_s2e["sys"]["Nph"] = 1e99
        # print '   NOTE: Nph is uniform.'

    def f_save_snp(self, a_snp):
        self.g_s2e["sys"]["xyz"] = self.f_dbase_Zq2id(
            self.g_s2e["sys"]["Z"], self.g_s2e["sys"]["q"]
        )
        self.g_s2e["sys"]["T"] = numpy.sort(numpy.unique(self.g_s2e["sys"]["xyz"]))
        ff = numpy.zeros((len(self.g_s2e["sys"]["T"]), len(self.g_dbase["halfQ"])))
        for ii in range(len(self.g_s2e["sys"]["T"])):
            ff[ii, :] = self.g_dbase["ff"][
                self.g_s2e["sys"]["T"][ii].astype(int), :
            ].copy()
        ###        print self.g_s2e['sys']['T'][ii].astype(int) , ff[ii,:]

        pmi_file = self.g_s2e["setup"]["pmi_out"]
        grp = "/data/snp_" + str(a_snp).zfill(self.g_s2e["setup"]["num_digits"])
        ###    print pmi_file , grp
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

    ##############################################################################

    def f_num_snp_xxx(self, all_real):
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

    #        try:
    #            if type( a_fp.get( "/data/snp_" + str( cc ).zfill(NUM_DIGITS) + '/Nph' ) ) == 'NoneType' :
    #                print 'N'
    #            else :
    #                print 1
    #
    #        except:
    #            return cc

    ##############################################################################

    def f_load_pulse(self, a_prop_out):

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
        # g_s2e['pulse']['']   = xfp.get( '' )   .value
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

        #    print self.g_s2e['pulse']['arrEhor'].shape , dt , dx , dy ,  NPH

        #    print self.g_s2e['pulse']['sel_int']

        #    self.g_s2e_pulse['sliceMax']   = self.g_s2e_pulse[''] - self.g_s2e_pulse['']
        #    self.g_s2e_pulse['sliceMin']   = 0
        #    self.g_s2e_pulse['sliceDelta']   = self.g_s2e_pulse['']  / ( self.g_s2e_pulse[''] - 1.0 )

        #    self.g_s2e_pulse['slices']   =

        #    self.g_s2e_pulse['xMax']   = ( self.g_s2e_pulse[''] - self.g_s2e_pulse[''] ) / 2.0
        #    self.g_s2e_pulse['xMin']   = - self.g_s2e_pulse['']
        #    self.g_s2e_pulse['xDelta']   = ( self.g_s2e_pulse[''] - self.g_s2e_pulse[''] ) / ( self.g_s2e_pulse[''] - 1.0 )

        #    self.g_s2e_pulse['sel_pix_x']   = ( self.g_s2e_pulse[''] + 1 ) / 2
        #    self.g_s2e_pulse['sel_pix_y']   = ( self.g_s2e_pulse[''] + 1 ) / 2

        return

    #    /**  Some transformation  and  derived useful parameters  */
    #    data_prop_out.sliceMax = data_prop_out.sliceMax - data_prop_out.sliceMin ;
    #    data_prop_out.sliceMin = 0 ;
    #
    #    data_prop_out.sliceDelta = data_prop_out.sliceMax / (double) (data_prop_out.nSlices-1) ;

    #    data_prop_out.slices = calloc( data_prop_out.nSlices , sizeof(double) ) ;
    #    for ( ii = 0 ; ii < data_prop_out.nSlices ; ii++ )
    #    {
    #        data_prop_out.slices[ii] = data_prop_out.sliceDelta * ii ;
    #    }

    #    data_prop_out.xMax =  ( data_prop_out.xMax - data_prop_out.xMin ) / 2.0 ;
    #    data_prop_out.xMin = - data_prop_out.xMax ;
    #    data_prop_out.xDelta = ( data_prop_out.xMax - data_prop_out.xMin ) /
    #                           (double) (data_prop_out.nx - 1 ) ;

    #    data_prop_out.yMax =  ( data_prop_out.yMax - data_prop_out.yMin ) / 2.0 ;
    #
    #    data_prop_out.yMin = - data_prop_out.yMax ;
    #    data_prop_out.yDelta = ( data_prop_out.yMax - data_prop_out.yMin ) /
    #                           (double) ( data_prop_out.ny - 1 ) ;

    #    /**  Selecting center (ot highest fluence) pixel */
    #    data_prop_out.sel_pix_x = ( data_prop_out.nx + 1 ) / 2 ;
    #    data_prop_out.sel_pix_y = ( data_prop_out.ny + 1 ) / 2 ;

    ##############################################################################

    def f_time_evolution(self):

        for step in range(1, self.g_s2e["steps"] + 1):
            self.f_save_snp(step)

    ##############################################################################


def f_eval_disp(a_snp, a_r0, a_sample):

    num_Z = len(list(a_sample["selZ"].keys()))
    all_disp = numpy.zeros((num_Z,))
    cc = 0
    for sel_Z in list(a_sample["selZ"].keys()):
        dr = a_snp["r"][a_sample["selZ"][sel_Z], :] - a_r0[a_sample["selZ"][sel_Z], :]
        all_disp[cc] = numpy.mean(numpy.sqrt(numpy.sum(dr * dr, axis=1))) / 1e-10
        cc = cc + 1
    return all_disp


def s2e_gen_randrot_quat(quat, rotmat):

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


#        inversematrix3( (void*) (rotmat + ii) , (void*) (invmat + ii) ) ;

#    for ( ii = 0 ; ii < randrot ; ii++ )
#    {
#        for ( jj=0 ; jj < 3 ; jj++ )
#        {
#            printf( "% e % e % e\n" , rotmat[ii][jj*3+0] ,  rotmat[ii][jj*3+1] ,
#                                      rotmat[ii][jj*3+2] ) ;
#        }
#        printf("\n") ;

#        for ( jj=0 ; jj < 3 ; jj++ )
#        {
#            printf( "% e % e % e\n" , invmat[ii][jj*3+0] ,  invmat[ii][jj*3+1] ,
#                                      invmat[ii][jj*3+2] ) ;
#        }
#        printf("\n\n\n") ;
#    }
# }


##############################################################################


def s2e_rand_orient(r, mat):

    N = r.shape[0]
    ###    print N
    vv = numpy.zeros((3, 0))
    for ii in range(N):
        vv = r[ii, :]
        ###        print vv , vv.shape , mat.shape
        r[ii, 0] = mat[0] * vv[0] + mat[1] * vv[1] + mat[2] * vv[2]
        r[ii, 1] = mat[3] * vv[0] + mat[4] * vv[1] + mat[5] * vv[2]
        r[ii, 2] = mat[6] * vv[0] + mat[7] * vv[1] + mat[8] * vv[2]


##############################################################################
def f_eval_numE(a_snp, a_sample):

    num_Z = len(list(a_sample["selZ"].keys()))
    all_numE = numpy.zeros((num_Z,))
    cc = 0
    for sel_Z in list(a_sample["selZ"].keys()):
        all_numE[cc] = numpy.mean(a_snp["q"][a_sample["selZ"][sel_Z]])
        cc = cc + 1
    return all_numE


##############################################################################


# def f_md_step(r, v, m, dt):
#     r = r.copy()
#     v = v.copy()
#     a = (force(config, param) + external_force(config, param)) / m
#     r = r + v * dt + 0.5 * a * dt**2.0
#     config["r"] = r
#     an = (force(config, param) + external_force(config, param)) / m
#     v = v + 0.5 * (a + an) * dt
#     config["v"] = v
#     E = f_sysenergy_kin(v, m) + syspot(config, param) + ext_syspot(config, param)


##############################################################################


# def f_pmi_diagnostics_help():
#     print(
#         """
#     ----
#     """
#     )

    ##############################################################################
    ##############################################################################
    ##############################################################################


def load_ff_database():

    # INTERNAL NOTE #  ########    To get to the nice array below:    ########
    # INTERNAL NOTE #   for x in `seq 1 100` ; do echo $x ; RES=`time xatom -Z $x  -formfactor -Q 10 -N_Q 100 2>ff-$x.err` ; echo "$RES" | grep -v \# > ff-$x.dat ; echo "$RES" | grep \# > ff-$x.log ; done
    # INTERNAL NOTE #   cp ff-1.dat ff_all.dat
    # INTERNAL NOTE #   for x in `seq 2 100` ; do cat ff-${x}.dat| cut -c14-26 | paste -d" " ff_all.dat - > ff_all.xxx ; mv ff_all.xxx ff_all.dat ; done
    # INTERNAL NOTE #   cat ff_all.dat |while read x; do echo '[' `echo $x|sed s/\ /\ ,\ /g` '] ,'; done > ff_all.dat--numpy_array

    # fmt:off
    dbase = numpy.array(
            [
    [ 0.00000000 , 1.00000000 , 2.00000000 , 3.00000000 , 4.00000000 , 5.00000000 , 6.00000000 , 7.00000000 , 8.00000000 , 9.00000000 , 10.00000000 , 11.00000000 , 12.00000000 , 13.00000000 , 14.00000000 , 15.00000000 , 16.00000000 , 17.00000000 , 18.00000000 , 19.00000000 , 20.00000000 , 21.00000000 , 22.00000000 , 23.00000000 , 24.00000000 , 25.00000000 , 26.00000000 , 27.00000000 , 28.00000000 , 29.00000000 , 30.00000000 , 31.00000000 , 32.00000000 , 33.00000000 , 34.00000000 , 35.00000000 , 36.00000000 , 37.00000000 , 38.00000000 , 39.00000000 , 40.00000000 , 41.00000000 , 42.00000000 , 43.00000000 , 44.00000000 , 45.00000000 , 46.00000000 , 47.00000000 , 48.00000000 , 49.00000000 , 50.00000000 , 51.00000000 , 52.00000000 , 53.00000000 , 54.00000000 , 55.00000000 , 56.00000000 , 57.00000000 , 58.00000000 , 59.00000000 , 60.00000000 , 61.00000000 , 62.00000000 , 63.00000000 , 64.00000000 , 65.00000000 , 66.00000000 , 67.00000000 , 68.00000000 , 69.00000000 , 70.00000000 , 71.00000000 , 72.00000000 , 73.00000000 , 74.00000000 , 75.00000000 , 76.00000000 , 77.00000000 , 78.00000000 , 79.00000000 , 80.00000000 , 81.00000000 , 82.00000000 , 83.00000000 , 84.00000000 , 85.00000000 , 86.00000000 , 87.00000000 , 88.00000000 , 89.00000000 , 90.00000000 , 91.00000000 , 92.00000000 , 93.00000000 , 94.00000000 , 95.00000000 , 96.00000000 , 97.00000000 , 98.00000000 , 99.00000000 , 100.00000000 ] ,
    [ 0.10000000 , 0.99501869 , 1.99589518 , 2.97109688 , 3.97186951 , 4.97376297 , 5.97710119 , 6.97983622 , 7.98198772 , 8.98370590 , 9.98510701 , 10.95863233 , 11.95411841 , 12.94697205 , 13.94883406 , 14.95181561 , 15.95472957 , 16.95738950 , 17.95978500 , 18.92347251 , 19.91505510 , 20.92051573 , 21.92515832 , 22.92918270 , 23.93272217 , 24.93587259 , 25.93870298 , 26.94126494 , 27.94359833 , 28.94573704 , 29.94770446 , 30.93632139 , 31.93476608 , 32.93527378 , 33.93636001 , 34.93766419 , 35.93905535 , 36.89860308 , 37.88700546 , 38.89138618 , 39.89563164 , 40.89945789 , 41.90291796 , 42.90607326 , 43.90897276 , 44.91165362 , 45.91414473 , 46.91646886 , 47.91864602 , 48.90557917 , 49.90242200 , 50.90177205 , 51.90202494 , 52.90273336 , 53.90370475 , 54.85504426 , 55.83966594 , 56.84315999 , 57.84642273 , 58.84948038 , 59.85237085 , 60.85511933 , 61.85773122 , 62.86022128 , 63.86261346 , 64.86490228 , 65.86709654 , 66.86920692 , 67.87124385 , 68.87315927 , 65.70484550 , 70.87732340 , 71.87995066 , 72.88245856 , 73.88481283 , 74.88702796 , 75.88912120 , 76.89111007 , 77.89300402 , 78.89481198 , 79.89654525 , 80.88208473 , 81.87752692 , 82.87569085 , 83.87492735 , 84.87474801 , 85.87494376 , 86.82204392 , 87.80407602 , 88.80756308 , 89.81077554 , 90.81379738 , 91.81664367 , 92.81934342 , 93.82192852 , 94.82440199 , 95.82677312 , 96.82905187 , 97.83125374 , 98.83338014 , 99.83543301 ] ,
    [ 0.20000000 , 0.98029605 , 1.98366686 , 2.88921088 , 3.89009359 , 4.89691003 , 5.90953192 , 6.92007026 , 7.92844659 , 8.93517905 , 9.94069267 , 10.84074020 , 11.82133362 , 12.79369182 , 13.79942414 , 14.81016110 , 15.82105494 , 16.83118715 , 17.84041641 , 18.70703268 , 19.67168476 , 20.69126881 , 21.70830160 , 22.72326773 , 23.73655472 , 24.74846395 , 25.75922180 , 26.76900232 , 27.77794277 , 28.78616221 , 29.79374354 , 30.75062359 , 31.74354167 , 32.74471755 , 33.74841947 , 34.75315225 , 35.75834338 , 36.61113191 , 37.56357676 , 38.57797106 , 39.59287804 , 40.60671665 , 41.61945796 , 42.63122066 , 43.64212718 , 44.65228081 , 45.66176717 , 46.67065688 , 47.67901460 , 48.62978395 , 49.61644777 , 50.61293848 , 51.61318966 , 52.61540564 , 53.61878380 , 54.44503336 , 55.38266318 , 56.39539293 , 57.40736925 , 58.41865683 , 59.42937020 , 60.43958725 , 61.44932434 , 62.45862952 , 63.46758192 , 64.47616376 , 65.48440499 , 66.49234191 , 67.50000992 , 68.50723078 , 58.59679107 , 70.52117789 , 71.53003270 , 72.53884491 , 73.54732205 , 74.55543164 , 75.56318833 , 76.57062537 , 77.57775962 , 78.58461047 , 79.59120927 , 80.53685275 , 81.51815627 , 82.50999807 , 83.50621495 , 84.50487903 , 85.50513585 , 86.31789370 , 87.24567400 , 88.25789195 , 89.26939086 , 90.28034080 , 91.29074942 , 92.30068887 , 93.31024983 , 94.31943542 , 95.32827176 , 96.33678884 , 97.34503560 , 98.35301568 , 99.36073514 ] ,
    [ 0.30000000 , 0.95647444 , 1.96356927 , 2.76725396 , 3.76202384 , 4.77469897 , 5.80053613 , 6.82281216 , 7.84082870 , 8.85546554 , 9.86753855 , 10.66278836 , 11.61507472 , 12.55597175 , 13.56323619 , 14.58331441 , 15.60514753 , 16.62613454 , 17.64562925 , 18.38422557 , 19.30061077 , 20.33726052 , 21.37044718 , 22.40029681 , 23.42722305 , 24.45164178 , 25.47390092 , 26.49428619 , 27.51303335 , 28.53035515 , 29.54640225 , 30.45748664 , 31.43886499 , 32.43864338 , 33.44475101 , 34.45369745 , 35.46404778 , 36.17978454 , 37.07091417 , 38.09331718 , 39.12003428 , 40.14626084 , 41.17120383 , 42.19473420 , 43.21689325 , 44.23776649 , 45.25744874 , 46.27603108 , 47.29360778 , 48.19297191 , 49.16091549 , 50.15005800 , 51.14805288 , 52.15090436 , 53.15672600 , 53.83123557 , 54.69130076 , 55.71596026 , 56.73945708 , 57.76181343 , 58.78317381 , 59.80364353 , 60.82324219 , 61.84204421 , 62.86017619 , 63.87761046 , 64.89439780 , 65.91060009 , 66.92627746 , 67.94107350 , 54.84584738 , 69.96380297 , 70.97831430 , 71.99407663 , 73.00997568 , 74.02566146 , 75.04099668 , 76.05593832 , 77.07045685 , 78.08454262 , 79.09822011 , 79.98752852 , 80.94428540 , 81.92335210 , 82.91242101 , 83.90730939 , 84.90606510 , 85.56010225 , 86.40035022 , 87.42241101 , 88.44399556 , 89.46500028 , 90.48528371 , 91.50487565 , 92.52386888 , 93.54224160 , 94.56001847 , 95.57723620 , 96.59396505 , 97.61020646 , 98.62596806 ] ,
    [ 0.40000000 , 0.92455621 , 1.93601227 , 2.62232893 , 3.59841530 , 4.61493641 , 5.65509324 , 6.69136999 , 7.72144206 , 8.74624382 , 9.76690710 , 10.44616204 , 11.35432393 , 12.25561182 , 13.25699772 , 14.28378698 , 15.31654594 , 16.34967161 , 17.38134713 , 17.99539144 , 18.84265110 , 19.89263310 , 20.94083906 , 21.98573092 , 23.02717079 , 24.06538374 , 25.10066516 , 26.13330746 , 27.16357917 , 28.19174339 , 29.21799259 , 30.07712696 , 31.03897574 , 32.03254155 , 33.03850511 , 34.05055802 , 35.06589554 , 35.65421747 , 36.46249711 , 37.48277611 , 38.51628058 , 39.55255813 , 40.58890695 , 41.62435443 , 42.65851878 , 43.69125927 , 44.72254578 , 45.75240032 , 46.78088351 , 47.62328985 , 48.56297666 , 49.53772579 , 50.52868777 , 51.52905722 , 52.53540169 , 53.08246387 , 53.84327594 , 54.87924466 , 55.91414980 , 56.94780259 , 57.98025254 , 59.01155753 , 60.04171761 , 61.07080159 , 62.09893947 , 63.12610276 , 64.15235003 , 65.17775391 , 66.20238446 , 67.22569648 , 53.77158699 , 69.24916173 , 70.26396349 , 71.28348456 , 72.30497838 , 73.32732177 , 74.34994957 , 75.37255635 , 76.39495547 , 77.41702259 , 78.43870681 , 79.26628124 , 80.18811351 , 81.14596657 , 82.12153596 , 83.10791921 , 84.10168406 , 84.62872470 , 85.36063499 , 86.38940919 , 87.41938379 , 88.44954277 , 89.47934987 , 90.50861941 , 91.53731537 , 92.56534232 , 93.59267935 , 94.61933367 , 95.64535648 , 96.67073589 , 97.69547273 ] ,
    [ 0.50000000 , 0.88581315 , 1.90154194 , 2.47128459 , 3.41164524 , 4.42684260 , 5.47937602 , 6.52997369 , 7.57329808 , 8.60973451 , 9.64048533 , 10.21130830 , 11.05981047 , 11.91572346 , 12.89994752 , 13.92673250 , 14.96718947 , 16.01132022 , 17.05527218 , 17.57472317 , 18.33832831 , 19.39279499 , 20.45070795 , 21.50736254 , 22.56132437 , 23.61219550 , 24.65995195 , 25.70471925 , 26.74668104 , 27.78606500 , 28.82305042 , 29.63121183 , 30.56478205 , 31.54501020 , 32.54596126 , 33.55797113 , 34.57638064 , 35.07527909 , 35.78958735 , 36.79269137 , 37.82321755 , 38.86315351 , 39.90668868 , 40.95129788 , 41.99573343 , 43.03934029 , 44.08176745 , 45.12283050 , 46.16245391 , 46.95084195 , 47.85335828 , 48.80499280 , 49.78195182 , 50.77451053 , 51.77738373 , 52.25164568 , 52.90865377 , 53.95302715 , 54.99714730 , 56.04040855 , 57.08260976 , 58.12366528 , 59.16352059 , 60.20219426 , 61.23976038 , 62.27619693 , 63.31155027 , 64.34588124 , 65.37924789 , 66.41093009 , 53.34331597 , 68.42285081 , 69.42908605 , 70.44599651 , 71.46845787 , 72.49408310 , 73.52155447 , 74.55006885 , 75.57913724 , 76.60840409 , 77.63764422 , 78.40766887 , 79.28597354 , 80.21331316 , 81.16736085 , 82.13861321 , 83.12198887 , 83.58406554 , 84.20780807 , 85.23762691 , 86.27197669 , 87.30827778 , 88.34532446 , 89.38251522 , 90.41953039 , 91.45613656 , 92.49220900 , 93.52767722 , 94.56252102 , 95.59669769 , 96.63018709 ] ,
    [ 0.60000000 , 0.84168000 , 1.86081572 , 2.32740221 , 3.21394637 , 4.21991898 , 5.28015422 , 6.34345194 , 7.39992596 , 8.44858758 , 9.49031292 , 9.97368392 , 10.75058678 , 11.55702803 , 12.51121459 , 13.52825992 , 14.57032459 , 15.62195592 , 16.67638570 , 17.14385913 , 17.82019564 , 18.86810754 , 19.92799298 , 20.99083800 , 22.05324757 , 23.11377421 , 24.17179140 , 25.22706244 , 26.27954693 , 27.32933025 , 28.37650763 , 29.13955740 , 30.03702072 , 30.99560833 , 31.98492625 , 32.99194537 , 34.00983966 , 34.46804038 , 35.09144622 , 36.06211723 , 37.07789461 , 38.11271627 , 39.15687842 , 40.20572009 , 41.25671490 , 42.30840150 , 43.35989684 , 44.41065454 , 45.46034181 , 46.20319923 , 47.06207809 , 47.98178032 , 48.93656723 , 49.91435513 , 50.90800566 , 51.36887140 , 51.93675289 , 52.98578133 , 54.03605697 , 55.08637085 , 56.13613662 , 57.18503871 , 58.23292611 , 59.27972368 , 60.32539845 , 61.36993236 , 62.41333884 , 63.45564515 , 64.49687684 , 65.53615883 , 52.81666341 , 67.52418198 , 68.51187755 , 69.51816350 , 70.53519235 , 71.55897650 , 72.58718164 , 73.61829301 , 74.65137732 , 75.68572861 , 76.72084065 , 77.44362983 , 78.27328358 , 79.16166561 , 80.08569965 , 81.03408600 , 82.00026517 , 82.46022952 , 82.99725104 , 84.02200597 , 85.05595505 , 86.09454020 , 87.13566362 , 88.17814411 , 89.22125191 , 90.26454760 , 91.30774448 , 92.35064714 , 93.39311718 , 94.43505882 , 95.47641235 ] ,
    [ 0.70000000 , 0.79364686 , 1.81457407 , 2.19896515 , 3.01602383 , 4.00303679 , 5.06424188 , 6.13690608 , 7.20517486 , 8.26575767 , 9.31870059 , 9.74236809 , 10.44176995 , 11.19586053 , 12.10786494 , 13.10395516 , 14.13945295 , 15.19306393 , 16.25441629 , 16.71233922 , 17.30959628 , 18.34058896 , 19.39424143 , 20.45681050 , 21.52254882 , 22.58865301 , 23.65366578 , 24.71681785 , 25.77771592 , 26.83619887 , 27.89220602 , 28.61835849 , 29.47420076 , 30.40303468 , 31.37324282 , 32.36906555 , 33.38149662 , 33.84362086 , 34.39223705 , 35.31890935 , 36.30891518 , 37.32938195 , 38.36663704 , 39.41361140 , 40.46623253 , 41.52201003 , 42.57935033 , 43.63720388 , 44.69486475 , 45.40308874 , 46.21551091 , 47.09599562 , 48.02053127 , 48.97587912 , 49.95343583 , 50.44722911 , 50.95463927 , 52.00480344 , 53.05824339 , 54.11301678 , 55.16806740 , 56.22279112 , 57.27689677 , 58.33018153 , 59.38247572 , 60.43374909 , 61.48396476 , 62.53310045 , 63.58113541 , 64.62705117 , 52.14748237 , 66.58222593 , 67.54264278 , 68.53036511 , 69.53505878 , 70.55108813 , 71.57498957 , 72.60440906 , 73.63786814 , 74.67421803 , 75.71258150 , 76.40093039 , 77.18117266 , 78.02460519 , 78.91106524 , 79.82883275 , 80.77041879 , 81.27334337 , 81.75842093 , 82.77295990 , 83.80208419 , 84.83918250 , 85.88114304 , 86.92611287 , 87.97288187 , 89.02074363 , 90.06920147 , 91.11789687 , 92.16654215 , 93.21496352 , 94.26304051 ] ,
    [ 0.80000000 , 0.74316291 , 1.76361084 , 2.08949307 , 2.82623746 , 3.78384632 , 4.83805563 , 5.91541744 , 6.99302326 , 8.06437811 , 9.12814485 , 9.52081046 , 10.14365457 , 10.84372193 , 11.70380928 , 12.66779701 , 13.68744819 , 14.73606111 , 15.79932766 , 16.28174627 , 16.81727493 , 17.82354825 , 18.86380028 , 19.91992495 , 20.98377819 , 22.05107357 , 23.11939280 , 24.18731980 , 25.25401272 , 26.31898084 , 27.38194655 , 28.07979432 , 28.89151415 , 29.78385801 , 30.72759501 , 31.70545022 , 32.70657998 , 33.20496452 , 33.70308534 , 34.57978156 , 35.53562620 , 36.53356317 , 37.55660942 , 38.59539705 , 39.64424780 , 40.69953572 , 41.75884551 , 42.82052284 , 43.88339747 , 44.56795836 , 45.33500201 , 46.17168689 , 47.05918582 , 47.98472703 , 48.93899469 , 49.49219658 , 49.97287718 , 51.02133305 , 52.07542562 , 53.13241559 , 54.19074475 , 55.24949174 , 56.30818423 , 57.36646892 , 58.42403158 , 59.48080211 , 60.53668013 , 61.59158443 , 62.64544160 , 63.69708687 , 51.41384236 , 65.61556471 , 66.54277042 , 67.50542190 , 68.49148747 , 69.49395992 , 70.50832620 , 71.53138932 , 72.56109135 , 73.59579658 , 74.63420309 , 75.30068664 , 76.03496285 , 76.83087883 , 77.67431571 , 78.55478434 , 79.46471790 , 80.03262325 , 80.50296452 , 81.50351987 , 82.52417364 , 83.55648659 , 84.59632142 , 85.64113630 , 86.68922704 , 87.73957379 , 88.79143599 , 89.84426558 , 90.89761056 , 91.95119424 , 93.00481351 ] ,
    [ 0.90000000 , 0.69155995 , 1.70874421 , 1.99892358 , 2.65034287 , 3.56849982 , 4.60731355 , 5.68381162 , 6.76741051 , 7.84764266 , 8.92124458 , 9.30860724 , 9.86194485 , 10.50779900 , 11.30947860 , 12.23152025 , 13.22591134 , 14.26174067 , 15.32086745 , 15.85022196 , 16.34612318 , 17.32313111 , 18.34466225 , 19.38922639 , 20.44655135 , 21.51092050 , 22.57893199 , 23.64847579 , 24.71820938 , 25.78725968 , 26.85508887 , 27.53247390 , 28.30057665 , 29.15183830 , 30.06269614 , 31.01594821 , 31.99958594 , 32.55226835 , 33.02644433 , 33.85271718 , 34.76940890 , 35.73859055 , 36.74117295 , 37.76594008 , 38.80575876 , 39.85589125 , 40.91307189 , 41.97499292 , 43.03996516 , 43.71063046 , 44.43672032 , 45.22822678 , 46.07405462 , 46.96360875 , 47.88785772 , 48.50845032 , 48.99311361 , 50.03764756 , 51.09035078 , 52.14768259 , 53.20758963 , 54.26882719 , 55.33070715 , 56.39271172 , 57.45438839 , 58.51559380 , 59.57615398 , 60.63592396 , 61.69477633 , 62.75138448 , 50.66547697 , 64.63434724 , 65.52579140 , 66.45904602 , 67.42153655 , 68.40542704 , 69.40541505 , 70.41758548 , 71.43934217 , 72.46857594 , 73.50355285 , 74.15906209 , 74.85409162 , 75.60354668 , 76.40132579 , 77.23973798 , 78.11213375 , 78.74744238 , 79.23397909 , 80.21793961 , 81.22718765 , 82.25186821 , 83.28690079 , 84.32909657 , 85.37628477 , 86.42710414 , 87.48055072 , 88.53587098 , 89.59244498 , 90.64987049 , 91.70784136 ] ,
    [ 1.00000000 , 0.64000001 , 1.65078993 , 1.92503082 , 2.49166074 , 3.36161857 , 4.37687093 , 5.44649005 , 6.53209991 , 7.61870184 , 8.70062405 , 9.10335085 , 9.59865059 , 10.19187951 , 10.93203206 , 11.80437763 , 12.76477831 , 13.77986698 , 14.82820315 , 15.41562025 , 15.89439849 , 16.84060400 , 17.84010968 , 18.86935184 , 19.91641397 , 20.97434298 , 22.03882309 , 23.10706496 , 24.17721548 , 25.24799821 , 26.31859085 , 26.98220258 , 27.70971524 , 28.51774692 , 29.39085608 , 30.31360463 , 31.27372732 , 31.88624873 , 32.36043416 , 33.14008005 , 34.01587701 , 34.95228897 , 35.92958811 , 36.93539371 , 37.96143798 , 39.00201210 , 40.05305166 , 41.11160213 , 42.17544086 , 42.84033602 , 43.53225992 , 44.28029673 , 45.08238121 , 45.93157357 , 46.82019712 , 47.50272619 , 48.01409708 , 49.05286349 , 50.10239897 , 51.15840163 , 52.21835202 , 53.28068877 , 54.34448240 , 55.40904200 , 56.47378772 , 57.53847039 , 58.60283400 , 59.66666682 , 60.72978773 , 61.79068615 , 49.92058999 , 63.64313041 , 64.49940386 , 65.40128241 , 66.33692263 , 67.29835746 , 68.27988582 , 69.27710532 , 70.28699211 , 71.30703253 , 72.33510055 , 72.98835660 , 73.65286559 , 74.36009363 , 75.11256497 , 75.90657005 , 76.73732899 , 77.42960124 , 77.95261593 , 78.91807613 , 79.91343471 , 80.92790288 , 81.95560647 , 82.99278980 , 84.03686602 , 85.08612448 , 86.13929116 , 87.19539964 , 88.25366386 , 89.31353788 , 90.37459525 ] ,
    [ 1.10000000 , 0.58944670 , 1.59053807 , 1.86463339 , 2.35149945 , 3.16641724 , 4.15066929 , 5.20732716 , 6.29057735 , 7.38057801 , 8.46886569 , 8.90204382 , 9.35321146 , 9.89729321 , 10.57584831 , 11.39319906 , 12.31215198 , 13.29892244 , 14.32965627 , 14.97703488 , 15.45840155 , 16.37452668 , 17.35046027 , 18.36193585 , 19.39597767 , 20.44467565 , 21.50293393 , 22.56734532 , 23.63557045 , 24.70593563 , 25.77732703 , 26.43274501 , 27.12452151 , 27.88953496 , 28.72186574 , 29.60938142 , 30.54057564 , 31.20933210 , 31.70199907 , 32.44134773 , 33.27708176 , 34.17874423 , 35.12742839 , 36.11037553 , 37.11861065 , 38.14568194 , 39.18684438 , 40.23855255 , 41.29807357 , 41.96371185 , 42.62955056 , 43.33837453 , 44.09720255 , 44.90377435 , 45.75274146 , 46.48392297 , 47.03512455 , 48.06637935 , 49.11101288 , 50.16403232 , 51.22249001 , 52.28452027 , 53.34893714 , 54.41487105 , 55.48162324 , 56.54881229 , 57.61609229 , 58.68318150 , 59.74984448 , 60.81436440 , 49.18185481 , 62.64346897 , 63.46758877 , 64.33820970 , 65.24539202 , 66.18176826 , 67.14169422 , 68.12057935 , 69.11513593 , 70.12256018 , 71.14041452 , 71.79803960 , 72.44152636 , 73.11311287 , 73.82333597 , 74.57309702 , 75.36023552 , 76.09270092 , 76.66134025 , 77.60671603 , 78.58591805 , 79.58769113 , 80.60555737 , 81.63529557 , 82.67396276 , 83.71951033 , 84.77039879 , 85.82544834 , 86.88371019 , 87.94448221 , 89.00720505 ] ,
    [ 1.20000000 , 0.54065745 , 1.52873411 , 1.81442438 , 2.22967262 , 2.98490886 , 3.93176683 , 4.96962441 , 6.04598472 , 7.13610073 , 8.22845455 , 8.70195703 , 9.12354924 , 9.62371069 , 10.24310916 , 11.00263652 , 11.87430964 , 12.82598975 , 13.83253305 , 14.53515033 , 15.03425731 , 15.92240060 , 16.87451650 , 17.86686560 , 18.88600178 , 19.92337014 , 20.97326280 , 22.03174536 , 23.09604009 , 24.16410211 , 25.23453228 , 25.88644799 , 26.54846728 , 27.27269821 , 28.06311062 , 28.91208920 , 29.80988013 , 30.52556550 , 31.04869046 , 31.75503183 , 32.55325675 , 33.41981977 , 34.33788813 , 35.29510007 , 36.28224385 , 37.29240500 , 38.32032326 , 39.36195701 , 40.41411795 , 41.08559939 , 41.73378748 , 42.40946000 , 43.12776752 , 43.89160115 , 44.69868552 , 45.46201796 , 46.05733245 , 47.07926457 , 48.11716501 , 49.16543865 , 50.22074929 , 51.28094107 , 52.34456730 , 53.41057613 , 54.47815267 , 55.54676563 , 56.61597185 , 57.68541503 , 58.75480261 , 59.82219421 , 48.44712040 , 61.63579660 , 62.43233534 , 63.27344871 , 64.15202089 , 65.06194587 , 65.99809300 , 66.95600985 , 67.93234113 , 68.92413807 , 69.92876228 , 70.59556413 , 71.22730200 , 71.87123091 , 72.54441041 , 73.25239870 , 73.99610147 , 74.75055821 , 75.36472991 , 76.28854722 , 77.24941936 , 78.23603226 , 79.24151271 , 80.26128500 , 81.29211262 , 82.33163769 , 83.37806994 , 84.43002190 , 85.48638548 , 86.54629649 , 87.60905537 ] ,
    [ 1.30000000 , 0.49419171 , 1.46606461 , 1.77143879 , 2.12499957 , 2.81813566 , 3.72241927 , 4.73610834 , 5.80108414 , 6.88786206 , 7.98173514 , 8.50102651 , 8.90689849 , 9.36975918 , 9.93435908 , 10.63549946 , 11.45583008 , 12.36674285 , 13.34304132 , 14.09197426 , 14.61886243 , 15.48171479 , 16.41058224 , 17.38322668 , 18.38625665 , 19.41077592 , 20.45064145 , 21.50149553 , 22.56018302 , 23.62432644 , 24.69225665 , 25.34470227 , 25.98346793 , 26.67071966 , 27.41982567 , 28.22847531 , 29.08953266 , 29.83999519 , 30.39937173 , 31.07978496 , 31.84398189 , 32.67625762 , 33.56278827 , 34.49228875 , 35.45577006 , 36.44615471 , 37.45785979 , 38.48646900 , 39.52841723 , 40.20962790 , 40.84823568 , 41.49785017 , 42.18013186 , 42.90305570 , 43.66786090 , 44.44683145 , 45.08367645 , 46.09435278 , 47.12354710 , 48.16516038 , 49.21550710 , 50.27215651 , 51.33340679 , 52.39802253 , 53.46506967 , 54.53385894 , 55.60384333 , 56.67458632 , 57.74573309 , 58.81511029 , 47.71411284 , 60.62055376 , 61.39482812 , 62.20929123 , 63.06024677 , 63.94337481 , 64.85446570 , 65.78952147 , 66.74532730 , 67.71895003 , 68.70767912 , 69.38695249 , 70.01529231 , 70.64005080 , 71.28284161 , 71.95341925 , 72.65586621 , 73.41576538 , 74.06897863 , 74.96982404 , 75.91027570 , 76.87929371 , 77.86981975 , 78.87703787 , 79.89748116 , 80.92852563 , 81.96815387 , 83.01478257 , 84.06714843 , 85.12422605 , 86.18517392 ] ,
    [ 1.40000000 , 0.45043017 , 1.40314753 , 1.73325127 , 2.03572653 , 2.66639203 , 3.52418610 , 4.50895960 , 5.55824740 , 6.63818981 , 7.73088047 , 8.29794582 , 8.70038070 , 9.13347256 , 9.64898569 , 10.29311259 , 11.05979088 , 11.92551676 , 12.86627769 , 13.65035836 , 14.21022951 , 15.05048833 , 15.95707245 , 16.90992278 , 17.89612652 , 18.90671385 , 19.93527403 , 20.97713079 , 22.02881709 , 23.08766744 , 24.15176356 , 24.80827002 , 25.43034673 , 26.08551045 , 26.79541880 , 27.56341340 , 28.38564232 , 29.15797485 , 29.75425671 , 30.41488836 , 31.14883984 , 31.94837266 , 32.80325397 , 33.70381114 , 34.64168752 , 35.60993446 , 36.60284848 , 37.61577536 , 38.64486781 , 39.33862035 , 39.97486316 , 40.60585358 , 41.25780391 , 41.94325443 , 42.66707753 , 43.44709472 , 44.11833045 , 45.11572792 , 46.13413212 , 47.16704260 , 48.21046396 , 49.26170784 , 50.31883158 , 51.38041768 , 52.44540635 , 53.51295068 , 54.58239458 , 55.65321527 , 56.72498899 , 57.79530865 , 46.98195531 , 59.59871794 , 60.35614289 , 61.14743767 , 61.97258850 , 62.82941530 , 63.71495435 , 64.62594038 , 65.55950054 , 66.51287918 , 67.48342859 , 68.17719938 , 68.80914920 , 69.42299224 , 70.04280035 , 70.68169414 , 71.34673047 , 72.09877809 , 72.78097222 , 73.65754822 , 74.57563481 , 75.52472836 , 76.49778568 , 77.48986477 , 78.49733271 , 79.51735351 , 80.54771435 , 81.58665405 , 82.63276044 , 83.68485419 , 84.74195546 ] ,
    [ 1.50000000 , 0.40960001 , 1.34052665 , 1.69800606 , 1.95984648 , 2.52942218 , 3.33804417 , 4.28986113 , 5.31946448 , 6.38913599 , 7.47787205 , 8.09209451 , 8.50135130 , 8.91260908 , 9.38560576 , 9.97565426 , 10.68799634 , 11.50542838 , 12.40626807 , 13.21352945 , 13.80746965 , 14.62746321 , 15.51281108 , 16.44602473 , 17.41497996 , 18.41085130 , 19.42710709 , 20.45884975 , 21.50236443 , 22.55474329 , 23.61384242 , 24.27751370 , 24.88919445 , 25.51780631 , 26.19181055 , 26.92014849 , 27.70268392 , 28.48460976 , 29.11462405 , 29.76034782 , 30.46770696 , 31.23642780 , 32.06011721 , 32.93108793 , 33.84195185 , 34.78615382 , 35.75806680 , 36.75294076 , 37.76674958 , 38.47486859 , 39.11481046 , 39.73439362 , 40.36236106 , 41.01497400 , 41.70055838 , 42.46991703 , 43.16596620 , 44.14805347 , 45.15354848 , 46.17565188 , 47.21009995 , 48.25396769 , 49.30509258 , 50.36188014 , 51.42313771 , 52.48786771 , 53.55530182 , 54.62482544 , 55.69593894 , 56.76600867 , 46.25131941 , 58.57194050 , 59.31757665 , 60.08941635 , 60.89109477 , 61.72274910 , 62.58288722 , 63.46919847 , 64.37933262 , 65.31086308 , 66.26133628 , 66.97054389 , 67.61156997 , 68.22198034 , 68.82634119 , 69.44009325 , 70.07281285 , 70.80753174 , 71.50741574 , 72.35864181 , 73.25266025 , 74.17970628 , 75.13293442 , 76.10738865 , 77.09933714 , 78.10579350 , 79.12438804 , 80.15320593 , 81.19069643 , 82.23553925 , 83.28662491 ] ,
    [ 1.60000000 , 0.37180251 , 1.27866981 , 1.66435990 , 1.89532103 , 2.40658579 , 3.16449744 , 4.08005611 , 5.08636533 , 6.14247735 , 7.22448964 , 7.88339959 , 8.30757447 , 8.70486927 , 9.14236231 , 9.68245425 , 10.34120866 , 11.10852514 , 11.96604487 , 12.78472025 , 13.41059887 , 14.21208920 , 15.07712246 , 15.99092583 , 16.94236323 , 17.92291746 , 18.92605650 , 19.94674650 , 20.98108352 , 22.02596086 , 23.07903307 , 23.75255608 , 24.35963719 , 24.96750170 , 25.60975673 , 26.30056185 , 27.04368973 , 27.82438944 , 28.48243149 , 29.11678352 , 29.80081783 , 30.54079274 , 31.33412120 , 32.17531429 , 33.05820453 , 33.97685532 , 34.92589752 , 35.90062453 , 36.89693747 , 37.62031583 , 38.26872437 , 38.88348897 , 39.49399361 , 40.11918128 , 40.77040660 , 41.52059033 , 42.23113971 , 43.19597659 , 44.18650118 , 45.19571546 , 46.21913281 , 47.25361742 , 48.29681292 , 49.34695719 , 50.40271986 , 51.46296418 , 52.52680895 , 53.59354384 , 54.66258729 , 55.73109278 , 45.52400906 , 57.54246486 , 58.28074202 , 59.03677983 , 59.81759089 , 60.62564532 , 61.46104592 , 62.32259289 , 63.20860848 , 64.11712782 , 65.04601118 , 65.77065101 , 66.42464048 , 67.03797857 , 67.63405541 , 68.22951143 , 68.83581367 , 69.54745035 , 70.25420142 , 71.07931753 , 71.94790172 , 72.85108381 , 73.78237632 , 74.73691765 , 75.71094762 , 76.70139520 , 77.70577804 , 78.72205759 , 79.74856011 , 80.78384236 , 81.82667821 ] ,
    [ 1.70000000 , 0.33704008 , 1.21797001 , 1.63139075 , 1.84022000 , 2.29699108 , 3.00367644 , 3.88040906 , 4.86024987 , 5.89972484 , 6.97230870 , 7.67218618 , 8.11728152 , 8.50803998 , 8.91714628 , 9.41224347 , 10.01936530 , 10.73594379 , 11.54774681 , 12.36691631 , 13.02028748 , 13.80440582 , 14.64980344 , 15.54437466 , 16.47807406 , 17.44280480 , 18.43212770 , 19.44094327 , 20.46520985 , 21.50166111 , 22.54777354 , 23.23339222 , 23.84103084 , 24.43391961 , 25.04913624 , 25.70543180 , 26.41046007 , 27.18098986 , 27.85995081 , 28.48523867 , 29.14871002 , 29.86197412 , 30.62599879 , 31.43756346 , 32.29188858 , 33.18383504 , 34.10845049 , 35.06120204 , 36.03802180 , 36.77667452 , 37.43698696 , 38.05261956 , 38.65195878 , 39.25551327 , 39.87706292 , 40.60262953 , 41.31786013 , 42.26369241 , 43.23733366 , 44.23168349 , 45.24208263 , 46.26521596 , 47.29856274 , 48.34020691 , 49.38868010 , 50.44272057 , 51.50133645 , 52.56372013 , 53.62920397 , 54.69474698 , 44.80246762 , 56.51294928 , 57.24753073 , 57.99116258 , 58.75379221 , 59.54010251 , 60.35181867 , 61.18894078 , 62.05057669 , 62.93533125 , 63.84148117 , 64.58073155 , 65.25006575 , 65.87138273 , 66.46559768 , 67.04946958 , 67.63563426 , 68.32169854 , 69.02604532 , 69.82469247 , 70.66688901 , 71.54477879 , 72.45236833 , 73.38499358 , 74.33893973 , 75.31111836 , 76.29898266 , 77.30040535 , 78.31361117 , 79.33705595 , 80.36941362 ] ,
    [ 1.80000000 , 0.30524100 , 1.15874889 , 1.59850271 , 1.79279877 , 2.19959804 , 2.85542480 , 3.69146527 , 4.64212234 , 5.66213947 , 6.72270421 , 7.45904447 , 7.92915901 , 8.32008449 , 8.70775781 , 9.16335659 , 9.72177319 , 10.38806702 , 11.15272978 , 11.96270392 , 12.63761772 , 13.40488848 , 14.23103791 , 15.10643981 , 16.02216296 , 16.97059733 , 17.94546383 , 18.94165332 , 19.95502972 , 20.98220106 , 22.02048790 , 22.71996689 , 23.33259982 , 23.91602250 , 24.50919691 , 25.13467508 , 25.80377517 , 26.55720399 , 27.24947463 , 27.86697926 , 28.51211983 , 29.20057991 , 29.93647998 , 30.71881929 , 31.54429461 , 32.40869558 , 33.30761879 , 34.23682210 , 35.19236636 , 35.94549876 , 36.61986692 , 37.24099481 , 37.83494367 , 38.42269017 , 39.01972626 , 39.71795495 , 40.42933872 , 41.35467588 , 42.30974531 , 43.28743592 , 44.28297094 , 45.29289297 , 46.31454853 , 47.34588578 , 48.38530364 , 49.43143100 , 50.48317048 , 51.53961834 , 52.60001940 , 53.66115966 , 44.08934336 , 55.48626880 , 56.22001791 , 56.95426360 , 57.70133850 , 58.46791365 , 59.25728090 , 60.07066578 , 60.90803577 , 61.76864570 , 62.65127071 , 63.40362002 , 64.08931929 , 64.72230009 , 65.32009218 , 65.89861220 , 66.47092251 , 67.13155704 , 67.82634976 , 68.59861639 , 69.41393138 , 70.26554288 , 71.14806289 , 72.05712091 , 72.98912307 , 73.94102981 , 74.91028054 , 75.89469824 , 76.89243326 , 77.90186574 , 78.92158935 ] ,
    [ 1.90000000 , 0.27628078 , 1.10126181 , 1.56534123 , 1.75153187 , 2.11329607 , 2.71937225 , 3.51350607 , 4.43272698 , 5.43075187 , 6.47685889 , 7.24472253 , 7.74229966 , 8.13919355 , 8.51202077 , 8.93389189 , 9.44727623 , 10.06467016 , 10.78168031 , 11.57419494 , 12.26387898 , 13.01429668 , 13.82129267 , 14.67744365 , 15.57489646 , 16.50655661 , 17.46634950 , 18.44919882 , 19.45090921 , 20.46799171 , 21.49763124 , 22.21222676 , 22.83353426 , 23.41257344 , 23.98875864 , 24.58756129 , 25.22359646 , 25.95495939 , 26.65310679 , 27.26332046 , 27.89187014 , 28.55725839 , 29.26626588 , 30.01997187 , 30.81656891 , 31.65286077 , 32.52509672 , 33.42942635 , 34.36212828 , 35.12822545 , 35.81761476 , 36.44774256 , 37.04134456 , 37.61885659 , 38.19672311 , 38.86714667 , 39.56788450 , 40.47155441 , 41.40664438 , 42.36611912 , 43.34514362 , 44.34016008 , 45.34841516 , 46.36774316 , 47.39642186 , 48.43298667 , 49.47624265 , 50.52519418 , 51.57900002 , 52.63429623 , 43.38715802 , 54.46533535 , 55.20035072 , 55.92779542 , 56.66178741 , 57.41068836 , 58.17923391 , 58.96984453 , 59.78338254 , 60.61980451 , 61.47844378 , 62.24182417 , 62.94373497 , 63.59073785 , 64.19643206 , 64.77510157 , 65.33953168 , 65.97683903 , 66.65722872 , 67.40366135 , 68.19207627 , 69.01689127 , 69.87341156 , 70.75764736 , 71.66620073 , 72.59614441 , 73.54495565 , 74.51044931 , 75.49073330 , 76.48413962 , 77.48920374 ] ,
    [ 2.00000000 , 0.25000001 , 1.04570402 , 1.53172391 , 1.71511826 , 2.03696035 , 2.59499480 , 3.34659838 , 4.23258311 , 5.20638411 , 6.23577475 , 7.03004531 , 7.55613822 , 7.96380864 , 8.32786145 , 8.72183494 , 9.19439590 , 9.76505365 , 10.43472567 , 11.20300541 , 11.90040920 , 12.63354217 , 13.42121603 , 14.25788771 , 15.13670445 , 16.05108700 , 16.99519070 , 17.96400249 , 18.95329568 , 19.95950769 , 20.97970619 , 21.71015353 , 22.34305652 , 22.92225622 , 23.48637697 , 24.06289714 , 24.66925022 , 25.37538948 , 26.07262899 , 26.67549258 , 27.28877129 , 27.93263451 , 28.61599184 , 29.34179818 , 30.10970456 , 30.91757218 , 31.76237873 , 32.64074898 , 33.54925780 , 34.32619407 , 35.03051764 , 35.67203565 , 36.26947368 , 36.84185334 , 37.40581970 , 38.04972280 , 38.73490599 , 39.61608567 , 40.53010445 , 41.47008418 , 42.43119333 , 43.40981911 , 44.40314188 , 45.40890716 , 46.42528873 , 47.45074436 , 48.48399215 , 49.52395160 , 50.56969991 , 51.61774686 , 42.69810383 , 53.45295260 , 54.19064490 , 54.91342474 , 55.63659076 , 56.36985453 , 57.11922218 , 57.88823219 , 58.67864067 , 59.49112986 , 60.32562885 , 61.09755600 , 61.81455885 , 62.47672226 , 63.09348976 , 63.67691688 , 64.23889053 , 64.85629513 , 65.51963744 , 66.24121921 , 67.00317845 , 67.80114465 , 68.63118197 , 69.48975770 , 70.37374165 , 71.28037803 , 72.20723289 , 73.15215577 , 74.11324764 , 75.08882137 , 76.07737797 ] ,
    [ 2.10000000 , 0.22621844 , 0.99221736 , 1.49758691 , 1.68246977 , 1.96949143 , 2.48166342 , 3.19063820 , 4.04201815 , 4.98967202 , 6.00028643 , 6.81585644 , 7.37038493 , 7.79262584 , 8.15336018 , 8.52515197 , 8.96144669 , 9.48815927 , 10.11153674 , 10.85026965 , 11.54848018 , 12.26358332 , 13.03154980 , 13.84838214 , 14.70812516 , 15.60469379 , 16.53248385 , 17.48656618 , 18.46270420 , 19.45728050 , 20.46726201 , 21.21378295 , 21.86046492 , 22.44376282 , 23.00047175 , 23.55918073 , 24.13959004 , 24.81893394 , 25.50942894 , 26.10454722 , 26.70354319 , 27.32725509 , 27.98619217 , 28.68494041 , 29.42452779 , 30.20387982 , 31.02075168 , 31.87230896 , 32.75548965 , 33.54065254 , 34.25892572 , 34.91317074 , 35.51770546 , 36.08942625 , 36.64447697 , 37.26441132 , 37.93098292 , 38.78920687 , 39.68139369 , 40.60089818 , 41.54295467 , 42.50394279 , 43.48101017 , 44.47184098 , 45.47452674 , 46.48746327 , 47.50929436 , 48.53886427 , 49.57517583 , 50.61463600 , 42.02392975 , 52.45170891 , 53.19289963 , 53.91271759 , 54.62706764 , 55.34665268 , 56.07854209 , 56.82727926 , 57.59548089 , 58.38455308 , 59.19503697 , 59.97275100 , 60.70297340 , 61.38036601 , 62.01025495 , 62.60207033 , 63.16628983 , 63.76797705 , 64.41355936 , 65.11166281 , 65.84803736 , 66.61954353 , 67.42304998 , 68.25554504 , 69.11423201 , 69.99658048 , 70.90029402 , 71.82329950 , 72.76372829 , 73.71990387 , 74.69031757 ] ,
    [ 2.20000000 , 0.20474602 , 0.94089711 , 1.46294502 , 1.65269064 , 1.90984155 , 2.37868277 , 3.04538782 , 3.86119801 , 4.78108729 , 5.77107579 , 6.60297822 , 7.18496395 , 7.62458687 , 7.98678267 , 8.34185885 , 8.74662909 , 9.23267006 , 9.81142152 , 10.51667604 , 11.20922032 , 11.90534564 , 12.65305804 , 13.44958501 , 14.28975469 , 15.16794183 , 16.07878257 , 17.01744446 , 17.97969726 , 18.96188355 , 19.96088426 , 20.72321341 , 21.38516068 , 21.97585514 , 22.52942599 , 23.07472791 , 23.63313689 , 24.28545154 , 24.96447497 , 25.55129899 , 26.13675998 , 26.74154717 , 27.37727209 , 28.04988802 , 28.76168643 , 29.51263365 , 30.30128728 , 31.12540188 , 31.98233354 , 32.77275470 , 33.50325863 , 34.17061100 , 34.78457357 , 35.35937982 , 35.91005179 , 36.50939782 , 37.15597907 , 37.99112839 , 38.86105073 , 39.75940391 , 40.68154906 , 41.62390575 , 42.58362232 , 43.55835028 , 44.54612381 , 45.54529239 , 46.55443986 , 47.57234687 , 48.59795140 , 49.62758041 , 41.36590017 , 51.46390564 , 52.20893382 , 52.92709525 , 53.63438114 , 54.34213016 , 55.05824870 , 55.78814618 , 56.53523930 , 57.30163356 , 58.08847905 , 58.86908056 , 59.61010344 , 60.30189778 , 60.94591575 , 61.54875333 , 62.11909371 , 62.70954531 , 63.33821618 , 64.01453737 , 64.72657049 , 65.47240357 , 66.24973687 , 67.05613016 , 67.88917734 , 68.74662107 , 69.62634782 , 70.52640270 , 71.44498510 , 72.38045874 , 73.33133062 ] ,
    [ 2.30000000 , 0.18539097 , 0.89179869 , 1.42786270 , 1.62505359 , 1.85703112 , 2.28532149 , 2.91050752 , 3.69015432 , 4.58095845 , 5.54868669 , 6.39218539 , 6.99995958 , 7.45886175 , 7.82659606 , 8.17007037 , 8.54810311 , 8.99709452 , 9.53340826 , 10.20251491 , 10.88356732 , 11.55966526 , 12.28647263 , 13.06215332 , 13.88220424 , 14.74141889 , 15.63466644 , 16.55721831 , 17.50486275 , 18.47391405 , 19.46118030 , 20.23860690 , 20.91666214 , 21.51740644 , 22.07165972 , 22.60777334 , 23.14819731 , 23.77433424 , 24.43832348 , 25.01629604 , 25.58881529 , 26.17578989 , 26.78948866 , 27.43696620 , 28.12164318 , 28.84447918 , 29.60483802 , 30.40109504 , 31.23106748 , 32.02355310 , 32.76399854 , 33.44400213 , 34.06882911 , 34.64968456 , 35.19994980 , 35.78253982 , 36.40917490 , 37.22145089 , 38.06898729 , 38.94580867 , 39.84746046 , 40.77044824 , 41.71195379 , 42.66962499 , 43.64146534 , 44.62579361 , 45.62114919 , 46.62626231 , 47.64001727 , 48.65868295 , 40.72480778 , 50.49151538 , 51.24034286 , 51.95780234 , 52.65952156 , 53.35713851 , 54.05916410 , 54.77171879 , 55.49893686 , 56.24357947 , 57.00738555 , 57.78796089 , 58.53701017 , 59.24166506 , 59.89989654 , 60.51542606 , 61.09488628 , 61.67851625 , 62.29227767 , 62.94875879 , 63.63799927 , 64.35928852 , 65.11116853 , 65.89180650 , 66.69923334 , 67.53150572 , 68.38673370 , 69.26311876 , 70.15896447 , 71.07270373 , 72.00288443 ] ,
    [ 2.40000000 , 0.16796561 , 0.84494404 , 1.39243373 , 1.59897550 , 1.81015783 , 2.20083558 , 2.78558195 , 3.52880864 , 4.38949049 , 5.33353960 , 6.18418899 , 6.81557129 , 7.29482685 , 7.67147372 , 8.00803389 , 8.36404525 , 8.77983644 , 9.27631801 , 9.90773187 , 10.57224360 , 11.22725163 , 11.93245376 , 12.68670547 , 13.48606596 , 14.32570508 , 15.20071401 , 16.10647145 , 17.03879336 , 17.99397513 , 18.96876383 , 19.76018495 , 20.45460958 , 21.06742716 , 21.62568336 , 22.15654947 , 22.68296098 , 23.28461572 , 23.93114822 , 24.49981270 , 25.05990463 , 25.63009879 , 26.22294066 , 26.84633101 , 27.50467443 , 28.19985806 , 28.93203798 , 29.70022714 , 30.50273568 , 31.29399014 , 32.04167466 , 32.73316915 , 33.36946838 , 33.95854583 , 34.51173604 , 35.08154423 , 35.68940524 , 36.47929134 , 37.30460287 , 38.15978786 , 39.04062818 , 39.94375858 , 40.86642585 , 41.80630275 , 42.76138893 , 43.72998829 , 44.71061189 , 45.70195358 , 46.70285629 , 47.70955177 , 40.10101326 , 49.53616407 , 50.28847326 , 51.00588681 , 51.70329684 , 52.39233490 , 53.08188833 , 53.77862599 , 54.48730111 , 55.21127116 , 55.95282950 , 56.73056070 , 57.48467842 , 58.20011895 , 58.87186382 , 59.50086195 , 60.09156409 , 60.67244969 , 61.27405638 , 61.91280320 , 62.58103171 , 63.27918472 , 64.00664038 , 64.76219448 , 65.54434943 , 66.35150937 , 67.18204320 , 68.03434288 , 68.90684959 , 69.79809296 , 70.70668630 ] ,
    [ 2.50000000 , 0.15229031 , 0.80032744 , 1.35676692 , 1.57399453 , 1.76840045 , 2.12448606 , 2.67014202 , 3.37699347 , 4.20678284 , 5.12594566 , 5.97962753 , 6.63207718 , 7.13204047 , 7.52029188 , 7.85415070 , 8.19269153 , 8.57925184 , 9.03882694 , 9.63198246 , 10.27574859 , 10.90866536 , 11.59156312 , 12.32379392 , 13.10188688 , 13.92134882 , 14.77748083 , 15.66577040 , 16.58206858 , 17.52265967 , 18.48424049 , 19.28822108 , 19.99876325 , 20.62507847 , 21.19013435 , 21.71934662 , 22.23557961 , 22.81507024 , 23.44278326 , 24.00185847 , 24.55002143 , 25.10442032 , 25.67756598 , 26.27797056 , 26.91087415 , 27.57901338 , 28.28330818 , 29.02341274 , 29.79815120 , 30.58488898 , 31.33684271 , 32.03809993 , 32.68573798 , 33.28444195 , 33.84320983 , 34.40410796 , 34.99519164 , 35.76340760 , 36.56690131 , 37.40059297 , 38.26054643 , 39.14356446 , 40.04698881 , 40.96854422 , 41.90625226 , 42.85841804 , 43.82354047 , 44.80029143 , 45.78748523 , 46.78133642 , 39.49450381 , 48.59913160 , 49.35441223 , 50.07219033 , 50.76632967 , 51.44818775 , 52.12681289 , 52.80925940 , 53.50078993 , 54.20528708 , 54.92555273 , 55.69780894 , 56.45400065 , 57.17778757 , 57.86170924 , 58.50415803 , 59.10738482 , 59.68908257 , 60.28167822 , 60.90487782 , 61.55403108 , 62.23066610 , 62.93497671 , 63.66639392 , 64.42391339 , 65.20631246 , 66.01224777 , 66.84033118 , 67.68917102 , 68.55741915 , 69.44377767 ] ,
    [ 2.60000000 , 0.13819600 , 0.75792078 , 1.32097667 , 1.54974967 , 1.73101898 , 2.05555202 , 2.56368287 , 3.23447052 , 4.03284552 , 4.92611993 , 5.77906315 , 6.44980478 , 6.97021782 , 7.37212033 , 7.70698770 , 8.03236908 , 8.39369471 , 8.81951916 , 9.37468504 , 9.99436301 , 10.60430775 , 11.26424724 , 11.97388639 , 12.73015003 , 13.52884859 , 14.36548237 , 15.23564862 , 16.13523998 , 17.06053667 , 18.00819528 , 18.82303129 , 19.54899625 , 20.18967657 , 20.76380023 , 21.29455693 , 21.80422930 , 22.36429969 , 22.97277325 , 23.52219836 , 24.05896348 , 24.59853451 , 25.15314534 , 25.73171101 , 26.34016209 , 26.98199910 , 27.65886612 , 28.37105087 , 29.11790304 , 29.89694580 , 30.65006221 , 31.35892008 , 32.01712309 , 32.62613800 , 33.19244998 , 33.74802414 , 34.32486322 , 35.07231477 , 35.85460201 , 36.66715701 , 37.50636347 , 38.36922582 , 39.25320849 , 40.15611322 , 41.07600717 , 42.01121281 , 42.96023274 , 43.92173109 , 44.89450625 , 45.87477446 , 38.90496104 , 47.68136592 , 48.43898891 , 49.15734725 , 49.84906021 , 50.52498575 , 51.19413645 , 51.86379455 , 52.53961683 , 53.22593158 , 53.92599440 , 54.69040358 , 55.44576023 , 56.17524345 , 56.86951780 , 57.52472010 , 58.14098166 , 58.72641559 , 59.31322433 , 59.92306760 , 60.55516453 , 61.21204271 , 61.89467714 , 62.60312662 , 63.33688927 , 64.09513317 , 64.87682487 , 65.68082014 , 66.50591943 , 67.35091975 , 68.21463355 ] ,
    [ 2.70000000 , 0.12552555 , 0.71767825 , 1.28517654 , 1.52596289 , 1.69735234 , 1.99334002 , 2.46567844 , 3.10094638 , 3.86761368 , 4.73419363 , 5.58298135 , 6.26910835 , 6.80920654 , 7.22620915 , 7.56528156 , 7.88151815 , 8.22155281 , 8.61693076 , 9.13507035 , 9.72816154 , 10.31441912 , 10.95082889 , 11.63735424 , 12.37126159 , 13.14864005 , 13.96518136 , 14.81659437 , 15.69881970 , 16.60814042 , 17.54118233 , 18.36496363 , 19.10528403 , 19.76068989 , 20.34563101 , 20.88070496 , 21.38715826 , 21.93080814 , 22.52042658 , 23.06038083 , 23.58634699 , 24.11206386 , 24.64931072 , 25.20722648 , 25.79229523 , 26.40869237 , 27.05873825 , 27.74333700 , 28.46236674 , 29.23072377 , 29.98187344 , 30.69586291 , 31.36332425 , 31.98268130 , 32.55783605 , 33.11125742 , 33.67666193 , 34.40438920 , 35.16624148 , 35.95819254 , 36.77697553 , 37.61982440 , 38.48435106 , 39.36845659 , 40.27027469 , 41.18816116 , 42.12063735 , 43.06637320 , 44.02416343 , 44.99024369 , 38.33182365 , 46.78350697 , 47.54278478 , 48.26179062 , 48.95175351 , 49.62284970 , 50.28388200 , 50.94221297 , 51.60377705 , 52.27326366 , 52.95432117 , 53.70882165 , 54.46061622 , 55.19306885 , 55.89552710 , 56.56223054 , 57.19135175 , 57.78276087 , 58.36684275 , 58.96545509 , 59.58252834 , 60.22148899 , 60.88404566 , 61.57086449 , 62.28194332 , 63.01685019 , 63.77487668 , 64.55514075 , 65.35665486 , 66.17838108 , 67.01926154 ] ,
    [ 2.80000000 , 0.11413441 , 0.67954034 , 1.24947526 , 1.50242392 , 1.66681438 , 1.93719061 , 2.37559316 , 2.97608581 , 3.71096042 , 4.55022549 , 5.39179296 , 6.09035129 , 6.64896347 , 7.08197287 , 7.42793716 , 7.73870652 , 8.06127532 , 8.42958605 , 8.91222669 , 9.47703087 , 10.03908372 , 10.65150462 , 11.31446625 , 12.02554303 , 12.78108736 , 13.57697899 , 14.40904195 , 15.27327197 , 16.16596216 , 17.08371686 , 17.91438747 , 18.66769172 , 19.33773116 , 19.93474302 , 20.47646716 , 20.98272217 , 21.51306389 , 22.08486825 , 22.61577027 , 23.13162592 , 23.64448683 , 24.16555737 , 24.70405159 , 25.26688138 , 25.85880809 , 26.48277485 , 27.14027737 , 27.83171773 , 28.58664931 , 29.33277586 , 30.04923735 , 30.72422666 , 31.35338335 , 31.93805075 , 32.49199286 , 33.04883039 , 33.75795753 , 34.50026224 , 35.27227927 , 36.07111225 , 36.89424645 , 37.73946256 , 38.60478028 , 39.48841769 , 40.38877924 , 41.30441898 , 42.23402529 , 43.17640060 , 44.12781654 , 37.77435550 , 45.90591691 , 46.66615073 , 47.38576357 , 48.07451058 , 48.74174636 , 49.39591489 , 50.04432462 , 50.69307361 , 51.34712590 , 52.01045772 , 52.75333088 , 53.49909062 , 54.23182210 , 54.94008271 , 55.61660525 , 56.25782625 , 56.85675859 , 57.44083057 , 58.03021318 , 58.63424835 , 59.25714968 , 59.90129983 , 60.56794023 , 61.25755479 , 61.97011244 , 62.70523779 , 63.46232340 , 64.24060848 , 65.03923658 , 65.85729617 ] ,
    [ 2.90000000 , 0.10389064 , 0.64343735 , 1.21397430 , 1.47897751 , 1.63888908 , 1.88648252 , 2.29289135 , 2.85952301 , 3.56270804 , 4.37421189 , 5.20583774 , 5.91389286 , 6.48953313 , 6.93897309 , 7.29402174 , 7.60263745 , 7.91139319 , 8.25602689 , 8.70514019 , 9.24069124 , 9.77823912 , 10.36634711 , 11.00538688 , 11.69322710 , 12.42647810 , 13.20120925 , 14.01336584 , 14.85900706 , 15.73444412 , 16.63626932 , 17.47168311 , 18.23636004 , 18.92054570 , 19.53041627 , 20.08068232 , 20.58940884 , 21.10954955 , 21.66509024 , 22.18758153 , 22.69411483 , 23.19515451 , 23.70125834 , 24.22159596 , 24.76339450 , 25.33191483 , 25.93066619 , 26.56170506 , 27.22594662 , 27.96501061 , 28.70320872 , 29.41939609 , 30.09986551 , 30.73779253 , 31.33206805 , 31.88866263 , 32.43968173 , 33.13136998 , 33.85508786 , 34.60793945 , 35.38741166 , 36.19125656 , 37.01744103 , 37.86411931 , 38.72960840 , 39.61237573 , 40.51102057 , 41.42426114 , 42.35091795 , 43.28731381 , 37.23169521 , 45.04871442 , 45.80922897 , 46.52933473 , 47.21728217 , 47.88150378 , 48.52996133 , 49.16978990 , 49.80714288 , 50.44717286 , 51.09411711 , 51.82400280 , 52.56155927 , 53.29200705 , 54.00359345 , 54.68794492 , 55.34002811 , 55.94737014 , 56.53368864 , 57.11567187 , 57.70855640 , 58.31722332 , 58.94465952 , 59.59263943 , 60.26210995 , 60.95343379 , 61.66656967 , 62.40119131 , 63.15677430 , 63.93265635 , 64.72808600 ] ,
    [ 3.00000000 , 0.09467456 , 0.60929230 , 1.17876653 , 1.45551279 , 1.61312514 , 1.84063521 , 2.21704450 , 2.75087113 , 3.42263792 , 4.20609614 , 5.02538886 , 5.74007838 , 6.33102823 , 6.79690061 , 7.16275589 , 7.47215284 , 7.77053365 , 8.09483590 , 8.51273005 , 9.01871962 , 9.53168888 , 10.09531090 , 10.71017797 , 11.37445706 , 12.08502102 , 12.83813585 , 13.62987715 , 14.45637751 , 15.31397557 , 16.19926120 , 17.03723197 , 17.81149086 , 18.50899735 , 19.13208684 , 19.69235483 , 20.20585399 , 20.71880136 , 21.25999786 , 21.77491487 , 22.27301364 , 22.76330938 , 23.25568066 , 23.75915985 , 24.28119065 , 24.82745147 , 25.40195949 , 26.00729683 , 26.64487551 , 27.36595848 , 28.09353484 , 28.80670550 , 29.49038982 , 30.13566101 , 30.73913098 , 31.29995508 , 31.84765189 , 32.52305766 , 33.22918354 , 33.96370056 , 34.72448370 , 35.50956144 , 36.31709980 , 37.14540002 , 37.99288947 , 38.85811126 , 39.73972086 , 40.63647636 , 41.54722552 , 42.46835605 , 36.70289986 , 44.21181068 , 44.97197793 , 45.69241653 , 46.37988454 , 47.04182748 , 47.68562685 , 48.31814122 , 48.94547918 , 49.57289839 , 50.20483018 , 50.92072728 , 51.64824653 , 52.37404720 , 53.08648922 , 53.77648483 , 54.43782295 , 55.05385445 , 55.64415213 , 56.22036144 , 56.80384392 , 57.40002428 , 58.01241532 , 58.64327395 , 59.29397892 , 59.96527209 , 60.65744080 , 61.37044095 , 62.10398923 , 62.85762633 , 63.63077139 ] ,
    [ 3.10000000 , 0.08637812 , 0.57702337 , 1.14393554 , 1.43195449 , 1.58913044 , 1.79910991 , 2.14753694 , 2.64973012 , 3.29049911 , 4.04577675 , 4.85065788 , 5.56923200 , 6.17361233 , 6.65555751 , 7.03350240 , 7.34623223 , 7.63742967 , 7.94465446 , 8.33387879 , 8.81057346 , 9.29911726 , 9.83824078 , 10.42880284 , 11.06928826 , 11.75684603 , 12.48795123 , 13.25882193 , 14.06567608 , 14.90489038 , 15.77306256 , 16.61140772 , 17.39333284 , 18.10305294 , 18.73933570 , 19.31065217 , 19.83084970 , 20.33943865 , 20.86845110 , 21.37678978 , 21.86743311 , 22.34810519 , 22.82800244 , 23.31595048 , 23.81952446 , 24.34474399 , 24.89607618 , 25.47659043 , 26.08817503 , 26.78950946 , 27.50402770 , 28.21151862 , 28.89602714 , 29.54690878 , 30.15872236 , 30.72481009 , 31.27133568 , 31.93157464 , 32.62110264 , 33.33814492 , 34.08096212 , 34.84786296 , 35.63722114 , 36.44749386 , 37.27722730 , 38.12505106 , 38.98968606 , 39.86993883 , 40.76469230 , 41.67041121 , 36.18706281 , 43.39494567 , 44.15419903 , 44.87478546 , 45.56201662 , 46.22231726 , 46.86241445 , 47.48880361 , 48.10745811 , 48.72366153 , 49.34197365 , 50.04322824 , 50.75922417 , 51.47826525 , 52.18918357 , 52.88254621 , 53.55126707 , 54.17573324 , 54.77120064 , 55.34303506 , 55.91869536 , 56.50402502 , 57.10297825 , 57.71823741 , 58.35157561 , 59.00409242 , 59.67639234 , 60.36870914 , 61.08100096 , 61.81301635 , 62.56435223 ] ,
    [ 3.20000000 , 0.07890418 , 0.54654589 , 1.10955560 , 1.40825571 , 1.56656663 , 1.76140978 , 2.08387020 , 2.55569337 , 3.16601569 , 3.89311475 , 4.68180010 , 5.40165177 , 6.01748460 , 6.51483990 , 6.90575367 , 7.22398890 , 7.51092533 , 7.80419610 , 8.16745774 , 8.61561406 , 9.08010508 , 9.59488177 , 10.16113243 , 10.77769158 , 11.44200595 , 12.15077713 , 12.90038111 , 13.68713508 , 14.50746610 , 15.35799065 , 16.19456842 , 16.98216761 , 17.70276611 , 18.35187512 , 18.93489812 , 19.46334683 , 19.97018481 , 20.48930057 , 20.99217661 , 21.47642009 , 21.94862731 , 22.41733048 , 22.89109842 , 23.37756549 , 23.88302228 , 24.41232892 , 24.96900182 , 25.55538142 , 26.23555077 , 26.93486231 , 27.63415195 , 28.31705033 , 28.97158699 , 29.59053139 , 30.16240440 , 30.70950815 , 31.35562622 , 32.02952002 , 32.72994713 , 33.45554480 , 34.20490076 , 34.97660036 , 35.76926233 , 36.58155749 , 37.41221044 , 38.26001503 , 39.12383336 , 40.00259020 , 40.89283765 , 35.68301932 , 42.59772327 , 43.35556381 , 44.07610319 , 44.76327782 , 45.42248401 , 46.05974230 , 46.68111418 , 47.29235840 , 47.89871081 , 48.50479648 , 49.19108034 , 49.89441411 , 50.60486851 , 51.31204207 , 52.00649171 , 52.68055612 , 53.31275002 , 53.91405213 , 54.48267421 , 55.05190413 , 55.62788096 , 56.21491227 , 56.81604429 , 57.43340203 , 58.06841552 , 58.72198964 , 59.39462706 , 60.08652358 , 60.79763669 , 61.52774506 ] ,
    [ 3.30000000 , 0.07216566 , 0.51777399 , 1.07569180 , 1.38439200 , 1.54514376 , 1.72707927 , 2.02556613 , 2.46835307 , 3.04889319 , 3.74794023 , 4.51891982 , 5.23760632 , 5.86286675 , 6.37472159 , 6.77911836 , 7.10466352 , 7.38997780 , 7.67225605 , 8.01234814 , 8.43312896 , 8.87414608 , 9.36489042 , 9.90695280 , 10.49955835 , 11.14047961 , 11.82666657 , 12.55467153 , 13.32092690 , 14.12192396 , 14.95430970 , 15.78704973 , 16.57829696 , 17.30826125 , 17.96953356 , 18.56456266 , 19.10245271 , 19.60988099 , 20.12141756 , 20.62002539 , 21.09898165 , 21.56391273 , 22.02271773 , 22.48367404 , 22.95441436 , 23.44143637 , 23.94993826 , 24.48384202 , 25.04591331 , 25.70384723 , 26.38610954 , 27.07486640 , 27.75374780 , 28.40984239 , 29.03441837 , 29.61212992 , 30.16113365 , 30.79408478 , 31.45325358 , 32.13790008 , 32.84702351 , 33.57948468 , 34.33408036 , 35.10959323 , 35.90482211 , 36.71859275 , 37.54977765 , 38.39730012 , 39.26013225 , 40.13492208 , 35.19037732 , 41.81964440 , 42.57564072 , 43.29593807 , 43.98318611 , 44.64176653 , 45.27696071 , 45.89434062 , 46.49938227 , 47.09720669 , 47.69244437 , 48.36372643 , 49.05359483 , 49.75394016 , 50.45535717 , 51.14868624 , 51.82597671 , 52.46482650 , 53.07214461 , 53.63848081 , 54.20247424 , 54.77044081 , 55.34695228 , 55.93535449 , 56.53807839 , 57.15685251 , 57.79286083 , 58.44686176 , 59.11928138 , 59.81028367 , 60.51982981 ] ,
    [ 3.40000000 , 0.06608468 , 0.49062188 , 1.04240048 , 1.36035650 , 1.52461528 , 1.69570282 , 1.97216919 , 2.38730464 , 2.93882405 , 3.61005810 , 4.36207562 , 5.07733296 , 5.70999199 , 6.23523894 , 6.65330785 , 6.98761627 , 7.27365663 , 7.54771751 , 7.86745821 , 8.26235274 , 8.68066306 , 9.14784659 , 9.66597351 , 10.23470626 , 10.85217601 , 11.51560668 , 12.22174797 , 12.96716537 , 13.74842976 , 14.56223139 , 15.38915925 , 16.18203118 , 16.91971787 , 17.59223987 , 18.19924966 , 18.74742506 , 19.25749374 , 19.76371855 , 20.25929112 , 20.73410758 , 21.19296936 , 21.64318028 , 22.09270329 , 22.54911829 , 23.01907219 , 23.50804861 , 24.02033333 , 24.55908813 , 25.19404952 , 25.85773384 , 26.53385268 , 27.20639771 , 27.86188426 , 28.49037940 , 29.07356786 , 29.62536459 , 30.24599535 , 30.89127538 , 31.56093092 , 32.25430379 , 32.97051795 , 33.70857749 , 34.46742852 , 35.24599920 , 36.04322010 , 36.85804638 , 37.68946682 , 38.53650518 , 39.39591213 , 34.70703295 , 41.06013723 , 41.81392071 , 42.53378612 , 43.22119591 , 43.87954775 , 44.51336829 , 45.12769827 , 45.72767418 , 46.31824219 , 46.90398243 , 47.56049534 , 48.23641082 , 48.92543579 , 49.61932973 , 50.30946427 , 50.98786277 , 51.63201940 , 52.24510967 , 52.80985923 , 53.36961093 , 53.93074500 , 54.49800985 , 55.07498557 , 55.66436097 , 56.26812754 , 56.88772352 , 57.52414633 , 58.17804185 , 58.84977478 , 59.53948667 ] ,
    [ 3.50000000 , 0.06059172 , 0.46500486 , 1.00972971 , 1.33615595 , 1.50477328 , 1.66690335 , 1.92324793 , 2.31215030 , 2.83549227 , 3.47925316 , 4.21128538 , 4.92103676 , 5.55909589 , 6.09647715 , 6.52812280 , 6.87231767 , 7.16114088 , 7.42955514 , 7.73173649 , 8.10248598 , 8.49902367 , 8.94326556 , 9.43783665 , 9.98288599 , 10.57693919 , 11.21752239 , 11.90160588 , 12.62590780 , 13.38709548 , 14.18191602 , 15.00117198 , 15.79367881 , 16.53735604 , 17.22000742 , 17.83868319 , 18.39766315 , 18.91211761 , 19.41518415 , 19.90895535 , 20.38079063 , 20.83479411 , 21.27771368 , 21.71718297 , 22.16068599 , 22.61496651 , 23.08574354 , 23.57762489 , 24.09413779 , 24.70570377 , 25.34959410 , 26.01122092 , 26.67524655 , 27.32795462 , 27.95851251 , 28.54646051 , 29.10153226 , 29.71057270 , 30.34271427 , 30.99810845 , 31.67641644 , 32.37701205 , 33.09909930 , 33.84178466 , 34.60412502 , 35.38515719 , 36.18392135 , 36.99947473 , 37.83089606 , 38.67504354 , 34.23454877 , 40.31858408 , 41.06984084 , 41.78909106 , 42.47671525 , 43.13517043 , 43.76822726 , 44.38036610 , 44.97633804 , 45.56086179 , 46.13841571 , 46.78061989 , 47.44238467 , 48.11918497 , 48.80405695 , 49.48910384 , 50.16655780 , 50.81447961 , 51.43274105 , 51.99639182 , 52.55270315 , 53.10801528 , 53.66716930 , 54.23391493 , 54.81114970 , 55.40109024 , 56.00540144 , 56.62530015 , 57.26163886 , 57.91497441 , 58.58562393 ] ,
    [ 3.60000000 , 0.05562478 , 0.44084009 , 0.97771989 , 1.31180746 , 1.48544415 , 1.64034030 , 1.87839590 , 2.24250194 , 2.73857741 , 3.35529452 , 4.06653112 , 4.76889054 , 5.41040901 , 5.95855806 , 6.40344022 , 6.75833882 , 7.05171461 , 7.31683629 , 7.60418213 , 7.95271222 , 8.32855516 , 8.75060995 , 9.22212617 , 9.74378839 , 10.31455380 , 10.93228066 , 11.59418469 , 12.29715763 , 13.03798131 , 13.81347422 , 14.62332687 , 15.41353768 , 16.16142295 , 16.85291857 , 17.48269295 , 18.05269702 , 18.57297383 , 19.07487292 , 19.56804389 , 20.03804439 , 20.48838932 , 20.92530804 , 21.35609505 , 21.78810168 , 22.22812105 , 22.68206007 , 23.15480730 , 23.65022348 , 24.23826203 , 24.86144719 , 25.50699432 , 26.16049224 , 26.80830236 , 27.43898618 , 28.03068258 , 28.58913197 , 29.18719205 , 29.80685162 , 30.44864338 , 31.11252180 , 31.79809452 , 32.50475540 , 33.23176595 , 33.97830958 , 34.74352868 , 35.52654935 , 36.32649901 , 37.14251363 , 37.97156225 , 33.76802454 , 39.59434481 , 40.34280571 , 41.06126295 , 41.74912202 , 42.40795183 , 43.04077761 , 43.65150126 , 44.24445287 , 44.82407842 , 45.39470795 , 46.02325466 , 46.67093103 , 47.33489682 , 48.00952610 , 48.68780729 , 49.36238347 , 50.01241511 , 50.63496144 , 51.19781064 , 51.75130097 , 52.30163786 , 52.85367671 , 53.41127426 , 53.97748765 , 54.55471972 , 55.14483255 , 55.74924062 , 56.36898757 , 57.00481142 , 57.65719777 ] ,
    [ 3.70000000 , 0.05112865 , 0.41804720 , 0.94640436 , 1.28733578 , 1.46648450 , 1.61570758 , 1.83723201 , 2.17798331 , 2.64775789 , 3.23793949 , 3.92776349 , 4.62103545 , 5.26415117 , 5.82162938 , 6.27920122 , 6.64534129 , 6.94476108 , 7.20872035 , 7.48385226 , 7.81221262 , 8.16855811 , 8.56930131 , 9.01837718 , 9.51705186 , 10.06475085 , 10.65969509 , 11.29937153 , 11.98086742 , 12.70109814 , 13.45696895 , 14.25582438 , 15.04188765 , 15.79218096 , 16.49111002 , 17.13119964 , 17.71217527 , 18.23940601 , 18.74193071 , 19.23564071 , 19.70491834 , 20.15277752 , 20.58496196 , 21.00841999 , 21.43033821 , 21.85751567 , 22.29600218 , 22.75092641 , 23.22644981 , 23.79109346 , 24.39295363 , 25.02110644 , 25.66227149 , 26.30316155 , 26.93201111 , 27.52621323 , 28.08780433 , 28.67537509 , 29.28311186 , 29.91188305 , 30.56190822 , 31.23301077 , 31.92476229 , 32.63657213 , 33.36774652 , 34.11753106 , 34.88513736 , 35.66976364 , 36.47060450 , 37.28474158 , 33.31334454 , 38.88677634 , 39.63220615 , 40.34969500 , 41.03777889 , 41.69719735 , 42.33025019 , 42.94025243 , 43.53108686 , 44.10688883 , 44.67179835 , 45.28749336 , 45.92137179 , 46.57216885 , 47.23561343 , 47.90568827 , 48.57561481 , 49.22605859 , 49.85178946 , 50.41396775 , 50.96509000 , 51.51114262 , 52.05692390 , 52.60633821 , 53.16255426 , 53.72812205 , 54.30507034 , 54.89498787 , 55.49909223 , 56.11828964 , 56.75322516 ] ,
    [ 3.80000000 , 0.04705418 , 0.39654868 , 0.91581000 , 1.26277118 , 1.44777745 , 1.59273139 , 1.79940060 , 2.11823178 , 2.56271380 , 3.12693694 , 3.79490598 , 4.47758212 , 5.12052709 , 5.68585554 , 6.15539971 , 6.53306692 , 6.83975618 , 7.10445656 , 7.36986702 , 7.68017856 , 8.01831881 , 8.39873105 , 8.82608515 , 9.30226986 , 9.82721386 , 10.39953087 , 11.01700522 , 11.67694217 , 12.37641032 , 13.11241783 , 13.89882495 , 14.67898455 , 15.42989709 , 16.13475920 , 16.78420049 , 17.37585227 , 17.91087342 , 18.41559584 , 18.91089818 , 19.38051017 , 19.82701406 , 20.25569493 , 20.67314884 , 21.08636903 , 21.50212053 , 21.92655322 , 22.36499606 , 22.82187780 , 23.36349581 , 23.94368520 , 24.55340158 , 25.18065126 , 25.81273392 , 26.43781554 , 27.03310978 , 27.59731447 , 28.17477309 , 28.77104950 , 29.38730208 , 30.02398616 , 30.68112133 , 31.35844340 , 32.05550091 , 32.77171795 , 33.50643956 , 34.25896125 , 35.02855172 , 35.81446473 , 36.61389501 , 32.86050779 , 38.19524862 , 38.93743518 , 39.65377833 , 40.34204675 , 41.00221284 , 41.63587852 , 42.24577174 , 42.83531008 , 43.40828729 , 43.96861662 , 44.57238544 , 45.19295206 , 45.83049835 , 46.48208735 , 47.14276435 , 47.80646167 , 48.45563997 , 49.08330880 , 49.64480604 , 50.19386502 , 50.73618031 , 51.27642948 , 51.81850943 , 52.36565426 , 52.92052285 , 53.48527992 , 54.06166414 , 54.65104838 , 55.25449271 , 55.87279107 ] ,
    [ 3.90000000 , 0.04335760 , 0.37627021 , 0.88595782 , 1.23814761 , 1.42922924 , 1.57116801 , 1.76457106 , 2.06289962 , 2.48312927 , 3.02203025 , 3.66785889 , 4.33861211 , 4.97972333 , 5.55140993 , 6.03207203 , 6.42132795 , 6.73626116 , 7.00338073 , 7.26141253 , 7.55582197 , 7.87712027 , 8.23827064 , 8.64471475 , 9.09899838 , 9.60158496 , 10.15150989 , 10.74688054 , 11.38524285 , 12.06383869 , 12.77979575 , 13.55244837 , 14.32505565 , 15.07483413 , 15.78407192 , 16.44175546 , 17.04357496 , 17.58694280 , 18.09520095 , 18.59304404 , 19.06397539 , 19.51019771 , 19.93655811 , 20.34929405 , 20.75517918 , 21.16090725 , 21.57268742 , 21.99600993 , 22.43553708 , 22.95470715 , 23.51313375 , 24.10363782 , 24.71562379 , 25.33717549 , 25.95662438 , 26.55148360 , 27.11753055 , 27.68514846 , 28.27033378 , 28.87449016 , 29.49827890 , 30.14189540 , 30.80522531 , 31.48794667 , 32.18959529 , 32.90961091 , 33.64737040 , 34.40221170 , 35.17344749 , 35.95838505 , 32.42128556 , 37.51915700 , 38.25790107 , 38.97291463 , 39.66129636 , 40.32231557 , 40.95690935 , 41.56722544 , 42.15620561 , 42.72727761 , 43.28409617 , 43.87695179 , 44.48485613 , 45.10929534 , 45.74861501 , 46.39895467 , 47.05505600 , 47.70136406 , 48.32964034 , 48.89033188 , 49.43750425 , 49.97649924 , 50.51181852 , 51.04730135 , 51.58620368 , 52.13125662 , 52.68473039 , 53.24848891 , 53.82404080 , 54.41258448 , 55.01505098 ] ,
    [ 4.00000000 , 0.04000000 , 0.35714076 , 0.85686352 , 1.21350129 , 1.41076614 , 1.55080156 , 1.73243727 , 2.01165484 , 2.40869434 , 2.92295980 , 3.54650280 , 4.20417974 , 4.84190632 , 5.41846855 , 5.90928773 , 6.30999744 , 6.63391517 , 6.90491095 , 7.15774225 , 7.43838370 , 7.74425173 , 8.08728087 , 8.47370821 , 8.90676309 , 9.38747111 , 9.91531586 , 10.48875256 , 11.10559008 , 11.76326367 , 12.45903754 , 13.21677390 , 13.98029637 , 14.72724318 , 15.43927139 , 16.10397429 , 16.71526992 , 17.26727910 , 17.78017204 , 18.28138527 , 18.75453428 , 19.20147912 , 19.62664349 , 20.03589897 , 20.43577496 , 20.83285891 , 21.23338024 , 21.64295236 , 22.06643711 , 22.56391729 , 23.10072087 , 23.67149208 , 24.26710486 , 24.87658683 , 25.48864215 , 26.08147867 , 26.64840267 , 27.20635578 , 27.78073230 , 28.37313816 , 28.98441122 , 29.61490200 , 30.26463125 , 30.93339608 , 31.62083697 , 32.32648298 , 33.04978899 , 33.79016020 , 34.54696730 , 35.31762872 , 31.98118599 , 36.85793143 , 37.59303766 , 38.30652653 , 38.99491833 , 39.65684362 , 40.29261178 , 40.90380310 , 41.49287926 , 42.06288375 , 42.61718582 , 43.20019924 , 43.79622310 , 44.40789656 , 45.03477139 , 45.67408151 , 46.32144439 , 46.96339308 , 47.59091798 , 48.15059035 , 48.69594521 , 49.23192279 , 49.76280206 , 50.29232012 , 50.82371449 , 51.35975391 , 51.90278470 , 52.45477138 , 53.01733824 , 53.59180597 , 54.17923003 ] ,
    [ 4.10000000 , 0.03694672 , 0.33909280 , 0.82853809 , 1.18886950 , 1.39233168 , 1.53144181 , 1.70271690 , 1.96418188 , 2.33910654 , 2.82946515 , 3.43070194 , 4.07431397 , 4.70722125 , 5.28720487 , 5.78714135 , 6.19900035 , 6.53242761 , 6.80854273 , 7.05817681 , 7.32713998 , 7.61901674 , 7.94512020 , 8.31249308 , 8.72506637 , 9.18445004 , 9.69059955 , 10.24234104 , 10.83776794 , 11.47452858 , 12.15004082 , 12.89184106 , 13.64486808 , 14.38735775 , 15.10058874 , 15.77100458 , 16.39093075 , 16.95163561 , 17.47002525 , 17.97530956 , 18.45147641 , 18.90006729 , 19.32509136 , 19.73204587 , 20.12719247 , 20.51697905 , 20.90761785 , 21.30480818 , 21.71357738 , 22.19027905 , 22.70580814 , 23.25656676 , 23.83493458 , 24.43100688 , 25.03403961 , 25.62325285 , 26.18994283 , 26.73832334 , 27.30209430 , 27.88302353 , 28.48209685 , 29.09979945 , 29.73627255 , 30.39142148 , 31.06498365 , 31.75657169 , 32.46571451 , 33.19188205 , 33.93450138 , 34.69110017 , 31.55297441 , 36.21104279 , 36.94231209 , 37.65406572 , 38.34233120 , 39.00516377 , 39.64228507 , 40.25472555 , 40.84446796 , 41.41415888 , 41.96685980 , 42.54113375 , 43.12616174 , 43.72557964 , 44.34005019 , 44.96787519 , 45.60558505 , 46.24183378 , 46.86726844 , 47.42564367 , 47.96916305 , 48.50232834 , 49.02915748 , 49.55324671 , 50.07777865 , 50.60552767 , 51.13888804 , 51.67990092 , 52.23028608 , 52.79147002 , 53.36461943 ] ,
    [ 4.20000000 , 0.03416689 , 0.32206221 , 0.80098824 , 1.16428965 , 1.37388413 , 1.51292204 , 1.67515047 , 1.92018186 , 2.27407217 , 2.74128689 , 3.32030709 , 3.94902059 , 4.57579171 , 5.15778584 , 5.66574537 , 6.08830511 , 6.43157061 , 6.71384363 , 6.96210290 , 7.22140715 , 7.50073981 , 7.81115198 , 8.16048936 , 8.55339378 , 8.99207612 , 9.47698379 , 10.00733489 , 10.58152775 , 11.19744292 , 11.85266891 , 12.57765095 , 13.31889701 , 14.05538913 , 14.76825483 , 15.44302104 , 16.07060620 , 16.63984392 , 17.16436210 , 17.67428452 , 18.15416309 , 18.60523400 , 19.03109607 , 19.43686262 , 19.82850484 , 20.21229943 , 20.59440539 , 20.98057153 , 21.37595676 , 21.83291885 , 22.32770735 , 22.85839751 , 23.41888039 , 24.00040961 , 24.59294371 , 25.17696207 , 25.74220658 , 26.28103562 , 26.83433454 , 27.40399553 , 27.99112535 , 28.59632404 , 29.21983899 , 29.86167288 , 30.52165186 , 31.19946616 , 31.89471441 , 32.60692817 , 33.33558892 , 34.07833109 , 31.12912320 , 35.57800668 , 36.30523016 , 37.01501914 , 37.70298775 , 38.36667780 , 39.00526490 , 39.61925135 , 40.21014673 , 40.78019306 , 41.33212635 , 41.89877223 , 42.47376431 , 43.06157710 , 43.66387568 , 44.27998131 , 44.90734847 , 45.53672861 , 46.15879489 , 46.71555301 , 47.25715154 , 47.78762843 , 48.31071030 , 48.82981986 , 49.34805256 , 49.86815922 , 50.39255573 , 50.92333677 , 51.46229768 , 52.01095435 , 52.57057118 ] ,
    [ 4.30000000 , 0.03163305 , 0.30598837 , 0.77421690 , 1.13979852 , 1.35539425 , 1.49509694 , 1.64950033 , 1.87937271 , 2.21330725 , 2.65816823 , 3.21515827 , 3.82828429 , 4.44772000 , 5.03036894 , 5.54522408 , 5.97791609 , 6.33117174 , 6.62044771 , 6.86897120 , 7.12054497 , 7.38877176 , 7.68475075 , 8.01711588 , 8.39122014 , 8.80988586 , 9.27406846 , 9.78339644 , 10.33659190 , 10.93178572 , 11.56675376 , 12.27416806 , 13.00247393 , 13.73152304 , 14.44249356 , 15.12021603 , 15.75438914 , 16.33180394 , 16.86286347 , 17.37785530 , 17.86202781 , 18.31631651 , 18.74391023 , 19.14952787 , 19.53882832 , 19.91788676 , 20.29277430 , 20.66925374 , 21.05258181 , 21.49094673 , 21.96569067 , 22.47646151 , 23.01864157 , 23.58470322 , 24.16543065 , 24.74274725 , 25.30527658 , 25.83451727 , 26.37741799 , 26.93596109 , 27.51134915 , 28.10427835 , 28.71508855 , 29.34386906 , 29.99052640 , 30.65482252 , 31.33642110 , 32.03491195 , 32.74982846 , 33.47890920 , 30.70470211 , 34.95838519 , 35.68133959 , 36.38891303 , 37.07637959 , 37.74082726 , 38.38092841 , 38.99668207 , 39.58913432 , 40.16011957 , 40.71203485 , 41.27215279 , 41.83811900 , 42.41508978 , 43.00561496 , 43.60996975 , 44.22652105 , 44.84805076 , 45.46556420 , 46.02036351 , 46.55990692 , 47.08775410 , 47.60731774 , 48.12182033 , 48.63424235 , 49.14728485 , 49.66336102 , 50.18459723 , 50.71284513 , 51.24969380 , 51.79649170 ] ,
    [ 4.40000000 , 0.02932070 , 0.29081399 , 0.74822369 , 1.11543166 , 1.33684327 , 1.47784066 , 1.62554959 , 1.84148913 , 2.15653831 , 2.57985629 , 3.11508715 , 3.71207087 , 4.32308772 , 4.90509999 , 5.42570853 , 5.86786667 , 6.23110697 , 6.52804971 , 6.77829362 , 7.02395854 , 7.28249379 , 7.56530746 , 7.88179593 , 8.23801509 , 8.63740312 , 9.08143517 , 9.57016573 , 10.10265758 , 10.67730887 , 11.29209891 , 11.98132241 , 12.69565467 , 13.41591736 , 14.12351638 , 14.80279123 , 15.44240638 , 16.02747423 , 16.56528289 , 17.08564084 , 17.57457529 , 18.03271870 , 18.46284743 , 18.86927501 , 19.25732704 , 19.63284831 , 20.00178863 , 20.36989022 , 20.74247428 , 21.16346556 , 21.61900034 , 22.11018618 , 22.63385503 , 23.18373140 , 23.75152165 , 24.32072366 , 24.87924815 , 25.39881859 , 25.93134575 , 26.47887138 , 27.04267106 , 27.62351978 , 28.22183695 , 28.83778828 , 29.47135230 , 30.12235691 , 30.79052611 , 31.47550435 , 32.17687419 , 32.89247547 , 30.30086154 , 34.35178693 , 35.07023149 , 35.77531548 , 36.46204014 , 37.12709685 , 37.76869778 , 38.38636620 , 38.98069766 , 39.55311994 , 40.10568171 , 40.66034354 , 41.21832107 , 41.78529922 , 42.36459025 , 42.95734464 , 43.56281091 , 44.17570188 , 44.78759760 , 45.34009247 , 45.87741460 , 46.40264078 , 46.91885436 , 47.42905679 , 47.93609030 , 48.44258306 , 48.95092344 , 49.46324921 , 49.98144993 , 50.50717212 , 51.04183483 ] ,
    [ 4.50000000 , 0.02720799 , 0.27648510 , 0.72300527 , 1.09122295 , 1.31822108 , 1.46104492 , 1.60310101 , 1.80628236 , 2.10350291 , 2.50610326 , 3.01991915 , 3.60032939 , 4.20195687 , 4.78211176 , 5.30733235 , 5.75821310 , 6.13129413 , 6.43639944 , 6.68964020 , 6.93109923 , 7.18132048 , 7.45223379 , 7.75396211 , 8.09324808 , 8.47414391 , 8.89865179 , 9.36726455 , 9.87940047 , 10.43374041 , 11.02848242 , 11.69901199 , 12.39846109 , 13.10870076 , 13.81151805 , 14.49095062 , 15.13480966 , 15.72686283 , 16.27143943 , 16.79732932 , 17.29137914 , 17.75391077 , 18.18728359 , 18.59539478 , 18.98321674 , 19.35633637 , 19.72055023 , 20.08154638 , 20.44467758 , 20.84957941 , 21.28685778 , 21.75895779 , 22.26410180 , 22.79727612 , 23.35118094 , 23.91097308 , 24.46421690 , 24.97400290 , 25.49614240 , 26.03270954 , 26.58503257 , 27.15394958 , 27.73994760 , 28.34325903 , 28.96392645 , 29.60183812 , 30.25677364 , 30.92842839 , 31.61643121 , 32.31872035 , 29.88129855 , 33.75786575 , 34.47154045 , 35.17383735 , 35.85954629 , 36.52501639 , 37.16804261 , 37.78770190 , 38.38415504 , 38.95842780 , 39.51221489 , 40.06244987 , 40.61348248 , 41.17137908 , 41.74009062 , 42.32155487 , 42.91585535 , 43.51951311 , 44.12486431 , 44.67472053 , 45.20963854 , 45.73221654 , 46.24519979 , 46.75135349 , 47.25336279 , 47.75376303 , 48.25489799 , 48.75889818 , 49.26767387 , 49.78291390 , 50.30609470 ] ,
    [ 4.60000000 , 0.02527544 , 0.26295090 , 0.69855574 , 1.06720428 , 1.29952473 , 1.44461722 , 1.58197577 , 1.77351980 , 2.05395002 , 2.43666723 , 2.92947537 , 3.49299420 , 4.08437106 , 4.66152312 , 5.19022828 , 5.64902918 , 6.03168680 , 6.34529609 , 6.60263552 , 6.84146470 , 7.08470185 , 7.34496547 , 7.63306054 , 7.95639280 , 8.31962084 , 8.72527660 , 9.17430034 , 9.66647826 , 10.20078773 , 10.77565975 , 11.42710539 , 12.11088265 , 12.80997220 , 13.50667339 , 14.18489455 , 14.83176751 , 15.43001858 , 15.98121046 , 16.51267282 , 17.01207864 , 17.47942786 , 17.91665716 , 18.32723678 , 18.71576727 , 19.08755182 , 19.44820314 , 19.80332268 , 20.15826250 , 20.54840094 , 20.96847206 , 21.42212986 , 21.90891402 , 22.42506169 , 22.96431573 , 23.51353780 , 24.06026835 , 24.56013548 , 25.07184479 , 25.59747955 , 26.13840305 , 26.69550257 , 27.26932181 , 27.86015102 , 28.46808936 , 29.09308004 , 29.73495379 , 30.39345322 , 31.06825047 , 31.75737931 , 29.48556998 , 33.17631852 , 33.88494336 , 34.58413200 , 35.26851867 , 35.93416169 , 36.57848113 , 37.20013860 , 37.79887824 , 38.37533157 , 38.93083731 , 39.47762034 , 40.02274006 , 40.57250520 , 41.13138313 , 41.70200471 , 42.28522924 , 42.87924784 , 43.47727788 , 44.02418531 , 44.55651308 , 45.07639258 , 45.58622847 , 46.08853963 , 46.58583967 , 47.08055420 , 47.57496514 , 48.07117886 , 48.57111045 , 49.07647674 , 49.58879874 ] ,
    [ 4.70000000 , 0.02350563 , 0.25016362 , 0.67486699 , 1.04340529 , 1.28075696 , 1.42847916 , 1.56201235 , 1.74298461 , 2.00764028 , 2.37131304 , 2.84357421 , 3.38998695 , 3.97035688 , 4.54343872 , 5.07452557 , 5.54040151 , 5.93226864 , 6.25458286 , 6.51695500 , 6.75459819 , 6.99212450 , 7.24296491 , 7.51855420 , 7.82693100 , 8.17334702 , 8.56086220 , 8.99086986 , 9.46353406 , 9.97814064 , 10.53336660 , 11.16544443 , 11.83287819 , 12.51980098 , 13.20913504 , 13.88481490 , 14.53345828 , 15.13702310 , 15.69452449 , 16.23148181 , 16.73637480 , 17.20886773 , 17.65046828 , 18.06420992 , 18.45430425 , 18.82574661 , 19.18393693 , 19.53435875 , 19.88233198 , 20.25905802 , 20.66304756 , 21.09903116 , 21.56778201 , 22.06675964 , 22.59077763 , 23.12841639 , 23.66746939 , 24.15727427 , 24.65849231 , 25.17319643 , 25.70277006 , 26.24813768 , 26.80988985 , 27.38836668 , 27.98371713 , 28.59593436 , 29.22489588 , 29.87038797 , 30.53212324 , 31.20822806 , 29.09061164 , 32.60688211 , 33.31015741 , 34.00589408 , 34.68862106 , 35.35415428 , 35.99958038 , 36.62317758 , 37.22429359 , 37.80317615 , 38.36080925 , 38.90505116 , 39.44526235 , 39.98786453 , 40.53772301 , 41.09806410 , 41.67045404 , 42.25460558 , 42.84469469 , 43.38837758 , 43.91793707 , 44.43505595 , 44.94180136 , 45.44044055 , 45.93330514 , 46.42269729 , 46.91082212 , 47.39974686 , 47.89137701 , 48.38744391 , 48.88950097 ] ,
    [ 4.80000000 , 0.02188299 , 0.23807842 , 0.65192896 , 1.01985324 , 1.26192505 , 1.41256490 , 1.54306536 , 1.71447518 , 1.96434607 , 2.30981275 , 2.76203289 , 3.29121844 , 3.85992530 , 4.42794895 , 4.96034789 , 5.43242557 , 5.83304836 , 6.16414179 , 6.43232115 , 6.67008732 , 6.90311217 , 7.14572303 , 7.40992578 , 7.70435587 , 8.03483964 , 8.40495904 , 8.81656261 , 9.27019963 , 9.76547443 , 10.30132167 , 10.91384699 , 11.56437801 , 12.23822740 , 12.91903194 , 13.59089125 , 14.24006410 , 14.84798367 , 15.41135421 , 15.95361935 , 16.46402594 , 16.94188775 , 17.38827709 , 17.80578195 , 18.19820965 , 18.57022543 , 18.92698920 , 19.27383671 , 19.61602517 , 19.98069936 , 20.36979082 , 20.78897320 , 21.24016139 , 21.72199417 , 22.23036529 , 22.75556237 , 23.28586155 , 23.76546221 , 24.25611859 , 24.75987764 , 25.27813072 , 25.81182940 , 26.36160259 , 26.92783318 , 27.51071401 , 28.11028344 , 28.72646180 , 29.35907578 , 30.00787563 , 30.67107756 , 28.68503742 , 32.04932999 , 32.74693744 , 33.43885744 , 34.11955880 , 34.78466029 , 35.43095551 , 36.05637171 , 36.65988211 , 37.24136359 , 37.80144961 , 38.34398956 , 38.88025507 , 39.41666279 , 39.95836294 , 40.50907855 , 41.07100701 , 41.64522940 , 42.22691484 , 42.76713949 , 43.29377015 , 43.80806428 , 44.31175956 , 44.80687060 , 45.29554030 , 45.77993656 , 46.26217519 , 46.74427122 , 47.22810760 , 47.71541770 , 48.20777578 ] ,
    [ 4.90000000 , 0.02039360 , 0.22665321 , 0.62972995 , 0.99657291 , 1.24303976 , 1.39681972 , 1.52500432 , 1.68780455 , 1.92385154 , 2.25194621 , 2.68466865 , 3.19659040 , 3.75307318 , 4.31513029 , 4.84781181 , 5.32520228 , 5.73405509 , 6.07388891 , 6.34849957 , 6.58756244 , 6.81722563 , 7.05276045 , 7.30667978 , 7.58817469 , 7.90362303 , 8.25711857 , 8.65096398 , 9.08609838 , 9.56245265 , 10.07922924 , 10.67210970 , 11.30528611 , 11.96526378 , 12.63646856 , 13.30328787 , 13.95176577 , 14.56302634 , 15.13170988 , 15.67899535 , 16.19484301 , 16.67820131 , 17.12970137 , 17.55147829 , 17.94692167 , 18.32034650 , 18.67664733 , 19.02098367 , 19.35852064 , 19.71249923 , 20.08791663 , 20.49125714 , 20.92547993 , 21.39034790 , 21.88282795 , 22.39488247 , 22.91545585 , 23.38472092 , 23.86474454 , 24.35753569 , 24.86448408 , 25.38656019 , 25.92442399 , 26.47849514 , 27.04900526 , 27.63603362 , 28.23953979 , 28.85938783 , 29.49536315 , 30.14576905 , 28.31521441 , 31.50346846 , 32.19507280 , 32.88279258 , 33.56107662 , 34.22538871 , 34.87226826 , 35.49932429 , 36.10517885 , 36.68935292 , 37.25213638 , 37.79373591 , 38.32696547 , 38.85813095 , 39.39256128 , 39.93437836 , 40.48633030 , 41.05071099 , 41.62368417 , 42.16026444 , 42.68383062 , 43.19524214 , 43.69591951 , 44.18762751 , 44.67231686 , 45.15201326 , 45.62873310 , 46.10442791 , 46.58094664 , 47.06001333 , 47.54321228 ] ,
    [ 5.00000000 , 0.01902497 , 0.21584851 , 0.60825687 , 0.97358660 , 1.22411444 , 1.38119867 , 1.50771260 , 1.66279978 , 1.88595247 , 2.19750133 , 2.61129988 , 3.10599705 , 3.64978458 , 4.20504572 , 4.73702571 , 5.21883521 , 5.63533432 , 5.98376970 , 6.26529531 , 6.50669469 , 6.73406216 , 6.96362817 , 7.20834410 , 7.47791119 , 7.77923132 , 8.11689617 , 8.49365812 , 8.91084820 , 9.36872981 , 9.86678175 , 10.44001058 , 11.05548238 , 11.70089578 , 12.36152464 , 13.02215152 , 13.66873852 , 14.28229018 , 14.85563307 , 15.40756093 , 15.92868473 , 16.41757400 , 16.87441370 , 17.30088018 , 17.69993391 , 18.07552171 , 18.43224940 , 18.77507352 , 19.10903889 , 19.45366152 , 19.81665336 , 20.20518006 , 20.62314412 , 21.07136774 , 21.54786958 , 22.04623725 , 22.55622917 , 23.01504604 , 23.48437279 , 23.96617201 , 24.46182468 , 24.97231379 , 25.49832441 , 26.04030801 , 26.59853077 , 27.17310903 , 27.76403846 , 28.37121782 , 28.99446543 , 29.63216911 , 27.92633522 , 30.96913284 , 31.65438404 , 32.33750367 , 33.01295601 , 33.67608890 , 34.32322491 , 34.95168731 , 35.55977151 , 36.14665929 , 36.71230631 , 37.25364493 , 37.78468558 , 38.31153059 , 38.83958933 , 39.37328705 , 39.91583976 , 40.47059799 , 41.03469815 , 41.56749878 , 42.08789525 , 42.59637923 , 43.09406996 , 43.58248837 , 44.06339252 , 44.53866061 , 45.01020168 , 45.47989434 , 45.94954357 , 46.42085375 , 46.89540926 ] ,
    [ 5.10000000 , 0.01776593 , 0.20562734 , 0.58749549 , 0.95091416 , 1.20516428 , 1.36566534 , 1.49108632 , 1.63930128 , 1.85045614 , 2.14627435 , 2.54174703 , 3.01932659 , 3.55003220 , 4.09774540 , 4.62808906 , 5.11342828 , 5.53694433 , 5.89375494 , 6.18254925 , 6.42719388 , 6.65325468 , 6.87790780 , 7.11447124 , 7.37310728 , 7.66121068 , 7.98385356 , 8.34423055 , 8.74406407 , 9.18395391 , 9.66366218 , 10.21731167 , 10.81482499 , 11.44508388 , 12.09425540 , 12.74760989 , 13.39114862 , 14.00592239 , 14.58319082 , 15.13930295 , 15.66545280 , 16.15981950 , 16.62213819 , 17.05362230 , 17.45679392 , 17.83521604 , 18.19318457 , 18.53542806 , 18.86684424 , 19.20342291 , 19.55524754 , 19.93004063 , 20.33254536 , 20.76457072 , 21.22515346 , 21.70944446 , 22.20812212 , 22.65640377 , 23.11498336 , 23.58577200 , 24.07013712 , 24.56906952 , 25.08327481 , 25.61323224 , 26.15923924 , 26.72144590 , 27.29988131 , 27.89447666 , 28.50508125 , 29.13016499 , 27.54078805 , 30.44618348 , 31.12471934 , 31.80282528 , 32.47501220 , 33.13654788 , 33.78357369 , 34.41315917 , 35.02329846 , 35.61285240 , 36.18145382 , 36.72312612 , 37.25275449 , 37.77615837 , 38.29873760 , 38.82512910 , 39.35893323 , 39.90440483 , 40.45960699 , 40.98854481 , 41.50570048 , 42.01123009 , 42.50597032 , 42.99120700 , 43.46850753 , 43.93959978 , 44.40627960 , 44.87034495 , 45.33354826 , 45.79756509 , 46.26397083 ] ,
    [ 5.20000000 , 0.01660644 , 0.19595501 , 0.56743057 , 0.92857302 , 1.18620571 , 1.35019077 , 1.47503324 , 1.61716215 , 1.81718103 , 2.09806998 , 2.47583341 , 2.93646252 , 3.45377854 , 3.99326730 , 4.52109201 , 5.00908387 , 5.43895305 , 5.80383686 , 6.10013419 , 6.34880620 , 6.57447054 , 6.79521136 , 7.02463891 , 7.27332444 , 7.54912117 , 7.85756103 , 8.20227049 , 8.58536037 , 9.00776876 , 9.46954628 , 10.00376135 , 10.58315255 , 11.19776511 , 11.83469209 , 12.47977066 , 13.11915066 , 13.73407298 , 14.31447022 , 14.87423881 , 15.40508711 , 15.90479536 , 16.37264698 , 16.80939009 , 17.21710130 , 17.59894651 , 17.95889272 , 18.30141746 , 18.63124602 , 18.96105535 , 19.30296777 , 19.66514424 , 20.05306565 , 20.46944966 , 20.91430694 , 21.38427845 , 21.87103770 , 22.30872834 , 22.75653022 , 23.21630088 , 23.68939139 , 24.17679733 , 24.67924151 , 25.19722799 , 25.73108290 , 26.28098734 , 26.84700166 , 27.42908759 , 28.02712381 , 28.63966007 , 27.19251360 , 29.93450197 , 30.60595096 , 31.27861907 , 31.94709095 , 32.60658722 , 33.25310183 , 33.88348190 , 34.49544629 , 35.08755436 , 35.65912935 , 36.20164328 , 36.73055987 , 37.25134940 , 37.76932115 , 38.28923678 , 38.81499838 , 39.35161551 , 39.89802055 , 40.42306420 , 40.93694421 , 41.43951452 , 41.93134995 , 42.41351223 , 42.88738222 , 43.35453687 , 43.81665484 , 44.27544741 , 44.73260718 , 45.18977284 , 45.64850260 ] ,
    [ 5.30000000 , 0.01553748 , 0.18679906 , 0.54804613 , 0.90657834 , 1.16725581 , 1.33475243 , 1.45947183 , 1.59624750 , 1.78595662 , 2.05270149 , 2.41338586 , 2.85728481 , 3.36097716 , 3.89163802 , 4.41611516 , 4.90590132 , 5.34143533 , 5.71402572 , 6.01795176 , 6.27131188 , 6.49741021 , 6.71518084 , 6.93845043 , 7.17814473 , 7.44253825 , 7.73759920 , 8.06737287 , 8.43435310 , 8.83981614 , 9.28410471 , 9.79909674 , 10.36028633 , 10.95885473 , 11.58284286 , 12.21872093 , 12.85288540 , 13.46689133 , 14.04957349 , 14.61241153 , 15.14756110 , 15.65239884 , 16.12575660 , 16.56791671 , 16.98050543 , 17.36628063 , 17.72886377 , 18.07246024 , 18.40159925 , 18.72586805 , 19.05910801 , 19.40980743 , 19.78408293 , 20.18547864 , 20.61492635 , 21.07047455 , 21.54484161 , 21.97192111 , 22.40893940 , 22.85770095 , 23.31953956 , 23.79545395 , 24.28618208 , 24.79225076 , 25.31401301 , 25.85167884 , 26.40533813 , 26.97498172 , 27.56051642 , 28.16056977 , 26.81497664 , 29.43398737 , 30.09797175 , 30.76477039 , 31.42906525 , 32.08605977 , 32.73163240 , 33.36243814 , 33.97594698 , 34.57043718 , 35.14493718 , 35.68871361 , 36.21753867 , 36.73647996 , 37.25068408 , 37.76495624 , 38.28341985 , 38.81169289 , 39.34951504 , 39.87068308 , 40.38128942 , 40.88091976 , 41.36990911 , 41.84910779 , 42.31971609 , 42.78316128 , 43.24100265 , 43.69486019 , 44.14636064 , 44.59709893 , 45.04860874 ] ,
    [ 5.40000000 , 0.01455094 , 0.17812906 , 0.52932557 , 0.88494308 , 1.14833194 , 1.31933331 , 1.44433028 , 1.57643370 , 1.75662295 , 2.00999070 , 2.35423527 , 2.78167095 , 3.27157370 , 3.79287351 , 4.31322957 , 4.80397584 , 5.24447069 , 5.62434666 , 5.93592947 , 6.19452279 , 6.42180569 , 6.63748750 , 6.85553472 , 7.08717145 , 7.34105393 , 7.62356062 , 7.93914014 , 8.29066169 , 8.67973775 , 9.10700496 , 9.60304579 , 10.14603235 , 10.72824802 , 11.33869370 , 11.96452717 , 12.59247829 , 13.20452356 , 13.78861348 , 14.35388503 , 14.89287732 , 15.40256276 , 15.88132426 , 16.32897992 , 16.74670287 , 17.13683451 , 17.50263639 , 17.84802279 , 18.17730485 , 18.49720882 , 18.82299037 , 19.16336191 , 19.52497590 , 19.91211821 , 20.32658192 , 20.76773569 , 21.22936340 , 21.64585047 , 22.07210785 , 22.50988967 , 22.96051317 , 23.42497983 , 23.90404188 , 24.39824767 , 24.90797595 , 25.43346420 , 25.97483062 , 26.53209406 , 27.10518852 , 27.69281761 , 26.44750812 , 28.94455260 , 29.60069165 , 30.26118489 , 30.92083197 , 31.57484636 , 32.21902095 , 32.84984794 , 33.46457478 , 34.06121988 , 34.63853290 , 35.18390623 , 35.71317722 , 36.23096931 , 36.74220321 , 37.25165280 , 37.76358574 , 38.28409162 , 38.81363984 , 39.33099754 , 39.83836834 , 40.33510343 , 40.82132073 , 41.29767308 , 41.76518767 , 42.22514497 , 42.67898417 , 43.12823077 , 43.57444080 , 44.01915951 , 44.46388965 ] ,
    [ 5.50000000 , 0.01363951 , 0.16991653 , 0.51125181 , 0.86367813 , 1.12945141 , 1.30392110 , 1.42954557 , 1.55760776 , 1.72903035 , 1.96976796 , 2.29821700 , 2.70949690 , 3.18550693 , 3.69697980 , 4.21249686 , 4.70339754 , 5.14814133 , 5.53483698 , 5.85401685 , 6.11828001 , 6.34741893 , 6.56183098 , 6.77554615 , 7.00002955 , 7.24427765 , 7.51505098 , 7.81718374 , 8.15391078 , 8.52717695 , 8.93791313 , 9.41532919 , 9.94018334 , 10.50582203 , 11.10220971 , 11.71723534 , 12.33803837 , 12.94710798 , 13.53170951 , 14.09873986 , 14.64106315 , 15.15525148 , 15.63924415 , 16.09239870 , 16.51543463 , 16.91027067 , 17.27979649 , 17.62761840 , 17.95780932 , 18.27446487 , 18.59396725 , 18.92515796 , 19.27512838 , 19.64882019 , 20.04882247 , 20.47573028 , 20.92439742 , 21.33035182 , 21.74590259 , 22.17275807 , 22.61222102 , 23.06529645 , 23.53275099 , 24.01515410 , 24.51290971 , 25.02628195 , 25.55541657 , 26.10035974 , 26.66107204 , 27.23633166 , 26.12094736 , 28.46612102 , 29.11403439 , 29.76778529 , 30.42230859 , 31.07285243 , 31.71515220 , 32.34556531 , 32.96114294 , 33.55966535 , 34.13962050 , 34.68684021 , 35.21701081 , 35.73428092 , 36.24329097 , 36.74871546 , 37.25489344 , 37.76825496 , 38.28992244 , 38.80357793 , 39.30778589 , 39.80169604 , 40.28523199 , 40.75886398 , 41.22345466 , 41.68014189 , 42.13024542 , 42.57519424 , 43.01646988 , 43.45556302 , 43.89393990 ] ,
    [ 5.60000000 , 0.01279663 , 0.16213477 , 0.49380744 , 0.84279252 , 1.11063117 , 1.28850747 , 1.41506268 , 1.53966659 , 1.70303897 , 1.93187201 , 2.24517129 , 2.64063786 , 3.10270961 , 3.60395384 , 4.11396947 , 4.60425085 , 5.05253048 , 5.44554363 , 5.77218322 , 6.04245149 , 6.27404013 , 6.48793824 , 6.69816410 , 6.91636573 , 7.15183693 , 7.41169012 , 7.70112539 , 8.02373159 , 8.38178040 , 8.77649559 , 9.23566229 , 9.74252068 , 10.29143735 , 10.87333632 , 11.47687140 , 12.08965757 , 12.69477371 , 13.27898384 , 13.84706918 , 14.39216679 , 14.91045700 , 15.39944377 , 15.85803001 , 16.28648323 , 16.68629563 , 17.05997536 , 17.41080606 , 17.74260409 , 18.05706335 , 18.37142317 , 18.69456743 , 19.03393331 , 19.39503229 , 19.78118013 , 20.19409841 , 20.62970573 , 21.02522941 , 21.43016159 , 21.84617078 , 22.27454849 , 22.71630504 , 23.17222241 , 23.64289151 , 24.12874138 , 24.63006258 , 25.14702808 , 25.67971104 , 26.22809829 , 26.79104142 , 25.76206375 , 27.99862324 , 28.63793438 , 29.28450819 , 29.93342997 , 30.58000479 , 31.21993661 , 31.84947485 , 32.46550026 , 33.06557700 , 33.64794922 , 34.19718239 , 34.72862269 , 35.24592301 , 35.75339758 , 36.25556069 , 36.75675485 , 37.26362387 , 37.77787573 , 38.28797530 , 38.78912514 , 39.28030543 , 39.76126787 , 40.23231541 , 40.69415566 , 41.14778914 , 41.59441782 , 42.03537334 , 42.47205989 , 42.90590960 , 43.33834738 ] ,
    [ 5.70000000 , 0.01201634 , 0.15475879 , 0.47697484 , 0.82229346 , 1.09188764 , 1.27308744 , 1.40083377 , 1.52251637 , 1.67851839 , 1.89614985 , 2.19494353 , 2.57496898 , 3.02310945 , 3.51378412 , 4.01769086 , 4.50661403 , 4.95772109 , 5.35652111 , 5.69041573 , 5.96692970 , 6.20148596 , 6.41556247 , 6.62309237 , 6.83584844 , 7.06337771 , 7.31311281 , 7.59059819 , 7.89976327 , 8.24319939 , 8.62242046 , 9.06375669 , 9.55281612 , 10.08493975 , 10.65200061 , 11.24344189 , 11.84741039 , 12.44764065 , 13.03055868 , 13.59897512 , 14.14625349 , 14.66819523 , 15.16188038 , 15.62576544 , 16.05966976 , 16.46465739 , 16.84284761 , 17.19718888 , 17.53122458 , 17.84447144 , 18.15477602 , 18.47098622 , 18.80079620 , 19.15020222 , 19.52317471 , 19.92246282 , 20.34502151 , 20.73025866 , 21.12469513 , 21.52996657 , 21.94735739 , 22.37788580 , 22.82235082 , 23.28136575 , 23.75538513 , 24.24472627 , 24.74958944 , 25.27007476 , 25.80619527 , 26.35687506 , 25.40709444 , 27.54199419 , 28.17233363 , 28.81130107 , 29.45414529 , 30.09624836 , 30.73330708 , 31.36148833 , 31.97752767 , 32.57879540 , 33.16331028 , 33.71464497 , 34.24764276 , 34.76544857 , 35.27201264 , 35.77163554 , 36.26860081 , 36.76965456 , 37.27700527 , 37.78372787 , 38.28195301 , 38.77052156 , 39.24903501 , 39.71764443 , 40.17691257 , 40.62770858 , 41.07111930 , 41.50837907 , 41.94081279 , 42.36979090 , 42.79669292 ] ,
    [ 5.80000000 , 0.01129330 , 0.14776516 , 0.46073626 , 0.80218660 , 1.07323658 , 1.25765880 , 1.38681743 , 1.50607188 , 1.65534722 , 1.86245659 , 2.14738432 , 2.51236597 , 2.94662975 , 3.42645147 , 3.92369594 , 4.41055887 , 4.86379461 , 5.26782955 , 5.60871548 , 5.89162926 , 6.12959783 , 6.34448183 , 6.55005853 , 6.75816763 , 6.97856460 , 7.21896928 , 7.48524738 , 7.78165389 , 8.11109110 , 8.47535887 , 8.89932175 , 9.37083346 , 9.88616188 , 10.43811270 , 11.01693475 , 11.61135382 , 12.20581475 , 12.78655301 , 13.35456532 , 13.90340193 , 14.42850245 , 14.92653754 , 15.39552793 , 15.83485085 , 16.24514274 , 16.62812892 , 16.98641235 , 17.32324889 , 17.63619595 , 17.94347801 , 18.25383637 , 18.57513827 , 18.91378161 , 19.27431793 , 19.66042290 , 20.07005049 , 20.44518717 , 20.82928626 , 21.22395824 , 21.63048535 , 22.04989686 , 22.48301114 , 22.93046526 , 23.39274015 , 23.87018062 , 24.36301466 , 24.87136965 , 25.39528502 , 25.93375678 , 25.10214450 , 27.09617031 , 27.71717905 , 28.34811942 , 28.98441510 , 29.62154316 , 30.25521574 , 30.88154134 , 31.49713481 , 32.09919477 , 32.68553350 , 33.23898264 , 33.77374578 , 34.29245482 , 34.79866604 , 35.29642009 , 35.78988499 , 36.28580731 , 36.78681190 , 37.29036393 , 37.78582300 , 38.27191894 , 38.74812372 , 39.21445183 , 39.67133166 , 40.11950754 , 40.55995455 , 40.99381058 , 41.42232015 , 41.84678956 , 42.26854950 ] ,
    [ 5.90000000 , 0.01062265 , 0.14113195 , 0.44507389 , 0.78247609 , 1.05469293 , 1.24222162 , 1.37297803 , 1.49025590 , 1.63341263 , 1.83065522 , 2.10234973 , 2.45270563 , 2.87319018 , 3.34192969 , 3.83201141 , 4.31615054 , 4.77083020 , 5.17953307 , 5.52709558 , 5.81648482 , 6.05824006 , 6.27449818 , 6.47881304 , 6.68303437 , 6.89708089 , 7.12892561 , 7.38473109 , 7.66906140 , 7.98511966 , 8.33498621 , 8.74206597 , 9.19633013 , 9.69492482 , 10.23156713 , 10.79732023 , 11.38152753 , 11.96938745 , 12.54708053 , 13.11395012 , 13.66370102 , 14.19143197 , 14.69342180 , 15.16726864 , 15.61191568 , 16.02757457 , 16.41557374 , 16.77816239 , 17.11829636 , 17.43178292 , 17.73701625 , 18.04256775 , 18.35639913 , 18.68522942 , 19.03411734 , 19.40755825 , 19.80447479 , 20.16973776 , 20.54369312 , 20.92793431 , 21.32374684 , 21.73217477 , 22.15405847 , 22.59006065 , 23.04068984 , 23.50631950 , 23.98720609 , 24.48350478 , 24.99528182 , 25.52160479 , 24.77201462 , 26.66108724 , 27.27241984 , 27.89492414 , 28.52420854 , 29.15586136 , 29.78563087 , 30.40959006 , 31.02425664 , 31.62667961 , 32.21448386 , 32.76998984 , 33.30664936 , 33.82658230 , 34.33292829 , 34.82942919 , 35.32008711 , 35.81154891 , 36.30679755 , 36.80740752 , 37.30028052 , 37.78406144 , 38.25811227 , 38.72232577 , 39.17700665 , 39.62278134 , 40.06051709 , 40.49125687 , 40.91616442 , 41.33648011 , 41.75348300 ] ,
    [ 6.00000000 , 0.01000000 , 0.13483859 , 0.42997004 , 0.76316477 , 1.03627081 , 1.22677784 , 1.35928509 , 1.47499857 , 1.61260992 , 1.80061637 , 2.05970146 , 2.39586626 , 2.80270756 , 3.26018622 , 3.74265616 , 4.22344746 , 4.67890390 , 5.09169841 , 5.44558127 , 5.74144898 , 5.98729822 , 6.20543579 , 6.40912846 , 6.61018041 , 6.81862847 , 7.04266397 , 7.28872079 , 7.56165431 , 7.86495704 , 8.20098308 , 8.59169832 , 9.02905865 , 9.51103963 , 10.03224420 , 10.58455183 , 11.15795415 , 11.73843931 , 12.31224816 , 12.87723995 , 13.42724691 , 13.95705096 , 14.46255957 , 14.94096378 , 15.39078311 , 15.81180920 , 16.20497281 , 16.57216334 , 16.91602587 , 17.23081694 , 17.53491298 , 17.83665933 , 18.14403905 , 18.46401514 , 18.80208000 , 19.16344747 , 19.54795830 , 19.90361290 , 20.26765251 , 20.64166179 , 21.02693528 , 21.42453590 , 21.83532896 , 22.26000503 , 22.69910174 , 23.15302263 , 23.62205362 , 24.10637851 , 24.60609096 , 25.12032999 , 24.42563549 , 26.23667769 , 26.83800519 , 27.45167902 , 28.07350074 , 28.69918453 , 29.32453397 , 29.94560813 , 30.55885018 , 31.16118126 , 31.75005811 , 32.30749799 , 32.84611166 , 33.36751345 , 33.87441040 , 34.37021377 , 34.85871546 , 35.34638088 , 35.83647382 , 36.33438613 , 36.82486989 , 37.30650856 , 37.77857239 , 38.24084666 , 38.69352299 , 39.13711698 , 39.57239241 , 40.00029941 , 40.42192114 , 40.83843084 , 41.25105364 ] ,
    [ 6.10000000 , 0.00942139 , 0.12886580 , 0.41540709 , 0.74425427 , 1.01798345 , 1.21133089 , 1.34571267 , 1.46023686 , 1.59284210 , 1.77221811 , 2.01930670 , 2.34172807 , 2.73509635 , 3.18118279 , 3.65564170 , 4.13250136 , 4.58808810 , 5.00439369 , 5.36420588 , 5.66649013 , 5.91667728 , 6.13713995 , 6.34079844 , 6.53935760 , 6.74292757 , 6.95988270 , 7.19690168 , 7.45911228 , 7.75028380 , 8.07303623 , 8.44792927 , 8.86876795 , 9.33430880 , 9.84001137 , 10.37856735 , 10.94063984 , 11.51303552 , 12.08215378 , 12.64454286 , 13.19414016 , 13.72543751 , 14.23399408 , 14.71661171 , 15.17139873 , 15.59773361 , 15.99615077 , 16.36817573 , 16.71613411 , 17.03291997 , 17.33672544 , 17.63562010 , 17.93754094 , 18.24962150 , 18.57771587 , 18.92766069 , 19.30014756 , 19.64649559 , 20.00088051 , 20.36488653 , 20.73982309 , 21.12677622 , 21.52663932 , 21.94013320 , 22.36782645 , 22.81015425 , 23.26743325 , 23.73987683 , 24.22760695 , 24.72983402 , 24.13458944 , 25.82286947 , 26.41388216 , 27.01834848 , 27.63227042 , 28.25150107 , 28.87191697 , 29.48958366 , 30.10089139 , 30.70265468 , 31.29218139 , 31.85137221 , 32.39192884 , 32.91497093 , 33.42276327 , 33.91836140 , 34.40530900 , 34.88982586 , 35.37536184 , 35.87083148 , 36.35913545 , 36.83881672 , 37.30907062 , 37.76958838 , 38.22045884 , 38.66209391 , 39.09515855 , 39.52051251 , 39.93915915 , 40.35220383 , 40.76081593 ] ,
    [ 6.20000000 , 0.00888320 , 0.12319548 , 0.40136752 , 0.72574517 , 0.99984318 , 1.19588539 , 1.33223891 , 1.44591400 , 1.57401943 , 1.74534560 , 1.98103804 , 2.29017348 , 2.67026915 , 3.10487604 , 3.57097260 , 4.04335730 , 4.49845108 , 4.91768738 , 5.28300780 , 5.59159044 , 5.84629994 , 6.06947564 , 6.27363672 , 6.47033723 , 6.66971646 , 6.88029626 , 7.10897289 , 7.36112658 , 7.64078972 , 7.95083932 , 8.31047171 , 8.71520472 , 9.16452763 , 9.65472460 , 10.17929003 , 10.72957485 , 11.29322243 , 11.85688497 , 12.41596264 , 12.96448335 , 13.49667790 , 14.00778255 , 14.49423008 , 14.95373210 , 15.38526286 , 15.78896367 , 16.16599415 , 16.51835362 , 16.83775011 , 17.14204558 , 17.43898969 , 17.73641184 , 18.04154698 , 18.36054091 , 18.69975071 , 19.06067390 , 19.39805127 , 19.74307426 , 20.09733470 , 20.46216282 , 20.83867214 , 21.22778728 , 21.63026188 , 22.04669755 , 22.47756282 , 22.92320647 , 23.38387265 , 23.85971256 , 24.35000822 , 23.84412002 , 25.41958396 , 25.99999386 , 26.59489556 , 27.20049763 , 27.81280376 , 28.42777963 , 29.04151648 , 29.65037212 , 30.25107524 , 30.84080398 , 31.40150817 , 31.94393243 , 32.46871566 , 32.97767667 , 33.47349651 , 33.95943871 , 34.44140926 , 34.92299324 , 35.41628126 , 35.90262377 , 36.38054163 , 36.84917064 , 37.30812047 , 37.75738711 , 38.19728588 , 38.62838770 , 39.05146479 , 39.46744183 , 39.87735601 , 40.28231954 ] ,
    [ 6.30000000 , 0.00838216 , 0.11781070 , 0.38783417 , 0.70763707 , 0.98186143 , 1.18044687 , 1.31884549 , 1.43197896 , 1.55605903 , 1.71989092 , 1.94477382 , 2.24108741 , 2.60813754 , 3.03121812 , 3.48864693 , 3.95605383 , 4.41005670 , 4.83164748 , 5.20203302 , 5.51674450 , 5.77610505 , 6.00232619 , 6.20747619 , 6.40290937 , 6.59875109 , 6.80363515 , 7.02464760 , 7.26740041 , 7.53617434 , 7.83409355 , 8.17904216 , 8.56811452 , 9.00148559 , 9.47622964 , 9.98662958 , 10.52473424 , 11.07903548 , 11.63651913 , 12.19159744 , 12.73837897 , 13.27086418 , 13.78399360 , 14.27385310 , 14.73777412 , 15.17433745 , 15.58329655 , 15.96544500 , 16.32245085 , 16.64500061 , 16.95049945 , 17.24633860 , 17.54018416 , 17.83930783 , 18.15007985 , 18.47927951 , 18.82916098 , 19.15793443 , 19.49391753 , 19.83871759 , 20.19369130 , 20.55998391 , 20.93855445 , 21.33019204 , 21.73553346 , 22.15508240 , 22.58922129 , 23.03822635 , 23.50227917 , 23.98073359 , 23.51355292 , 25.02673507 , 25.59627792 , 26.18128013 , 26.77816180 , 27.38308759 , 27.99212716 , 28.60141545 , 29.20729733 , 29.80643574 , 30.39589811 , 30.95782957 , 31.50198654 , 32.02854455 , 32.53887783 , 33.03528007 , 33.52070853 , 34.00069753 , 34.47892112 , 34.97028895 , 35.45489250 , 35.93124638 , 36.39844060 , 36.85601487 , 37.30388161 , 37.74226649 , 38.17165128 , 38.59272367 , 39.00633117 , 39.41344282 , 39.81511266 ] ,
    [ 6.40000000 , 0.00791530 , 0.11269552 , 0.37479014 , 0.68992875 , 0.96404875 , 1.16502154 , 1.30551726 , 1.41838600 , 1.53888441 , 1.69575269 , 1.91039791 , 2.19435749 , 2.54861243 , 2.96015724 , 3.40865671 , 3.87062313 , 4.32296410 , 4.74634073 , 5.12133337 , 5.44195745 , 5.70604601 , 5.93559193 , 6.14216773 , 6.33688209 , 6.52980457 , 6.72964568 , 6.94365312 , 7.17764913 , 7.43614729 , 7.72250821 , 8.05336144 , 8.42724295 , 8.84496757 , 9.30436331 , 9.80048334 , 10.32607870 , 10.87049912 , 11.42112244 , 11.97153828 , 12.51592751 , 13.04809182 , 13.56270472 , 14.05552902 , 14.52353440 , 14.96492083 , 15.37906100 , 15.76638424 , 16.12822418 , 16.45439838 , 16.76174639 , 17.05726824 , 17.34841656 , 17.64243986 , 17.94586871 , 18.26582351 , 18.60522695 , 18.92579055 , 19.25308260 , 19.58873321 , 19.93413088 , 20.29045664 , 20.65870704 , 21.03970926 , 21.43413758 , 21.84253256 , 22.26531192 , 22.70278537 , 23.15516612 , 23.62188010 , 23.22003215 , 24.64422811 , 25.20266520 , 25.77745727 , 26.36523989 , 26.96234774 , 27.56496796 , 28.16929605 , 28.77168235 , 29.36874353 , 29.95745497 , 30.52028494 , 31.06598508 , 31.59428813 , 32.10612980 , 32.60340887 , 33.08875578 , 33.56730518 , 34.04272168 , 34.53242572 , 35.01551252 , 35.49050360 , 35.95645538 , 36.41284800 , 36.85951897 , 37.29661097 , 37.72452149 , 38.14385682 , 38.55538902 , 38.96001933 , 39.35874290 ] ,
    [ 6.50000000 , 0.00747991 , 0.10783501 , 0.36221869 , 0.67261822 , 0.94641486 , 1.14961615 , 1.29224181 , 1.40509416 , 1.52242513 , 1.67283586 , 1.87779915 , 2.14987425 , 2.49160422 , 2.89163823 , 3.33098835 , 3.78709123 , 4.23722759 , 4.66183202 , 5.04096005 , 5.36724298 , 5.63608906 , 5.86918875 , 6.07757922 , 6.27208065 , 6.46266665 , 6.65808966 , 6.86573073 , 7.09160038 , 7.34042868 , 7.61580113 , 7.93315517 , 8.29233655 , 8.69475505 , 9.13895476 , 9.62073739 , 10.13355532 , 10.66761670 , 11.21074816 , 11.75586767 , 12.29722566 , 12.82845769 , 13.34399997 , 13.83931768 , 14.31103881 , 14.75699695 , 15.17619287 , 15.56869522 , 15.93550187 , 16.26570186 , 16.57547797 , 16.87141060 , 17.16069448 , 17.45049986 , 17.74745696 , 18.05894447 , 18.38848180 , 18.70125420 , 19.02022874 , 19.34706509 , 19.68318843 , 20.02981939 , 20.38799497 , 20.75858297 , 21.14229739 , 21.53971746 , 21.95129780 , 22.37738311 , 22.81821953 , 23.27330537 , 22.96728162 , 24.27195878 , 24.81907854 , 25.38337589 , 25.96170473 , 26.55057769 , 27.14631154 , 27.74517804 , 28.34355045 , 28.93801781 , 29.52548179 , 30.08884410 , 30.63584873 , 31.16580806 , 31.67922956 , 32.17761446 , 32.66325114 , 33.14084585 , 33.61398609 , 34.10227467 , 34.58406364 , 35.05789226 , 35.52279398 , 35.97819871 , 36.42387692 , 36.85989473 , 37.28657007 , 37.70443106 , 38.11417613 , 38.51663932 , 38.91275649 ] ,
    [ 6.60000000 , 0.00707353 , 0.10321513 , 0.35010343 , 0.65570283 , 0.92896864 , 1.13423777 , 1.27900915 , 1.39206690 , 1.50661636 , 1.65105135 , 1.84687171 , 2.10753128 , 2.43702351 , 2.82560308 , 3.25562315 , 3.70547823 , 4.15289651 , 4.57818393 , 4.96096581 , 5.29262247 , 5.56621203 , 5.80304695 , 6.01359443 , 6.20834676 , 6.39714320 , 6.58874412 , 6.79063565 , 7.00899415 , 7.24874923 , 7.51369903 , 7.81815465 , 8.16314384 , 8.55062726 , 8.97982666 , 9.44726770 , 9.94709855 , 10.47037641 , 11.00543767 , 11.54465919 , 12.08236518 , 12.61205830 , 13.12796795 , 13.62528829 , 14.10032718 , 14.55056793 , 14.97464994 , 15.37228647 , 15.74414004 , 16.07869978 , 16.39141687 , 16.68842779 , 16.97663049 , 17.26306670 , 17.55440940 , 17.85820458 , 18.17853402 , 18.48395509 , 18.79500771 , 19.11338717 , 19.44055974 , 19.77778905 , 20.12615533 , 20.48656936 , 20.85978705 , 21.24642801 , 21.64698542 , 22.06184045 , 22.49127357 , 22.93485572 , 22.67637792 , 23.90981305 , 24.44543216 , 24.99897769 , 25.56752377 , 26.14776764 , 26.73616668 , 27.32908343 , 27.92293046 , 28.51428706 , 29.09999916 , 29.66349575 , 30.21152227 , 30.74299453 , 31.25800590 , 31.75766182 , 32.24389821 , 32.72095064 , 33.19232857 , 33.67943837 , 34.16014166 , 34.63300436 , 35.09704589 , 35.55165419 , 35.99653991 , 36.43169859 , 36.85737319 , 37.27401683 , 37.68225630 , 38.08285919 , 38.47670191 ] ,
    [ 6.70000000 , 0.00669391 , 0.09882272 , 0.33842858 , 0.63917932 , 0.91171819 , 1.11889371 , 1.26581141 , 1.37927165 , 1.49139855 , 1.63031584 , 1.81751539 , 2.06722538 , 2.38478177 , 2.76199142 , 3.18253768 , 3.62579855 , 4.07001520 , 4.49545627 , 4.88140976 , 5.21812414 , 5.49640321 , 5.73711002 , 5.95011205 , 6.14553770 , 6.33305557 , 6.52140090 , 6.71813678 , 6.92958278 , 7.16085048 , 7.41593780 , 7.70809772 , 8.03941609 , 8.41236217 , 8.82679631 , 9.27994118 , 9.76663104 , 10.27876332 , 10.80522175 , 11.33797728 , 11.87143187 , 12.39898832 , 12.91469997 , 13.41351736 , 13.89145114 , 14.34565186 , 14.77440973 , 15.17708961 , 15.55402068 , 15.89321006 , 16.20931569 , 16.50801133 , 16.79586425 , 17.07974215 , 17.36630778 , 17.66320359 , 17.97499919 , 18.27352551 , 18.57707028 , 18.88736962 , 19.20593459 , 19.53407481 , 19.87291623 , 20.22341477 , 20.58637031 , 20.96244442 , 21.35217047 , 21.75596755 , 22.17415190 , 22.60636731 , 22.37424587 , 23.55766711 , 24.08163112 , 24.62419632 , 25.18265785 , 25.75390313 , 26.33453980 , 26.92103454 , 27.50985468 , 28.09758675 , 28.68103839 , 29.24424543 , 29.79297184 , 30.32576368 , 30.84231726 , 31.34334775 , 31.83043274 , 32.30732341 , 32.77739880 , 33.26354950 , 33.74336800 , 34.21545359 , 34.67881901 , 35.13281735 , 35.57710584 , 36.01161500 , 36.43651714 , 36.85219352 , 37.25920127 , 37.65824246 , 38.05013405 ] ,
    [ 6.80000000 , 0.00633900 , 0.09464537 , 0.32717856 , 0.62304393 , 0.89467086 , 1.10359140 , 1.25264254 , 1.36667948 , 1.47671701 , 1.61055140 , 1.78963469 , 2.02885662 , 2.33479112 , 2.70074098 , 3.11170432 , 3.54806121 , 3.98862303 , 4.41370575 , 4.80235018 , 5.14378106 , 5.42665963 , 5.67133323 , 5.88704447 , 6.08352546 , 6.27023999 , 6.45586622 , 6.64801649 , 6.85313083 , 7.07648481 , 7.32226270 , 7.60272876 , 7.92090805 , 8.27973749 , 8.67967680 , 9.11861681 , 9.59206462 , 10.09274846 , 10.61011854 , 11.13587607 , 11.66450435 , 12.18933903 , 12.70428819 , 13.20408672 , 13.68447194 , 14.14228060 , 14.57546737 , 14.98305722 , 15.36504968 , 15.70907721 , 16.02895540 , 16.32988128 , 16.61806235 , 16.90015144 , 17.18275206 , 17.47355117 , 17.77749467 , 18.06959619 , 18.36606288 , 18.66867597 , 18.97899433 , 19.29837604 , 19.62799494 , 19.96885402 , 20.32179887 , 20.68753463 , 21.06663631 , 21.45956242 , 21.86666627 , 22.28766472 , 22.12983462 , 23.21538666 , 23.72757069 , 24.25895652 , 24.80706020 , 25.36896368 , 25.94143340 , 26.52105228 , 27.10435688 , 27.68795709 , 28.26863916 , 28.83111189 , 29.38018207 , 29.91405498 , 30.43204937 , 30.93449908 , 31.42262160 , 31.89969726 , 32.36887000 , 32.85426148 , 33.33338204 , 33.80486905 , 34.26773433 , 34.72130221 , 35.16518206 , 35.59924448 , 36.02359520 , 36.43854663 , 36.84458816 , 37.24235741 , 37.63261205 ] ,
    [ 6.90000000 , 0.00600693 , 0.09067144 , 0.31633796 , 0.60729241 , 0.87783326 , 1.08833829 , 1.23949807 , 1.35426475 , 1.46252162 , 1.59168528 , 1.76313835 , 1.99232838 , 2.28696441 , 2.64178799 , 3.04309159 , 3.47227012 , 3.90875441 , 4.33298577 , 4.72383853 , 5.06962972 , 5.35698588 , 5.60568248 , 5.82431683 , 6.02219586 , 6.20854682 , 6.39196016 , 6.58007034 , 6.77941501 , 6.99541550 , 7.23242850 , 7.50179892 , 7.80737865 , 8.15253157 , 8.53827795 , 8.96314668 , 9.42330124 , 9.91227881 , 10.42013252 , 10.93839887 , 11.46165327 , 11.98319718 , 12.49682415 , 12.99708173 , 13.47945862 , 13.94049784 , 14.37783357 , 14.79016087 , 15.17715485 , 15.52617009 , 15.85014386 , 16.15378527 , 16.44291792 , 16.72394356 , 17.00336145 , 17.28883492 , 17.58563640 , 17.87179404 , 18.16162601 , 18.45696200 , 18.75941108 , 19.07038172 , 19.39109747 , 19.72260998 , 20.06581215 , 20.42145406 , 20.79015378 , 21.17241057 , 21.56861616 , 21.97856061 , 21.89575828 , 22.88282682 , 23.38313607 , 23.90317365 , 24.44067562 , 24.99292181 , 25.55684477 , 26.12915456 , 26.70647049 , 27.28544101 , 27.86284728 , 28.42412400 , 28.97315345 , 29.50782870 , 30.02711298 , 30.53097079 , 31.02026147 , 31.49778099 , 31.96642909 , 32.45124126 , 32.92983560 , 33.40089092 , 33.86342258 , 34.31673116 , 34.76038320 , 35.19419391 , 35.61820622 , 36.03266655 , 36.43799848 , 36.83477629 , 37.22369866 ] ,
    [ 7.00000000 , 0.00569598 , 0.08688999 , 0.30589200 , 0.59192011 , 0.86121134 , 1.07314181 , 1.22637492 , 1.34200480 , 1.44876648 , 1.57364959 , 1.73794031 , 1.95754750 , 2.24121618 , 2.58506762 , 2.97666467 , 3.39842442 , 3.83043889 , 4.25334618 , 4.64592870 , 4.99571054 , 5.28739358 , 5.54013343 , 5.76186606 , 5.96144781 , 6.14784001 , 6.32951630 , 6.51410672 , 6.70822398 , 6.91741669 , 7.14619960 , 7.40506711 , 7.69859156 , 8.03052416 , 8.40240736 , 8.81337701 , 9.26023388 , 9.73729565 , 10.23525826 , 10.74557920 , 11.26294129 , 11.78064429 , 12.29239762 , 12.79258983 , 13.27648621 , 13.74035719 , 14.18153267 , 14.59838919 , 14.99028410 , 15.34438136 , 15.67271450 , 15.97949736 , 16.27015004 , 16.55079134 , 16.82777517 , 17.10866799 , 17.39905235 , 17.67975398 , 17.96340476 , 18.25188522 , 18.54685622 , 18.84977807 , 19.16192540 , 19.48439982 , 19.81814277 , 20.16395057 , 20.52248558 , 20.89428906 , 21.27979238 , 21.67885886 , 21.61655158 , 22.55983320 , 23.04820276 , 23.55675360 , 24.08344010 , 24.62574228 , 25.18076493 , 25.74535503 , 26.31622706 , 26.89008236 , 27.46371262 , 28.02331985 , 28.57190011 , 29.10706348 , 29.62744152 , 30.13264396 , 30.62317731 , 31.10132680 , 31.56979625 , 32.05418602 , 32.53240788 , 33.00318402 , 33.46553657 , 33.91874652 , 34.36234185 , 34.79608642 , 35.21996383 , 35.63415721 , 36.03902619 , 36.43508284 , 36.82296727 ] ,
    [ 7.10000000 , 0.00540459 , 0.08329069 , 0.29582664 , 0.57692203 , 0.84481040 , 1.05800928 , 1.21327120 , 1.32987966 , 1.43540963 , 1.55638105 , 1.71395975 , 1.92442429 , 2.19746301 , 2.53051435 , 2.91238577 , 3.32651874 , 3.75370130 , 4.17483315 , 4.56868090 , 4.92206714 , 5.21790034 , 5.47467047 , 5.69963993 , 5.90119239 , 6.08799636 , 6.26838108 , 6.44994654 , 6.63935817 , 6.84227327 , 7.06334999 , 7.31230044 , 7.59431578 , 7.91349717 , 8.27187127 , 8.66914911 , 9.10274752 , 9.56774468 , 10.05548149 , 10.55744092 , 11.06842265 , 11.58175582 , 12.09109540 , 12.59069902 , 13.07563415 , 13.54192041 , 13.98660082 , 14.40774599 , 14.80440357 , 15.16362604 , 15.49652480 , 15.80681691 , 16.09950305 , 16.38039129 , 16.65565299 , 16.93271990 , 17.21738849 , 17.49312429 , 17.77105362 , 18.05310909 , 18.34100424 , 18.63625198 , 18.94017897 , 19.25393768 , 19.57851902 , 19.91476660 , 20.26338816 , 20.62496804 , 20.99997838 , 21.38835573 , 21.34942937 , 22.24624224 , 22.72263664 , 23.21959261 , 23.73528033 , 24.26738133 , 24.81317772 , 25.36966181 , 25.93365479 , 26.50192424 , 27.07128720 , 27.62874504 , 28.17644753 , 28.71175392 , 29.23298879 , 29.73942377 , 30.23122077 , 30.71017646 , 31.17873324 , 31.66283019 , 32.14081164 , 32.61144346 , 33.07375651 , 33.52701537 , 33.97071307 , 34.40456564 , 34.82850043 , 35.24263979 , 35.64728118 , 36.04287557 , 36.43000496 ] ,
    [ 7.20000000 , 0.00513132 , 0.07986386 , 0.28612786 , 0.56229283 , 0.82863510 , 1.04294791 , 1.20018604 , 1.31787179 , 1.42241272 , 1.53982071 , 1.69111942 , 1.89287242 , 2.15562275 , 2.47806221 , 2.85021451 , 3.25654355 , 3.67856184 , 4.09748906 , 4.49214814 , 4.84874380 , 5.14852818 , 5.40928539 , 5.63759592 , 5.84135194 , 6.02890476 , 6.20841328 , 6.38742279 , 6.57262946 , 6.76978076 , 6.98366334 , 7.22327352 , 7.49432591 , 7.80123531 , 8.14647543 , 8.53030037 , 8.95072003 , 9.40355300 , 9.88077508 , 10.37399672 , 10.87814231 , 11.38660024 , 11.89300017 , 12.39149653 , 12.87698463 , 13.34525572 , 13.79308417 , 14.21824846 , 14.61949586 , 14.98383814 , 15.32145445 , 15.63556729 , 15.93074571 , 16.21246333 , 16.48667555 , 16.76065565 , 17.04029477 , 17.31155496 , 17.58422661 , 17.86029465 , 18.14152544 , 18.42948468 , 18.72555148 , 19.03092971 , 19.34666033 , 19.67363512 , 20.01260803 , 20.36420744 , 20.72894721 , 21.10683704 , 21.14022364 , 21.94188039 , 22.40629360 , 22.89157693 , 23.39611331 , 23.91778618 , 24.45405889 , 25.00207648 , 25.55877725 , 26.12100740 , 26.68562347 , 27.24044867 , 27.78682992 , 28.32190826 , 28.84372670 , 29.35123734 , 29.84426842 , 30.32416894 , 30.79301665 , 31.27692354 , 31.75477465 , 32.22537858 , 32.68777588 , 33.14121711 , 33.58516331 , 34.01928569 , 34.44345812 , 34.85774446 , 35.26238169 , 35.65776081 , 36.04440616 ] ,
    [ 7.30000000 , 0.00487486 , 0.07660034 , 0.27678167 , 0.54802687 , 0.81268951 , 1.02796470 , 1.18711944 , 1.30596587 , 1.40974075 , 1.52391371 , 1.66934537 , 1.86280894 , 2.11561447 , 2.42764507 , 2.79010832 , 3.18848549 , 3.60503630 , 4.02135248 , 4.41637232 , 4.77578487 , 5.07930280 , 5.34397653 , 5.57570035 , 5.78185927 , 5.97046552 , 6.14948352 , 6.32638016 , 6.50786100 , 6.69974521 , 6.90693287 , 7.13776857 , 7.39840255 , 7.69352665 , 8.02602579 , 8.39666509 , 8.80402309 , 9.24462214 , 9.71109915 , 10.19524845 , 10.69213582 , 11.19523860 , 11.69818973 , 12.19506773 , 12.68062135 , 13.15043627 , 13.60103729 , 14.02992551 , 14.43555831 , 14.80496880 , 15.14740392 , 15.46559461 , 15.76367032 , 16.04675037 , 16.32054443 , 16.59211082 , 16.86742323 , 17.13469663 , 17.40257684 , 17.67310049 , 17.94808620 , 18.22915217 , 18.51772989 , 18.81507476 , 19.12227808 , 19.44028041 , 19.76988255 , 20.11175766 , 20.46646217 , 20.83407870 , 20.92396235 , 21.64656469 , 22.09901992 , 22.57258306 , 23.06584632 , 23.57689464 , 24.10337564 , 24.64259324 , 25.19161227 , 25.74736903 , 26.30677272 , 26.85848118 , 27.40308830 , 27.93754623 , 28.45964310 , 28.96803174 , 29.46221997 , 29.94309793 , 30.41243051 , 30.89622568 , 31.37403552 , 31.84470981 , 32.30729912 , 32.76104172 , 33.20536914 , 33.63991033 , 34.06448815 , 34.47911011 , 34.88395430 , 35.27935281 , 35.66577283 ] ,
    [ 7.40000000 , 0.00463400 , 0.07349154 , 0.26777508 , 0.53411831 , 0.79697712 , 1.01306647 , 1.17407214 , 1.29414853 , 1.39736183 , 1.50860906 , 1.64856879 , 1.83415444 , 2.07735998 , 2.37919700 , 2.73202275 , 3.12232771 , 3.53313620 , 3.94645812 , 4.34140063 , 4.70323663 , 5.01025382 , 5.27874849 , 5.51392782 , 5.72265705 , 5.91258980 , 6.09147365 , 6.26667463 , 6.44488683 , 6.63198295 , 6.83296133 , 7.05557669 , 7.30633273 , 7.59016315 , 7.91032930 , 8.26807535 , 8.66252309 , 9.09085866 , 9.54640760 , 10.02118945 , 10.51043029 , 11.00772473 , 11.50673662 , 12.00149534 , 12.48662836 , 12.95753885 , 13.41052166 , 13.84281617 , 14.25260143 , 14.62698671 , 14.97429324 , 15.29676648 , 15.59809172 , 15.88301768 , 16.15698215 , 16.42676834 , 16.69844892 , 16.96221891 , 17.22577274 , 17.49119723 , 17.76036207 , 18.03493707 , 18.31640550 , 18.60607404 , 18.90508433 , 19.21442597 , 19.53494707 , 19.86736612 , 20.21228276 , 20.56985222 , 20.66611474 , 21.36010491 , 21.80065351 , 22.26247839 , 22.74437715 , 23.24463511 , 23.76108620 , 24.29119832 , 24.83217113 , 25.38104152 , 25.93478374 , 26.48289528 , 27.02526906 , 27.55869709 , 28.08073967 , 28.58977190 , 29.08499636 , 29.56682226 , 30.03679861 , 30.52053332 , 30.99836759 , 31.46919007 , 31.93206104 , 32.38620758 , 32.83103369 , 33.26612821 , 33.69126516 , 34.10639760 , 34.51164627 , 34.90728537 , 35.29372544 ] ,
    [ 7.50000000 , 0.00440764 , 0.07052934 , 0.25909601 , 0.52056105 , 0.78150092 , 0.99825979 , 1.16104554 , 1.28240822 , 1.38524693 , 1.49385935 , 1.62872589 , 1.80683289 , 2.04078387 , 2.33265244 , 2.67591185 , 3.05805015 , 3.46286904 , 3.87283687 , 4.26728858 , 4.63114657 , 4.94141397 , 5.21361116 , 5.45226029 , 5.66369689 , 5.85519885 , 6.03427627 , 6.20817301 , 6.38355163 , 6.56632044 , 6.76156084 , 6.97649793 , 7.21791008 , 7.49094106 , 7.79919444 , 8.14436177 , 8.52608189 , 8.94218218 , 9.38664876 , 9.85180463 , 10.33304421 , 10.82410478 , 11.31870749 , 11.81085853 , 12.29508900 , 12.76664255 , 13.22160422 , 13.65696807 , 14.07064732 , 14.44987670 , 14.80206046 , 15.12897070 , 15.43384627 , 15.72105230 , 15.99573192 , 16.26438328 , 16.53307339 , 16.79381344 , 17.05350082 , 17.31427011 , 17.57804009 , 17.84653068 , 18.12127585 , 18.40363291 , 18.69479340 , 18.99579600 , 19.30753627 , 19.63077838 , 19.96616566 , 20.31392545 , 20.42648458 , 21.08230400 , 21.51102408 , 21.96112132 , 22.43159420 , 22.92092649 , 23.42713956 , 23.94786939 , 24.48045768 , 25.02205148 , 25.56970150 , 26.11374464 , 26.65342212 , 27.18539764 , 27.70702991 , 28.21643860 , 28.71253798 , 29.19530358 , 29.66598948 , 30.14968412 , 30.62758218 , 31.09860762 , 31.56182943 , 32.01646392 , 32.46188895 , 32.89765503 , 33.32348917 , 33.73929171 , 34.14512743 , 34.54121356 , 34.92790451 ] ,
    [ 7.60000000 , 0.00419474 , 0.06770610 , 0.25073205 , 0.50734882 , 0.76626334 , 0.98355099 , 1.14804155 , 1.27073496 , 1.37336965 , 1.47962056 , 1.60975509 , 1.78077142 , 2.00581195 , 2.28794630 , 2.62172840 , 2.99562988 , 3.39423848 , 3.80051582 , 4.19407947 , 4.55955987 , 4.87281717 , 5.14857845 , 5.39068602 , 5.60493852 , 5.79822324 , 5.97779398 , 6.15075245 , 6.32371029 , 6.50259395 , 6.69255280 , 6.90033978 , 7.13293485 , 7.39566129 , 7.69243186 , 8.02535423 , 8.39455770 , 8.79849015 , 9.23175857 , 9.68706824 , 10.15998640 , 10.64441650 , 11.13416233 , 11.62323198 , 12.10608470 , 12.57782753 , 13.03435602 , 13.47243598 , 13.88972813 , 14.27363555 , 14.63065974 , 14.96211387 , 15.27079076 , 15.56066224 , 15.83655732 , 16.10469301 , 16.37100089 , 16.62917373 , 16.88544832 , 17.14200384 , 17.40080553 , 17.66362137 , 17.93203445 , 18.20745162 , 18.49111364 , 18.78410792 , 19.08737740 , 19.40173204 , 19.72785916 , 20.06605758 , 20.24281822 , 20.81295656 , 21.22995275 , 21.66836118 , 22.12737633 , 22.60567795 , 23.10147514 , 23.61257508 , 24.13646772 , 24.67041882 , 25.21156609 , 25.75107930 , 26.28759868 , 26.81769033 , 27.33853717 , 27.84802658 , 28.34480278 , 28.82847382 , 29.29987453 , 29.78352171 , 30.26149834 , 30.73275951 , 31.19638141 , 31.65156953 , 32.09767653 , 32.53421601 , 32.96086961 , 33.37748644 , 33.78407660 , 34.18080127 , 34.56795916 ] ,
    [ 7.70000000 , 0.00399438 , 0.06501459 , 0.24267052 , 0.49447519 , 0.75126631 , 0.96894615 , 1.13506256 , 1.25912024 , 1.36170603 , 1.46585188 , 1.59159682 , 1.75590034 , 1.97237119 , 2.24501410 , 2.56942421 , 2.93504139 , 3.32724457 , 3.72951836 , 4.12180026 , 4.48851914 , 4.80449815 , 5.08366772 , 5.32919893 , 5.54634907 , 5.74160225 , 5.92193895 , 6.09429997 , 6.26522759 , 6.44064936 , 6.62576768 , 6.82691717 , 7.05121405 , 7.30412972 , 7.58985481 , 7.91088253 , 8.26780580 , 8.65964995 , 9.08166093 , 9.52694444 , 9.99125632 , 10.46868931 , 10.95315417 , 11.43868544 , 11.91969432 , 12.39117397 , 12.84885100 , 13.28928049 , 13.70988469 , 14.09827036 , 14.46006008 , 14.79612011 , 15.10880133 , 15.40167568 , 15.67924187 , 15.94738908 , 16.21193530 , 16.46799306 , 16.72130195 , 16.97408195 , 17.22834166 , 17.48589463 , 17.74837105 , 18.01722585 , 18.29374807 , 18.57907314 , 18.87419108 , 19.17995756 , 19.49710401 , 19.82599986 , 20.05033342 , 20.55184975 , 20.95725273 , 21.38403874 , 21.83159329 , 22.29878916 , 22.78402277 , 23.28527477 , 23.80018848 , 24.32615603 , 24.86041173 , 25.39494417 , 25.92784987 , 26.45562159 , 26.97529286 , 27.48454260 , 27.98176442 , 28.46618900 , 28.93831920 , 29.42188889 , 29.89993741 , 30.37144716 , 30.83549985 , 31.29128987 , 31.73814532 , 32.17554411 , 32.60312390 , 33.02068393 , 33.42818086 , 33.82572064 , 34.21354677 ] ,
    [ 7.80000000 , 0.00380570 , 0.06244802 , 0.23490007 , 0.48193360 , 0.73651130 , 0.95445103 , 1.12211132 , 1.24755684 , 1.35023435 , 1.45251543 , 1.57419667 , 1.73215331 , 1.94039185 , 2.20379233 , 2.51895037 , 2.87625690 , 3.26188399 , 3.65986424 , 4.05048564 , 4.41806807 , 4.73649371 , 5.01890010 , 5.26779846 , 5.48790272 , 5.68528340 , 5.86663236 , 6.03871209 , 6.20797789 , 6.38034192 , 6.56104486 , 6.75605416 , 6.97256183 , 7.21615748 , 7.49127961 , 7.80077700 , 8.14567926 , 8.52554152 , 8.93627767 , 9.37139125 , 9.82684601 , 10.29694517 , 10.77572952 , 11.25728350 , 11.73599360 , 12.20676137 , 12.66516506 , 13.10756688 , 13.53116530 , 13.92380046 , 14.29024447 , 14.63092996 , 14.94777238 , 15.24394015 , 15.52358847 , 15.79221972 , 16.05561008 , 16.30999066 , 16.56077094 , 16.81020740 , 17.06034835 , 17.31304991 , 17.56998693 , 17.83266065 , 18.10240707 , 18.38040869 , 18.66770198 , 18.96518804 , 19.27364235 , 19.59350393 , 19.81740701 , 20.29876675 , 20.69273131 , 21.10798750 , 21.54410659 , 22.00015088 , 22.47470305 , 22.96591862 , 23.47159845 , 23.98926776 , 24.51626608 , 25.04538198 , 25.57422626 , 26.09924044 , 26.61733476 , 27.12600366 , 27.62341054 , 28.10837524 , 28.58122996 , 29.06466719 , 29.54275770 , 30.01450735 , 30.47900147 , 30.93542276 , 31.38307521 , 31.82140194 , 32.24999784 , 32.66861356 , 33.07715338 , 33.47566884 , 33.86434871 ] ,
    [ 7.90000000 , 0.00362788 , 0.05999995 , 0.22741070 , 0.46971740 , 0.72199938 , 0.94007114 , 1.10919087 , 1.23603870 , 1.33893493 , 1.43957613 , 1.55750549 , 1.70946717 , 1.90980776 , 2.16421852 , 2.47025748 , 2.81924663 , 3.19815029 , 3.59156972 , 3.98018462 , 4.34825139 , 4.66884223 , 4.95429983 , 5.20648882 , 5.42958000 , 5.62922182 , 5.81180390 , 5.98389430 , 6.15184468 , 6.32153589 , 6.49823245 , 6.68758414 , 6.89679941 , 7.13156112 , 7.39652601 , 7.69486902 , 8.02802960 , 8.39607144 , 8.79553039 , 9.22036117 , 9.66674023 , 10.12919858 , 10.60192802 , 11.07908525 , 11.55505452 , 12.02466766 , 12.48337499 , 12.92736395 , 13.35362438 , 13.75025659 , 14.12120861 , 14.46649899 , 14.78761545 , 15.08732157 , 15.36941882 , 15.63902902 , 15.90179522 , 16.15491757 , 16.40359226 , 16.65010724 , 16.89654619 , 17.14480434 , 17.39659834 , 17.65347352 , 17.91681122 , 18.18783970 , 18.46764106 , 18.75716127 , 19.05721958 , 19.36832343 , 19.59594291 , 20.05348748 , 20.43619036 , 20.84003411 , 21.26476980 , 21.70964517 , 22.17342737 , 22.65444747 , 23.15066708 , 23.65975026 , 24.17914956 , 24.70243304 , 25.22677660 , 25.74859699 , 26.26470532 , 26.77243531 , 27.26974099 , 27.75508759 , 28.22856585 , 28.71178604 , 29.18986216 , 29.66181882 , 30.12674263 , 30.58380368 , 31.03228179 , 31.47158607 , 31.90126965 , 32.32103560 , 32.73073686 , 33.13037126 , 33.52007333 ] ,
    [ 8.00000000 , 0.00346021 , 0.05766433 , 0.22019183 , 0.45781984 , 0.70773113 , 0.92581165 , 1.09630453 , 1.22456081 , 1.32778999 , 1.42700151 , 1.54147535 , 1.68778152 , 1.88055382 , 2.12623111 , 2.42329577 , 2.76397902 , 3.13603410 , 3.52464769 , 3.91093288 , 4.27910964 , 4.60158106 , 4.88989262 , 5.14527786 , 5.37136683 , 5.57337941 , 5.75739102 , 5.92976052 , 6.09672018 , 6.26410425 , 6.43718699 , 6.62134743 , 6.82375486 , 7.05016280 , 7.30541754 , 7.59299152 , 7.91470744 , 8.27112630 , 8.65932988 , 9.07379736 , 9.51091480 , 9.96545556 , 10.43178172 , 10.90414347 , 11.37694449 , 11.84496827 , 12.30355742 , 12.74874285 , 13.17732132 , 13.57767585 , 13.95295882 , 14.30279653 , 14.62825807 , 14.93170337 , 15.21657274 , 15.48764423 , 15.75026284 , 16.00252708 , 16.24950477 , 16.49350976 , 16.73665630 , 16.98087471 , 17.22792030 , 17.47937989 , 17.73667819 , 18.00108765 , 18.27373488 , 18.55560998 , 18.84757548 , 19.15020583 , 19.42813701 , 19.81578594 , 20.18742529 , 20.57999797 , 20.99342841 , 21.42714533 , 21.88009789 , 22.35079274 , 22.83735450 , 23.33759100 , 23.84907467 , 24.36612975 , 24.88554572 , 25.40374092 , 25.91745020 , 26.42386994 , 26.92076615 , 27.40634832 , 27.88028136 , 28.36317443 , 28.84115605 , 29.31326462 , 29.77858545 , 30.23627484 , 30.68558821 , 31.12590121 , 31.55672604 , 31.97771918 , 32.38868302 , 32.78956248 , 33.18043827 ] ,
    [ 8.10000000 , 0.00330200 , 0.05543541 , 0.21323183 , 0.44623409 , 0.69370673 , 0.91167745 , 1.08345579 , 1.21311911 , 1.31678352 , 1.41476151 , 1.52605829 , 1.66703866 , 1.85256527 , 2.08976954 , 2.37801537 , 2.71042103 , 3.07552342 , 3.45910777 , 3.84274094 , 4.21067795 , 4.53474586 , 4.82570519 , 5.08417653 , 5.31325395 , 5.51772429 , 5.70333848 , 5.87623263 , 6.04250493 , 6.20792838 , 6.37777330 , 6.55719051 , 6.75326302 , 6.97179036 , 7.21778177 , 7.49497942 , 7.80556301 , 8.15055119 , 8.52757347 , 8.93163337 , 9.35933669 , 9.80571377 , 10.26531506 , 10.73250443 , 11.20172596 , 11.66773556 , 12.12578809 , 12.57177619 , 13.00231940 , 13.40609924 , 13.78551080 , 14.13980443 , 14.46964266 , 14.77698556 , 15.06490744 , 15.33781542 , 15.60077398 , 15.85256377 , 16.09824012 , 16.34013687 , 16.58039378 , 16.82097198 , 17.06366193 , 17.31008908 , 17.56171929 , 17.81986738 , 18.08570309 , 18.36025967 , 18.64444232 , 18.93889089 , 19.26561030 , 19.58543030 , 19.94622558 , 20.32769178 , 20.72992041 , 21.15251632 , 21.59460786 , 22.05487653 , 22.53161153 , 23.02276846 , 23.52604565 , 24.03649437 , 24.55057339 , 25.06472029 , 25.57561677 , 26.08034527 , 26.57650533 , 27.06205614 , 27.53630165 , 28.01874046 , 28.49652947 , 28.96871690 , 29.43438439 , 29.89267333 , 30.34281455 , 30.78415067 , 31.21615376 , 31.63843451 , 32.05074570 , 32.45297996 , 32.84516471 ] ,
    [ 8.20000000 , 0.00315262 , 0.05330779 , 0.20652041 , 0.43495332 , 0.67992599 , 0.89767312 , 1.07064831 , 1.20171036 , 1.30590106 , 1.40282835 , 1.51121083 , 1.64718392 , 1.82578058 , 2.05477464 , 2.33436641 , 2.65853832 , 3.01660375 , 3.39495654 , 3.77562419 , 4.14299174 , 4.46837304 , 4.76176619 , 5.02319917 , 5.25523694 , 5.46223064 , 5.64959800 , 5.82324018 , 5.98910748 , 6.15289779 , 6.31986417 , 6.49496846 , 6.68516591 , 6.89627749 , 7.13345054 , 7.40067002 , 7.70044673 , 8.03420064 , 8.40015864 , 8.79379886 , 9.21196698 , 9.64996418 , 10.10254582 , 10.56420842 , 11.02945649 , 11.49303857 , 11.95014132 , 12.39653733 , 12.82868491 , 13.23557507 , 13.61888939 , 13.97751610 , 14.31172549 , 14.62308371 , 14.91429680 , 15.18933112 , 15.45311673 , 15.70479696 , 15.94955242 , 16.18973076 , 16.42749187 , 16.66482317 , 16.90354646 , 17.14532270 , 17.39165638 , 17.64390259 , 17.90327265 , 18.17084180 , 18.44755706 , 18.73412187 , 19.05957588 , 19.36218788 , 19.71237757 , 20.08292341 , 20.47407755 , 20.88561583 , 21.31684233 , 21.76661222 , 22.23337998 , 22.71525218 , 23.21005827 , 23.71354380 , 24.22189487 , 24.73158075 , 25.23925296 , 25.74190290 , 26.23698517 , 26.72214786 , 27.19658168 , 27.67842165 , 28.15590170 , 28.62807671 , 29.09402239 , 29.55286429 , 30.00380843 , 30.44616478 , 30.87936594 , 31.30297771 , 31.71670399 , 32.12038587 , 32.51399795 ] ,
    [ 8.30000000 , 0.00301151 , 0.05127635 , 0.20004960 , 0.42397071 , 0.66638844 , 0.88380290 , 1.05788583 , 1.19033208 , 1.29512967 , 1.39117636 , 1.49689603 , 1.62816566 , 1.80014294 , 2.02118874 , 2.29229920 , 2.60829548 , 2.95925841 , 3.33219763 , 3.70962288 , 4.07608928 , 4.40250046 , 4.69810632 , 4.96236332 , 5.19731576 , 5.40687818 , 5.59612780 , 5.77071989 , 5.93644404 , 6.09890980 , 6.26334020 , 6.43454608 , 6.61931270 , 6.82346382 , 7.05226017 , 7.30990330 , 7.59920964 , 7.92197475 , 8.27699038 , 8.66022231 , 9.06876223 , 9.49819180 , 9.94348543 , 10.39928972 , 10.86018857 , 11.32094263 , 11.77668945 , 12.22309959 , 12.65648631 , 13.06616035 , 13.45312779 , 13.81593540 , 14.15447558 , 14.46992805 , 14.76463057 , 15.04210786 , 15.30712962 , 15.55904089 , 15.80323593 , 16.04206955 , 16.27771596 , 16.51218395 , 16.74732258 , 16.98482486 , 17.22623110 , 17.47293435 , 17.72618569 , 17.98710090 , 18.25666781 , 18.53565152 , 18.85224117 , 19.14582753 , 19.48566590 , 19.84549695 , 20.22572620 , 20.62629481 , 21.04667867 , 21.48590473 , 21.94259279 , 22.41500279 , 22.90109971 , 23.39729219 , 23.89954070 , 24.40436466 , 24.90840604 , 25.40858693 , 25.90223823 , 26.38672764 , 26.86114446 , 27.34221668 , 27.81924862 , 28.29129811 , 28.75743258 , 29.21676057 , 29.66846295 , 30.11181733 , 30.54621741 , 30.97118484 , 31.38637540 , 31.79157930 , 32.18671883 ] ,
    [ 8.40000000 , 0.00287812 , 0.04933625 , 0.19381118 , 0.41327942 , 0.65309326 , 0.87007074 , 1.04517218 , 1.17898248 , 1.28445773 , 1.37978184 , 1.48307853 , 1.60993462 , 1.77559723 , 1.98895540 , 2.25176430 , 2.55965621 , 2.90346872 , 3.27083192 , 3.64477250 , 4.01000513 , 4.33716414 , 4.63475633 , 4.90168830 , 5.13949380 , 5.35165134 , 5.54289192 , 5.71861509 , 5.88443792 , 6.04586911 , 6.20808940 , 6.37579500 , 6.55555923 , 6.75319483 , 6.97405164 , 7.22252227 , 7.50170387 , 7.81377113 , 8.15796797 , 8.53082590 , 8.92967199 , 9.35037425 , 9.78813807 , 10.23777588 , 10.69396893 , 11.15150861 , 11.60550201 , 12.05153542 , 12.48579321 , 12.89791523 , 13.28826541 , 13.65507529 , 13.99787358 , 14.31746249 , 14.61581355 , 14.89608120 , 15.16266263 , 15.41512064 , 15.65909495 , 15.89694043 , 16.13083946 , 16.36281694 , 16.59474482 , 16.82834446 , 17.06518880 , 17.30670637 , 17.55418593 , 17.80878222 , 18.07152257 , 18.34323165 , 18.68681965 , 18.93611573 , 19.26587177 , 19.61521181 , 19.98468690 , 20.37439739 , 20.78398650 , 21.21265052 , 21.65917399 , 22.12197183 , 22.59914819 , 23.08774503 , 23.58353455 , 24.08310985 , 24.58312146 , 25.08044269 , 25.57230155 , 26.05591565 , 26.53001942 , 27.01013242 , 27.48655582 , 27.95834604 , 28.42455984 , 28.88428749 , 29.33668427 , 29.78099556 , 30.21657672 , 30.64290594 , 31.05959152 , 31.46637350 , 31.86312238 ] ,
    [ 8.50000000 , 0.00275195 , 0.04748291 , 0.18779469 , 0.40287256 , 0.64003923 , 0.85648025 , 1.03251120 , 1.16766034 , 1.27387487 , 1.36862295 , 1.46972027 , 1.59244353 , 1.75208725 , 1.95801922 , 2.21271262 , 2.51258349 , 2.84921416 , 3.21085772 , 3.58107320 , 3.94476511 , 4.27239600 , 4.57174566 , 4.84119434 , 5.08177704 , 5.29653867 , 5.48985962 , 5.66687522 , 5.83301915 , 5.99368750 , 6.15400695 , 6.31859109 , 6.49376763 , 6.68532192 , 6.89867067 , 7.13837320 , 7.40778297 , 7.70943230 , 8.04297371 , 8.40552173 , 8.79463732 , 9.20648111 , 9.63650021 , 10.07968739 , 10.53083813 , 10.98479249 , 11.43664516 , 11.88191564 , 12.31667555 , 12.73089802 , 13.12434622 , 13.49495675 , 13.84191074 , 14.16564364 , 14.46776480 , 14.75107772 , 15.01953899 , 15.27283930 , 15.51691523 , 15.75411452 , 15.98662152 , 16.21647186 , 16.44555581 , 16.67561916 , 16.90826414 , 17.14495207 , 17.38700711 , 17.63562113 , 17.89185957 , 18.15660440 , 18.55194264 , 18.73281381 , 19.05277199 , 19.39186255 , 19.75077450 , 20.12976104 , 20.52862791 , 20.94673782 , 21.38303885 , 21.83610182 , 22.30417298 , 22.78489385 , 23.27389177 , 23.76784881 , 24.26344190 , 24.75751557 , 25.24721534 , 25.72966494 , 26.20317932 , 26.68213063 , 27.15777188 , 27.62915478 , 28.09532342 , 28.55534883 , 29.00836041 , 29.45357155 , 29.89029980 , 30.31798056 , 30.73617542 , 31.14457491 , 31.54299826 ] ,
    [ 8.60000000 , 0.00263255 , 0.04571201 , 0.18198988 , 0.39274333 , 0.62722487 , 0.84303473 , 1.01990676 , 1.15636498 , 1.26337186 , 1.35767953 , 1.45678488 , 1.57564765 , 1.72955856 , 1.92832633 , 2.17509559 , 2.46703971 , 2.79647262 , 3.15227092 , 3.51851433 , 3.88039234 , 4.20822665 , 4.50910388 , 4.78090319 , 5.02417440 , 5.24153278 , 5.43700526 , 5.61545561 , 5.78212421 , 5.94228351 , 6.10099498 , 6.26281678 , 6.43380670 , 6.61970243 , 6.82596787 , 7.05730583 , 7.31730232 , 7.60878516 , 7.93188583 , 8.28421774 , 8.66359414 , 9.06647596 , 9.48856196 , 9.92503849 , 10.37083104 , 10.82084548 , 11.27018159 , 11.71430919 , 12.14920318 , 12.56516843 , 12.96141888 , 13.33560798 , 13.68658793 , 14.01443984 , 14.32041678 , 14.60689670 , 14.87758783 , 15.13200695 , 15.37648996 , 15.61337045 , 15.84482859 , 16.07290530 , 16.29950450 , 16.52639228 , 16.75519673 , 16.98740903 , 17.22438636 , 17.46735570 , 17.71741900 , 17.97551314 , 18.38199789 , 18.53568321 , 18.84614211 , 19.17524105 , 19.52379974 , 19.89221787 , 20.28045854 , 20.68804743 , 21.11409450 , 21.55732669 , 22.01613461 , 22.48872093 , 22.97062048 , 23.45860839 , 23.94940650 , 24.43984999 , 24.92702178 , 25.40787184 , 25.88058897 , 26.35816998 , 26.83284579 , 27.30366173 , 27.76964790 , 28.22985545 , 28.68338798 , 29.12942714 , 29.56725328 , 29.99625980 , 30.41596235 , 30.82600267 , 31.22614934 ] ,
    [ 8.70000000 , 0.00251949 , 0.04401945 , 0.17638987 , 0.38288505 , 0.61464856 , 0.82973720 , 1.00736269 , 1.14509620 , 1.25294051 , 1.34693307 , 1.44424391 , 1.55950516 , 1.70796247 , 1.89982474 , 2.13886523 , 2.42298689 , 2.74522057 , 3.09506515 , 3.45711719 , 3.81691529 , 4.14468891 , 4.44686230 , 4.72083888 , 4.96669790 , 5.18663037 , 5.38430814 , 5.56431724 , 5.73169578 , 5.89158228 , 6.04896232 , 6.20836445 , 6.37555226 , 6.55619968 , 6.75579882 , 6.97917360 , 7.23011936 , 7.51171316 , 7.82459706 , 8.16682529 , 8.53647708 , 8.93031871 , 9.34430853 , 9.77383807 , 10.21397736 , 10.65971426 , 11.10617047 , 11.54878284 , 11.98344535 , 12.40079306 , 12.79953708 , 13.17706368 , 13.53191474 , 13.86383032 , 14.17371452 , 14.46347503 , 14.73669779 , 14.99248742 , 15.23766120 , 15.47453139 , 15.70526772 , 15.93191089 , 16.15637349 , 16.38043776 , 16.60575392 , 16.83383997 , 17.06608346 , 17.30374434 , 17.54795929 , 17.79971754 , 18.18628534 , 18.34449167 , 18.64575994 , 18.96513876 , 19.30357095 , 19.66159590 , 20.03932853 , 20.43645355 , 20.85224057 , 21.28557225 , 21.73498514 , 22.19920679 , 22.67372308 , 23.15540973 , 23.64105025 , 24.12748850 , 24.61176385 , 25.09060708 , 25.56228999 , 26.03827791 , 26.51179014 , 26.98186396 , 27.44751435 , 27.90777214 , 28.36171518 , 28.80849370 , 29.24735149 , 29.67764073 , 30.09883196 , 30.51051887 , 30.91241999 ] ,
    [ 8.80000000 , 0.00241237 , 0.04240135 , 0.17098948 , 0.37329111 , 0.60230851 , 0.81659033 , 0.99488277 , 1.13385420 , 1.24257362 , 1.33636650 , 1.43207380 , 1.54397665 , 1.68725421 , 1.87246403 , 2.10397422 , 2.38038670 , 2.69543321 , 3.03923200 , 3.39692260 , 3.75436360 , 4.08181546 , 4.38505243 , 4.66102657 , 4.90936184 , 5.13183146 , 5.33175186 , 5.51342617 , 5.68168223 , 5.84151502 , 5.99782416 , 6.15513460 , 6.31888664 , 6.49468285 , 6.68802413 , 6.90383378 , 7.14609395 , 7.41813827 , 7.72100720 , 8.05325571 , 8.41321776 , 8.79796456 , 9.20371950 , 9.62608911 , 10.06030108 , 10.50144045 , 10.94466690 , 11.38540053 , 11.81947002 , 12.23784218 , 12.63875798 , 13.01936394 , 13.37790847 , 13.71380415 , 14.02761478 , 14.32085298 , 14.59679820 , 14.85418143 , 15.10030456 , 15.33745116 , 15.56777397 , 15.79330767 , 16.01596851 , 16.23755041 , 16.45972185 , 16.68402439 , 16.91187317 , 17.14455874 , 17.38325052 , 17.62898747 , 18.01953669 , 18.15901063 , 18.45140426 , 18.76134614 , 19.08989378 , 19.43771901 , 19.80508262 , 20.19182386 , 20.59736931 , 21.02075628 , 21.46066822 , 21.91632716 , 22.38319492 , 22.85826747 , 23.33840320 , 23.82047084 , 24.30148434 , 24.77807215 , 25.24837358 , 25.72252636 , 26.19465891 , 26.66379769 , 27.12894139 , 27.58909987 , 28.04332519 , 28.49073656 , 28.93054178 , 29.36205260 , 29.78469525 , 30.19801614 , 30.60168440 ] ,
    [ 8.90000000 , 0.00231084 , 0.04085403 , 0.16578072 , 0.36395489 , 0.59020256 , 0.80359653 , 0.98247071 , 1.12263955 , 1.23226482 , 1.32596417 , 1.42024720 , 1.52902404 , 1.66738756 , 1.84619489 , 2.07037592 , 2.33920067 , 2.64708463 , 2.98476111 , 3.33793860 , 3.69275697 , 4.01963354 , 4.32370301 , 4.60149068 , 4.85218145 , 5.07713843 , 5.27932352 , 5.46275295 , 5.63203714 , 5.79201865 , 5.94750169 , 6.10303085 , 6.26369776 , 6.43502685 , 6.62250941 , 6.83114760 , 7.06508852 , 7.32793519 , 7.62099954 , 7.94341099 , 8.29374026 , 8.66936154 , 9.06676739 , 9.48178771 , 9.90981974 , 10.34605990 , 10.78572123 , 11.22422275 , 11.65734314 , 12.07638105 , 12.47913954 , 12.86255302 , 13.22459314 , 13.56435942 , 13.88208519 , 14.17898168 , 14.45779022 , 14.71696636 , 14.96427597 , 15.20196662 , 15.43216748 , 15.65690145 , 15.87808327 , 16.09751399 , 16.31687632 , 16.53773203 , 16.76152086 , 16.98956147 , 17.22305387 , 17.46308404 , 17.88885875 , 17.97900773 , 18.26285121 , 18.56365077 , 18.88257021 , 19.22040646 , 19.57755988 , 19.95401944 , 20.34936550 , 20.76278846 , 21.19311896 , 21.64004340 , 22.09902163 , 22.56718888 , 23.04148982 , 23.51883323 , 23.99622485 , 24.47033298 , 24.93887300 , 25.41093949 , 25.88146572 , 26.34946478 , 26.81391810 , 27.27381422 , 27.72817938 , 28.17610228 , 28.61675546 , 29.04941101 , 29.47345170 , 29.88837749 , 30.29380881 ] ,
    [ 9.00000000 , 0.00221453 , 0.03937403 , 0.16075294 , 0.35486978 , 0.57832828 , 0.79075790 , 0.97013013 , 1.11145316 , 1.22200859 , 1.31571171 , 1.40873274 , 1.51461078 , 1.64831457 , 1.82096914 , 2.03802445 , 2.29939024 , 2.60014798 , 2.93164038 , 3.28013338 , 3.63210541 , 3.95816530 , 4.26284019 , 4.54225498 , 4.79517285 , 5.02255589 , 5.22701356 , 5.41227233 , 5.58271897 , 5.74303554 , 5.89792187 , 6.05195955 , 6.20987911 , 6.37711222 , 6.55912537 , 6.76098039 , 6.98696838 , 7.24091744 , 7.52444037 , 7.83718453 , 8.17796205 , 8.54445135 , 8.93341825 , 9.34092352 , 9.76254471 , 10.19360287 , 10.62937905 , 11.06530630 , 11.49712829 , 11.91646885 , 12.32074014 , 12.70667869 , 13.07199869 , 13.41550232 , 13.73710345 , 14.03768315 , 14.31953916 , 14.58069004 , 14.82940659 , 15.06789352 , 15.29825024 , 15.52248215 , 15.74249736 , 15.96009953 , 16.17698156 , 16.39472191 , 16.61478190 , 16.83850562 , 17.06712149 , 17.30175960 , 17.76272916 , 17.80424780 , 18.07987533 , 18.37183833 , 18.68139947 , 19.00947365 , 19.35659450 , 19.72289546 , 20.10810713 , 20.51157090 , 20.93226437 , 21.37030192 , 21.82117933 , 22.28217377 , 22.75032869 , 23.22260773 , 23.69602500 , 24.16726083 , 24.63374855 , 25.10348147 , 25.57217346 , 26.03882370 , 26.50239624 , 26.96185841 , 27.41621115 , 27.86451329 , 28.30590297 , 28.73961360 , 29.16498546 , 29.58147295 , 29.98864859 ] ,
    [ 9.10000000 , 0.00212315 , 0.03795805 , 0.15589802 , 0.34602939 , 0.56668322 , 0.77807624 , 0.95786456 , 1.10029616 , 1.21180013 , 1.30559597 , 1.39750460 , 1.50070291 , 1.62999160 , 1.79674058 , 2.00687483 , 2.26091689 , 2.55459558 , 2.87985611 , 3.22349042 , 3.57242230 , 3.89743414 , 4.20249100 , 4.48334440 , 4.73835408 , 4.96809118 , 5.17481600 , 5.36196335 , 5.53369108 , 5.69451336 , 5.84901725 , 6.00183503 , 6.15733057 , 6.32082527 , 6.49774777 , 6.69320166 , 6.91160179 , 7.15692624 , 7.43120641 , 7.73447313 , 8.06580044 , 8.42317331 , 8.80363434 , 9.20348157 , 9.61848245 , 10.04409486 , 10.47568169 , 10.90870458 , 11.33888676 , 11.75816720 , 12.16362014 , 12.55179203 , 12.92016033 , 13.26724637 , 13.59265652 , 13.89683976 , 14.18194717 , 14.44523487 , 14.69556011 , 14.93507820 , 15.16585285 , 15.38986647 , 15.60901538 , 15.82510128 , 16.03982331 , 16.25477293 , 16.47142987 , 16.69116099 , 16.91522075 , 17.14478033 , 17.59388172 , 17.63450284 , 17.90225526 , 18.18569632 , 18.48618075 , 18.80473429 , 19.14201740 , 19.49830251 , 19.87346646 , 20.26699909 , 20.67802410 , 21.10704514 , 21.54963778 , 22.00321517 , 22.46493228 , 22.93182171 , 23.40092164 , 23.86879060 , 24.33299867 , 24.80015210 , 25.26677922 , 25.73186624 , 26.19436022 , 26.65320788 , 27.10738568 , 27.55592342 , 27.99792584 , 28.43258874 , 28.85921107 , 29.27720259 , 29.68608876 ] ,
    [ 9.20000000 , 0.00203639 , 0.03660296 , 0.15121271 , 0.33742756 , 0.55526495 , 0.76555315 , 0.94567739 , 1.08916997 , 1.20163531 , 1.29560490 , 1.38654719 , 1.48726937 , 1.61238228 , 1.77346516 , 1.97688306 , 2.22374223 , 2.51039907 , 2.82939313 , 3.16804135 , 3.51373029 , 3.83746716 , 4.14268435 , 4.42478556 , 4.68174523 , 4.91375433 , 5.12272818 , 5.31180906 , 5.48492143 , 5.64640482 , 5.80072579 , 5.95258202 , 6.10595855 , 6.26605796 , 6.43825748 , 6.62768518 , 6.83886022 , 7.07588577 , 7.34119871 , 7.63518248 , 7.95717533 , 8.30546602 , 8.67737521 , 9.06944298 , 9.47763491 , 9.89755679 , 10.32466625 , 10.75446743 , 11.18267725 , 11.60154435 , 12.00784222 , 12.39794680 , 12.76911772 , 13.11961157 , 13.44873976 , 13.75651963 , 14.04499409 , 14.31055332 , 14.56266396 , 14.80342544 , 15.03485967 , 15.25892054 , 15.47748742 , 15.69235544 , 15.90522586 , 16.11769938 , 16.33127092 , 16.54732722 , 16.76714632 , 16.99193745 , 17.41835838 , 17.46955661 , 17.72977616 , 18.00501570 , 18.29671433 , 18.60600129 , 18.93365709 , 19.28008731 , 19.64531063 , 20.02896231 , 20.43031079 , 20.85021739 , 21.28436174 , 21.73029946 , 22.18530676 , 22.64649747 , 23.11094824 , 23.57509606 , 24.03672513 , 24.50104201 , 24.96536274 , 25.42866064 , 25.88986608 , 26.34790580 , 26.80173250 , 27.25034793 , 27.69282450 , 28.12832149 , 28.55609763 , 28.97551910 , 29.38606525 ] ,
    [ 9.30000000 , 0.00195397 , 0.03530582 , 0.14669373 , 0.32905818 , 0.54407088 , 0.75318992 , 0.93357189 , 1.07807619 , 1.19151063 , 1.28572751 , 1.37584631 , 1.47428055 , 1.59545206 , 1.75110020 , 1.94800605 , 2.18782804 , 2.46752948 , 2.78023496 , 3.11382119 , 3.45604936 , 3.77828908 , 4.08344755 , 4.36660438 , 4.62536679 , 4.85955683 , 5.07074995 , 5.26179584 , 5.43638193 , 5.59866718 , 5.75299034 , 5.90413059 , 6.05567481 , 6.21270759 , 6.38054031 , 6.56430899 , 6.76861844 , 6.99773314 , 7.25431897 , 7.53921665 , 7.85200368 , 8.19126414 , 8.55459561 , 8.93878355 , 9.33999854 , 9.75400418 , 10.17636490 , 10.60264049 , 11.02855521 , 11.44666695 , 11.85346855 , 12.24519833 , 12.61891416 , 12.97262364 , 13.30535624 , 13.61683083 , 13.90867516 , 14.17661269 , 14.43065985 , 14.67285363 , 14.90516802 , 15.12952268 , 15.34777500 , 15.56170882 , 15.77302323 , 15.98332443 , 16.19411917 , 16.40681107 , 16.62269916 , 16.84302759 , 17.28368420 , 17.30919584 , 17.56222507 , 17.82958813 , 18.11280002 , 18.41308578 , 18.73133903 , 19.06809234 , 19.42350146 , 19.79734361 , 20.18903004 , 20.59975586 , 21.02530801 , 21.46340544 , 21.91145157 , 22.36665171 , 22.82613426 , 23.28639449 , 23.74504012 , 24.20625168 , 24.66801371 , 25.12928539 , 25.58898065 , 26.04600665 , 26.49929302 , 26.94781449 , 27.39061225 , 27.82681023 , 28.25562802 , 28.67638935 , 29.08852843 ] ,
    [ 9.40000000 , 0.00187565 , 0.03406382 , 0.14233258 , 0.32091502 , 0.53309806 , 0.74098760 , 0.92155117 , 1.06701656 , 1.18142315 , 1.27595378 , 1.36537917 , 1.46170723 , 1.57916197 , 1.72960370 , 1.92020158 , 2.15313640 , 2.42595741 , 2.73236392 , 3.06081024 , 3.39938390 , 3.71991606 , 4.02480284 , 4.30882410 , 4.56923830 , 4.80551071 , 5.01888282 , 5.21191272 , 5.38804804 , 5.55126183 , 5.70575836 , 5.85641042 , 6.00639531 , 6.16067656 , 6.32448704 , 6.50295547 , 6.70075462 , 6.92232411 , 7.17044224 , 7.44646692 , 7.75019404 , 8.08049530 , 8.43524372 , 8.81147260 , 9.20556344 , 9.61344655 , 10.03080428 , 10.45326463 , 10.87657228 , 11.29359043 , 11.70055825 , 12.09360246 , 12.46959583 , 12.82631325 , 13.16251590 , 13.47771599 , 13.77292357 , 14.04332703 , 14.29944323 , 14.54324054 , 14.77663914 , 15.00151907 , 15.21971069 , 15.43298193 , 15.64302549 , 15.85144927 , 16.05976839 , 16.26940034 , 16.48166248 , 16.69783065 , 17.16922399 , 17.15320131 , 17.39938641 , 17.65920351 , 17.93423568 , 18.22579633 , 18.53488521 , 18.86215566 , 19.20789540 , 19.57201977 , 19.95408045 , 20.35557983 , 20.77242258 , 21.20250366 , 21.64335907 , 22.09229521 , 22.54650468 , 23.00266630 , 23.45794698 , 23.91578868 , 24.37474036 , 24.83374685 , 25.29170621 , 25.74750689 , 26.20005633 , 26.64830352 , 27.09125966 , 27.52801460 , 27.95775002 , 28.37974841 , 28.79339995 ] ,
    [ 9.50000000 , 0.00180118 , 0.03287429 , 0.13811829 , 0.31299198 , 0.52234337 , 0.72894700 , 0.90961820 , 1.05599298 , 1.17137043 , 1.26627459 , 1.35511892 , 1.44952136 , 1.56347137 , 1.70893486 , 1.89342845 , 2.11962972 , 2.38565306 , 2.68576125 , 3.00895292 , 3.34372953 , 3.66235947 , 3.96676967 , 4.25146653 , 4.51337914 , 4.75162890 , 4.96713026 , 5.16215156 , 5.33989866 , 5.50415417 , 5.65898177 , 5.80935305 , 5.95804077 , 6.10987240 , 6.26999334 , 6.44351136 , 6.63515048 , 6.84946055 , 7.08942945 , 7.35681841 , 7.65165058 , 7.97308288 , 8.31926306 , 8.68747442 , 9.07431445 , 9.47588814 , 9.88800610 , 10.30637628 , 10.72677644 , 11.14236261 , 11.54916836 , 11.94321552 , 12.32121133 , 12.68071538 , 13.02023488 , 13.33900120 , 13.63763744 , 13.91058155 , 14.16888557 , 14.41444376 , 14.64911726 , 14.87474134 , 15.09311457 , 15.30598445 , 15.51503324 , 15.72186663 , 15.92800474 , 16.13487590 , 16.34381307 , 16.55612049 , 17.04794044 , 17.00135352 , 17.24104558 , 17.49365258 , 17.76081928 , 18.04394056 , 18.34411558 , 18.66211213 , 18.99834456 , 19.35286223 , 19.72535441 , 20.11759554 , 20.52564280 , 20.94755724 , 21.38101477 , 21.82343273 , 22.27207961 , 22.72371764 , 23.17537837 , 23.62960143 , 24.08550017 , 24.54200735 , 24.99800662 , 25.45236926 , 25.90398205 , 26.35176969 , 26.79471486 , 27.23187478 , 27.66239467 , 28.08551710 , 28.50058941 ] ,
    [ 9.60000000 , 0.00173034 , 0.03173473 , 0.13404484 , 0.30528326 , 0.51180386 , 0.71706875 , 0.89777581 , 1.04500746 , 1.16135052 , 1.25668167 , 1.34504826 , 1.43769780 , 1.54834631 , 1.68905518 , 1.86764664 , 2.08727084 , 2.34658637 , 2.64040726 , 2.95823119 , 3.28909163 , 3.60563504 , 3.90936977 , 4.19455510 , 4.45781034 , 4.69792639 , 4.91549830 , 5.11250730 , 5.29191635 , 5.45731371 , 5.61261692 , 5.76289931 , 5.91053789 , 6.06020785 , 6.21695973 , 6.38586772 , 6.57169131 , 6.77900682 , 7.01116540 , 7.27016690 , 7.55628214 , 7.86895160 , 8.20659634 , 8.56675097 , 8.94623311 , 9.34132941 , 9.74798810 , 10.16200821 , 10.57921251 , 10.99303590 , 11.39935678 , 11.79409455 , 12.17381127 , 12.53586871 , 12.87853484 , 13.20063810 , 13.50277869 , 13.77832005 , 14.03891260 , 14.28637146 , 14.52249376 , 14.74906527 , 14.96784800 , 15.18056468 , 15.38888309 , 15.59440291 , 15.79864579 , 16.00304784 , 16.20895492 , 16.41769622 , 16.89179174 , 16.85344669 , 17.08699687 , 17.33273196 , 17.59235243 , 17.86732788 , 18.15885015 , 18.46779514 , 18.79469824 , 19.13973836 , 19.50273916 , 19.88571138 , 20.28490215 , 20.69852311 , 21.12439761 , 21.56006285 , 22.00287399 , 22.44950675 , 22.89734559 , 23.34770846 , 23.80031513 , 24.25408954 , 24.70790287 , 25.16061109 , 25.61108223 , 26.05821823 , 26.50097493 , 26.93837851 , 27.36953929 , 27.79366132 , 28.21005040 ] ,
    [ 9.70000000 , 0.00166292 , 0.03064275 , 0.13011240 , 0.29778341 , 0.50147678 , 0.70535326 , 0.88602664 , 1.03406208 , 1.15136187 , 1.24716754 , 1.33516202 , 1.42621427 , 1.53376125 , 1.66992847 , 1.84281727 , 2.05602310 , 2.30872709 , 2.59628139 , 2.90868583 , 3.23548856 , 3.54976407 , 3.85262755 , 4.13811487 , 4.40255439 , 4.64441993 , 4.86399521 , 5.06297770 , 5.24408698 , 5.41071374 , 5.56662433 , 5.71700061 , 5.86381928 , 6.01160068 , 6.16529148 , 6.32991997 , 6.51026607 , 6.71092573 , 6.93556698 , 7.18642170 , 7.46400363 , 7.76802824 , 8.09718588 , 8.44926219 , 8.82129785 , 9.20976705 , 9.61076410 , 10.02018932 , 10.43392191 , 10.84566981 , 11.25118225 , 11.64629687 , 12.02744766 , 12.39181502 , 12.73744228 , 13.06278563 , 13.36839859 , 13.64656696 , 13.90952359 , 14.15899935 , 14.39672246 , 14.62442431 , 14.84382583 , 15.05662060 , 15.26445779 , 15.46892729 , 15.67154883 , 15.87376314 , 16.07692614 , 16.28238864 , 16.73000776 , 16.70929106 , 16.93704453 , 17.17624486 , 17.42864094 , 17.69576997 , 17.97890951 , 18.27903710 , 18.59680331 , 18.93251186 , 19.28611714 , 19.65984171 , 20.05013106 , 20.45535222 , 20.87347991 , 21.30217787 , 21.73889728 , 22.18025820 , 22.62398050 , 23.07023366 , 23.51930245 , 23.97010359 , 24.42149745 , 24.87232643 , 25.32144145 , 25.76772340 , 26.21010290 , 26.64757678 , 27.07922197 , 27.50420553 , 27.92179310 ] ,
    [ 9.80000000 , 0.00159872 , 0.02959606 , 0.12631964 , 0.29048689 , 0.49135918 , 0.69380078 , 0.87437319 , 1.02315898 , 1.14140331 , 1.23772541 , 1.32545358 , 1.41504914 , 1.51969062 , 1.65151952 , 1.81890244 , 2.02585034 , 2.27204483 , 2.55336234 , 2.86034955 , 3.18293284 , 3.49476362 , 3.79656443 , 4.08216897 , 4.34763287 , 4.59112634 , 4.81263028 , 5.01356237 , 5.19639901 , 5.36433071 , 5.52096816 , 5.67161122 , 5.81782156 , 5.96397321 , 6.11489846 , 6.27556781 , 6.45076740 , 6.64517494 , 6.86254622 , 7.10548881 , 7.37472680 , 7.67023617 , 7.99097004 , 8.33496351 , 8.69948221 , 9.08119273 , 9.47634291 , 9.88094384 , 10.29094187 , 10.70031875 , 11.10470045 , 11.49987869 , 11.88217326 , 12.24859852 , 12.59698789 , 12.92560017 , 13.23454399 , 13.51534389 , 13.78071621 , 14.03230259 , 14.27175734 , 14.50075271 , 14.72096410 , 14.93405160 , 15.14164160 , 15.34531051 , 15.54657263 , 15.74687010 , 15.94756599 , 16.15002942 , 16.61383800 , 16.56869873 , 16.79099491 , 17.02399619 , 17.26949165 , 17.52907860 , 17.80411333 , 18.09566839 , 18.40450353 , 18.73104226 , 19.07536570 , 19.43989291 , 19.82125230 , 20.21798824 , 20.62822706 , 21.04976364 , 21.48015327 , 21.91618469 , 22.35539733 , 22.79728550 , 23.24256593 , 23.69014812 , 24.13888314 , 24.58760126 , 25.03513781 , 25.48035441 , 25.92215819 , 26.35951826 , 26.79147974 , 27.21717427 , 27.63582878 ] ,
    [ 9.90000000 , 0.00153757 , 0.02859254 , 0.12265758 , 0.28338799 , 0.48144768 , 0.68241130 , 0.86281777 , 1.01230034 , 1.13147404 , 1.22834922 , 1.31590329 , 1.40418003 , 1.50610171 , 1.63379320 , 1.79586520 , 1.99671695 , 2.23650920 , 2.51162816 , 2.81318399 , 3.13141600 , 3.44063921 , 3.74119470 , 4.02673609 , 4.29306481 , 4.53806140 , 4.76141300 , 4.96426214 , 5.14884295 , 5.31814384 , 5.47561587 , 5.62668167 , 5.77248404 , 5.91725200 , 6.06569502 , 6.22271518 , 6.39309171 , 6.58160681 , 6.79197875 , 7.02725754 , 7.28835351 , 7.57549138 , 7.88788085 , 8.22380440 , 8.58075386 , 8.95559228 , 9.34472774 , 9.74429078 , 10.15030497 , 10.55702140 , 10.95996115 , 11.35489429 , 11.73804096 , 12.10626535 , 12.45720599 , 12.78902476 , 13.10117173 , 13.38459397 , 13.65241902 , 13.90619482 , 14.14749731 , 14.37793517 , 14.59913406 , 14.81271636 , 15.02028171 , 15.22338935 , 15.42354471 , 15.62218813 , 15.82068696 , 16.02042523 , 16.51209019 , 16.43147268 , 16.64865069 , 16.87578929 , 17.11471037 , 17.36706442 , 17.63427957 , 17.91751695 , 18.21763933 , 18.53518485 , 18.87035706 , 19.22575136 , 19.59817768 , 19.98636696 , 20.38859741 , 20.80279944 , 21.22663985 , 21.65720374 , 22.09156335 , 22.52884489 , 22.97009582 , 23.41421956 , 23.86005980 , 24.30643660 , 24.75217158 , 25.19610899 , 25.63713435 , 26.07419088 , 26.50629360 , 26.93254038 , 27.35212103 ] ,
    [ 10.00000000 , 0.00147929 , 0.02763013 , 0.11911421 , 0.27648107 , 0.47173876 , 0.67118469 , 0.85136255 , 1.00148835 , 1.12157353 , 1.21903349 , 1.30648626 , 1.39358529 , 1.49295935 , 1.61671538 , 1.77366966 , 1.96858795 , 2.20208982 , 2.47105633 , 2.76711247 , 3.08091994 , 3.38739104 , 3.68652941 , 3.97183294 , 4.23886833 , 4.48524088 , 4.71035370 , 4.91507947 , 5.10141163 , 5.27213521 , 5.43053826 , 5.58216284 , 5.72774970 , 5.87136795 , 6.01759989 , 6.17127024 , 6.33713909 , 6.52001679 , 6.72372477 , 6.95161116 , 7.20478211 , 7.48370681 , 7.78784700 , 8.11573056 , 8.46507629 , 8.83294713 , 9.21591726 , 9.61024471 , 10.01203972 , 10.41580717 , 10.81701040 , 11.21139640 , 11.59510363 , 11.96486314 , 12.31813398 , 12.65287962 , 12.96819564 , 13.25422417 , 13.52452991 , 13.78056347 , 14.02381876 , 14.25583704 , 14.47819014 , 14.69245893 , 14.90021250 , 15.10298935 , 15.30228262 , 15.49952778 , 15.69609355 , 15.89337548 , 16.39326667 , 16.29741587 , 16.50981654 , 16.73142973 , 16.96410480 , 17.20953920 , 17.46922644 , 17.74440988 , 18.03604924 , 18.34479193 , 18.67095945 , 19.01729152 , 19.38081157 , 19.76041759 , 20.15454281 , 20.56125823 , 20.97834901 , 21.40305530 , 21.83236614 , 22.26482470 , 22.70182268 , 23.14226144 , 23.58498015 , 24.02879126 , 24.47250520 , 24.91495098 , 25.35499461 , 25.79155544 , 26.22362037 , 26.65025530 , 27.07061454 ] ,

                ]
                )

    return dbase
    # fmt:on


##############################################################################


def f_hdf5_simple_read(self, a_file, a_dataset):
    xfp = h5py.File(a_file, "r")
    xxx = xfp.get(a_dataset)[()]
    xfp.close()
    return xxx


##############################################################################


def f_h5_out2in(src, dest, *args):

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
