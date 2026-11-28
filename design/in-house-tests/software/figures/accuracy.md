| Test | Quantity | Unit | n | Mean error | Max abs error | RMS | Target |
|---|---|---|---|---|---|---|---|
| 1 heap | flank angle, roughness 0 mm | deg | 24 | +0.000325 | 0.0107 | 0.00488 | 0.5 |
| 1 heap | flank angle, roughness 0.03 mm | deg | 24 | -0.00634 | 0.217 | 0.0984 | 0.5 |
| 1 heap | apex angle atan(2h/D) | deg | 12 | +0.0337 | 0.211 | 0.0796 | - |
| 1 heap | heap volume | % | 12 | -0.671 | 1.66 | 0.749 | - |
| 1 heap | flank angle, roughness 0.05 mm | deg | 24 | +0.0325 | 0.553 | 0.184 | 0.5 |
| 1 heap | flank angle, roughness 0.1 mm | deg | 24 | +0.0609 | 1.11 | 0.422 | 0.5 |
| 2 density | column height (16 px/mm) | mm | 8 | -0.00298 | 0.0439 | 0.0306 | 0.05 |
| 2 density | Kawakita a (volume noise 0.003 mL) | - | 20 | +3.16e-05 | 0.000785 | 0.000355 | - |
| 2 density | Kawakita 1/b | % | 20 | -0.36 | 4.09 | 1.27 | - |
| 3 plate | slip angle (5 fps camera, 20 Hz IMU) | deg | 6 | +0.0104 | 0.0394 | 0.0196 | 0.5 (about +-2 on phi_w) |
| 3 plate | phi_w (3 lids x 3, slip SD 0.25 deg) | deg | 30 | +0.0195 | 0.438 | 0.187 | 2 |
| 3 plate | wall adhesion c_w | Pa | 30 | -0.0858 | 1.31 | 0.605 | - |
| 4 PSD | d10 (number), 6 fields, 15 % touching | % | 3 | -0.568 | 1.76 | 1.63 | 5 |
| 4 PSD | d50 (number), 6 fields, 15 % touching | % | 3 | -0.517 | 1.35 | 1.28 | 5 |
| 4 PSD | d90 (number), 6 fields, 15 % touching | % | 3 | -0.727 | 4.49 | 2.76 | 5 |
| 4 PSD | d50 (volume) | % | 3 | -1.31 | 5.12 | 3 | - |
| 4 PSD | grain count after watershed | % | 3 | -0.657 | 0.927 | 0.686 | - |
| 5 orifice | flow rate, 10 Hz, 0.25 s balance lag corrected | % | 7 | +0.0549 | 0.272 | 0.107 | - |
| 5 orifice | Beverloo C (2 % rate scatter) | % | 20 | +0.471 | 3.68 | 1.78 | - |
| 5 orifice | Beverloo k | - | 20 | +0.0114 | 0.0982 | 0.0434 | - |
| 6 humidity | u_eq (6 weighings, 2 % noise) | % | 20 | +0.593 | 4.01 | 2.24 | - |
| 6 humidity | tau | % | 20 | +1.74 | 19.4 | 8.68 | - |
| 7 drum | free-surface angle (12 px/mm) | deg | 8 | -0.000899 | 0.0649 | 0.0337 | 0.5 |
| 7 drum | avalanche start angle (1 rpm, 10 fps) | deg | 5 | -0.00397 | 0.0426 | 0.0235 | - |
| 7 drum | avalanche stop angle | deg | 5 | +0.00549 | 0.0185 | 0.0146 | - |
| 8 UCS | peak force (2 mg noise, 80 Hz) | % | 5 | -0.447 | 0.619 | 0.457 | - |
| 9 spread | coverage | % points | 6 | +0.0216 | 0.053 | 0.0327 | - |
| 9 spread | streak area | % | 6 | +0.27 | 1.22 | 0.554 | - |
| 10 Faraday | charge step (drift corrected) | nC | 10 | -0.0193 | 0.098 | 0.037 | - |

| Test | Quantity | Unit | Simulated run | Truth | Error | Checks passed |
|---|---|---|---|---|---|---|
| 1 heap | flank angle | deg | 32.92 | 33 | -0.0753 | 4/4 |
| 2 density | bulk density | kg/m3 | 1249 | 1250 | -1.4 | 5/5 |
| 2 density | Kawakita a | - | 0.14 | 0.14 | -1.56e-05 | 5/5 |
| 2 density | Kawakita 1/b | taps | 8.967 | 9 | -0.0331 | 5/5 |
| 3 plate | phi_w | deg | 22.42 | 22 | +0.421 | 5/5 |
| 3 plate | c_w | Pa | 6.896 | 8 | -1.1 | 5/5 |
| 4 PSD | d50 (number) | um | 420.4 | 425 | -4.6 | 4/4 |
| 5 orifice | Beverloo C | - | 0.6017 | 0.58 | +0.0217 | 5/5 |
| 5 orifice | Beverloo k | - | 1.586 | 1.5 | +0.0858 | 5/5 |
| 5 orifice | D_c | mm | 1.225 | 1.2 | +0.0247 | 5/5 |
| 5 orifice | D_c tapped | mm | 0.8944 | 0.9 | -0.00557 | 5/5 |
| 6 humidity | u_eq at 75 % RH | mg/g | 59.97 | 60 | -0.0267 | 3/3 |
| 7 drum | dynamic angle at 10 rpm | deg | 39.04 | 39 | +0.0408 | 3/3 |
| 7 drum | avalanche start at 1 rpm | deg | 39.58 | 40 | -0.425 | 3/3 |
| 7 drum | avalanche stop at 1 rpm | deg | 32.73 | 33 | -0.27 | 3/3 |
| 8 UCS | sigma_c at 1 kPa | Pa | 375.1 | 377 | -1.88 | 4/4 |
| 9 spread | coverage | - | 0.8963 | 0.8957 | +0.000547 | 4/4 |
| 10 Faraday | q/m | uC/kg | 19.78 | 20 | -0.221 | 5/5 |
