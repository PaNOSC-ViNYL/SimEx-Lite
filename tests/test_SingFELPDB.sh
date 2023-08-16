#!/bin/bash
#SBATCH --job-name=diffr
##SBATCH --partition=exfel-theory
#SBATCH --partition=exfel
##SBATCH --partition=exfel-spb
#SBATCH --nodes=4
#SBATCH --time=2-01:00:00
#SBATCH --output=log.diffr-%j


OUT_DIR=diffr
mkdir -p $OUT_DIR
/home/juncheng/GPFS/exfel/data/user/juncheng/SimExLite/SimExLite/DiffractionCalculators/SingFELPDB.py \
    --inputFile testFiles/2nip.pdb  \
    --outputDir diffr  \
	--uniformRotation 1 \
    --geomFile ./SingFELPDB_test.geom   \
    --beamFile ./SingFELPDB_test.beam   \
    --numDP 20

python /gpfs/exfel/data/user/juncheng/hydratedProject/src/program/externalLink.py $OUT_DIR