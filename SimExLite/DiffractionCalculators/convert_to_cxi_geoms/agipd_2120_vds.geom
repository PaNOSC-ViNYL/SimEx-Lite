; Adapted to virtual dataset dimensions in CXI file, 21 November 2018
; OY: Use ONLY geoptimiser from CrystFEL > 0.7.0
; OY: I think this is a very well optimized geometry!
; Optimized panel offsets can be found at the end of the file
; Optimized panel offsets can be found at the end of the file
; Optimized panel offsets can be found at the end of the file
; Optimized panel offsets can be found at the end of the file
; Optimized panel offsets can be found at the end of the file
; Optimized panel offsets can be found at the end of the file
; Optimized panel offsets can be found at the end of the file
; Optimized panel offsets can be found at the end of the file
; Optimized panel offsets can be found at the end of the file
; Optimized panel offsets can be found at the end of the file
; Manually optimized with hdfsee
; Optimized panel offsets can be found at the end of the file
; Optimized panel offsets can be found at the end of the file
; Optimized panel offsets can be found at the end of the file
; Optimized panel offsets can be found at the end of the file
; Optimized panel offsets can be found at the end of the file
; Optimized panel offsets can be found at the end of the file
; Optimized panel offsets can be found at the end of the file
; Optimized panel offsets can be found at the end of the file
; Optimized panel offsets can be found at the end of the file
; Optimized panel offsets can be found at the end of the file
; Optimized panel offsets can be found at the end of the file
; Optimized panel offsets can be found at the end of the file
; Optimized panel offsets can be found at the end of the file
; Manually optimized with hdfsee
; Optimized panel offsets can be found at the end of the file
; Manually optimized with hdfsee
; Optimized panel offsets can be found at the end of the file
; Manually optimized with hdfsee
; Camera length from LiTiO calibration
; Manually optimized with hdfsee
; Now all distances between panels is 5.8mm (29 pixels)
; OY: ACHTUNG! Orientation of the 2 halves of the detector might be wrong!
; A bit changed by OY: now 128 panels, rigid groups, bad lines to mask double pixels.
; Fixed errors noticed by Oleksandr
; Beginning of an AGIPD geometry construction by Helen Ginn on Thursday before beam time.
; Global panel positions not guesses
; Local positioning largely - but not entirely - guesses
; fast and slow scan directions have the potential to be accurate.

data = /entry_1/data_1/data
mask = /entry_1/data_1/mask
dim0 = %                      ; placeholder: this is the running frame# dimension

mask_good = 0x0
mask_bad = 0xffff

adu_per_eV = 0.0075  ; no idea
clen = 0.1185
;+clen = 0.1248
;clen = 0.164 ;for ADDU=-800
;19.57mm per 100ADDU
photon_energy = 9300
res = 5000 ; 200 um pixels

rigid_group_q0 = p0a0,p0a1,p0a2,p0a3,p0a4,p0a5,p0a6,p0a7,p1a0,p1a1,p1a2,p1a3,p1a4,p1a5,p1a6,p1a7,p2a0,p2a1,p2a2,p2a3,p2a4,p2a5,p2a6,p2a7,p3a0,p3a1,p3a2,p3a3,p3a4,p3a5,p3a6,p3a7
rigid_group_q1 = p4a0,p4a1,p4a2,p4a3,p4a4,p4a5,p4a6,p4a7,p5a0,p5a1,p5a2,p5a3,p5a4,p5a5,p5a6,p5a7,p6a0,p6a1,p6a2,p6a3,p6a4,p6a5,p6a6,p6a7,p7a0,p7a1,p7a2,p7a3,p7a4,p7a5,p7a6,p7a7
rigid_group_q2 = p8a0,p8a1,p8a2,p8a3,p8a4,p8a5,p8a6,p8a7,p9a0,p9a1,p9a2,p9a3,p9a4,p9a5,p9a6,p9a7,p10a0,p10a1,p10a2,p10a3,p10a4,p10a5,p10a6,p10a7,p11a0,p11a1,p11a2,p11a3,p11a4,p11a5,p11a6,p11a7
rigid_group_q3 = p12a0,p12a1,p12a2,p12a3,p12a4,p12a5,p12a6,p12a7,p13a0,p13a1,p13a2,p13a3,p13a4,p13a5,p13a6,p13a7,p14a0,p14a1,p14a2,p14a3,p14a4,p14a5,p14a6,p14a7,p15a0,p15a1,p15a2,p15a3,p15a4,p15a5,p15a6,p15a7

rigid_group_p0 = p0a0,p0a1,p0a2,p0a3,p0a4,p0a5,p0a6,p0a7
rigid_group_p1 = p1a0,p1a1,p1a2,p1a3,p1a4,p1a5,p1a6,p1a7
rigid_group_p2 = p2a0,p2a1,p2a2,p2a3,p2a4,p2a5,p2a6,p2a7
rigid_group_p3 = p3a0,p3a1,p3a2,p3a3,p3a4,p3a5,p3a6,p3a7
rigid_group_p4 = p4a0,p4a1,p4a2,p4a3,p4a4,p4a5,p4a6,p4a7
rigid_group_p5 = p5a0,p5a1,p5a2,p5a3,p5a4,p5a5,p5a6,p5a7
rigid_group_p6 = p6a0,p6a1,p6a2,p6a3,p6a4,p6a5,p6a6,p6a7
rigid_group_p7 = p7a0,p7a1,p7a2,p7a3,p7a4,p7a5,p7a6,p7a7
rigid_group_p8 = p8a0,p8a1,p8a2,p8a3,p8a4,p8a5,p8a6,p8a7
rigid_group_p9 = p9a0,p9a1,p9a2,p9a3,p9a4,p9a5,p9a6,p9a7
rigid_group_p10 = p10a0,p10a1,p10a2,p10a3,p10a4,p10a5,p10a6,p10a7
rigid_group_p11 = p11a0,p11a1,p11a2,p11a3,p11a4,p11a5,p11a6,p11a7
rigid_group_p12 = p12a0,p12a1,p12a2,p12a3,p12a4,p12a5,p12a6,p12a7
rigid_group_p13 = p13a0,p13a1,p13a2,p13a3,p13a4,p13a5,p13a6,p13a7
rigid_group_p14 = p14a0,p14a1,p14a2,p14a3,p14a4,p14a5,p14a6,p14a7
rigid_group_p15 = p15a0,p15a1,p15a2,p15a3,p15a4,p15a5,p15a6,p15a7

rigid_group_collection_quadrants = q0,q1,q2,q3
rigid_group_collection_asics = p0,p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12,p13,p14,p15


p0a0/dim1 = 0        ; panel number
p0a0/dim2 = ss       ; slow scan pixel direction within panel
p0a0/dim3 = fs       ; fast scan pixel direction within panel
p0a0/min_fs = 0
p0a0/min_ss = 0
p0a0/max_fs = 127
p0a0/max_ss = 63
p0a0/fs = -0.001328x -0.999995y
p0a0/ss = +0.999995x -0.001328y
p0a0/corner_x = -513.636000
p0a0/corner_y = 632.265000
p0a0/coffset = 0.001112

p0a1/dim1 = 0
p0a1/dim2 = ss
p0a1/dim3 = fs
p0a1/min_fs = 0
p0a1/min_ss = 64
p0a1/max_fs = 127
p0a1/max_ss = 127
p0a1/fs = -0.001328x -0.999995y
p0a1/ss = +0.999995x -0.001328y
p0a1/corner_x = -447.636000
p0a1/corner_y = 632.156000
p0a1/coffset = 0.001112

p0a2/dim1 = 0
p0a2/dim2 = ss
p0a2/dim3 = fs
p0a2/min_fs = 0
p0a2/min_ss = 128
p0a2/max_fs = 127
p0a2/max_ss = 191
p0a2/fs = -0.001328x -0.999995y
p0a2/ss = +0.999995x -0.001328y
p0a2/corner_x = -381.642000
p0a2/corner_y = 632.046000
p0a2/coffset = 0.001112

p0a3/dim1 = 0
p0a3/dim2 = ss
p0a3/dim3 = fs
p0a3/min_fs = 0
p0a3/min_ss = 192
p0a3/max_fs = 127
p0a3/max_ss = 255
p0a3/fs = -0.001328x -0.999995y
p0a3/ss = +0.999995x -0.001328y
p0a3/corner_x = -315.640000
p0a3/corner_y = 631.936000
p0a3/coffset = 0.001112

p0a4/dim1 = 0
p0a4/dim2 = ss
p0a4/dim3 = fs
p0a4/min_fs = 0
p0a4/min_ss = 256
p0a4/max_fs = 127
p0a4/max_ss = 319
p0a4/fs = -0.001328x -0.999995y
p0a4/ss = +0.999995x -0.001328y
p0a4/corner_x = -249.640000
p0a4/corner_y = 631.827000
p0a4/coffset = 0.001112

p0a5/dim1 = 0
p0a5/dim2 = ss
p0a5/dim3 = fs
p0a5/min_fs = 0
p0a5/min_ss = 320
p0a5/max_fs = 127
p0a5/max_ss = 383
p0a5/fs = -0.001328x -0.999995y
p0a5/ss = +0.999995x -0.001328y
p0a5/corner_x = -183.638000
p0a5/corner_y = 631.827000
p0a5/coffset = 0.001112

p0a6/dim1 = 0
p0a6/dim2 = ss
p0a6/dim3 = fs
p0a6/min_fs = 0
p0a6/min_ss = 384
p0a6/max_fs = 127
p0a6/max_ss = 447
p0a6/fs = -0.001328x -0.999995y
p0a6/ss = +0.999995x -0.001328y
p0a6/corner_x = -117.638000
p0a6/corner_y = 631.739000
p0a6/coffset = 0.001112

p0a7/dim1 = 0
p0a7/dim2 = ss
p0a7/dim3 = fs
p0a7/min_fs = 0
p0a7/min_ss = 448
p0a7/max_fs = 127
p0a7/max_ss = 511
p0a7/fs = -0.001328x -0.999995y
p0a7/ss = +0.999995x -0.001328y
p0a7/corner_x = -51.638300
p0a7/corner_y = 631.651000
p0a7/coffset = 0.001112

p1a0/dim1 = 1
p1a0/dim2 = ss
p1a0/dim3 = fs
p1a0/min_fs = 0
p1a0/min_ss = 0
p1a0/max_fs = 127
p1a0/max_ss = 63
p1a0/fs = -0.001977x -0.999998y
p1a0/ss = +0.999998x -0.001977y
p1a0/corner_x = -513.843000
p1a0/corner_y = 475.049000
p1a0/coffset = 0.000934

p1a1/dim1 = 1
p1a1/dim2 = ss
p1a1/dim3 = fs
p1a1/min_fs = 0
p1a1/min_ss = 64
p1a1/max_fs = 127
p1a1/max_ss = 127
p1a1/fs = -0.001977x -0.999998y
p1a1/ss = +0.999998x -0.001977y
p1a1/corner_x = -447.845000
p1a1/corner_y = 474.930000
p1a1/coffset = 0.000934

p1a2/dim1 = 1
p1a2/dim2 = ss
p1a2/dim3 = fs
p1a2/min_fs = 0
p1a2/min_ss = 128
p1a2/max_fs = 127
p1a2/max_ss = 191
p1a2/fs = -0.001977x -0.999998y
p1a2/ss = +0.999998x -0.001977y
p1a2/corner_x = -381.847000
p1a2/corner_y = 474.811000
p1a2/coffset = 0.000934

p1a3/dim1 = 1
p1a3/dim2 = ss
p1a3/dim3 = fs
p1a3/min_fs = 0
p1a3/min_ss = 192
p1a3/max_fs = 127
p1a3/max_ss = 255
p1a3/fs = -0.001977x -0.999998y
p1a3/ss = +0.999998x -0.001977y
p1a3/corner_x = -315.850000
p1a3/corner_y = 474.692000
p1a3/coffset = 0.000934

p1a4/dim1 = 1
p1a4/dim2 = ss
p1a4/dim3 = fs
p1a4/min_fs = 0
p1a4/min_ss = 256
p1a4/max_fs = 127
p1a4/max_ss = 319
p1a4/fs = -0.001977x -0.999998y
p1a4/ss = +0.999998x -0.001977y
p1a4/corner_x = -249.852000
p1a4/corner_y = 474.574000
p1a4/coffset = 0.000934

p1a5/dim1 = 1
p1a5/dim2 = ss
p1a5/dim3 = fs
p1a5/min_fs = 0
p1a5/min_ss = 320
p1a5/max_fs = 127
p1a5/max_ss = 383
p1a5/fs = -0.001977x -0.999998y
p1a5/ss = +0.999998x -0.001977y
p1a5/corner_x = -183.856000
p1a5/corner_y = 474.455000
p1a5/coffset = 0.000934

p1a6/dim1 = 1
p1a6/dim2 = ss
p1a6/dim3 = fs
p1a6/min_fs = 0
p1a6/min_ss = 384
p1a6/max_fs = 127
p1a6/max_ss = 447
p1a6/fs = -0.001977x -0.999998y
p1a6/ss = +0.999998x -0.001977y
p1a6/corner_x = -117.838000
p1a6/corner_y = 474.336000
p1a6/coffset = 0.000934

p1a7/dim1 = 1
p1a7/dim2 = ss
p1a7/dim3 = fs
p1a7/min_fs = 0
p1a7/min_ss = 448
p1a7/max_fs = 127
p1a7/max_ss = 511
p1a7/fs = -0.001977x -0.999998y
p1a7/ss = +0.999998x -0.001977y
p1a7/corner_x = -51.837000
p1a7/corner_y = 474.217000
p1a7/coffset = 0.000934

p2a0/dim1 = 2
p2a0/dim2 = ss
p2a0/dim3 = fs
p2a0/min_fs = 0
p2a0/min_ss = 0
p2a0/max_fs = 127
p2a0/max_ss = 63
p2a0/fs = -0.000961x -1.000001y
p2a0/ss = +1.000001x -0.000961y
p2a0/corner_x = -513.838000
p2a0/corner_y = 318.335000
p2a0/coffset = 0.000685

p2a1/dim1 = 2
p2a1/dim2 = ss
p2a1/dim3 = fs
p2a1/min_fs = 0
p2a1/min_ss = 64
p2a1/max_fs = 127
p2a1/max_ss = 127
p2a1/fs = -0.000961x -1.000001y
p2a1/ss = +1.000001x -0.000961y
p2a1/corner_x = -447.839000
p2a1/corner_y = 318.263000
p2a1/coffset = 0.000685

p2a2/dim1 = 2
p2a2/dim2 = ss
p2a2/dim3 = fs
p2a2/min_fs = 0
p2a2/min_ss = 128
p2a2/max_fs = 127
p2a2/max_ss = 191
p2a2/fs = -0.000961x -1.000001y
p2a2/ss = +1.000001x -0.000961y
p2a2/corner_x = -381.840000
p2a2/corner_y = 318.191000
p2a2/coffset = 0.000685

p2a3/dim1 = 2
p2a3/dim2 = ss
p2a3/dim3 = fs
p2a3/min_fs = 0
p2a3/min_ss = 192
p2a3/max_fs = 127
p2a3/max_ss = 255
p2a3/fs = -0.000961x -1.000001y
p2a3/ss = +1.000001x -0.000961y
p2a3/corner_x = -315.841000
p2a3/corner_y = 318.119000
p2a3/coffset = 0.000685

p2a4/dim1 = 2
p2a4/dim2 = ss
p2a4/dim3 = fs
p2a4/min_fs = 0
p2a4/min_ss = 256
p2a4/max_fs = 127
p2a4/max_ss = 319
p2a4/fs = -0.000961x -1.000001y
p2a4/ss = +1.000001x -0.000961y
p2a4/corner_x = -249.842000
p2a4/corner_y = 318.048000
p2a4/coffset = 0.000685

p2a5/dim1 = 2
p2a5/dim2 = ss
p2a5/dim3 = fs
p2a5/min_fs = 0
p2a5/min_ss = 320
p2a5/max_fs = 127
p2a5/max_ss = 383
p2a5/fs = -0.000961x -1.000001y
p2a5/ss = +1.000001x -0.000961y
p2a5/corner_x = -183.844000
p2a5/corner_y = 317.976000
p2a5/coffset = 0.000685

p2a6/dim1 = 2
p2a6/dim2 = ss
p2a6/dim3 = fs
p2a6/min_fs = 0
p2a6/min_ss = 384
p2a6/max_fs = 127
p2a6/max_ss = 447
p2a6/fs = -0.000961x -1.000001y
p2a6/ss = +1.000001x -0.000961y
p2a6/corner_x = -117.829000
p2a6/corner_y = 317.904000
p2a6/coffset = 0.000685

p2a7/dim1 = 2
p2a7/dim2 = ss
p2a7/dim3 = fs
p2a7/min_fs = 0
p2a7/min_ss = 448
p2a7/max_fs = 127
p2a7/max_ss = 511
p2a7/fs = -0.000961x -1.000001y
p2a7/ss = +1.000001x -0.000961y
p2a7/corner_x = -51.826300
p2a7/corner_y = 317.832000
p2a7/coffset = 0.000685

p3a0/dim1 = 3
p3a0/dim2 = ss
p3a0/dim3 = fs
p3a0/min_fs = 0
p3a0/min_ss = 0
p3a0/max_fs = 127
p3a0/max_ss = 63
p3a0/fs = +0.00159x -0.999999y
p3a0/ss = +0.999999x +0.00159y
p3a0/corner_x = -514.114000
p3a0/corner_y = 160.623000
p3a0/coffset = 0.00092

p3a1/dim1 = 3
p3a1/dim2 = ss
p3a1/dim3 = fs
p3a1/min_fs = 0
p3a1/min_ss = 64
p3a1/max_fs = 127
p3a1/max_ss = 127
p3a1/fs = +0.00159x -0.999999y
p3a1/ss = +0.999999x +0.00159y
p3a1/corner_x = -448.117000
p3a1/corner_y = 160.730000
p3a1/coffset = 0.00092

p3a2/dim1 = 3
p3a2/dim2 = ss
p3a2/dim3 = fs
p3a2/min_fs = 0
p3a2/min_ss = 128
p3a2/max_fs = 127
p3a2/max_ss = 191
p3a2/fs = +0.00159x -0.999999y
p3a2/ss = +0.999999x +0.00159y
p3a2/corner_x = -382.119000
p3a2/corner_y = 160.837000
p3a2/coffset = 0.00092

p3a3/dim1 = 3
p3a3/dim2 = ss
p3a3/dim3 = fs
p3a3/min_fs = 0
p3a3/min_ss = 192
p3a3/max_fs = 127
p3a3/max_ss = 255
p3a3/fs = +0.00159x -0.999999y
p3a3/ss = +0.999999x +0.00159y
p3a3/corner_x = -316.123000
p3a3/corner_y = 160.943000
p3a3/coffset = 0.00092

p3a4/dim1 = 3
p3a4/dim2 = ss
p3a4/dim3 = fs
p3a4/min_fs = 0
p3a4/min_ss = 256
p3a4/max_fs = 127
p3a4/max_ss = 319
p3a4/fs = +0.00159x -0.999999y
p3a4/ss = +0.999999x +0.00159y
p3a4/corner_x = -250.123000
p3a4/corner_y = 161.050000
p3a4/coffset = 0.00092

p3a5/dim1 = 3
p3a5/dim2 = ss
p3a5/dim3 = fs
p3a5/min_fs = 0
p3a5/min_ss = 320
p3a5/max_fs = 127
p3a5/max_ss = 383
p3a5/fs = +0.00159x -0.999999y
p3a5/ss = +0.999999x +0.00159y
p3a5/corner_x = -184.109000
p3a5/corner_y = 161.157000
p3a5/coffset = 0.00092

p3a6/dim1 = 3
p3a6/dim2 = ss
p3a6/dim3 = fs
p3a6/min_fs = 0
p3a6/min_ss = 384
p3a6/max_fs = 127
p3a6/max_ss = 447
p3a6/fs = +0.00159x -0.999999y
p3a6/ss = +0.999999x +0.00159y
p3a6/corner_x = -118.106000
p3a6/corner_y = 161.264000
p3a6/coffset = 0.00092

p3a7/dim1 = 3
p3a7/dim2 = ss
p3a7/dim3 = fs
p3a7/min_fs = 0
p3a7/min_ss = 448
p3a7/max_fs = 127
p3a7/max_ss = 511
p3a7/fs = +0.00159x -0.999999y
p3a7/ss = +0.999999x +0.00159y
p3a7/corner_x = -52.106300
p3a7/corner_y = 161.371000
p3a7/coffset = 0.00092

p4a0/dim1 = 4
p4a0/dim2 = ss
p4a0/dim3 = fs
p4a0/min_fs = 0
p4a0/min_ss = 0
p4a0/max_fs = 127
p4a0/max_ss = 63
p4a0/fs = -0.001899x -0.999999y
p4a0/ss = +0.999999x -0.001899y
p4a0/corner_x = -536.422000
p4a0/corner_y = -1.670290
p4a0/coffset = 0.00075

p4a1/dim1 = 4
p4a1/dim2 = ss
p4a1/dim3 = fs
p4a1/min_fs = 0
p4a1/min_ss = 64
p4a1/max_fs = 127
p4a1/max_ss = 127
p4a1/fs = -0.001899x -0.999999y
p4a1/ss = +0.999999x -0.001899y
p4a1/corner_x = -470.426000
p4a1/corner_y = -1.787270
p4a1/coffset = 0.00075

p4a2/dim1 = 4
p4a2/dim2 = ss
p4a2/dim3 = fs
p4a2/min_fs = 0
p4a2/min_ss = 128
p4a2/max_fs = 127
p4a2/max_ss = 191
p4a2/fs = -0.001899x -0.999999y
p4a2/ss = +0.999999x -0.001899y
p4a2/corner_x = -404.428000
p4a2/corner_y = -1.904270
p4a2/coffset = 0.00075

p4a3/dim1 = 4
p4a3/dim2 = ss
p4a3/dim3 = fs
p4a3/min_fs = 0
p4a3/min_ss = 192
p4a3/max_fs = 127
p4a3/max_ss = 255
p4a3/fs = -0.001899x -0.999999y
p4a3/ss = +0.999999x -0.001899y
p4a3/corner_x = -338.431000
p4a3/corner_y = -2.021260
p4a3/coffset = 0.00075

p4a4/dim1 = 4
p4a4/dim2 = ss
p4a4/dim3 = fs
p4a4/min_fs = 0
p4a4/min_ss = 256
p4a4/max_fs = 127
p4a4/max_ss = 319
p4a4/fs = -0.001899x -0.999999y
p4a4/ss = +0.999999x -0.001899y
p4a4/corner_x = -272.432000
p4a4/corner_y = -2.138250
p4a4/coffset = 0.00075

p4a5/dim1 = 4
p4a5/dim2 = ss
p4a5/dim3 = fs
p4a5/min_fs = 0
p4a5/min_ss = 320
p4a5/max_fs = 127
p4a5/max_ss = 383
p4a5/fs = -0.001899x -0.999999y
p4a5/ss = +0.999999x -0.001899y
p4a5/corner_x = -206.434000
p4a5/corner_y = -2.255240
p4a5/coffset = 0.00075

p4a6/dim1 = 4
p4a6/dim2 = ss
p4a6/dim3 = fs
p4a6/min_fs = 0
p4a6/min_ss = 384
p4a6/max_fs = 127
p4a6/max_ss = 447
p4a6/fs = -0.001899x -0.999999y
p4a6/ss = +0.999999x -0.001899y
p4a6/corner_x = -140.437000
p4a6/corner_y = -2.372220
p4a6/coffset = 0.00075

p4a7/dim1 = 4
p4a7/dim2 = ss
p4a7/dim3 = fs
p4a7/min_fs = 0
p4a7/min_ss = 448
p4a7/max_fs = 127
p4a7/max_ss = 511
p4a7/fs = -0.001899x -0.999999y
p4a7/ss = +0.999999x -0.001899y
p4a7/corner_x = -74.440400
p4a7/corner_y = -2.489210
p4a7/coffset = 0.00075

p5a0/dim1 = 5
p5a0/dim2 = ss
p5a0/dim3 = fs
p5a0/min_fs = 0
p5a0/min_ss = 0
p5a0/max_fs = 127
p5a0/max_ss = 63
p5a0/fs = -0.000318x -1.0y
p5a0/ss = +1.0x -0.000318y
p5a0/corner_x = -536.816000
p5a0/corner_y = -160.254000
p5a0/coffset = 0.000863

p5a1/dim1 = 5
p5a1/dim2 = ss
p5a1/dim3 = fs
p5a1/min_fs = 0
p5a1/min_ss = 64
p5a1/max_fs = 127
p5a1/max_ss = 127
p5a1/fs = -0.000318x -1.0y
p5a1/ss = +1.0x -0.000318y
p5a1/corner_x = -470.819000
p5a1/corner_y = -160.282000
p5a1/coffset = 0.000863

p5a2/dim1 = 5
p5a2/dim2 = ss
p5a2/dim3 = fs
p5a2/min_fs = 0
p5a2/min_ss = 128
p5a2/max_fs = 127
p5a2/max_ss = 191
p5a2/fs = -0.000318x -1.0y
p5a2/ss = +1.0x -0.000318y
p5a2/corner_x = -404.821000
p5a2/corner_y = -160.311000
p5a2/coffset = 0.000863

p5a3/dim1 = 5
p5a3/dim2 = ss
p5a3/dim3 = fs
p5a3/min_fs = 0
p5a3/min_ss = 192
p5a3/max_fs = 127
p5a3/max_ss = 255
p5a3/fs = -0.000318x -1.0y
p5a3/ss = +1.0x -0.000318y
p5a3/corner_x = -338.824000
p5a3/corner_y = -160.340000
p5a3/coffset = 0.000863

p5a4/dim1 = 5
p5a4/dim2 = ss
p5a4/dim3 = fs
p5a4/min_fs = 0
p5a4/min_ss = 256
p5a4/max_fs = 127
p5a4/max_ss = 319
p5a4/fs = -0.000318x -1.0y
p5a4/ss = +1.0x -0.000318y
p5a4/corner_x = -272.826000
p5a4/corner_y = -160.368000
p5a4/coffset = 0.000863

p5a5/dim1 = 5
p5a5/dim2 = ss
p5a5/dim3 = fs
p5a5/min_fs = 0
p5a5/min_ss = 320
p5a5/max_fs = 127
p5a5/max_ss = 383
p5a5/fs = -0.000318x -1.0y
p5a5/ss = +1.0x -0.000318y
p5a5/corner_x = -206.811000
p5a5/corner_y = -160.397000
p5a5/coffset = 0.000863

p5a6/dim1 = 5
p5a6/dim2 = ss
p5a6/dim3 = fs
p5a6/min_fs = 0
p5a6/min_ss = 384
p5a6/max_fs = 127
p5a6/max_ss = 447
p5a6/fs = -0.000318x -1.0y
p5a6/ss = +1.0x -0.000318y
p5a6/corner_x = -140.810000
p5a6/corner_y = -160.426000
p5a6/coffset = 0.000863

p5a7/dim1 = 5
p5a7/dim2 = ss
p5a7/dim3 = fs
p5a7/min_fs = 0
p5a7/min_ss = 448
p5a7/max_fs = 127
p5a7/max_ss = 511
p5a7/fs = -0.000318x -1.0y
p5a7/ss = +1.0x -0.000318y
p5a7/corner_x = -74.809900
p5a7/corner_y = -160.454000
p5a7/coffset = 0.000863

p6a0/dim1 = 6
p6a0/dim2 = ss
p6a0/dim3 = fs
p6a0/min_fs = 0
p6a0/min_ss = 0
p6a0/max_fs = 127
p6a0/max_ss = 63
p6a0/fs = -0.004196x -0.999992y
p6a0/ss = +0.999992x -0.004196y
p6a0/corner_x = -536.783000
p6a0/corner_y = -315.796000
p6a0/coffset = 0.000926

p6a1/dim1 = 6
p6a1/dim2 = ss
p6a1/dim3 = fs
p6a1/min_fs = 0
p6a1/min_ss = 64
p6a1/max_fs = 127
p6a1/max_ss = 127
p6a1/fs = -0.004196x -0.999992y
p6a1/ss = +0.999992x -0.004196y
p6a1/corner_x = -470.786000
p6a1/corner_y = -316.081000
p6a1/coffset = 0.000926

p6a2/dim1 = 6
p6a2/dim2 = ss
p6a2/dim3 = fs
p6a2/min_fs = 0
p6a2/min_ss = 128
p6a2/max_fs = 127
p6a2/max_ss = 191
p6a2/fs = -0.004196x -0.999992y
p6a2/ss = +0.999992x -0.004196y
p6a2/corner_x = -404.789000
p6a2/corner_y = -316.367000
p6a2/coffset = 0.000926

p6a3/dim1 = 6
p6a3/dim2 = ss
p6a3/dim3 = fs
p6a3/min_fs = 0
p6a3/min_ss = 192
p6a3/max_fs = 127
p6a3/max_ss = 255
p6a3/fs = -0.004196x -0.999992y
p6a3/ss = +0.999992x -0.004196y
p6a3/corner_x = -338.791000
p6a3/corner_y = -316.653000
p6a3/coffset = 0.000926

p6a4/dim1 = 6
p6a4/dim2 = ss
p6a4/dim3 = fs
p6a4/min_fs = 0
p6a4/min_ss = 256
p6a4/max_fs = 127
p6a4/max_ss = 319
p6a4/fs = -0.004196x -0.999992y
p6a4/ss = +0.999992x -0.004196y
p6a4/corner_x = -272.795000
p6a4/corner_y = -316.938000
p6a4/coffset = 0.000926

p6a5/dim1 = 6
p6a5/dim2 = ss
p6a5/dim3 = fs
p6a5/min_fs = 0
p6a5/min_ss = 320
p6a5/max_fs = 127
p6a5/max_ss = 383
p6a5/fs = -0.004196x -0.999992y
p6a5/ss = +0.999992x -0.004196y
p6a5/corner_x = -206.796000
p6a5/corner_y = -317.224000
p6a5/coffset = 0.000926

p6a6/dim1 = 6
p6a6/dim2 = ss
p6a6/dim3 = fs
p6a6/min_fs = 0
p6a6/min_ss = 384
p6a6/max_fs = 127
p6a6/max_ss = 447
p6a6/fs = -0.004196x -0.999992y
p6a6/ss = +0.999992x -0.004196y
p6a6/corner_x = -140.799000
p6a6/corner_y = -317.509000
p6a6/coffset = 0.000926

p6a7/dim1 = 6
p6a7/dim2 = ss
p6a7/dim3 = fs
p6a7/min_fs = 0
p6a7/min_ss = 448
p6a7/max_fs = 127
p6a7/max_ss = 511
p6a7/fs = -0.004196x -0.999992y
p6a7/ss = +0.999992x -0.004196y
p6a7/corner_x = -74.800900
p6a7/corner_y = -317.795000
p6a7/coffset = 0.000926

p7a0/dim1 = 7
p7a0/dim2 = ss
p7a0/dim3 = fs
p7a0/min_fs = 0
p7a0/min_ss = 0
p7a0/max_fs = 127
p7a0/max_ss = 63
p7a0/fs = -0.002957x -0.999994y
p7a0/ss = +0.999994x -0.002957y
p7a0/corner_x = -536.788000
p7a0/corner_y = -473.462000
p7a0/coffset = 0.001421

p7a1/dim1 = 7
p7a1/dim2 = ss
p7a1/dim3 = fs
p7a1/min_fs = 0
p7a1/min_ss = 64
p7a1/max_fs = 127
p7a1/max_ss = 127
p7a1/fs = -0.002957x -0.999994y
p7a1/ss = +0.999994x -0.002957y
p7a1/corner_x = -470.794000
p7a1/corner_y = -473.660000
p7a1/coffset = 0.001421

p7a2/dim1 = 7
p7a2/dim2 = ss
p7a2/dim3 = fs
p7a2/min_fs = 0
p7a2/min_ss = 128
p7a2/max_fs = 127
p7a2/max_ss = 191
p7a2/fs = -0.002957x -0.999994y
p7a2/ss = +0.999994x -0.002957y
p7a2/corner_x = -404.798000
p7a2/corner_y = -473.858000
p7a2/coffset = 0.001421

p7a3/dim1 = 7
p7a3/dim2 = ss
p7a3/dim3 = fs
p7a3/min_fs = 0
p7a3/min_ss = 192
p7a3/max_fs = 127
p7a3/max_ss = 255
p7a3/fs = -0.002957x -0.999994y
p7a3/ss = +0.999994x -0.002957y
p7a3/corner_x = -338.801000
p7a3/corner_y = -474.056000
p7a3/coffset = 0.001421

p7a4/dim1 = 7
p7a4/dim2 = ss
p7a4/dim3 = fs
p7a4/min_fs = 0
p7a4/min_ss = 256
p7a4/max_fs = 127
p7a4/max_ss = 319
p7a4/fs = -0.002957x -0.999994y
p7a4/ss = +0.999994x -0.002957y
p7a4/corner_x = -272.805000
p7a4/corner_y = -474.254000
p7a4/coffset = 0.001421

p7a5/dim1 = 7
p7a5/dim2 = ss
p7a5/dim3 = fs
p7a5/min_fs = 0
p7a5/min_ss = 320
p7a5/max_fs = 127
p7a5/max_ss = 383
p7a5/fs = -0.002957x -0.999994y
p7a5/ss = +0.999994x -0.002957y
p7a5/corner_x = -206.808000
p7a5/corner_y = -474.452000
p7a5/coffset = 0.001421

p7a6/dim1 = 7
p7a6/dim2 = ss
p7a6/dim3 = fs
p7a6/min_fs = 0
p7a6/min_ss = 384
p7a6/max_fs = 127
p7a6/max_ss = 447
p7a6/fs = -0.002957x -0.999994y
p7a6/ss = +0.999994x -0.002957y
p7a6/corner_x = -140.810000
p7a6/corner_y = -474.650000
p7a6/coffset = 0.001421

p7a7/dim1 = 7
p7a7/dim2 = ss
p7a7/dim3 = fs
p7a7/min_fs = 0
p7a7/min_ss = 448
p7a7/max_fs = 127
p7a7/max_ss = 511
p7a7/fs = -0.002957x -0.999994y
p7a7/ss = +0.999994x -0.002957y
p7a7/corner_x = -74.812600
p7a7/corner_y = -474.847000
p7a7/coffset = 0.001421

p8a0/dim1 = 8
p8a0/dim2 = ss
p8a0/dim3 = fs
p8a0/min_fs = 0
p8a0/min_ss = 0
p8a0/max_fs = 127
p8a0/max_ss = 63
p8a0/fs = +0.000124x +1.0y
p8a0/ss = -1.0x +0.000124y
p8a0/corner_x = 534.356000
p8a0/corner_y = -153.967000
p8a0/coffset = 0.000612

p8a1/dim1 = 8
p8a1/dim2 = ss
p8a1/dim3 = fs
p8a1/min_fs = 0
p8a1/min_ss = 64
p8a1/max_fs = 127
p8a1/max_ss = 127
p8a1/fs = +0.000124x +1.0y
p8a1/ss = -1.0x +0.000124y
p8a1/corner_x = 468.358000
p8a1/corner_y = -153.964000
p8a1/coffset = 0.000612

p8a2/dim1 = 8
p8a2/dim2 = ss
p8a2/dim3 = fs
p8a2/min_fs = 0
p8a2/min_ss = 128
p8a2/max_fs = 127
p8a2/max_ss = 191
p8a2/fs = +0.000124x +1.0y
p8a2/ss = -1.0x +0.000124y
p8a2/corner_x = 402.359000
p8a2/corner_y = -153.961000
p8a2/coffset = 0.000612

p8a3/dim1 = 8
p8a3/dim2 = ss
p8a3/dim3 = fs
p8a3/min_fs = 0
p8a3/min_ss = 192
p8a3/max_fs = 127
p8a3/max_ss = 255
p8a3/fs = +0.000124x +1.0y
p8a3/ss = -1.0x +0.000124y
p8a3/corner_x = 336.362000
p8a3/corner_y = -153.958000
p8a3/coffset = 0.000612

p8a4/dim1 = 8
p8a4/dim2 = ss
p8a4/dim3 = fs
p8a4/min_fs = 0
p8a4/min_ss = 256
p8a4/max_fs = 127
p8a4/max_ss = 319
p8a4/fs = +0.000124x +1.0y
p8a4/ss = -1.0x +0.000124y
p8a4/corner_x = 270.364000
p8a4/corner_y = -153.956000
p8a4/coffset = 0.000612

p8a5/dim1 = 8
p8a5/dim2 = ss
p8a5/dim3 = fs
p8a5/min_fs = 0
p8a5/min_ss = 320
p8a5/max_fs = 127
p8a5/max_ss = 383
p8a5/fs = +0.000124x +1.0y
p8a5/ss = -1.0x +0.000124y
p8a5/corner_x = 204.365000
p8a5/corner_y = -153.953000
p8a5/coffset = 0.000612

p8a6/dim1 = 8
p8a6/dim2 = ss
p8a6/dim3 = fs
p8a6/min_fs = 0
p8a6/min_ss = 384
p8a6/max_fs = 127
p8a6/max_ss = 447
p8a6/fs = +0.000124x +1.0y
p8a6/ss = -1.0x +0.000124y
p8a6/corner_x = 138.367000
p8a6/corner_y = -153.950000
p8a6/coffset = 0.000612

p8a7/dim1 = 8
p8a7/dim2 = ss
p8a7/dim3 = fs
p8a7/min_fs = 0
p8a7/min_ss = 448
p8a7/max_fs = 127
p8a7/max_ss = 511
p8a7/fs = +0.000124x +1.0y
p8a7/ss = -1.0x +0.000124y
p8a7/corner_x = 72.369700
p8a7/corner_y = -153.948000
p8a7/coffset = 0.000612

p9a0/dim1 = 9
p9a0/dim2 = ss
p9a0/dim3 = fs
p9a0/min_fs = 0
p9a0/min_ss = 0
p9a0/max_fs = 127
p9a0/max_ss = 63
p9a0/fs = +0.000404x +0.999999y
p9a0/ss = -0.999999x +0.000404y
p9a0/corner_x = 534.148000
p9a0/corner_y = -311.228000
p9a0/coffset = 0.000765

p9a1/dim1 = 9
p9a1/dim2 = ss
p9a1/dim3 = fs
p9a1/min_fs = 0
p9a1/min_ss = 64
p9a1/max_fs = 127
p9a1/max_ss = 127
p9a1/fs = +0.000404x +0.999999y
p9a1/ss = -0.999999x +0.000404y
p9a1/corner_x = 468.152000
p9a1/corner_y = -311.205000
p9a1/coffset = 0.000765

p9a2/dim1 = 9
p9a2/dim2 = ss
p9a2/dim3 = fs
p9a2/min_fs = 0
p9a2/min_ss = 128
p9a2/max_fs = 127
p9a2/max_ss = 191
p9a2/fs = +0.000404x +0.999999y
p9a2/ss = -0.999999x +0.000404y
p9a2/corner_x = 402.155000
p9a2/corner_y = -311.182000
p9a2/coffset = 0.000765

p9a3/dim1 = 9
p9a3/dim2 = ss
p9a3/dim3 = fs
p9a3/min_fs = 0
p9a3/min_ss = 192
p9a3/max_fs = 127
p9a3/max_ss = 255
p9a3/fs = +0.000404x +0.999999y
p9a3/ss = -0.999999x +0.000404y
p9a3/corner_x = 336.158000
p9a3/corner_y = -311.159000
p9a3/coffset = 0.000765

p9a4/dim1 = 9
p9a4/dim2 = ss
p9a4/dim3 = fs
p9a4/min_fs = 0
p9a4/min_ss = 256
p9a4/max_fs = 127
p9a4/max_ss = 319
p9a4/fs = +0.000404x +0.999999y
p9a4/ss = -0.999999x +0.000404y
p9a4/corner_x = 270.160000
p9a4/corner_y = -311.136000
p9a4/coffset = 0.000765

p9a5/dim1 = 9
p9a5/dim2 = ss
p9a5/dim3 = fs
p9a5/min_fs = 0
p9a5/min_ss = 320
p9a5/max_fs = 127
p9a5/max_ss = 383
p9a5/fs = +0.000404x +0.999999y
p9a5/ss = -0.999999x +0.000404y
p9a5/corner_x = 204.163000
p9a5/corner_y = -311.113000
p9a5/coffset = 0.000765

p9a6/dim1 = 9
p9a6/dim2 = ss
p9a6/dim3 = fs
p9a6/min_fs = 0
p9a6/min_ss = 384
p9a6/max_fs = 127
p9a6/max_ss = 447
p9a6/fs = +0.000404x +0.999999y
p9a6/ss = -0.999999x +0.000404y
p9a6/corner_x = 138.144000
p9a6/corner_y = -311.089000
p9a6/coffset = 0.000765

p9a7/dim1 = 9
p9a7/dim2 = ss
p9a7/dim3 = fs
p9a7/min_fs = 0
p9a7/min_ss = 448
p9a7/max_fs = 127
p9a7/max_ss = 511
p9a7/fs = +0.000404x +0.999999y
p9a7/ss = -0.999999x +0.000404y
p9a7/corner_x = 72.142300
p9a7/corner_y = -311.066000
p9a7/coffset = 0.000765

p10a0/dim1 = 10
p10a0/dim2 = ss
p10a0/dim3 = fs
p10a0/min_fs = 0
p10a0/min_ss = 0
p10a0/max_fs = 127
p10a0/max_ss = 63
p10a0/fs = -0.001205x +0.999999y
p10a0/ss = -0.999999x -0.001205y
p10a0/corner_x = 533.824000
p10a0/corner_y = -467.267000
p10a0/coffset = 0.000965

p10a1/dim1 = 10
p10a1/dim2 = ss
p10a1/dim3 = fs
p10a1/min_fs = 0
p10a1/min_ss = 64
p10a1/max_fs = 127
p10a1/max_ss = 127
p10a1/fs = -0.001205x +0.999999y
p10a1/ss = -0.999999x -0.001205y
p10a1/corner_x = 467.828000
p10a1/corner_y = -467.355000
p10a1/coffset = 0.000965

p10a2/dim1 = 10
p10a2/dim2 = ss
p10a2/dim3 = fs
p10a2/min_fs = 0
p10a2/min_ss = 128
p10a2/max_fs = 127
p10a2/max_ss = 191
p10a2/fs = -0.001205x +0.999999y
p10a2/ss = -0.999999x -0.001205y
p10a2/corner_x = 401.830000
p10a2/corner_y = -467.444000
p10a2/coffset = 0.000965

p10a3/dim1 = 10
p10a3/dim2 = ss
p10a3/dim3 = fs
p10a3/min_fs = 0
p10a3/min_ss = 192
p10a3/max_fs = 127
p10a3/max_ss = 255
p10a3/fs = -0.001205x +0.999999y
p10a3/ss = -0.999999x -0.001205y
p10a3/corner_x = 335.834000
p10a3/corner_y = -467.533000
p10a3/coffset = 0.000965

p10a4/dim1 = 10
p10a4/dim2 = ss
p10a4/dim3 = fs
p10a4/min_fs = 0
p10a4/min_ss = 256
p10a4/max_fs = 127
p10a4/max_ss = 319
p10a4/fs = -0.001205x +0.999999y
p10a4/ss = -0.999999x -0.001205y
p10a4/corner_x = 269.836000
p10a4/corner_y = -467.621000
p10a4/coffset = 0.000965

p10a5/dim1 = 10
p10a5/dim2 = ss
p10a5/dim3 = fs
p10a5/min_fs = 0
p10a5/min_ss = 320
p10a5/max_fs = 127
p10a5/max_ss = 383
p10a5/fs = -0.001205x +0.999999y
p10a5/ss = -0.999999x -0.001205y
p10a5/corner_x = 203.839000
p10a5/corner_y = -467.710000
p10a5/coffset = 0.000965

p10a6/dim1 = 10
p10a6/dim2 = ss
p10a6/dim3 = fs
p10a6/min_fs = 0
p10a6/min_ss = 384
p10a6/max_fs = 127
p10a6/max_ss = 447
p10a6/fs = -0.001205x +0.999999y
p10a6/ss = -0.999999x -0.001205y
p10a6/corner_x = 137.843000
p10a6/corner_y = -467.798000
p10a6/coffset = 0.000965

p10a7/dim1 = 10
p10a7/dim2 = ss
p10a7/dim3 = fs
p10a7/min_fs = 0
p10a7/min_ss = 448
p10a7/max_fs = 127
p10a7/max_ss = 511
p10a7/fs = -0.001205x +0.999999y
p10a7/ss = -0.999999x -0.001205y
p10a7/corner_x = 71.845500
p10a7/corner_y = -467.887000
p10a7/coffset = 0.000965

p11a0/dim1 = 11
p11a0/dim2 = ss
p11a0/dim3 = fs
p11a0/min_fs = 0
p11a0/min_ss = 0
p11a0/max_fs = 127
p11a0/max_ss = 63
p11a0/fs = -0.00052x +0.999999y
p11a0/ss = -0.999999x -0.00052y
p11a0/corner_x = 533.019000
p11a0/corner_y = -625.653000
p11a0/coffset = 0.001074

p11a1/dim1 = 11
p11a1/dim2 = ss
p11a1/dim3 = fs
p11a1/min_fs = 0
p11a1/min_ss = 64
p11a1/max_fs = 127
p11a1/max_ss = 127
p11a1/fs = -0.00052x +0.999999y
p11a1/ss = -0.999999x -0.00052y
p11a1/corner_x = 467.020000
p11a1/corner_y = -625.693000
p11a1/coffset = 0.001074

p11a2/dim1 = 11
p11a2/dim2 = ss
p11a2/dim3 = fs
p11a2/min_fs = 0
p11a2/min_ss = 128
p11a2/max_fs = 127
p11a2/max_ss = 191
p11a2/fs = -0.00052x +0.999999y
p11a2/ss = -0.999999x -0.00052y
p11a2/corner_x = 401.022000
p11a2/corner_y = -625.734000
p11a2/coffset = 0.001074

p11a3/dim1 = 11
p11a3/dim2 = ss
p11a3/dim3 = fs
p11a3/min_fs = 0
p11a3/min_ss = 192
p11a3/max_fs = 127
p11a3/max_ss = 255
p11a3/fs = -0.00052x +0.999999y
p11a3/ss = -0.999999x -0.00052y
p11a3/corner_x = 335.025000
p11a3/corner_y = -625.774000
p11a3/coffset = 0.001074

p11a4/dim1 = 11
p11a4/dim2 = ss
p11a4/dim3 = fs
p11a4/min_fs = 0
p11a4/min_ss = 256
p11a4/max_fs = 127
p11a4/max_ss = 319
p11a4/fs = -0.00052x +0.999999y
p11a4/ss = -0.999999x -0.00052y
p11a4/corner_x = 269.030000
p11a4/corner_y = -625.814000
p11a4/coffset = 0.001074

p11a5/dim1 = 11
p11a5/dim2 = ss
p11a5/dim3 = fs
p11a5/min_fs = 0
p11a5/min_ss = 320
p11a5/max_fs = 127
p11a5/max_ss = 383
p11a5/fs = -0.00052x +0.999999y
p11a5/ss = -0.999999x -0.00052y
p11a5/corner_x = 203.032000
p11a5/corner_y = -625.855000
p11a5/coffset = 0.001074

p11a6/dim1 = 11
p11a6/dim2 = ss
p11a6/dim3 = fs
p11a6/min_fs = 0
p11a6/min_ss = 384
p11a6/max_fs = 127
p11a6/max_ss = 447
p11a6/fs = -0.00052x +0.999999y
p11a6/ss = -0.999999x -0.00052y
p11a6/corner_x = 137.036000
p11a6/corner_y = -625.895000
p11a6/coffset = 0.001074

p11a7/dim1 = 11
p11a7/dim2 = ss
p11a7/dim3 = fs
p11a7/min_fs = 0
p11a7/min_ss = 448
p11a7/max_fs = 127
p11a7/max_ss = 511
p11a7/fs = -0.00052x +0.999999y
p11a7/ss = -0.999999x -0.00052y
p11a7/corner_x = 71.034500
p11a7/corner_y = -625.935000
p11a7/coffset = 0.001074

p12a0/dim1 = 12
p12a0/dim2 = ss
p12a0/dim3 = fs
p12a0/min_fs = 0
p12a0/min_ss = 0
p12a0/max_fs = 127
p12a0/max_ss = 63
p12a0/fs = +0.000306x +1.0y
p12a0/ss = -1.0x +0.000306y
p12a0/corner_x = 555.269000
p12a0/corner_y = 479.790000
p12a0/coffset = 0.000598

p12a1/dim1 = 12
p12a1/dim2 = ss
p12a1/dim3 = fs
p12a1/min_fs = 0
p12a1/min_ss = 64
p12a1/max_fs = 127
p12a1/max_ss = 127
p12a1/fs = +0.000306x +1.0y
p12a1/ss = -1.0x +0.000306y
p12a1/corner_x = 489.270000
p12a1/corner_y = 479.764000
p12a1/coffset = 0.000598

p12a2/dim1 = 12
p12a2/dim2 = ss
p12a2/dim3 = fs
p12a2/min_fs = 0
p12a2/min_ss = 128
p12a2/max_fs = 127
p12a2/max_ss = 191
p12a2/fs = +0.000306x +1.0y
p12a2/ss = -1.0x +0.000306y
p12a2/corner_x = 423.273000
p12a2/corner_y = 479.738000
p12a2/coffset = 0.000598

p12a3/dim1 = 12
p12a3/dim2 = ss
p12a3/dim3 = fs
p12a3/min_fs = 0
p12a3/min_ss = 192
p12a3/max_fs = 127
p12a3/max_ss = 255
p12a3/fs = +0.000306x +1.0y
p12a3/ss = -1.0x +0.000306y
p12a3/corner_x = 357.269000
p12a3/corner_y = 479.851000
p12a3/coffset = 0.000598

p12a4/dim1 = 12
p12a4/dim2 = ss
p12a4/dim3 = fs
p12a4/min_fs = 0
p12a4/min_ss = 256
p12a4/max_fs = 127
p12a4/max_ss = 319
p12a4/fs = +0.000306x +1.0y
p12a4/ss = -1.0x +0.000306y
p12a4/corner_x = 291.269000
p12a4/corner_y = 479.871000
p12a4/coffset = 0.000598

p12a5/dim1 = 12
p12a5/dim2 = ss
p12a5/dim3 = fs
p12a5/min_fs = 0
p12a5/min_ss = 320
p12a5/max_fs = 127
p12a5/max_ss = 383
p12a5/fs = +0.000306x +1.0y
p12a5/ss = -1.0x +0.000306y
p12a5/corner_x = 225.269000
p12a5/corner_y = 479.891000
p12a5/coffset = 0.000598

p12a6/dim1 = 12
p12a6/dim2 = ss
p12a6/dim3 = fs
p12a6/min_fs = 0
p12a6/min_ss = 384
p12a6/max_fs = 127
p12a6/max_ss = 447
p12a6/fs = +0.000306x +1.0y
p12a6/ss = -1.0x +0.000306y
p12a6/corner_x = 159.269000
p12a6/corner_y = 479.911000
p12a6/coffset = 0.000598

p12a7/dim1 = 12
p12a7/dim2 = ss
p12a7/dim3 = fs
p12a7/min_fs = 0
p12a7/min_ss = 448
p12a7/max_fs = 127
p12a7/max_ss = 511
p12a7/fs = +0.000306x +1.0y
p12a7/ss = -1.0x +0.000306y
p12a7/corner_x = 93.269000
p12a7/corner_y = 479.931000
p12a7/coffset = 0.000598

p13a0/dim1 = 13
p13a0/dim2 = ss
p13a0/dim3 = fs
p13a0/min_fs = 0
p13a0/min_ss = 0
p13a0/max_fs = 127
p13a0/max_ss = 63
p13a0/fs = +0.002537x +0.999996y
p13a0/ss = -0.999996x +0.002537y
p13a0/corner_x = 554.143000
p13a0/corner_y = 322.460000
p13a0/coffset = 0.000584

p13a1/dim1 = 13
p13a1/dim2 = ss
p13a1/dim3 = fs
p13a1/min_fs = 0
p13a1/min_ss = 64
p13a1/max_fs = 127
p13a1/max_ss = 127
p13a1/fs = +0.002537x +0.999996y
p13a1/ss = -0.999996x +0.002537y
p13a1/corner_x = 488.144000
p13a1/corner_y = 322.616000
p13a1/coffset = 0.000584

p13a2/dim1 = 13
p13a2/dim2 = ss
p13a2/dim3 = fs
p13a2/min_fs = 0
p13a2/min_ss = 128
p13a2/max_fs = 127
p13a2/max_ss = 191
p13a2/fs = +0.002537x +0.999996y
p13a2/ss = -0.999996x +0.002537y
p13a2/corner_x = 422.149000
p13a2/corner_y = 322.772000
p13a2/coffset = 0.000584

p13a3/dim1 = 13
p13a3/dim2 = ss
p13a3/dim3 = fs
p13a3/min_fs = 0
p13a3/min_ss = 192
p13a3/max_fs = 127
p13a3/max_ss = 255
p13a3/fs = +0.002537x +0.999996y
p13a3/ss = -0.999996x +0.002537y
p13a3/corner_x = 356.152000
p13a3/corner_y = 322.928000
p13a3/coffset = 0.000584

p13a4/dim1 = 13
p13a4/dim2 = ss
p13a4/dim3 = fs
p13a4/min_fs = 0
p13a4/min_ss = 256
p13a4/max_fs = 127
p13a4/max_ss = 319
p13a4/fs = +0.002537x +0.999996y
p13a4/ss = -0.999996x +0.002537y
p13a4/corner_x = 290.155000
p13a4/corner_y = 323.084000
p13a4/coffset = 0.000584

p13a5/dim1 = 13
p13a5/dim2 = ss
p13a5/dim3 = fs
p13a5/min_fs = 0
p13a5/min_ss = 320
p13a5/max_fs = 127
p13a5/max_ss = 383
p13a5/fs = +0.002537x +0.999996y
p13a5/ss = -0.999996x +0.002537y
p13a5/corner_x = 224.140000
p13a5/corner_y = 323.239000
p13a5/coffset = 0.000584

p13a6/dim1 = 13
p13a6/dim2 = ss
p13a6/dim3 = fs
p13a6/min_fs = 0
p13a6/min_ss = 384
p13a6/max_fs = 127
p13a6/max_ss = 447
p13a6/fs = +0.002537x +0.999996y
p13a6/ss = -0.999996x +0.002537y
p13a6/corner_x = 158.140000
p13a6/corner_y = 323.395000
p13a6/coffset = 0.000584

p13a7/dim1 = 13
p13a7/dim2 = ss
p13a7/dim3 = fs
p13a7/min_fs = 0
p13a7/min_ss = 448
p13a7/max_fs = 127
p13a7/max_ss = 511
p13a7/fs = +0.002537x +0.999996y
p13a7/ss = -0.999996x +0.002537y
p13a7/corner_x = 92.139900
p13a7/corner_y = 323.551000
p13a7/coffset = 0.000584

p14a0/dim1 = 14
p14a0/dim2 = ss
p14a0/dim3 = fs
p14a0/min_fs = 0
p14a0/min_ss = 0
p14a0/max_fs = 127
p14a0/max_ss = 63
p14a0/fs = -0.000234x +1.0y
p14a0/ss = -1.0x -0.000234y
p14a0/corner_x = 555.375000
p14a0/corner_y = 166.458000
p14a0/coffset = 0.000549

p14a1/dim1 = 14
p14a1/dim2 = ss
p14a1/dim3 = fs
p14a1/min_fs = 0
p14a1/min_ss = 64
p14a1/max_fs = 127
p14a1/max_ss = 127
p14a1/fs = -0.000234x +1.0y
p14a1/ss = -1.0x -0.000234y
p14a1/corner_x = 489.377000
p14a1/corner_y = 166.439000
p14a1/coffset = 0.000549

p14a2/dim1 = 14
p14a2/dim2 = ss
p14a2/dim3 = fs
p14a2/min_fs = 0
p14a2/min_ss = 128
p14a2/max_fs = 127
p14a2/max_ss = 191
p14a2/fs = -0.000234x +1.0y
p14a2/ss = -1.0x -0.000234y
p14a2/corner_x = 423.380000
p14a2/corner_y = 166.421000
p14a2/coffset = 0.000549

p14a3/dim1 = 14
p14a3/dim2 = ss
p14a3/dim3 = fs
p14a3/min_fs = 0
p14a3/min_ss = 192
p14a3/max_fs = 127
p14a3/max_ss = 255
p14a3/fs = -0.000234x +1.0y
p14a3/ss = -1.0x -0.000234y
p14a3/corner_x = 357.382000
p14a3/corner_y = 166.402000
p14a3/coffset = 0.000549

p14a4/dim1 = 14
p14a4/dim2 = ss
p14a4/dim3 = fs
p14a4/min_fs = 0
p14a4/min_ss = 256
p14a4/max_fs = 127
p14a4/max_ss = 319
p14a4/fs = -0.000234x +1.0y
p14a4/ss = -1.0x -0.000234y
p14a4/corner_x = 291.384000
p14a4/corner_y = 166.384000
p14a4/coffset = 0.000549

p14a5/dim1 = 14
p14a5/dim2 = ss
p14a5/dim3 = fs
p14a5/min_fs = 0
p14a5/min_ss = 320
p14a5/max_fs = 127
p14a5/max_ss = 383
p14a5/fs = -0.000234x +1.0y
p14a5/ss = -1.0x -0.000234y
p14a5/corner_x = 225.370000
p14a5/corner_y = 166.365000
p14a5/coffset = 0.000549

p14a6/dim1 = 14
p14a6/dim2 = ss
p14a6/dim3 = fs
p14a6/min_fs = 0
p14a6/min_ss = 384
p14a6/max_fs = 127
p14a6/max_ss = 447
p14a6/fs = -0.000234x +1.0y
p14a6/ss = -1.0x -0.000234y
p14a6/corner_x = 159.369000
p14a6/corner_y = 166.346000
p14a6/coffset = 0.000549

p14a7/dim1 = 14
p14a7/dim2 = ss
p14a7/dim3 = fs
p14a7/min_fs = 0
p14a7/min_ss = 448
p14a7/max_fs = 127
p14a7/max_ss = 511
p14a7/fs = -0.000234x +1.0y
p14a7/ss = -1.0x -0.000234y
p14a7/corner_x = 93.367000
p14a7/corner_y = 166.328000
p14a7/coffset = 0.000549

p15a0/dim1 = 15
p15a0/dim2 = ss
p15a0/dim3 = fs
p15a0/min_fs = 0
p15a0/min_ss = 0
p15a0/max_fs = 127
p15a0/max_ss = 63
p15a0/fs = +0.001282x +1.000001y
p15a0/ss = -1.000001x +0.001282y
p15a0/corner_x = 554.709000
p15a0/corner_y = 9.505970
p15a0/coffset = 0.000481

p15a1/dim1 = 15
p15a1/dim2 = ss
p15a1/dim3 = fs
p15a1/min_fs = 0
p15a1/min_ss = 64
p15a1/max_fs = 127
p15a1/max_ss = 127
p15a1/fs = +0.001282x +1.000001y
p15a1/ss = -1.000001x +0.001282y
p15a1/corner_x = 488.711000
p15a1/corner_y = 9.584410
p15a1/coffset = 0.000481

p15a2/dim1 = 15
p15a2/dim2 = ss
p15a2/dim3 = fs
p15a2/min_fs = 0
p15a2/min_ss = 128
p15a2/max_fs = 127
p15a2/max_ss = 191
p15a2/fs = +0.001282x +1.000001y
p15a2/ss = -1.000001x +0.001282y
p15a2/corner_x = 422.714000
p15a2/corner_y = 9.662840
p15a2/coffset = 0.000481

p15a3/dim1 = 15
p15a3/dim2 = ss
p15a3/dim3 = fs
p15a3/min_fs = 0
p15a3/min_ss = 192
p15a3/max_fs = 127
p15a3/max_ss = 255
p15a3/fs = +0.001282x +1.000001y
p15a3/ss = -1.000001x +0.001282y
p15a3/corner_x = 356.716000
p15a3/corner_y = 9.741280
p15a3/coffset = 0.000481

p15a4/dim1 = 15
p15a4/dim2 = ss
p15a4/dim3 = fs
p15a4/min_fs = 0
p15a4/min_ss = 256
p15a4/max_fs = 127
p15a4/max_ss = 319
p15a4/fs = +0.001282x +1.000001y
p15a4/ss = -1.000001x +0.001282y
p15a4/corner_x = 290.716000
p15a4/corner_y = 9.819720
p15a4/coffset = 0.000481

p15a5/dim1 = 15
p15a5/dim2 = ss
p15a5/dim3 = fs
p15a5/min_fs = 0
p15a5/min_ss = 320
p15a5/max_fs = 127
p15a5/max_ss = 383
p15a5/fs = +0.001282x +1.000001y
p15a5/ss = -1.000001x +0.001282y
p15a5/corner_x = 224.699000
p15a5/corner_y = 9.898180
p15a5/coffset = 0.000481

p15a6/dim1 = 15
p15a6/dim2 = ss
p15a6/dim3 = fs
p15a6/min_fs = 0
p15a6/min_ss = 384
p15a6/max_fs = 127
p15a6/max_ss = 447
p15a6/fs = +0.001282x +1.000001y
p15a6/ss = -1.000001x +0.001282y
p15a6/corner_x = 158.698000
p15a6/corner_y = 9.976620
p15a6/coffset = 0.000481

p15a7/dim1 = 15
p15a7/dim2 = ss
p15a7/dim3 = fs
p15a7/min_fs = 0
p15a7/min_ss = 448
p15a7/max_fs = 127
p15a7/max_ss = 511
p15a7/fs = +0.001282x +1.000001y
p15a7/ss = -1.000001x +0.001282y
p15a7/corner_x = 92.697300
p15a7/corner_y = 10.055070
p15a7/coffset = 0.000481
