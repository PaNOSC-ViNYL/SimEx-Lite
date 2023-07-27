#!/usr/bin/env python3

import argparse
import copy
import os
import sys
from tqdm import tqdm

from pysingfel.FileIO import saveAsDiffrOutFile, prepH5
from pysingfel.beam import Beam
from pysingfel.detector import Detector
from pysingfel.diffraction import calculate_molecularFormFactorSq
from pysingfel.particle import Particle
from pysingfel.radiationDamage import generateRotations, rotateParticle
from pysingfel.toolbox import convert_to_poisson


def parse_input(args):
    """
    Parse the input command arguments and return a dict containing all simulation parameters.
    """

    def ParseBoolean(b):
        # Handle different possible Boolean types.
        if b is None or b == "None":
            return b
        if b == False or b == True:
            return b
        b = b.strip()
        if len(b) < 1:
            raise ValueError("Cannot parse empty string into boolean.")
        b = b[0].lower()
        if b == "t" or b == "y" or b == "1":
            return True
        if b == "f" or b == "n" or b == "0":
            return False
        raise ValueError("Cannot parse string into boolean.")

    # fmt: off
    # Instantiate the parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputFile', help='Input PDF file')
    parser.add_argument('--outputDir', help='Output directory for saving diffraction')
    parser.add_argument('--beamFile', help='Beam file defining X-ray beam')
    parser.add_argument('--geomFile', help='Geometry file defining diffraction geometry')
    parser.add_argument('--rotationAxis', default='xyz', help='Euler rotation convention')
    parser.add_argument('--orientation',nargs='+', type=float, help='Specify the quternion r i j k of '
                        'each diffraction pattern. It overrides --unifromRotation')
    parser.add_argument('--uniformRotation', type=ParseBoolean,
                        help='If 1, rotates the sample uniformly in SO(3),\
                                if 0 random orientation in SO(3),\
                                if None (omitted): no orientation.')
    parser.add_argument('--numDP', type=int, help='Number of diffraction patterns per PMI file')
    # fmt: on

    # convert argparse to dict
    return vars(parser.parse_args(args))


def main(parameters):
    from mpi4py import MPI

    # Initialize MPI
    mpi_comm = MPI.COMM_WORLD
    mpi_rank = mpi_comm.Get_rank()
    mpi_size = mpi_comm.Get_size()

    # parameters
    numDP = int(parameters["numDP"])
    input_fn = parameters["inputFile"]
    output_dir = parameters["outputDir"]
    uniform_rotation = parameters["uniformRotation"]
    beamFile = parameters["beamFile"]
    geomFile = parameters["geomFile"]
    orientation = parameters["orientation"]

    # Perform common work on all cores.
    initial_particle = Particle()
    initial_particle.readPDB(input_fn, ff="WK")

    # Generate rotations.
    quaternions = generateRotations(uniform_rotation, "xyz", numDP, orientation)

    detector = Detector(geomFile)
    beam = Beam(beamFile)
    detector.init_dp(beam)

    # Determine which patterns to run on which core.
    number_of_patterns_per_core = numDP // mpi_size
    # Remainder of the division.
    remainder = numDP % mpi_size
    # Pattern indices
    pattern_indices = list(range(numDP))

    # Distribute patterns over cores.
    rank_indices = pattern_indices[
        mpi_rank
        * number_of_patterns_per_core : (mpi_rank + 1)
        * number_of_patterns_per_core
    ]
    # Distribute remainder
    if mpi_rank < remainder:
        rank_indices.append(
            pattern_indices[mpi_size * number_of_patterns_per_core + mpi_rank]
        )
        # Setup the output file.
    outputName = (
        output_dir + "/diffr_out_" + "{0:07}".format(mpi_comm.Get_rank() + 1) + ".h5"
    )

    if os.path.exists(outputName):
        os.remove(outputName)

    output_is_ready = False
    # Loop over assigned tasks
    if mpi_rank == 0:
        pbar = tqdm(total=100)

    for ii, pattern_index in enumerate(rank_indices):
        # Setup the output hdf5 file if not already done.
        if not output_is_ready:
            prepH5(outputName)
            output_is_ready = True

        # Make local copy of the sample.
        particle = copy.deepcopy(initial_particle)

        # Rotate particle.
        quaternion = quaternions[pattern_index, :]
        rotateParticle(quaternion, particle)

        # Calculate the diffraction intensity.
        detector_intensity = calculate_molecularFormFactorSq(particle, detector)

        # Correct for solid angle
        detector_intensity *= detector.solidAngle

        # Correct for polarization
        detector_intensity *= detector.PolarCorr

        # Multiply by photon fluence.
        detector_intensity *= beam.get_photonsPerPulsePerArea()

        # Poissonize.
        detector_counts = convert_to_poisson(detector_intensity)

        # Save to h5 file.
        saveAsDiffrOutFile(
            outputName,
            None,
            pattern_index,
            detector_counts,
            detector_intensity,
            quaternion,
            detector,
            beam,
        )

        del particle
        if mpi_rank == 0:
            pbar.update(1.0 / len(rank_indices) * 100)
    mpi_comm.Barrier()
    if mpi_rank == 0:
        pbar.close()

    return 0


if __name__ == "__main__":
    parameters = parse_input(sys.argv[1:])
    main(parameters=parameters)
