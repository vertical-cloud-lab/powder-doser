Question: I run an open-hardware benchtop gravimetric powder doser and want to infer each powder's particle (grain) size, or its particle size distribution (PSD), from the doser's own flow data, as a data assimilation / inverse problem. What published work predicts or infers the particle size or PSD of powders or granular materials from flow or process data, rather than from direct sizing (sieving, laser diffraction, imaging)?

The doser: a small auger (screw) in a tube that tilts 0-45 degrees above horizontal, driven by a stepper motor, with a vibration motor and a solenoid tapper, dispensing into a cup on an analytical balance (0.1 mg resolution). My data: balance mass-versus-time readings every 0.1-0.4 s during continuous auger rotation at fixed speeds (15, 45 and 90 rpm); mass delivered per single auger revolution at three tube angles; spontaneous outflow during holds; mass per tap; closed-loop doses to target masses (bulk, fine and tap stages) with an on-board Kalman filter's mass and flow-rate estimates; and stall and clog events. Powders (identity known, PSD not measured on the device): table salt, sodium sulfate, barium chloride, calcium lactate, silicon -110/+200 mesh and -325 mesh, gas-atomized AlSi10Mg and Al 4047, white and brown rice flour, xanthan gum, carboxymethyl cellulose, sodium alginate and fumed silica.

Please cover the following, with quantitative results (accuracy, R2, error in d50) where available and full citations with DOIs:
1. Physics-based inversion: discharge or throughput laws that depend on particle size (Beverloo-type orifice and hopper flow, screw/auger feeder models), and statistics of flow fluctuations, intermittency, avalanches and clogging (for example their dependence on the outlet-to-particle size ratio, or the shot-noise variance of mass increments) that have been used, or could be used, to estimate particle size.
2. Signal-based sizing of flowing particles: acoustic emission, vibration and impact sensors, and analogous grain-size inversions in geophysics (bedload transport, debris flows).
3. Data-driven models (soft sensors, machine learning, multivariate/PLS) that predict PSD from process or flow measurements, and the forward models that predict feeder or flow behavior from PSD and other material properties (pharmaceutical loss-in-weight feeders, material property databases, metal additive-manufacturing powder flow tests such as the Hall flowmeter, revolution powder analyzer and FT4).
4. Bayesian calibration and data assimilation for granular materials (for example DEM parameter inference with sequential Monte Carlo or particle filters, ensemble Kalman filters, Gaussian-process surrogates): what has been estimated from bulk flow measurements, and whether particle size is identifiable separately from cohesion, friction, shape, density and moisture.
5. Whether anyone has inferred particle size from screw/auger feeder or gravimetric dosing data specifically, which features of mass-versus-time data carry the most size information, and which extra measurements (for example a few laser-diffraction PSDs as ground truth) would make such a model credible.


# Inferring Particle Size from Flow and Process Data: A Literature Review

## Summary

No published study was found that directly inverts screw-feeder or gravimetric-dosing mass-versus-time data to recover particle size or a particle size distribution (PSD). However, a rich body of work establishes the physical, signal-based, data-driven, and Bayesian foundations from which such an inverse model could be built. The table below consolidates the key approaches, their observables, accuracy metrics, and references.

| Approach category | Method/model | Observable(s) used | What is estimated | Reported accuracy/metric | Key reference |
|---|---|---|---|---|---|
| Physics-based inversion | Beverloo discharge inversion: mass flow proportional to ρb√g(D−kd)^(5/2) | Mass-flow rate, known outlet diameter, bulk density | Effective characteristic diameter d, conditional on C, k, and density | No published inverse-sizing error; k≈1.6 for horizontal and 2.3 for vertical outlets; broader reported range ≈1.2–3 (sheldon2010granulardischargeand pages 2-3, wilson2013granulardischargerate pages 1-2) | Sheldon & Durian, 2010; DOI: [10.1007/s10035-010-0198-3](https://doi.org/10.1007/s10035-010-0198-3) |
| Physics-based inversion | Clogging and avalanche statistics | Mean mass or grain count between clogs; clogging probability versus D/d | Effective d from a calibrated D/d relationship; historical no-clog scale roughly D/d≈5 | Avalanche sizes often exponential; clogging fraction decays approximately exponentially with opening width raised to system dimensionality; sampling length 0.75±0.20d (zuriguel2014invitedreviewclogging pages 2-4, thomas2015fractionofclogging pages 2-3, thomas2015fractionofclogging pages 1-2) | Zuriguel, 2014; DOI: [10.48550/arXiv.1412.5806](https://doi.org/10.48550/arXiv.1412.5806); Thomas & Durian, 2015; DOI: [10.1103/PhysRevLett.114.178001](https://doi.org/10.1103/PhysRevLett.114.178001) |
| Physics-based inversion | Tilted-hopper discharge and clogging phase diagram | Mass flow and clogging versus outlet diameter and tilt | Effective d through orientation-dependent cutoff and D/d phase diagram | k0=1.6±0.1 and k90=2.3±0.2; C0=0.573±0.003 and C90=0.269±0.005 (sheldon2010granulardischargeand pages 2-3) | Sheldon & Durian, 2010; DOI: [10.1007/s10035-010-0198-3](https://doi.org/10.1007/s10035-010-0198-3) |
| Signal-based sizing | Quantitative acoustic-emission impact sizing with contact model | AE waveform, recovered peak impact force, impact duration, impact velocity | Individual diameter and diameter distribution | Mean-diameter error below 10%; optical mean 89.2 μm versus acoustic mean 80.6 μm; distribution-spread error about 26% (buttle1990characterizationofparticle pages 1-3, buttle1990characterizationofparticle pages 24-27) | Buttle & Scruby, 1990; DOI: [10.1016/0043-1648(90)90018-6](https://doi.org/10.1016/0043-1648(90)90018-6) |
| Signal-based sizing | AE plus triboelectric velocity sensing in pneumatic conveying | AE peak-voltage distribution and independently measured impact velocity | Full PSD | Spearman correlation above 0.8; maximum size-bin discrepancy 4.81%; average discrepancy 1.12–2.33%; repeatability better than 1.5% per bin (zheng2021onlinemeasurementof pages 1-6, zheng2021onlinemeasurementof pages 33-38) | Zheng et al., 2021; DOI: [10.1109/TIM.2021.3062407](https://doi.org/10.1109/TIM.2021.3062407) |
| Signal-based sizing | AE single-particle inversion using Stronge impact theory | AE waveform and impact velocity | Individual particle diameter | Mean relative error mostly within 12% for 0.4–1.2 mm glass beads at 22–37 m/s (zhang2019onlinesizemeasurement pages 1-2) | Zhang et al., 2019; DOI: [10.1016/j.powtec.2019.05.023](https://doi.org/10.1016/j.powtec.2019.05.023) |
| Geophysical analogue | Passive-acoustic bedload inversion with sphere–slab spectral dictionary and regularized NNLS | Hydrophone power spectral density | Full grain-size distribution from nonnegative spectral weights | Simulated distributions recovered even for the noisiest tested spectrum; field estimates described as fairly close to physical samples, but no scalar d50 error or R² reported (petrut2018passiveacousticmeasurement pages 1-2, petrut2018passiveacousticmeasurement pages 10-11, petrut2018passiveacousticmeasurement pages 6-8) | Petrut et al., 2018; DOI: [10.5194/hess-22-767-2018](https://doi.org/10.5194/hess-22-767-2018) |
| Geophysical analogue | Physics-based seismic inversion with Green-function propagation | Geophone PSD, attenuation, site response, discharge, impact mechanics | Bedload flux; GSD is an input rather than an independently retrieved output | Instantaneous flux generally within a factor of 5±1 and potentially about a factor of 2 after averaging; wrong grain-size assumptions can cause errors above one order of magnitude (bakker2020fieldapplicationand pages 14-16, bakker2020fieldapplicationand pages 1-3) | Bakker et al., 2020; DOI: [10.1029/2019JF005416](https://doi.org/10.1029/2019JF005416) |
| Geophysical analogue | Spectral regression after separating rainfall and turbulence | Seismic spectra, precipitation, river discharge | Bedload transport rate, not PSD | Predicted transport versus calibrated channel geophones: R²≈0.6, p<10⁻¹⁰ (roth2016bedloadsediment pages 1-2) | Roth et al., 2016; DOI: [10.1002/2015JF003782](https://doi.org/10.1002/2015JF003782) |
| Geophysical analogue | Impact-plate vibration with first-arrival atomic decomposition | Individual-impact amplitude and frequency | Time-varying d50 and grain-size information | Laboratory-calibrated and applied to field flood records; no numerical d50 error reported (barriere2015anadvancedsignal pages 1-2) | Barrière et al., 2015; DOI: [10.1002/esp.3693](https://doi.org/10.1002/esp.3693) |
| Feeder forward model | PLS feeder-performance prediction | Thirty properties including d10, d50, d90, density, compressibility, permeability, cohesion, and shear-cell measures | Forward mapping from PSD and properties to feeder RSD and relative mass deviation | Four-component PLS models explained over 95% cumulative variance; PCA retained four components explaining 96.4%; screw selection experimentally confirmed (wang2016usingmultivariateanalysis pages 73-78, wang2016usingmultivariateanalysis pages 82-86) | Wang, 2016; DOI: [10.7282/T39Z9770](https://doi.org/10.7282/T39Z9770) |
| Feeder forward model | PLS model for a low-feed-rate feeder | Twenty-five material descriptors; feed factor versus hopper level; catch-scale data | FFmax, FFdecay, feed-rate RSD, relative error | Validated on two unseen powders; volumetric responses predicted better than closed-loop gravimetric responses; numerical R² or Q² unavailable in the extract (bostijn2019amultivariateapproach pages 1-6, bostijn2019amultivariateapproach pages 10-14) | Bostijn et al., 2019; DOI: [10.1016/j.ijpharm.2018.12.066](https://doi.org/10.1016/j.ijpharm.2018.12.066) |
| Data-driven forward model | SVR using Earth-mover distances between complete PSD and shape distributions | Full size histogram and aspect-ratio distribution | Shear-cell flow-function coefficient FFc, not PSD | Predictive R²≈0.8; adding shape increased R² by 0.0346, p=5.3×10⁻⁴ (barjat2020demonstrationofthe pages 24-27, barjat2020demonstrationofthe pages 13-16, barjat2020demonstrationofthe pages 16-20) | Barjat et al., 2020; DOI: [10.1007/s12247-020-09433-5](https://doi.org/10.1007/s12247-020-09433-5) |
| Data-driven forward model | Neural-network and random-forest flowability classification | PSD and particle-shape descriptors | FFc flowability class | Best single-step multilayer perceptron AUC–ROC=0.823; external validation on eight unseen powders (diaz2023machinelearningapproaches pages 4-5) | Diaz et al., 2023; DOI: [10.1039/D2DD00106C](https://doi.org/10.1039/D2DD00106C) |
| Data-driven forward model | ML prediction of continuous-direct-compression flow performance | API PSD, shape descriptors, formulation composition | FFc and wall-friction angle; not the feeder mechanical feed factor | Best FFc regression MAPE=0.173; wall-friction-angle MAE=1.83°; viability classification precision about 0.9 (diaz2023machinelearningmodels pages 167-170) | Diaz, 2023 dissertation; DOI: [10.48730/dpnt-v318](https://doi.org/10.48730/dpnt-v318) |
| Bayesian and DEM calibration | Sequential quasi-Monte Carlo filter | Bulk stress–strain history | Posterior PDFs for five contact or micromechanical parameters; particle size prescribed | Best-posterior simulations agreed well with experiments; no particle-size error reported (cheng2018probabilisticcalibrationof pages 1-2) | Cheng et al., 2018; DOI: [10.1007/s10035-017-0781-y](https://doi.org/10.1007/s10035-017-0781-y) |
| Bayesian and DEM calibration | Particle-filter calibration | Sequential triaxial stress–strain observations | Elastic, rolling or bending, and friction parameters; not PSD | Multiple parameter solutions with explicit probabilities, demonstrating non-uniqueness (cheng2017calibrationofmicromechanical pages 1-2, cheng2017calibrationofmicromechanical pages 4-4) | Cheng et al., 2017; DOI: [10.1051/epjconf/201714012011](https://doi.org/10.1051/epjconf/201714012011) |
| Bayesian and DEM calibration | Likelihood-free Bayesian inference with BayesSim and granular simulation | Depth-image statistics of piles and rings | Sliding friction, rolling friction, restitution; not particle size | Calibrated simulation predicted unseen formations and transferred to pouring tasks; no particle-size accuracy reported (matl2020inferringthematerial pages 1-2) | Matl et al., 2020; DOI: [10.1109/ICRA40945.2020.9197063](https://doi.org/10.1109/ICRA40945.2020.9197063) |
| Bayesian powder handling | FLIP Bayesian optimization | Measured angle of repose | Friction, cohesion, adhesion, damping, and related simulation parameters; diameter bounded a priori to 0.22–0.32 mm | Robotic dispensing error 2.12±1.53 mg versus 6.11±3.92 mg under domain randomization; not a size-inference result (radulov2025flipflowabilityinformedpowder pages 3-4, radulov2025flipflowabilityinformedpowder pages 2-3, radulov2025flipflowabilityinformedpowder pages 1-2) | Radulov et al., 2025; DOI: [10.48550/arXiv.2506.03896](https://doi.org/10.48550/arXiv.2506.03896) |
| Direct auger or gravimetric inverse problem | Screw-feeder mass-time data to PSD | Auger or LIW mass-versus-time, feed factor, variability, dose errors, transients, clogs | Proposed d50, PSD width, or PSD bins | Not demonstrated in the located literature. Existing studies measure PSD independently and use it to predict feeding; none reports inverse d50 error, PSD R², or external validation from gravimetric traces alone (li2020predictiveperformanceof pages 36-40, li2020predictiveperformanceof pages 44-49, li2020predictiveperformanceof pages 40-44, bostijn2019amultivariateapproach pages 10-14) | Literature gap; no direct reference located |


*Table: Published inverse-sizing methods, related signal-based approaches, feeder forward models, and Bayesian granular calibrations. The final row highlights the absence of a validated PSD inversion based specifically on auger or loss-in-weight mass-time data.*

---

## 1. Physics-Based Inversion

### 1.1 Beverloo-Type Discharge Laws

The Beverloo equation provides the canonical relationship between mass discharge rate and grain diameter for gravity-driven granular flow through an orifice:

**W = C ρ_b g^{1/2} (D − kd)^{5/2}**

where *W* is mass flow rate, *ρ_b* is bulk density, *g* is gravitational acceleration, *D* is orifice diameter, *d* is particle diameter, *C* ≈ 0.5–0.7 is a dimensionless flow coefficient, and *k* ≈ 1.2–3 is an empirical parameter representing the "empty annulus" (wilson2013granulardischargerate pages 1-2, humby1998predictionofhopper pages 1-2). For spherical glass beads, Sheldon and Durian (2010, doi:10.1007/s10035-010-0198-3) fitted *C₀* = 0.573 ± 0.003 and *k₀* = 1.6 ± 0.1 for horizontal discharge, and *C₉₀* = 0.269 ± 0.005 and *k₉₀* = 2.3 ± 0.2 for vertical discharge, with the constants independent of bead size for 0.3 mm and 0.9 mm beads (sheldon2010granulardischargeand pages 2-3, sheldon2010granulardischargeand pages 1-2). Humby et al. (1998, doi:10.1016/S0009-2509(97)00326-6) reported *k* ≈ 1.5 for monosized spheres and noted that the geometric scaling applies only for particles larger than roughly 500 μm, below which interstitial air drag becomes important (humby1998predictionofhopper pages 1-2, humby1998predictionofhopper pages 7-8).

In principle, the Beverloo relation can be inverted: if *W*, *ρ_b*, *D*, *C*, and *k* are known or calibrated, one can solve for *d*. For the user's auger doser, the tube exit and screw geometry define an effective orifice, so the mass per revolution at different tube angles provides data analogous to tilted-hopper discharge rates at known *D*. Sheldon and Durian showed that for large holes the flux decreases linearly with cosine of the tilt angle, vanishing below the angle of repose (sheldon2010granulardischargeand pages 2-3). For submerged grains, a modified Beverloo form replaces √(*gD*) with terminal velocity *v_t*, and the cutoff increases to *k* ≈ 2.4 grain diameters (wilson2013granulardischargerate pages 4-5, wilson2013granulardischargerate pages 5-6).

### 1.2 Clogging and Avalanche Statistics

Clogging provides an independent, statistical route to particle-size information. Zuriguel (2014, doi:10.48550/arXiv.1412.5806) reviewed how the avalanche size—the number of grains discharged between successive clogs—follows an exponential distribution for non-cohesive particles, with the mean avalanche size diverging near an orifice-to-particle ratio *D/d* ≈ 5 (zuriguel2014invitedreviewclogging pages 2-4, zuriguel2014invitedreviewclogging pages 1-2). Thomas and Durian (2015, doi:10.1103/PhysRevLett.114.178001) modeled clogging as a memoryless process in which each flowing configuration has a constant probability of forming a stable arch; the resulting clogging fraction *F* decays exponentially with hole width raised to the system dimensionality, and the characteristic sampling length is *ℓ* = (0.75 ± 0.20)*d* (thomas2015fractionofclogging pages 2-3, thomas2015fractionofclogging pages 1-2). Gaida et al. (2026, doi:10.1103/x3bt-63wt) modeled the clogging transition using a cumulative normal distribution in *D/d₅₀*, with d₅₀ as the representative particle size (gaida2026granularcloggingacross pages 3-5). 

For the user's doser, the spontaneous-outflow holds, stall events, and clog-then-tap sequences provide direct analogues: the frequency and mass of spontaneous discharges versus tube angle or auger-tube gap effectively sweep *D/d*, and the mass per tap after a clog maps onto an avalanche-size measurement. Hafez et al. (2021, doi:10.1038/s41598-021-82744-w) showed that particle shape (cubes, crosses, spheres) modifies the clogging probability and introduces history-dependent effects for non-spherical particles at large *D/d* and high solidity, an important consideration for the user's irregularly shaped powders.

---

## 2. Signal-Based Sizing of Flowing Particles

### 2.1 Acoustic Emission and Impact Sensors

Buttle and Scruby (1990, doi:10.1016/0043-1648(90)90018-6) pioneered quantitative acoustic-emission (AE) particle sizing by deconvolving impact-force histories from calibrated plate responses. For 50–100 μm glass particles at 2.5–7.1 m/s, the acoustically inferred mean diameter agreed with optical measurements to within 10% (optical mean 89.2 μm versus acoustic 80.6 μm) (buttle1990characterizationofparticle pages 1-3, buttle1990characterizationofparticle pages 24-27). Zhang et al. (2019, doi:10.1016/j.powtec.2019.05.023) improved single-particle sizing using Stronge impact theory to account for plasticity, achieving mean relative error mostly within 12% for 0.4–1.2 mm glass beads at 22–37 m/s (zhang2019onlinesizemeasurement pages 1-2).

For full PSD estimation during continuous flow, Zheng et al. (2021, doi:10.1109/TIM.2021.3062407) combined AE peak-voltage detection with triboelectric velocity measurement in pneumatic conveying of silica sands (10–750 μm). A Gaussian-prediction algorithm corrected for overlapping impacts and noise, yielding Spearman rank correlations above 0.8 between measured and reference PSDs, per-bin discrepancies within ±4.8%, average discrepancies of 1.12–2.33%, and repeatability better than 1.5% per size segment (zheng2021onlinemeasurementof pages 1-6, zheng2021onlinemeasurementof pages 33-38). The physical basis is the Hertzian impact relation *V_max* = *K_V* *v*^{6/5} *d*², generalized empirically to *V_max* = *K_V* *v*^*m* *d*^*n* to accommodate non-ideal impacts (zheng2021onlinemeasurementof pages 14-19).

These methods require high-bandwidth sensors and isolated impacts. The user's doser lacks a dedicated AE sensor but does have a solenoid tapper and vibration motor; the balance itself records mass increments that are coarser analogues of impact counts. The per-revolution mass "shot noise" is conceptually similar.

### 2.2 Geophysical Grain-Size Inversion (Bedload Transport)

Petrut et al. (2018, doi:10.5194/hess-22-767-2018) achieved the most direct grain-size inversion from a flow signal in the geophysical domain. They modeled the power spectral density (PSD) of river-bottom noise as a linear combination of Hertzian sphere–slab impact spectra, one per grain-size class, and solved the resulting linear system **Aγ ≈ b** by non-negative least squares (NNLS) with regularization to obtain the grain-size distribution γ. Applied to hydrophone data from the Isère River, the inverted GSD was described as "fairly close" to physical-sampling estimates (petrut2018passiveacousticmeasurement pages 1-2, petrut2018passiveacousticmeasurement pages 10-11, petrut2018passiveacousticmeasurement pages 6-8). Barrière et al. (2015, doi:10.1002/esp.3693) used first-arrival atomic decomposition of impact-plate vibration to extract amplitude and frequency features linked to D₅₀ via Hertzian contact theory, calibrated in flume experiments and applied to field flood records (barriere2015anadvancedsignal pages 1-2).

For bedload flux rather than GSD, Bakker et al. (2020, doi:10.1029/2019JF005416) applied a revised Tsai et al. (2012) seismic model in which grain size enters strongly—seismic power scales approximately as *d*^{6.5}—but GSD was constrained from physical sampling rather than independently recovered from the signal; flux estimates were within a factor of ~5 (bakker2020fieldapplicationand pages 8-10, bakker2020fieldapplicationand pages 14-16). Roth et al. (2016, doi:10.1002/2015JF003782) used spectral regression of seismic data against discharge and precipitation, achieving *r*² ≈ 0.6 for transport rate (roth2016bedloadsediment pages 1-2).

The analogy to the user's doser is instructive: each auger revolution delivers a "burst" of grains whose mass increments constitute a time series analogous to impact-plate counts, and the frequency content of mass fluctuations encodes information about characteristic grain size.

---

## 3. Data-Driven Models (Forward: PSD → Flow)

### 3.1 Pharmaceutical Loss-in-Weight Feeder Models

The pharmaceutical continuous-manufacturing literature has developed numerous forward models linking powder material properties (including PSD) to feeder performance, but always in the PSD → flow direction. Wang (2016, doi:10.7282/T39Z9770) used PLS regression on 30 flow properties (including d₁₀, d₅₀, d₉₀, bulk density, compressibility, permeability, shear-cell parameters) for seven powders on a K-Tron KT20 twin-screw feeder. Four-component PLS models explained over 95% of cumulative variance in feed-rate relative standard deviation (RSD) and relative deviation from target (RDM) (wang2016usingmultivariateanalysis pages 73-78, wang2016usingmultivariateanalysis pages 82-86). Bostijn et al. (2019, doi:10.1016/j.ijpharm.2018.12.066) extended this to 15 powders and 25 descriptors for a low-feed-rate feeder, predicting maximum feed factor and feed-factor decay versus hopper fill level, with validation on two unseen powders; volumetric responses were predicted better than gravimetric responses because closed-loop control masks material-property effects (bostijn2019amultivariateapproach pages 6-10, bostijn2019amultivariateapproach pages 1-6, bostijn2019amultivariateapproach pages 10-14).

### 3.2 Flowability Prediction from PSD

Barjat et al. (2020, doi:10.1007/s12247-020-09433-5) trained a support vector regression model using Earth-mover (Wasserstein) distances between full particle-size and particle-shape distributions for 106 pharmaceutical materials, predicting the flow-function coefficient (FFc) with R² ≈ 0.8; adding shape information improved R² by 0.035 (p = 5.3 × 10⁻⁴) (barjat2020demonstrationofthe pages 24-27). Diaz et al. (2023, doi:10.1039/D2DD00106C) achieved an AUC-ROC of 0.823 for FFc flowability classification using a multilayer perceptron on PSD and shape descriptors from QICPIC measurements of 112 pharmaceutical systems, with SHAP analysis identifying PSD D₁₀, D₅₀, and aspect-ratio D₁₀ as the most influential variables (diaz2023machinelearningapproaches pages 1-2, diaz2023machinelearningapproaches pages 4-5). In a dissertation, Diaz (2023, doi:10.48730/dpnt-v318) reported feed-factor regression with MAPE = 0.173 and wall-friction-angle MAE = 1.83° from API PSD and shape descriptors (diaz2023machinelearningmodels pages 167-170).

### 3.3 Inverting the Forward Model

These forward models can, in principle, be inverted: given observed feeder performance (RSD, feed factor, dose variability), one can seek the PSD that best explains those observations. However, the forward mapping from PSD to feeder behavior is many-to-one because multiple material properties (cohesion, moisture, density, shape) jointly determine flow. No study in the located literature has attempted this inversion explicitly.

---

## 4. Bayesian Calibration and Data Assimilation for Granular Materials

### 4.1 DEM Parameter Inference

Cheng et al. (2018, doi:10.1007/s10035-017-0781-y) applied a sequential quasi-Monte Carlo (SQMC) filter to update posterior probability density functions for five DEM micromechanical parameters (elastic, friction, rolling/bending) conditioned on experimental stress–strain curves. The method operated on polydisperse packings and quantified parameter interactions and posterior breadth, but particle size was prescribed, not inferred (cheng2018probabilisticcalibrationof pages 1-2). In earlier work, Cheng et al. (2017, doi:10.1051/epjconf/201714012011) used a particle filter, explicitly noting that multiple parameter solutions exist with known probabilities of reproducing bulk behavior—a direct indicator of non-identifiability (cheng2017calibrationofmicromechanical pages 1-2, cheng2017calibrationofmicromechanical pages 4-4). Cheng et al. also developed the open-source GrainLearning toolbox (2024, doi:10.21105/joss.06338) for Bayesian uncertainty quantification of DEM models.

Matl et al. (2020, doi:10.1109/ICRA40945.2020.9197063) used likelihood-free Bayesian inference with the BayesSim framework and NVIDIA Isaac Sim to infer sliding friction, rolling friction, and coefficient of restitution from depth-image summary statistics of granular piles and rings. The calibrated simulator generalized to pouring tasks, but particle size was not among the inferred parameters (matl2020inferringthematerial pages 1-2). Radulov et al. (2025, doi:10.48550/arXiv.2506.03896) used Bayesian optimization to match simulated and measured angles of repose, calibrating friction, cohesion, adhesion, and damping while bounding particle diameter a priori to 0.22–0.32 mm; the resulting FLIP policy achieved robotic dispensing errors of 2.12 ± 1.53 mg (radulov2025flipflowabilityinformedpowder pages 3-4, radulov2025flipflowabilityinformedpowder pages 2-3, radulov2025flipflowabilityinformedpowder pages 1-2).

### 4.2 Identifiability of Particle Size

A critical finding across this literature is that **particle size has not been demonstrated as independently identifiable from bulk flow measurements alone**. DEM calibration studies typically fix particle size (often upscaled for computational tractability) and infer contact parameters. Dastgerdi and Malinowska (2024, doi:10.3390/ma17194833) used sequential, test-specific calibration—bulk-density measurement to fix particle density, then tilt tests for friction—precisely to reduce confounding; rolling friction was not identified but fixed at 0.1, and particle size was a prescribed modeling choice constrained by the requirement that several grains pass through the outlet simultaneously (dastgerdi2024asimplifiedcalibration pages 2-4, dastgerdi2024asimplifiedcalibration pages 4-6). Cheng et al. (2021, doi:10.1007/978-3-030-64514-4_90) showed that macro-scale calibration parameters remain strongly correlated with underlying DEM micro-parameters, and that several plasticity parameters are jointly controlled by interacting contact properties (cheng2021bayesianuncertaintyquantification pages 8-9). Hadi et al. (2024, doi:10.1038/s41598-024-78455-7) cited literature on "ambiguous parameter combinations" and emphasized that multiple complementary experiments are needed (hadi2024adaptiveaibasedsurrogate pages 19-19).

For the user's doser, this means that particle size will be confounded with cohesion, friction, shape, density, and moisture unless (i) multiple independent observables are used (e.g., flow rate, clogging frequency, tilt-angle dependence, mass-per-tap, dose variability at multiple speeds), and/or (ii) prior information (known identity, known density, a few ground-truth PSD measurements) is incorporated.

---

## 5. Particle Size Inference from Screw/Auger Feeder Data: Current Gap and Recommendations

### 5.1 Literature Gap

Despite extensive searching of the pharmaceutical, additive-manufacturing, granular-physics, and geophysical literatures, **no published study was found that infers particle size or PSD from auger/screw-feeder or gravimetric-dosing mass-versus-time data**. All located studies use PSD as an input to predict feeder performance. Li (2020, doi:10.7282/t3-6tgx-8f63) recorded one-second mass-flow data from twin-screw feeders across 14 materials, four screw designs, and six feed rates, reporting that conditioned bulk density correlated with feed factor, but did not attempt PSD inversion (li2020predictiveperformanceof pages 36-40, li2020predictiveperformanceof pages 44-49, li2020predictiveperformanceof pages 40-44). Bostijn et al. (2019) and Wang (2016) similarly treated PSD as a known input (bostijn2019amultivariateapproach pages 10-14, wang2016usingmultivariateanalysis pages 64-68).

### 5.2 Which Features of Mass-Time Data Carry Size Information

Based on the physical models reviewed, the following features of the user's data are expected to carry the most particle-size information:

1. **Mean mass per auger revolution** (feed factor) at each speed and tilt angle — analogous to a Beverloo discharge measurement; the tilt-angle dependence provides an additional constraint on *d* through the orientation-dependent cutoff *k* (sheldon2010granulardischargeand pages 2-3).
2. **Variance and autocorrelation of per-revolution mass increments** — the "shot noise" of granular discharge scales with grain mass (*m_grain* ∝ *d*³) and thus with *d*; larger grains produce lumpier mass traces.
3. **Clogging and stall events** — the frequency of clogging versus tube angle and auger speed maps onto the D/d phase diagram; larger grains clog more readily at a given orifice (zuriguel2014invitedreviewclogging pages 2-4, gaida2026granularcloggingacross pages 3-5).
4. **Mass per tap** after a stall — analogous to the avalanche-size distribution; the mean mass per avalanche is related to the sampling length ≈ 0.75*d* (thomas2015fractionofclogging pages 2-3).
5. **Spontaneous outflow during holds** — angle-dependent gravity drainage encodes information about d relative to the tube exit, analogous to a tilted hopper (sheldon2010granulardischargeand pages 2-3).
6. **Feed-factor decay versus hopper fill level** — sensitive to compressibility and density changes, which depend on PSD width and cohesion (bostijn2019amultivariateapproach pages 10-14).
7. **Kalman-filter innovation sequences** — the residuals from the on-board Kalman filter contain information about process noise, which is partially grain-size-dependent.

### 5.3 What Would Make the Model Credible

The inverse problem of estimating PSD from feeder data is inherently under-determined because multiple powder properties jointly affect flow. To make such a model credible:

- **A small number of ground-truth laser-diffraction or sieve PSD measurements** (perhaps 5–10 of the user's 14 powders) are needed for supervised training or Bayesian prior calibration. The forward-model literature consistently requires such ground truth (barjat2020demonstrationofthe pages 24-27, diaz2023machinelearningapproaches pages 4-5).
- **Known powder identity and density** substantially reduce confounding; when identity is known, density and particle shape are fixed, leaving PSD (d₅₀, span) as the main unknown.
- **Multiple independent flow observables** (different speeds, different angles, clog frequency, tap response) provide a richer likelihood and improve identifiability, following the DEM calibration principle of using multiple complementary experiments (dastgerdi2024asimplifiedcalibration pages 2-4, hadi2024adaptiveaibasedsurrogate pages 19-19).
- **Bayesian formulation with informative priors** — using known ranges for each powder's d₅₀ from literature or manufacturer data, combined with a Beverloo-type forward model augmented by clogging statistics, would allow posterior estimation of d₅₀ and span with quantified uncertainty.
- **External validation** on held-out powders with independently measured PSDs is essential; leave-one-out or leave-one-powder-out cross-validation is the standard in pharmaceutical feeder modeling (wang2016usingmultivariateanalysis pages 82-86, diaz2023machinelearningapproaches pages 4-5).

---

## References

Key references with DOIs (cited above):

- Sheldon HG, Durian DJ. *Granular Matter* 12:579–585 (2010). doi:10.1007/s10035-010-0198-3
- Humby SJ, Tüzün U, Yu A. *Chem Eng Sci* 53:483–494 (1998). doi:10.1016/S0009-2509(97)00326-6
- Wilson T et al. *Papers in Physics* 6:060009 (2013/2014). doi:10.48550/arXiv.1307.2812
- Zuriguel I. *Papers in Physics* 7:060014 (2014). doi:10.48550/arXiv.1412.5806
- Thomas CC, Durian DJ. *Phys Rev Lett* 114:178001 (2015). doi:10.1103/PhysRevLett.114.178001
- Hafez A et al. *Sci Rep* 11 (2021). doi:10.1038/s41598-021-82744-w
- Gaida O et al. *Phys Rev E* 114:035405 (2026). doi:10.1103/x3bt-63wt
- Buttle DJ, Scruby CB. *Wear* 137:63–90 (1990). doi:10.1016/0043-1648(90)90018-6
- Zhang G et al. *Powder Technol* 353:195–201 (2019). doi:10.1016/j.powtec.2019.05.023
- Zheng G et al. *IEEE Trans Instrum Meas* 70:1–17 (2021). doi:10.1109/TIM.2021.3062407
- Petrut T et al. *Hydrol Earth Syst Sci* 22:767–787 (2018). doi:10.5194/hess-22-767-2018
- Barrière J et al. *Earth Surf Process Landf* 40:913–924 (2015). doi:10.1002/esp.3693
- Bakker M et al. *J Geophys Res Earth Surf* 125 (2020). doi:10.1029/2019JF005416
- Roth DL et al. *J Geophys Res Earth Surf* 121:725–747 (2016). doi:10.1002/2015JF003782
- Wang Y. Dissertation, Rutgers (2016). doi:10.7282/T39Z9770
- Bostijn N et al. *Int J Pharm* 557:342–353 (2019). doi:10.1016/j.ijpharm.2018.12.066
- Barjat H et al. *J Pharm Innov* 16:181–196 (2020). doi:10.1007/s12247-020-09433-5
- Diaz LP et al. *Digital Discovery* 2:692–701 (2023). doi:10.1039/D2DD00106C
- Diaz LP. Dissertation, Strathclyde (2023). doi:10.48730/dpnt-v318
- Li T. Dissertation, Rutgers (2020). doi:10.7282/t3-6tgx-8f63
- Cheng H et al. *Granular Matter* 20 (2018). doi:10.1007/s10035-017-0781-y
- Cheng H et al. *EPJ Web Conf* 140:12011 (2017). doi:10.1051/epjconf/201714012011
- Cheng H et al. *J Open Source Softw* 9:6338 (2024). doi:10.21105/joss.06338
- Matl C et al. *ICRA 2020* pp 2770–2777 (2020). doi:10.1109/ICRA40945.2020.9197063
- Radulov N et al. arXiv:2506.03896 (2025). doi:10.48550/arXiv.2506.03896
- Dastgerdi RH, Malinowska AA. *Materials* 17:4833 (2024). doi:10.3390/ma17194833
- Cheng H et al. *Challenges and Innovations in Geomechanics* pp 837–845 (2021). doi:10.1007/978-3-030-64514-4_90
- Mort P. *Papers in Physics* 7:070004 (2015). doi:10.48550/arXiv.1510.04534
- Fathollahi S et al. *AAPS PharmSciTech* 21 (2020). doi:10.1208/s12249-020-01835-5

References

1. (sheldon2010granulardischargeand pages 2-3): Hannah G. Sheldon and Douglas J. Durian. Granular discharge and clogging for tilted hoppers. Granular Matter, 12:579-585, Jul 2010. URL: https://doi.org/10.1007/s10035-010-0198-3, doi:10.1007/s10035-010-0198-3. This article has 134 citations and is from a peer-reviewed journal.

2. (wilson2013granulardischargerate pages 1-2): T. Wilson, Charlotte R. Pfeifer, N. Mesyngier, and D. Durian. Granular discharge rate for submerged hoppers. Papers in Physics, 6:060009-060009, Jul 2013. URL: https://doi.org/10.48550/arxiv.1307.2812, doi:10.48550/arxiv.1307.2812. This article has 64 citations.

3. (zuriguel2014invitedreviewclogging pages 2-4): Iker Zuriguel. Invited review: clogging of granular materials in bottlenecks. arXiv: Soft Condensed Matter, pages 060014, Dec 2014. URL: https://doi.org/10.48550/arxiv.1412.5806, doi:10.48550/arxiv.1412.5806. This article has 110 citations.

4. (thomas2015fractionofclogging pages 2-3): Charles C Thomas and D. Durian. Fraction of clogging configurations sampled by granular hopper flow. Physical Review Letters, Apr 2015. URL: https://doi.org/10.1103/physrevlett.114.178001, doi:10.1103/physrevlett.114.178001. This article has 166 citations and is from a highest quality peer-reviewed journal.

5. (thomas2015fractionofclogging pages 1-2): Charles C Thomas and D. Durian. Fraction of clogging configurations sampled by granular hopper flow. Physical Review Letters, Apr 2015. URL: https://doi.org/10.1103/physrevlett.114.178001, doi:10.1103/physrevlett.114.178001. This article has 166 citations and is from a highest quality peer-reviewed journal.

6. (buttle1990characterizationofparticle pages 1-3): D.J. Buttle and C.B. Scruby. Characterization of particle impact by quantitative acoustic emission. Wear, 137:63-90, Apr 1990. URL: https://doi.org/10.1016/0043-1648(90)90018-6, doi:10.1016/0043-1648(90)90018-6. This article has 116 citations and is from a highest quality peer-reviewed journal.

7. (buttle1990characterizationofparticle pages 24-27): D.J. Buttle and C.B. Scruby. Characterization of particle impact by quantitative acoustic emission. Wear, 137:63-90, Apr 1990. URL: https://doi.org/10.1016/0043-1648(90)90018-6, doi:10.1016/0043-1648(90)90018-6. This article has 116 citations and is from a highest quality peer-reviewed journal.

8. (zheng2021onlinemeasurementof pages 1-6): Ge Zheng, Yong Yan, Yonghui Hu, and Wenbiao Zhang. Online measurement of the size distribution of pneumatically conveyed particles through acoustic emission detection and triboelectric sensing. IEEE Transactions on Instrumentation and Measurement, 70:1-17, Jan 2021. URL: https://doi.org/10.1109/tim.2021.3062407, doi:10.1109/tim.2021.3062407. This article has 20 citations and is from a highest quality peer-reviewed journal.

9. (zheng2021onlinemeasurementof pages 33-38): Ge Zheng, Yong Yan, Yonghui Hu, and Wenbiao Zhang. Online measurement of the size distribution of pneumatically conveyed particles through acoustic emission detection and triboelectric sensing. IEEE Transactions on Instrumentation and Measurement, 70:1-17, Jan 2021. URL: https://doi.org/10.1109/tim.2021.3062407, doi:10.1109/tim.2021.3062407. This article has 20 citations and is from a highest quality peer-reviewed journal.

10. (zhang2019onlinesizemeasurement pages 1-2): Guoqiang Zhang, Yong Yan, Yonghui Hu, and Ge Zheng. On-line size measurement of pneumatically conveyed particles through acoustic emission sensing. Powder Technology, 353:195-201, Jul 2019. URL: https://doi.org/10.1016/j.powtec.2019.05.023, doi:10.1016/j.powtec.2019.05.023. This article has 34 citations and is from a domain leading peer-reviewed journal.

11. (petrut2018passiveacousticmeasurement pages 1-2): Teodor Petrut, Thomas Geay, Cédric Gervaise, Philippe Belleudy, and Sebastien Zanker. Passive acoustic measurement of bedload grain size distribution using self-generated noise. Hydrology and Earth System Sciences, 22:767-787, Jan 2018. URL: https://doi.org/10.5194/hess-22-767-2018, doi:10.5194/hess-22-767-2018. This article has 36 citations and is from a domain leading peer-reviewed journal.

12. (petrut2018passiveacousticmeasurement pages 10-11): Teodor Petrut, Thomas Geay, Cédric Gervaise, Philippe Belleudy, and Sebastien Zanker. Passive acoustic measurement of bedload grain size distribution using self-generated noise. Hydrology and Earth System Sciences, 22:767-787, Jan 2018. URL: https://doi.org/10.5194/hess-22-767-2018, doi:10.5194/hess-22-767-2018. This article has 36 citations and is from a domain leading peer-reviewed journal.

13. (petrut2018passiveacousticmeasurement pages 6-8): Teodor Petrut, Thomas Geay, Cédric Gervaise, Philippe Belleudy, and Sebastien Zanker. Passive acoustic measurement of bedload grain size distribution using self-generated noise. Hydrology and Earth System Sciences, 22:767-787, Jan 2018. URL: https://doi.org/10.5194/hess-22-767-2018, doi:10.5194/hess-22-767-2018. This article has 36 citations and is from a domain leading peer-reviewed journal.

14. (bakker2020fieldapplicationand pages 14-16): Maarten Bakker, Florent Gimbert, Thomas Geay, Clément Misset, Sébastien Zanker, and Alain Recking. Field application and validation of a seismic bedload transport model. Journal of Geophysical Research: Earth Surface, May 2020. URL: https://doi.org/10.1029/2019jf005416, doi:10.1029/2019jf005416. This article has 75 citations.

15. (bakker2020fieldapplicationand pages 1-3): Maarten Bakker, Florent Gimbert, Thomas Geay, Clément Misset, Sébastien Zanker, and Alain Recking. Field application and validation of a seismic bedload transport model. Journal of Geophysical Research: Earth Surface, May 2020. URL: https://doi.org/10.1029/2019jf005416, doi:10.1029/2019jf005416. This article has 75 citations.

16. (roth2016bedloadsediment pages 1-2): Danica L. Roth, Emily E. Brodsky, Noah J. Finnegan, Dieter. Rickenmann, Jens M. Turowski, and Alexandre Badoux. Bed load sediment transport inferred from seismic signals near a river. Journal of Geophysical Research: Earth Surface, 121:725-747, Apr 2016. URL: https://doi.org/10.1002/2015jf003782, doi:10.1002/2015jf003782. This article has 119 citations.

17. (barriere2015anadvancedsignal pages 1-2): Julien Barrière, Andreas Krein, Adrien Oth, and Reimar Schenkluhn. An advanced signal processing technique for deriving grain size information of bedload transport from impact plate vibration measurements. Earth Surface Processes and Landforms, 40:913-924, Jan 2015. URL: https://doi.org/10.1002/esp.3693, doi:10.1002/esp.3693. This article has 58 citations and is from a domain leading peer-reviewed journal.

18. (wang2016usingmultivariateanalysis pages 73-78): Yifan Wang. Using multivariate analysis for pharmaceutical drug product development. ArXiv, Jan 2016. URL: https://doi.org/10.7282/t39z9770, doi:10.7282/t39z9770. This article has 10 citations.

19. (wang2016usingmultivariateanalysis pages 82-86): Yifan Wang. Using multivariate analysis for pharmaceutical drug product development. ArXiv, Jan 2016. URL: https://doi.org/10.7282/t39z9770, doi:10.7282/t39z9770. This article has 10 citations.

20. (bostijn2019amultivariateapproach pages 1-6): N. Bostijn, J. Dhondt, A. Ryckaert, E. Szabó, W. Dhondt, B. V. Snick, B. V. Snick, V. Vanhoorne, C. Vervaet, and T. D. Beer. A multivariate approach to predict the volumetric and gravimetric feeding behavior of a low feed rate feeder based on raw material properties. International Journal of Pharmaceutics, 557:342–353, Feb 2019. URL: https://doi.org/10.1016/j.ijpharm.2018.12.066, doi:10.1016/j.ijpharm.2018.12.066. This article has 90 citations and is from a domain leading peer-reviewed journal.

21. (bostijn2019amultivariateapproach pages 10-14): N. Bostijn, J. Dhondt, A. Ryckaert, E. Szabó, W. Dhondt, B. V. Snick, B. V. Snick, V. Vanhoorne, C. Vervaet, and T. D. Beer. A multivariate approach to predict the volumetric and gravimetric feeding behavior of a low feed rate feeder based on raw material properties. International Journal of Pharmaceutics, 557:342–353, Feb 2019. URL: https://doi.org/10.1016/j.ijpharm.2018.12.066, doi:10.1016/j.ijpharm.2018.12.066. This article has 90 citations and is from a domain leading peer-reviewed journal.

22. (barjat2020demonstrationofthe pages 24-27): Hervé Barjat, Stephen Checkley, Toma Chitu, Neil Dawson, Amin Farshchi, Ana Ferreira, John Gamble, Michael Leane, Andy Mitchell, Chris Morris, Kendal Pitt, Richard Storey, Furqan Tahir, and Mike Tobyn. Demonstration of the feasibility of predicting the flow of pharmaceutically relevant powders from particle and bulk physical properties. Journal of Pharmaceutical Innovation, 16:181-196, Feb 2020. URL: https://doi.org/10.1007/s12247-020-09433-5, doi:10.1007/s12247-020-09433-5. This article has 40 citations and is from a peer-reviewed journal.

23. (barjat2020demonstrationofthe pages 13-16): Hervé Barjat, Stephen Checkley, Toma Chitu, Neil Dawson, Amin Farshchi, Ana Ferreira, John Gamble, Michael Leane, Andy Mitchell, Chris Morris, Kendal Pitt, Richard Storey, Furqan Tahir, and Mike Tobyn. Demonstration of the feasibility of predicting the flow of pharmaceutically relevant powders from particle and bulk physical properties. Journal of Pharmaceutical Innovation, 16:181-196, Feb 2020. URL: https://doi.org/10.1007/s12247-020-09433-5, doi:10.1007/s12247-020-09433-5. This article has 40 citations and is from a peer-reviewed journal.

24. (barjat2020demonstrationofthe pages 16-20): Hervé Barjat, Stephen Checkley, Toma Chitu, Neil Dawson, Amin Farshchi, Ana Ferreira, John Gamble, Michael Leane, Andy Mitchell, Chris Morris, Kendal Pitt, Richard Storey, Furqan Tahir, and Mike Tobyn. Demonstration of the feasibility of predicting the flow of pharmaceutically relevant powders from particle and bulk physical properties. Journal of Pharmaceutical Innovation, 16:181-196, Feb 2020. URL: https://doi.org/10.1007/s12247-020-09433-5, doi:10.1007/s12247-020-09433-5. This article has 40 citations and is from a peer-reviewed journal.

25. (diaz2023machinelearningapproaches pages 4-5): Laura Pereira Diaz, Cameron J. Brown, Ebenezer Ojo, Chantal Mustoe, and Alastair J. Florence. Machine learning approaches to the prediction of powder flow behaviour of pharmaceutical materials from physical properties. Digital Discovery, 2:692-701, Jan 2023. URL: https://doi.org/10.1039/d2dd00106c, doi:10.1039/d2dd00106c. This article has 37 citations and is from a peer-reviewed journal.

26. (diaz2023machinelearningmodels pages 167-170): Laura Pereira Diaz. Machine learning models for the prediction of pharmaceutical powder properties. Dissertation, Jan 2023. URL: https://doi.org/10.48730/dpnt-v318, doi:10.48730/dpnt-v318. This article has 0 citations.

27. (cheng2018probabilisticcalibrationof pages 1-2): Hongyang Cheng, Takayuki Shuku, Klaus Thoeni, and Haruyuki Yamamoto. Probabilistic calibration of discrete element simulations using the sequential quasi-monte carlo filter. Granular Matter, Jan 2018. URL: https://doi.org/10.1007/s10035-017-0781-y, doi:10.1007/s10035-017-0781-y. This article has 78 citations and is from a peer-reviewed journal.

28. (cheng2017calibrationofmicromechanical pages 1-2): Hongyang Cheng, Takayuki Shuku, Klaus Thoeni, and Haruyuki Yamamoto. Calibration of micromechanical parameters for dem simulations by using the particle filter. ArXiv, 140:12011, Jun 2017. URL: https://doi.org/10.1051/epjconf/201714012011, doi:10.1051/epjconf/201714012011. This article has 15 citations.

29. (cheng2017calibrationofmicromechanical pages 4-4): Hongyang Cheng, Takayuki Shuku, Klaus Thoeni, and Haruyuki Yamamoto. Calibration of micromechanical parameters for dem simulations by using the particle filter. ArXiv, 140:12011, Jun 2017. URL: https://doi.org/10.1051/epjconf/201714012011, doi:10.1051/epjconf/201714012011. This article has 15 citations.

30. (matl2020inferringthematerial pages 1-2): Carolyn Matl, Yashraj Narang, Ruzena Bajcsy, Fabio Ramos, and Dieter Fox. Inferring the material properties of granular media for robotic tasks. 2020 IEEE International Conference on Robotics and Automation (ICRA), pages 2770-2777, May 2020. URL: https://doi.org/10.1109/icra40945.2020.9197063, doi:10.1109/icra40945.2020.9197063. This article has 61 citations.

31. (radulov2025flipflowabilityinformedpowder pages 3-4): Nikola Radulov, Alex Wright, Thomas little, Andrew I. Cooper, and Gabriella Pizzuto. Flip: flowability-informed powder weighing. ArXiv, Jun 2025. URL: https://doi.org/10.48550/arxiv.2506.03896, doi:10.48550/arxiv.2506.03896. This article has 6 citations.

32. (radulov2025flipflowabilityinformedpowder pages 2-3): Nikola Radulov, Alex Wright, Thomas little, Andrew I. Cooper, and Gabriella Pizzuto. Flip: flowability-informed powder weighing. ArXiv, Jun 2025. URL: https://doi.org/10.48550/arxiv.2506.03896, doi:10.48550/arxiv.2506.03896. This article has 6 citations.

33. (radulov2025flipflowabilityinformedpowder pages 1-2): Nikola Radulov, Alex Wright, Thomas little, Andrew I. Cooper, and Gabriella Pizzuto. Flip: flowability-informed powder weighing. ArXiv, Jun 2025. URL: https://doi.org/10.48550/arxiv.2506.03896, doi:10.48550/arxiv.2506.03896. This article has 6 citations.

34. (li2020predictiveperformanceof pages 36-40): Tianyi Li. Predictive performance of loss-in-weight feeders for continuous powder-based manufacturing. ArXiv, Jan 2020. URL: https://doi.org/10.7282/t3-6tgx-8f63, doi:10.7282/t3-6tgx-8f63. This article has 2 citations.

35. (li2020predictiveperformanceof pages 44-49): Tianyi Li. Predictive performance of loss-in-weight feeders for continuous powder-based manufacturing. ArXiv, Jan 2020. URL: https://doi.org/10.7282/t3-6tgx-8f63, doi:10.7282/t3-6tgx-8f63. This article has 2 citations.

36. (li2020predictiveperformanceof pages 40-44): Tianyi Li. Predictive performance of loss-in-weight feeders for continuous powder-based manufacturing. ArXiv, Jan 2020. URL: https://doi.org/10.7282/t3-6tgx-8f63, doi:10.7282/t3-6tgx-8f63. This article has 2 citations.

37. (humby1998predictionofhopper pages 1-2): S. J. Humby, U. Tüzün, and A. Yu. Prediction of hopper discharge rates of binary granular mixtures. Chemical Engineering Science, 53:483-494, Feb 1998. URL: https://doi.org/10.1016/s0009-2509(97)00326-6, doi:10.1016/s0009-2509(97)00326-6. This article has 74 citations and is from a highest quality peer-reviewed journal.

38. (sheldon2010granulardischargeand pages 1-2): Hannah G. Sheldon and Douglas J. Durian. Granular discharge and clogging for tilted hoppers. Granular Matter, 12:579-585, Jul 2010. URL: https://doi.org/10.1007/s10035-010-0198-3, doi:10.1007/s10035-010-0198-3. This article has 134 citations and is from a peer-reviewed journal.

39. (humby1998predictionofhopper pages 7-8): S. J. Humby, U. Tüzün, and A. Yu. Prediction of hopper discharge rates of binary granular mixtures. Chemical Engineering Science, 53:483-494, Feb 1998. URL: https://doi.org/10.1016/s0009-2509(97)00326-6, doi:10.1016/s0009-2509(97)00326-6. This article has 74 citations and is from a highest quality peer-reviewed journal.

40. (wilson2013granulardischargerate pages 4-5): T. Wilson, Charlotte R. Pfeifer, N. Mesyngier, and D. Durian. Granular discharge rate for submerged hoppers. Papers in Physics, 6:060009-060009, Jul 2013. URL: https://doi.org/10.48550/arxiv.1307.2812, doi:10.48550/arxiv.1307.2812. This article has 64 citations.

41. (wilson2013granulardischargerate pages 5-6): T. Wilson, Charlotte R. Pfeifer, N. Mesyngier, and D. Durian. Granular discharge rate for submerged hoppers. Papers in Physics, 6:060009-060009, Jul 2013. URL: https://doi.org/10.48550/arxiv.1307.2812, doi:10.48550/arxiv.1307.2812. This article has 64 citations.

42. (zuriguel2014invitedreviewclogging pages 1-2): Iker Zuriguel. Invited review: clogging of granular materials in bottlenecks. arXiv: Soft Condensed Matter, pages 060014, Dec 2014. URL: https://doi.org/10.48550/arxiv.1412.5806, doi:10.48550/arxiv.1412.5806. This article has 110 citations.

43. (gaida2026granularcloggingacross pages 3-5): Oliver Gaida, Olfa D'Angelo, and Jonathan E. Kollmer. Granular clogging across gravities: a unified scaling. Physical Review E, 114:035405, Sep 2026. URL: https://doi.org/10.1103/x3bt-63wt, doi:10.1103/x3bt-63wt. This article has 5 citations and is from a domain leading peer-reviewed journal.

44. (zheng2021onlinemeasurementof pages 14-19): Ge Zheng, Yong Yan, Yonghui Hu, and Wenbiao Zhang. Online measurement of the size distribution of pneumatically conveyed particles through acoustic emission detection and triboelectric sensing. IEEE Transactions on Instrumentation and Measurement, 70:1-17, Jan 2021. URL: https://doi.org/10.1109/tim.2021.3062407, doi:10.1109/tim.2021.3062407. This article has 20 citations and is from a highest quality peer-reviewed journal.

45. (bakker2020fieldapplicationand pages 8-10): Maarten Bakker, Florent Gimbert, Thomas Geay, Clément Misset, Sébastien Zanker, and Alain Recking. Field application and validation of a seismic bedload transport model. Journal of Geophysical Research: Earth Surface, May 2020. URL: https://doi.org/10.1029/2019jf005416, doi:10.1029/2019jf005416. This article has 75 citations.

46. (bostijn2019amultivariateapproach pages 6-10): N. Bostijn, J. Dhondt, A. Ryckaert, E. Szabó, W. Dhondt, B. V. Snick, B. V. Snick, V. Vanhoorne, C. Vervaet, and T. D. Beer. A multivariate approach to predict the volumetric and gravimetric feeding behavior of a low feed rate feeder based on raw material properties. International Journal of Pharmaceutics, 557:342–353, Feb 2019. URL: https://doi.org/10.1016/j.ijpharm.2018.12.066, doi:10.1016/j.ijpharm.2018.12.066. This article has 90 citations and is from a domain leading peer-reviewed journal.

47. (diaz2023machinelearningapproaches pages 1-2): Laura Pereira Diaz, Cameron J. Brown, Ebenezer Ojo, Chantal Mustoe, and Alastair J. Florence. Machine learning approaches to the prediction of powder flow behaviour of pharmaceutical materials from physical properties. Digital Discovery, 2:692-701, Jan 2023. URL: https://doi.org/10.1039/d2dd00106c, doi:10.1039/d2dd00106c. This article has 37 citations and is from a peer-reviewed journal.

48. (dastgerdi2024asimplifiedcalibration pages 2-4): Rashid Hajivand Dastgerdi and Agnieszka A. Malinowska. A simplified calibration procedure for dem simulations of granular material flow. Materials, 17:4833, Sep 2024. URL: https://doi.org/10.3390/ma17194833, doi:10.3390/ma17194833. This article has 22 citations.

49. (dastgerdi2024asimplifiedcalibration pages 4-6): Rashid Hajivand Dastgerdi and Agnieszka A. Malinowska. A simplified calibration procedure for dem simulations of granular material flow. Materials, 17:4833, Sep 2024. URL: https://doi.org/10.3390/ma17194833, doi:10.3390/ma17194833. This article has 22 citations.

50. (cheng2021bayesianuncertaintyquantification pages 8-9): Hongyang Cheng, Vanessa Magnanimo, Takayuki Shuku, Stefan Luding, and Thomas Weinhart. Bayesian uncertainty quantification for geomechanical models at micro and macro scales. Challenges and Innovations in Geomechanics, pages 837-845, Jan 2021. URL: https://doi.org/10.1007/978-3-030-64514-4\_90, doi:10.1007/978-3-030-64514-4\_90. This article has 3 citations.

51. (hadi2024adaptiveaibasedsurrogate pages 19-19): Ahmed Hadi, Morteza Moradi, Yusong Pang, and Dingena Schott. Adaptive ai-based surrogate modelling via transfer learning for dem simulation of multi-component segregation. Scientific Reports, Nov 2024. URL: https://doi.org/10.1038/s41598-024-78455-7, doi:10.1038/s41598-024-78455-7. This article has 23 citations and is from a peer-reviewed journal.

52. (wang2016usingmultivariateanalysis pages 64-68): Yifan Wang. Using multivariate analysis for pharmaceutical drug product development. ArXiv, Jan 2016. URL: https://doi.org/10.7282/t39z9770, doi:10.7282/t39z9770. This article has 10 citations.
