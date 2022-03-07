import numpy as np
import h5py
from libpyvinyl.BaseFormat import BaseFormat
from .WavefrontData import WavefrontData


class WPGFormat(BaseFormat):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def data_type():
        """Return the DataClass for which this FormatClass is working"""
        return WavefrontData

    @classmethod
    def format_register(self):
        key = "WPG"
        desciption = "WPG format for WavefrontData"
        file_extension = ".h5"
        read_kwargs = [""]
        write_kwargs = [""]
        return self._create_format_register(
            key, desciption, file_extension, read_kwargs, write_kwargs
        )

    @staticmethod
    def direct_convert_formats():
        # Assume the format can be converted directly to the formats supported by these classes:
        # AFormat, BFormat
        # Redefine this `direct_convert_formats` for a concrete format class
        return []

    @classmethod
    def read(cls, filename: str) -> dict:
        """Read the data from the file with the `filename` to a dictionary."""
        # Reference : https://github.com/LUME-SIMEX/openPMD-wavefront/blob/master/scripts/wpg_to_opmd.py
        data_dict = {}
        with h5py.File(filename, "r") as h5:
            Ex = h5["data/arrEhor"][:, :, :, 0] + 1j * h5["data/arrEhor"][:, :, :, 1]
            Ey = h5["data/arrEver"][:, :, :, 0] + 1j * h5["data/arrEver"][:, :, :, 1]
            assert Ex.shape == Ey.shape
            data_dict["electricField"] = {}
            data_dict["electricField"]["x"] = Ex
            data_dict["electricField"]["y"] = Ey
            assert Ex.shape[0] == h5["params/Mesh/nx"][()]
            assert Ex.shape[1] == h5["params/Mesh/ny"][()]
            assert Ex.shape[2] == h5["params/Mesh/nSlices"][()]

            data_dict["zCoordinate"] = h5["params/Mesh/zCoord"][()]
            data_dict["radiusOfCurvatureX"] = h5["params/Rx"][()]
            data_dict["radiusOfCurvatureY"] = h5["params/Ry"][()]
            data_dict["deltaRadiusOfCurvatureX"] = h5["params/dRx"][()]
            data_dict["deltaRadiusOfCurvatureY"] = h5["params/dRy"][()]
            data_dict["photonEnergy"] = h5["params/photonEnergy"][()]  # eV
            data_dict["temporalDomain"] = str(h5["params/wDomain"][()])
            data_dict["spatialDomain"] = str(h5["params/wSpace"][()])
            data_dict["timeMin"] = h5["params/Mesh/sliceMin"][()]
            data_dict["timeMax"] = h5["params/Mesh/sliceMax"][()]
            data_dict["gridxMax"] = h5["params/Mesh/xMax"][()]
            data_dict["gridxMin"] = h5["params/Mesh/xMin"][()]
            data_dict["gridyMax"] = h5["params/Mesh/yMax"][()]
            data_dict["gridyMin"] = h5["params/Mesh/yMin"][()]
            horizontalBaseVector = (
                h5["/params/Mesh/hvx"][()],
                h5["/params/Mesh/hvy"][()],
                h5["/params/Mesh/hvz"][()],
            )
            normalBaseVector = (
                h5["/params/Mesh/nvx"][()],
                h5["/params/Mesh/nvy"][()],
                h5["/params/Mesh/nvz"][()],
            )
            data_dict["horizontalBaseVector"] = np.array(horizontalBaseVector)
            data_dict["normalBaseVector"] = np.array(normalBaseVector)

        return data_dict

    @classmethod
    def write(cls, object: WavefrontData, filename: str, key: str = None):
        """Save the data with the `filename`."""
        data_dict = object.get_data()
        with h5py.File(filename, "w") as h5:
            Ex = data_dict["electricField"]["x"]
            Ey = data_dict["electricField"]["y"]
            Ehor_shape = Ex.shape + (2,)
            Ever_shape = Ey.shape + (2,)
            arrEhor = np.empty(Ehor_shape)
            arrEhor[:, :, :, 0] = Ex.real
            arrEhor[:, :, :, 1] = Ex.imag
            arrEver = np.empty(Ever_shape)
            arrEver[:, :, :, 0] = Ey.real
            arrEver[:, :, :, 1] = Ey.imag
            data_grp = h5.create_group("data")
            data_grp["arrEhor"] = arrEhor
            data_grp["arrEver"] = arrEver

            params_grp = h5.create_group("params")
            params_grp["photonEnergy"] = data_dict["photonEnergy"]
            params_grp["wDomain"] = data_dict["temporalDomain"]
            params_grp["wSpace"] = data_dict["spatialDomain"]
            params_grp["Rx"] = data_dict["radiusOfCurvatureX"]
            params_grp["Ry"] = data_dict["radiusOfCurvatureY"]
            params_grp["dRx"] = data_dict["deltaRadiusOfCurvatureX"]
            params_grp["dRy"] = data_dict["deltaRadiusOfCurvatureY"]

            mesh_grp = params_grp.create_group("Mesh")
            mesh_grp["zCoord"] = data_dict["zCoordinate"]
            mesh_grp["xMax"] = data_dict["gridxMax"]
            mesh_grp["xMin"] = data_dict["gridxMin"]
            mesh_grp["yMin"] = data_dict["gridyMin"]
            mesh_grp["yMax"] = data_dict["gridyMax"]
            mesh_grp["sliceMax"] = data_dict["timeMax"]
            mesh_grp["sliceMin"] = data_dict["timeMin"]
            mesh_grp["hvx"] = data_dict["horizontalBaseVector"][0]
            mesh_grp["hvy"] = data_dict["horizontalBaseVector"][1]
            mesh_grp["hvz"] = data_dict["horizontalBaseVector"][2]
            mesh_grp["nvx"] = data_dict["normalBaseVector"][0]
            mesh_grp["nvy"] = data_dict["normalBaseVector"][1]
            mesh_grp["nvz"] = data_dict["normalBaseVector"][2]
            mesh_grp["nx"] = data_dict["electricField"]["x"].shape[0]
            mesh_grp["ny"] = data_dict["electricField"]["x"].shape[1]
            mesh_grp["nSlices"] = data_dict["electricField"]["x"].shape[2]

            info_grp = h5.create_group("info")
            info_grp["package_version"] = "Written by SimEx"

        if key is None:
            original_key = object.key
            key = original_key + "_to_WPGFormat"
        return object.from_file(filename, cls, key)
