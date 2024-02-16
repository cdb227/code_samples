## Overview

This folder showcases visualizations created for various projects, providing insights into atmospheric phenomena and ensemble forecasting. While the focus is on visualizations, snippets of code used in their creation are included, extracted from larger projects.

## Contents

### Project: Barotropic Model

The purpose of this project is to create an atmospheric toy model to solve the forced barotropic vorticity equations and apply this model within the context of ensemble forecasts.
It has several different settings which can be modified, such as using linear or nonlinear dynamics, different forcing scenarios, the number of ensemble members and how the initial conditions are perturbed.
One of the mains goals of this project is to explore how different forcing scenarios or ensemble initialisations can lead to bimodality in ensemble forecasts.

This model, developed from scratch, solves the vorticity equation using spherical harmonics via the **spharm** Python package.

#### Example Run
An example 4-week integration of the model is displayed below. The animation depicts winds stirring the temperature field, with the left panel showing winds relative to the zonal mean and the right panel showing total winds. The complex forcing term ensures phase shifts among individual wave numbers, removing zonally-dependent mixing over time.

![Example Run](https://github.com/cdb227/code_samples/blob/main/visualizations/barotropic_overview.gif)

#### Ensemble Run
The animation below illustrates a 10-member ensemble run of the model. Ensemble members decorrelate over time via the forcing term. The point in the domain with the largest variance at t=T is selected and ensemble members are traced back to their origin locations. Lines change color based on ensemble member temperature at each time step, while dashed contours represent the equilibrium temperature structure. Dots indicate initial temperature of the ensemble member. This visualization shows the memory in temperature and how it leads to ensemble spread via advection.

![Ensemble Run](https://github.com/cdb227/code_samples/blob/main/visualizations/barotropic_ensemble.gif)

