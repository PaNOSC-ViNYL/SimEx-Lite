ARG SIMEX_LITE_VERSION=233190d4c68c8454eef274e3d0efb2d3584277e8
ARG CCP4_VERSION=8.0.0
ARG CRYSTFEL_VERSION=0.10.2
ARG MMDB2_VERSION=2.0.22
ARG MOSFLM_VERSION="ver740"
ARG PYSINGFEL_VERSION=ff535c0323bd03af1b09e56c770334b6a89cfd1f
ARG WPG_VERSION=1f00e866a6f05f48658ec1892cba6f346123f4da


FROM alpine:3.19.1 AS build-mosflm

ARG MOSFLM_VERSION

WORKDIR /src

ADD https://www.mrc-lmb.cam.ac.uk/mosflm/mosflm/$MOSFLM_VERSION/pre-built/mosflm-linux-64-noX11.zip /src/mosflm.zip

RUN apk add --no-cache unzip && \
    unzip /src/mosflm.zip && \
    mkdir -p /build/bin && \
    mv mosflm-linux-64-noX11 /build/bin/mosflm


FROM ubuntu:23.10 AS build-crystfel

ARG CRYSTFEL_VERSION

WORKDIR /src

RUN apt update && apt install -y \
    bison \
    build-essential \
    cmake \
    curl \
    flex \
    gfortran \
    git \
    libcairo2-dev \
    libeigen3-dev \
    libfftw3-dev \
    libgdk-pixbuf2.0-dev \
    libgsl-dev \
    libgtk-3-dev \
    libhdf5-dev \
    libmsgpack-dev \
    libncurses-dev \
    libpango1.0-dev \
    libpng-dev \
    libtiff5-dev \
    libzmq3-dev \
    ninja-build \
    pkg-config \
    python3 \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    unzip \
    wget && \
    apt clean && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache/pip \
  python3 -m pip install --break-system-packages meson

# Use 0.10.2 - recent dev versions remove pattern_sim which is used by simex-lite
#   - https://gitlab.desy.de/thomas.white/crystfel/-/blob/3a62ae8eb067baacc12bb23404211275c3ed3d38/ChangeLog#L7
ADD https://gitlab.desy.de/thomas.white/crystfel.git#$CRYSTFEL_VERSION /src

COPY --link --from=build-mosflm /build/bin/mosflm /build/bin/mosflm

RUN meson build -Dprefix=/build
RUN ninja -C build
RUN ninja -C build test
RUN ninja -C build install
RUN cp /src/scripts/gen-sfs /build/bin/gen-sfs  # required by simex-lite


FROM ubuntu:23.10 AS build-ccp4

ARG CCP4_VERSION
ARG MMDB2_VERSION

RUN apt update && apt install -y \
  bison \
  build-essential \
  flex \
  gfortran \
  m4 \
  yasm \
  && \
  apt clean && rm -rf /var/lib/apt/lists/*

ADD https://ftp.ccp4.ac.uk/opensource/libccp4-$CCP4_VERSION.tar.gz /src/

WORKDIR /src

RUN tar -xzf libccp4-$CCP4_VERSION.tar.gz && \
    cd libccp4-$CCP4_VERSION && \
    ./configure --prefix /build && \
    make && \
    make install

ADD https://ftp.ccp4.ac.uk/opensource/mmdb2-$MMDB2_VERSION.tar.gz /src/

RUN tar -xzf mmdb2-$MMDB2_VERSION.tar.gz && \
    cd mmdb2-$MMDB2_VERSION && \
    ./configure --prefix /build && \
    make && \
    make install


FROM python:3.9 AS build-wpg

ARG WPG_VERSION

WORKDIR /src

RUN apt update && apt install -y \
    build-essential \
    unzip \
    wget \
    && \
    apt clean && rm -rf /var/lib/apt/lists/*

ADD --link https://github.com/JunCEEE/WPG.git#$WPG_VERSION /src
ADD --link https://github.com/SergeyYakubov/SRW/archive/openmp_memoryfix.zip /src/build/sources/srw.zip

RUN make

# Use pyproject toml to make building wheels easier, include .so files, include deps
# TODO: PR to upstream `pyproject.toml` file?
RUN rm -f ./setup.py && mkdir src && mv wpg ./src/wpg && mv s2e ./src/s2e && printf "[build-system] \n\
requires = ['setuptools', 'wheel'] \n\
build-backend = 'setuptools.build_meta' \n\
[project] \n\
name = 'wpg' \n\
version = '2019.12' \n\
dependencies =[ \n\
  'numpy >= 1.9', \n\
  'scipy', \n\
  'matplotlib', \n\
  'h5py', \n\
  'requests', \n\
] \n\
[tool.setuptools.packages.find] \n\
where = ['src'] \n\
[tool.setuptools.package-data] \n\
wpg = ['srw/*.so']" > pyproject.toml

RUN --mount=type=cache,target=/root/.cache/pip \
  python3 -m pip install build && python3 -m build && mv dist /dist


FROM python:3.9-alpine AS build-pysingfel

ARG PYSINGFEL_VERSION

WORKDIR /src

ADD https://github.com/JunCEEE/pysingfel.git#$PYSINGFEL_VERSION /src

RUN --mount=type=cache,target=/root/.cache/pip \
  python3 -m pip install build && python3 -m build && mv dist /dist


FROM python:3.9-alpine AS build-simex-lite

ARG SIMEX_LITE_VERSION

WORKDIR /src

ADD https://github.com/PaNOSC-ViNYL/SimEx-Lite.git#$SIMEX_LITE_VERSION /src

RUN --mount=type=cache,target=/root/.cache/pip \
  python3 -m pip install build && python3 -m build && mv dist /dist


# Use 3.9, 3.10+ has some changes that are not compatible with SimEx-Lite
# TODO: PR to update SimEx-Lite for 3.10+?
FROM python:3.9

ARG SIMEX_LITE_VERSION
ARG CCP4_VERSION
ARG CRYSTFEL_VERSION
ARG MMDB2_VERSION
ARG MOSFLM_VERSION
ARG PYSINGFEL_VERSION
ARG WPG_VERSION

LABEL simex_lite.version="$SIMEX_LITE_VERSION"

LABEL simex_lite.deps.ccp4.version="$CCP4_version" \
      simex_lite.deps.crystfel.version="$CRYSTFEL_VERSION" \
      simex_lite.deps.mmdb2.version="$MMDB2_VERSION" \
      simex_lite.deps.mosflm.version="MOSFLM_VERSION" \
      simex_lite.deps.pysingfel.version="$PYSINGFEL_VERSION" \
      simex_lite.deps.wpg.version="$WPG_VERSION"

# Crystfel requirements
RUN apt-get update && apt-get install -y \
  libcairo2 \
  libfftw3-double3 \
  libgdk-pixbuf2.0 \
  libgslcblas0 \
  libgtk-3-0 \
  libhdf5-103 \
  libmsgpackc2 \
  libncurses6 \
  libpango1.0 \
  libpng16-16 \
  libtiff5-dev \
  libzmq5 \
  mpich && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --link --from=build-crystfel /build /usr/local
COPY --link --from=build-wpg /dist /dist
COPY --link --from=build-pysingfel /dist /dist
COPY --link --from=build-simex-lite /dist /dist

WORKDIR /src

ADD --link https://github.com/PaNOSC-ViNYL/SimEx-Lite.git#$SIMEX_LITE_VERSION /src

RUN --mount=type=cache,target=/root/.cache/pip \
  python3 -m pip install --break-system-packages --find-links /dist pysingfel wpg SimEx-Lite && \
  python3 -m pip install -r /src/requirements_dev.txt && \
  python3 -m pip install jupyter jupyterlab ipykernel && \
  python3 -m pip install -e /src

