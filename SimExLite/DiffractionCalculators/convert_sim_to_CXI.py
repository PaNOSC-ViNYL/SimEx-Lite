#!/usr/bin/env python3
# Copyright (C) 2022 Oleksii Turkot, Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
import argparse
import logging
import os
import re
from textwrap import dedent
import timeit

import numpy as np
import h5py

from cfelpyutils.geometry import load_crystfel_geometry
from cfelpyutils.geometry.crystfel_utils import CrystFELGeometry

log = logging.getLogger(__name__)
dtype_str = h5py.string_dtype(encoding="utf-8")


def get_sim_files(sim_folder: str, sim_file_re: str) -> dict:
    """Get a dictionary of simulated files in the folder with frame
    number as a key.

    Parameters
    ----------
    sim_folder : str
        Folder with simulated h5 files per frame.
    sim_file_re : str
        Regular expression representing simulated h5 files names with
        a single group corresponding to the file number, e.g.:
        r"diffr_out.(\d+).h5"

    Returns
    -------
    dict
        Dictionary with frame numbers as keys and simulated h5 files
        names as values.
    """
    sim_files = {}
    for file in os.listdir(sim_folder):
        sim_match = re.match(sim_file_re, file)
        if sim_match is not None:
            sim_files[int(sim_match.group(1)) - 1] = file
    return dict(sorted(sim_files.items()))


def check_n_panels(geom_sim: CrystFELGeometry, geom_vds: CrystFELGeometry) -> None:
    """Check consistency in number of panels between geometries for
    simulation and VDS-type data.

    Parameters
    ----------
    geom_sim : CrystFELGeometry
        CrystFELGeometry object for simulated geometry.
    geom_vds : CrystFELGeometry
        CrystFELGeometry object for VDS-type geometry.
    """

    n_panels_sim = len(geom_sim.detector["panels"])
    n_panels_vds = len(geom_vds.detector["panels"])
    if n_panels_sim == n_panels_vds:
        log.info("Check consistency in number of panels - OK.")
    else:
        log.error(
            f"Inconsistent number of panels - {n_panels_sim} in simulation "
            f"and {n_panels_vds} in VDS geometry files."
        )
        exit(1)


def estimate_dims_id(dims: list) -> dict:
    """Estimate ids for 'frame', 'panel', 'ss' and 'fs' dimensions from
    the geometry dimensions list.

    Parameters
    ----------
    dims : list
        List of the dimensions as in the CrystFEL geometry file.

    Returns
    -------
    dict
        Dictionary of dimensions ids in the form:
            {'dimension_name': {'id': 'dimension_id'}}

    Raises
    ------
    RuntimeError
        In case any dimension does not correspond to 'frame', 'panel',
        'ss' or 'fs'.
    """
    dims_id = {}
    for dim_id, dim_name in enumerate(dims):
        if dim_name == "%":
            dims_id["frame"] = {"id": dim_id}
        elif dim_name in ["ss", "fs"]:
            dims_id[dim_name] = {"id": dim_id}
        elif isinstance(dim_name, int):
            dims_id["panel"] = {"id": dim_id}
        else:
            raise RuntimeError(f"Could not identify dimension '{dim_name}' in {dims}.")
    return dims_id


def get_dims_data(geom: CrystFELGeometry) -> dict:
    """Retrieve dimensions data from CrystFELGeometry object.

    Parameters
    ----------
    geom : CrystFELGeometry
        CrystFELGeometry object.

    Returns
    -------
    dict
        Dictionary of dimensions by name in the form:
        {'dimension_name': {
            'id': 'dimension_id',
            'max_val': 'maximum_value'}
        }
    """
    first_panel = next(iter(geom.detector["panels"].keys()))
    dims = geom.detector["panels"][first_panel]["dim_structure"]
    dims_data = estimate_dims_id(dims)
    for dim_name in dims_data:
        dims_data[dim_name]["max_val"] = -1

    for panel in geom.detector["panels"]:
        geom_panel = geom.detector["panels"][panel]
        for dim_name in dims_data:
            if dim_name == "frame":
                continue
            elif dim_name in ["ss", "fs"]:
                par_value = geom_panel[f"orig_max_{dim_name}"]
            elif dim_name == "panel":
                dim_id = dims_data[dim_name]["id"]
                par_value = geom_panel["dim_structure"][dim_id]
            curr_max = dims_data[dim_name]["max_val"]
            dims_data[dim_name]["max_val"] = max(par_value, curr_max)
    return dims_data


def check_dims_match(dims_sim: dict, dims_vds: dict) -> None:
    """Check consistency in 'ss' and 'fs' dimensions between simulation
    and VDS-type geometries.

    Parameters
    ----------
    dims_sim : dict
        Dictionary of dimensions by name from simulation geometry.
    dims_vds : dict
        Dictionary of dimensions by name from VDS-type geometry.
    """
    match_fs = dims_sim["fs"]["max_val"] == dims_vds["fs"]["max_val"]
    conv_ss_vds = (dims_vds["panel"]["max_val"] + 1) * (
        dims_vds["ss"]["max_val"] + 1
    ) - 1
    match_ss = dims_sim["ss"]["max_val"] == conv_ss_vds
    if match_fs and match_ss:
        log.info("Check consistency in fs and ss dimensions - OK.")
    else:
        log.error(
            f"Inconsistent dimensions in simulation: {dims_sim} and "
            f"VDS: {dims_vds} geometry files."
        )
        exit(1)


def transform_dims_by_id(dims_data: dict) -> dict:
    """_summary_

    Parameters
    ----------
    dims_data : dict
        Dictionary of dimensions by name in the form:
        {'dimension_name': {
            'id': 'dimension_id',
            'max_val': 'maximum_value'}
        }

    Returns
    -------
    dict
        Dictionary of dimensions by id in the form:
        {'dimension_id': {
            'name': 'dimension_name',
            'max_val': 'maximum_value'}
        }
    """
    dims_by_id = {}
    for dim_name in dims_data:
        dim_id = dims_data[dim_name]["id"]
        dims_by_id[dim_id] = {}
        dims_by_id[dim_id]["name"] = dim_name
        dims_by_id[dim_id]["max_val"] = dims_data[dim_name]["max_val"]
    return dict(sorted(dims_by_id.items()))


def get_vds_shapes(dims_id_vds: dict, n_frames: int) -> dict:
    """Retrieve a dictionary of shapes for VDS data array, chunk size,
    panel and frame identifier.

    Parameters
    ----------
    dims_id_vds : dict
        Dictionary of dimensions by id.
    n_frames : int
        Total number of frames in the simulation.

    Returns
    -------
    dict
        Dictionary of arrays shapes.
    """
    shapes_vds = {"data": [], "chunk": [], "panel": [], "identifier": []}
    for dim_val in dims_id_vds.values():
        if dim_val["name"] == "frame":
            shapes_vds["data"].append(n_frames)
            shapes_vds["chunk"].append(1)
        else:
            shapes_vds["data"].append(dim_val["max_val"] + 1)
            shapes_vds["chunk"].append(dim_val["max_val"] + 1)
            if dim_val["name"] != "panel":
                shapes_vds["panel"].append(dim_val["max_val"] + 1)
    shapes_vds["data"] = tuple(shapes_vds["data"])
    shapes_vds["chunk"] = tuple(shapes_vds["chunk"])
    shapes_vds["panel"] = tuple(shapes_vds["panel"])
    shapes_vds["identifier"] = (n_frames,)
    return shapes_vds


def get_dims_slice(dims_id_data: dict, dict_slice: dict) -> tuple:
    """Generate dimensions slice from the specified dictionary of ranges.

    Parameters
    ----------
    dims_id_data : dict
        Dictionary of dimensions by id.
    dict_slice : dict
        Dictionary of slices for (some of) dimensions with dimension names
        as keys.

    Returns
    -------
    tuple
        Multidimensional slice.
    """
    dims_slice = []
    for dim_val in dims_id_data.values():
        if dim_val["name"] not in dict_slice:
            dims_slice.append(np.s_[:])
        else:
            dims_slice.append(dict_slice[dim_val["name"]])
    return tuple(dims_slice)


def convert_to_CXI(
    geom_sim_path,
    geom_vds_path,
    sim_folder,
    sim_output,
    sim_files_re,
    noise_base,
    noise_std,
):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    geom_sim = load_crystfel_geometry(geom_sim_path)
    geom_vds = load_crystfel_geometry(geom_vds_path)
    check_n_panels(geom_sim, geom_vds)

    dims_name_sim = get_dims_data(geom_sim)
    dims_name_vds = get_dims_data(geom_vds)
    check_dims_match(dims_name_sim, dims_name_vds)
    dims_id_sim = transform_dims_by_id(dims_name_sim)
    dims_id_vds = transform_dims_by_id(dims_name_vds)

    det_path = "/entry_1/instrument_1/detector_1"
    exp_id_path = "/entry_1/experiment_identifier"
    mask_good = geom_vds.detector["mask_good"]
    mask_bad = geom_vds.detector["mask_bad"]
    shape_ss = dims_name_vds["ss"]["max_val"] + 1
    ssfs_order_sim = dims_name_sim["ss"]["id"] < dims_name_sim["fs"]["id"]
    ssfs_order_vds = dims_name_vds["ss"]["id"] < dims_name_vds["fs"]["id"]
    same_ssfs_order = ssfs_order_sim == ssfs_order_vds

    # import pdb; pdb.set_trace()
    sim_files = get_sim_files(sim_folder, sim_files_re)
    n_frames = max(list(sim_files)) + 1
    shapes_vds = get_vds_shapes(dims_id_vds, n_frames)

    start = timeit.default_timer()
    with h5py.File(sim_output, "w") as h5_w:
        h5_w.create_dataset(
            f"{det_path}/data",
            shapes_vds["data"],
            dtype="float32",
            fillvalue=0,
            chunks=shapes_vds["chunk"],
        )
        h5_w.create_dataset(
            f"{det_path}/mask",
            shapes_vds["data"],
            dtype="uint32",
            fillvalue=mask_bad,
            chunks=shapes_vds["chunk"],
        )
        h5_w["/entry_1/data_1"] = h5py.SoftLink(det_path)
        h5_w.create_dataset(exp_id_path, shapes_vds["identifier"], dtype=dtype_str)
        h5_w[f"{det_path}/experiment_identifier"] = h5py.SoftLink(exp_id_path)

        for i_frame in range(n_frames):
            h5_w[exp_id_path][i_frame] = f"115105109:{i_frame}"
            slice_mask = get_dims_slice(dims_id_vds, {"frame": i_frame})
            if i_frame in sim_files:
                h5_w[f"{det_path}/mask"][slice_mask] = np.full(
                    shapes_vds["chunk"], mask_good
                )
                for i_pnl in range(dims_name_vds["panel"]["max_val"] + 1):
                    slice_vds = get_dims_slice(
                        dims_id_vds, {"frame": i_frame, "panel": i_pnl}
                    )
                    slice_sim = get_dims_slice(
                        dims_id_sim,
                        {
                            "frame": 0,
                            "ss": np.s_[(shape_ss * i_pnl) : (shape_ss * (i_pnl + 1))],
                        },
                    )
                    noise_val = (
                        noise_base + np.random.randn(*shapes_vds["panel"]) * noise_std
                    )

                    with h5py.File(f"{sim_folder}/{sim_files[i_frame]}", "r") as h5_r:
                        if same_ssfs_order:
                            h5_w[f"{det_path}/data"][slice_vds] = (
                                h5_r["/data/data"][slice_sim] + noise_val
                            )
                        else:
                            h5_w[f"{det_path}/data"][slice_vds] = (
                                h5_r["/data/data"][slice_sim].transpose() + noise_val
                            )
    exec_time = timeit.default_timer() - start
    log.info(f"Wrote {n_frames} frames in {exec_time:.2f}s.")


def main(argv=None):

    example = dedent(
        """
        Example:

            ./convert_sim_data.py agipd_sim.geom agipd_vds.geom \\
                /gpfs/exfel/data/user/turkot/store/simex/diffr_03 \\
                -r 'diffr_out.(\\d+).h5' -o sim_vds.cxi --noise 100 5
    """
    )
    ap = argparse.ArgumentParser(
        "convert_sim_data.py",
        epilog=example,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Convert SFX data simulated with simex into VDS format.",
    )
    ap.add_argument("geom_sim", help="Path to the simulated geometry file.")
    ap.add_argument("geom_vds", help="Path to the VDS-type geometry file.")
    ap.add_argument("sim_folder", help="Path to the folder with simulated h5 files.")
    ap.add_argument(
        "-re",
        "--sim-re",
        default=r"diffr_out.(\d+).h5",
        help="Regular expression representing simulated h5 files names with "
        "a single group corresponding to the file number.",
    )
    ap.add_argument(
        "-o",
        "--output-cxi",
        default="sim_vds.cxi",
        help="Filename for the output cxi file.",
    )
    ap.add_argument(
        "--noise",
        nargs=2,
        type=int,
        default=(0, 0),
        help="Base value and standard deviation of the artificial noise "
        "to be added.",
    )
    args = ap.parse_args(argv)

    geom_sim_path = args.geom_sim
    geom_vds_path = args.geom_vds
    sim_folder = args.sim_folder
    sim_output = args.output_cxi
    sim_files_re = args.sim_re
    noise_base = args.noise[0]
    noise_std = args.noise[1]

    convert_to_CXI(
        geom_sim_path,
        geom_vds_path,
        sim_folder,
        sim_output,
        sim_files_re,
        noise_base,
        noise_std,
    )


if __name__ == "__main__":
    main()
