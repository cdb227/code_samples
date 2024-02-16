## Overview

This folder is dedicated less to the code and more to the visualizations I've created. I have attached portions of code which are used to create these visualizations, however, these are typically extracted from larger projects.
Here I'll describe what is being shown and for what purpose.

## Contents

### Project: Barotropic Model
The purpose of this project is to create an atmospheric toy model to solve the forced barotropic vorticity equations and apply this model within the context of ensemble forecasts.
It has several different settings which can be modified, such as using linear or nonlinear dynamics, different forcing scenarios, the number of ensemble members and how the initial conditions are perturbed.
One of the mains goals of this project is to explore how different forcing scenarios or ensemble initialisations can lead to bimodality in ensemble forecasts.

This model was created from scratch, solving the vorticity equation through spherical harmonics (via the **spharm** Python package)
#### Example Run
<p align="center">
  <img src="https://github.com/cdb227/code_samples/new/main/visualizations/barotropic_overview.gif" alt="animated" />
</p>
<p align="center">
  <em>An example 4-week integration of the model. Winds stir the temperature field. The left panel depicts winds relative to the zonal mean and the right panel are the total winds. The complex forcing term ensures that individual wave numbers are phase shifted relative to one another, removing zonally-dependent mixing over time.</em>
</p>

#### Ensemble Run
<p align="center">
 <img src="https://github.com/cdb227/code_samples/new/main/visualizations/barotropic_ensemble.gif" alt="animated" />
</p>
<p align="center">
  <em>
  A 10-member ensemble run of the above model, ensemble members decorrelate over time via the forcing term. The point in the domain with the largest variance at time = T is chosen and ensemble members are tracked to their origin location (as seen at t=0).
    Lines change color based on the temperature value of the ensemble member at time = t. Dashed contours depict the equilibrium temperature structure. Dots indicate the initial ensemble temperature. Here you can see the influence of initial condition on ensemble spread at t=T
  </em>
</p>
