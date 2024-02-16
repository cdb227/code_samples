import numpy as np
import xarray as xr
import random

import cartopy                   
import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from cartopy.util import add_cyclic_point

import matplotlib as mpl          
from matplotlib.colors import BoundaryNorm
import matplotlib.pyplot as plt    
import matplotlib.animation as manim
import matplotlib.ticker as mticker
import matplotlib.path as mpath

import seaborn as sns

s2d = 1/86400.
d2r = np.pi / 180.



#+++Simple plot modifications+++#
def make_ax_circular(ax):
    """
    Make an axes circular, useful for polar stereographic projections
    """
    theta = np.linspace(0, 2*np.pi, 100)
    center, radius = [0.5, 0.5], 0.5
    verts = np.vstack([np.sin(theta), np.cos(theta)]).T
    circle = mpath.Path(verts * radius + center) 
    ax.set_boundary(circle, transform=ax.transAxes)
    return ax

def add_gridlines(ax):
    """
    Add gridlines to plot
    """
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, 
                  linewidth=2, color='gray', alpha=0.5, linestyle='--')
    gl.xlabels = False
    #gl.xlabel_bottom = False
    gl.xlines = False
    gl.ylocator = mticker.FixedLocator([45,60,75])
    gl.xlocator = mticker.FixedLocator([])
    #gl.xlocator = mticker.FixedLocator([-180, -45, 0, 45, 180])
    return ax



def overview_animation(ds, times, xs, ts=None, filename = './images/overview.gif', step=3600*2):
     """
    Generate an animation providing an overview of a single barotropic model run.

    This function creates an animation showing the evolution of vorticity and potential temperature over time,
    along with wind vectors. Optionally, it can overlay trajectories on the plots.

    Parameters:
        ds (xarray.Dataset): Dataset containing vorticity, potential temperature, and wind data.
        times (tuple): Tuple containing the start and end times for the animation.
        xs (numpy.ndarray): Array containing trajectory positions.
        ts (numpy.ndarray, optional): Array containing trajectory times.
        filename (str, optional): Name of the output file.
        step (int, optional): Time step for animation.
    """
	proj=ccrs.NorthPolarStereo()
    #frames to be generated
    frames = np.arange(times[0], times[1], step)
    
    # Check if the specified time period is within the data range
    if times[0] < ds.time.data[0] or times[1] > ds.time.data[-1]:
        raise ValueError('You are trying to animate a time period there is no data for.')
        
    skip = 3
    x = ds.x.data[::skip] #thin wind vectors to make things  a bit more clear.
    y = ds.y.data[::skip]
        
    plt.ioff()
    fig, axs = plt.subplots(1,2, subplot_kw={'projection': proj}, figsize=(5,3.5),sharex=True,sharey=True, dpi=120)

    axs[0].set_extent([-179.9, 179.9, 20, 90], crs=ccrs.PlateCarree())

    make_ax_circular(axs[0])
    
    ds = xr.concat([ds, ds.isel(x=slice(0,1)).assign_coords(x=[360])], dim='x')
    
    # Set up color mapping and levels for vorticity
    #temporary patch due to cartopy's bug with certain contourf levels not showing
    cmap = plt.colormaps['bwr']
    norm = BoundaryNorm(np.linspace(-1.5,1.5,6), ncolors=cmap.N, clip=True)      
    cf=axs[0].pcolormesh(ds.x.data,ds.y.data,ds.vortp.interp(time=0).data*1e5, transform = ccrs.PlateCarree(), 
            cmap=cmap,norm=norm)
    plt.colorbar(cf, ax=axs[0], label= r"$\zeta$' (s$^{-1}$)", orientation='horizontal', shrink=0.9)
    
    
    # Set up color mapping and levels for potential temperature
    templevs = np.arange(255,300,5)
    cf=axs[1].contourf(ds.x.data,ds.y.data,ds.theta.interp(time=0).data, transform = ccrs.PlateCarree(), 
            levels = templevs, cmap='RdBu_r', extend='both')
    cbar=plt.colorbar(cf, ax=axs[1], label= r"$\theta$ (K)", orientation='horizontal', shrink=0.9)
    plt.setp(cbar.ax.get_xticklabels()[::2], visible=False)
    
    # Plot wind vectors
    #find thinned winds
    u = ds.u.interp(time=0).data[::skip, ::skip]
    v = ds.v.interp(time=0).data[::skip, ::skip]
    
    #note we plot u' on vorticity and total u on theta
    q=axs[0].quiver(x, y, u - u.mean(axis=1)[:,None], v, transform = ccrs.PlateCarree(), 
                    color = '0.2', units='inches', scale=50., width=0.01, pivot = 'mid',zorder=10)
    axs[0].quiverkey(q, X=0.9, Y=1.0, U=10,label="u' 10 m/s", labelpos='N')
    
    q=axs[1].quiver(x, y, u, v, transform = ccrs.PlateCarree(), 
                    color = '0.2', units='inches', scale=100., width=0.01, pivot = 'mid',zorder=10)
    axs[1].quiverkey(q, X=0.9, Y=1.0, U=10,label='U 10 m/s', labelpos='N')
    

    def anim(t):
        #find thinned winds at frame time
        u = ds.u.interp(time=t).data[::skip, ::skip]
        v = ds.v.interp(time=t).data[::skip, ::skip]
        
        plt.ioff()
        title = '{:.2f} days'.format(t*s2d)
        
        for ax in axs: #do these to each axes
            ax.cla() #clear the axis
            make_ax_circular(ax)
            ax.set_extent([-179.9, 179.9, 20, 90], crs=ccrs.PlateCarree())
            # Set the plot title
            ax.set_title(title, fontsize=9) #add titile

        #plot vorticity
        cf=axs[0].pcolormesh(ds.x.data,ds.y.data,ds.vortp.interp(time=t).data*1e5, transform = ccrs.PlateCarree(), 
            cmap=cmap,norm=norm)
        #plot theta
        cf=axs[1].contourf(ds.x.data,ds.y.data,ds.theta.interp(time=t).data, transform = ccrs.PlateCarree(), 
                    levels =templevs, cmap='RdBu_r', extend='both')
        
        #add quivers
        q=axs[0].quiver(x, y, u - u.mean(axis=1)[:,None], v, transform = ccrs.PlateCarree(), 
                        color = '0.2', units='inches', scale=50., width=0.01, pivot = 'mid',zorder=10)
        axs[0].quiverkey(q, X=0.9, Y=1.0, U=10,label="u' 10 m/s", labelpos='N')
        
        
        q=axs[1].quiver(x, y, u, v, transform = ccrs.PlateCarree(), 
                        color = '0.2', units='inches', scale=100., width=0.01, pivot = 'mid',zorder=10)
        axs[1].quiverkey(q, X=0.9, Y=1.0, U=10,label='U 10 m/s', labelpos='N')
            

        #add trajectories if supplied
        if ts != None:
            Ntraj = xs.shape[2]
            for i in range(Ntraj):
                ind = np.where(ts[:, i] < t)[0] #only plot trajectories less than animation time
                if len(ind) > 0:
                    #plot traj in red, add xs every so often to make tracks clearer
                    ax.plot( xs[ind      , 0, i] ,  xs[ind      , 1, i],  'r', lw=2., transform = ccrs.PlateCarree(),)
                    ax.plot([xs[ind[0]   , 0, i]], [xs[ind[0]   , 1, i]], 'kx', transform = ccrs.PlateCarree(),)
                    ax.plot( xs[ind[25::50], 0, i] ,  xs[ind[25::50], 1, i],  'k+', transform = ccrs.PlateCarree(),)

                    if len(ind) < ts.shape[0]: #first timestep condition
                        ax.plot([xs[ind[-1]  , 0, i]], [xs[ind[-1]  , 1, i]], 'ro', transform = ccrs.PlateCarree(),)

        plt.ion()
        plt.draw()

    anim = manim.FuncAnimation(fig, anim, frames, repeat=False)
    
    anim.save(filename, fps=12, codec='h264', dpi=120)
    plt.ion()

	
def animate_thetaens(ds, times, xs, ts=None, tlevs = np.arange(0,12,2),
                     filename = 'espread.gif', step=3600*2, mod=False):
    """
    Animate the spread of theta and optionally include trajectories.

    Parameters:
        ds (xarray.Dataset): Dataset containing temperature data for an ensemble.
        times (tuple): Tuple containing the start and end times for animation.
        xs (numpy.ndarray): Array containing trajectory positions.
        ts (numpy.ndarray, optional): Array containing trajectory times.
        tlevs (numpy.ndarray, optional): Levels for contour plot.
        filename (str, optional): Name of the output file.
        step (int, optional): Time step for animation.
        
    """

    frames = np.arange(times[0], times[1], step)
    
    # Check if the specified time period is within the data range
    if times[0] < ds.time.data[0] or times[1] > ds.time.data[-1]:
        raise ValueError('You are trying to animate a time period '
                        'there is no data for.')
    skip = 3
        
    plt.ioff()
    #create figure
    f = plt.figure(3, figsize = (5, 3.5), dpi = 200)
    f.clf()
    ax = plt.subplot(1, 1, 1, projection = ccrs.NorthPolarStereo())
    ax.set_extent([-179.9, 179.9, 20, 90], crs=ccrs.PlateCarree())

    make_ax_circular(ax) #make ciruclar since we'll use NPS projection
    
    # Fix prime meridian issue when plotting
    ds=xr.concat([ds, ds.isel(lon=slice(0,1)).assign_coords(lon=[180])], dim='lon')
    background = ds.theta.sel(ens_mem=0).sel(time=0) #equilibrium temp profile
    theta = ds.theta.std('ens_mem')
    
    #use to get colorbar
    cm = sns.color_palette("light:seagreen", as_cmap=True)
    normcm = mpl.colors.BoundaryNorm(tlevs, cm.N)
    
    #plot contourf of ensemble spread in theta
    cf=ax.contourf(theta.lon.data, theta.lat.data, theta.interp(time=times[1]).data, transform = ccrs.PlateCarree(), 
            levels=tlevs,cmap=cm, norm=normcm)
    #add colorbar
    plt.colorbar(cf, ax=ax, label='Std(Temp) (K)',shrink=0.8)
    Ntraj = xs.shape[2] #find how many trajectories there are
    
    btlev= np.arange(250,300,5)
    norm = plt.Normalize(btlev[0], btlev[-1])
    cmap = plt.cm.coolwarm
    #plot equilibrium temperature profile
    ax.contour(background.lon.data, background.lat.data, background.data,
           cmap=cmap, levels=btlev, transform=ccrs.PlateCarree(),linestyles='--', alpha=0.75,zorder=10)
        
    
    def anim(t):
        """
        Animate each frame of the plot.
        Parameters:
            t (int): Frame index.
        """
        
        plt.ioff()
        ax.cla()
        make_ax_circular(ax)
        ax.set_extent([-179.9, 179.9, 20, 90], crs=ccrs.PlateCarree())
        
        # Update contourf plot for theta, equil temp contours
        cf=ax.contourf(theta.lon,theta.lat, theta.interp(time=t).data, transform = ccrs.PlateCarree(), 
                    cmap=cm, levels=tlevs,norm=normcm)
        ct=ax.contour(background.lon.data, background.lat.data, background.data,
           cmap=cmap, levels=btlev, transform=ccrs.PlateCarree(),zorder=10,linestyles='--', alpha=0.75)

        # Set the plot title
        title = '{:.2f} days'.format(t*s2d)
        ax.set_title(title, fontsize=9)
        
        for i in range(Ntraj):# plot each individual contour
            ind = np.where(ts[:, i] < t)[0] #only plot portion of traj that is less than current time

            if len(ind) > 0:
                #cols = ds.theta.sel(ens_mem=i).interp(time=ts[50::100,i], lon=xs[50::100, 0, i] ,  lat=xs[50::100, 1, i]).values
                #ax.plot( xs[50::100, 0, i] ,  xs[50::100, 1, i],   c=cmap(norm(cols)), lw=0., marker='o', transform = ccrs.PlateCarree(),)
                
                # Get color of trajectory based on current temperature
                col = ds.theta.sel(ens_mem=i).interp(time=t, lon=xs[ind[-1],0,i], lat=xs[ind[-1],1,i]).item(0)
                
                #plot trajectory
                if mod: #there's a weird artifact that occurs if our traj cross the prime meridian. Adjust if necessary
                    ax.plot( sanitize_lonlist(xs[ind      , 0, i]) ,  xs[ind      , 1, i],
                            c=cmap(norm(col)), lw=2., transform = ccrs.PlateCarree(),zorder=20)
                else:
                    ax.plot( xs[ind      , 0, i] ,  xs[ind      , 1, i],  c=cmap(norm(col)), lw=2.,
                            transform = ccrs.PlateCarree(),zorder=20)
                #plot an 'x' tick every so often to help with clarity
                ax.plot([xs[ind[0]   , 0, i]], [xs[ind[0]   , 1, i]], 'kx', zorder=20,transform = ccrs.PlateCarree(),)
                #ax.plot( xs[ind[25::50], 0, i] ,  xs[ind[25::50], 1, i],  'k+', transform = ccrs.PlateCarree(),)

                if len(ind) < ts.shape[0]: #first timestep condition
                    #initial point with a scatter dot, use equilibrium temp.
                    col = ds.theta.sel(ens_mem=i).interp(time=0, lon=xs[-1,0,i],lat=xs[-1,1,i]).item(0)

                    ax.scatter([xs[ind[-1]  , 0, i]], [xs[ind[-1]  , 1, i]], c= col, norm=norm, cmap=cmap,
                     transform=ccrs.PlateCarree(), zorder=30)

        plt.ion()
        plt.draw()

    anim = manim.FuncAnimation(f, anim, frames, repeat=False)
    
    anim.save(filename, fps=12, codec='h264', dpi=200)
    plt.ion()
    
        
def sanitize_lonlist(lons):
    """
    This fixes an issue when moving across meridians with line plots 
    """
    lons = np.array(lons)
    diffs = np.diff(lons)
    wraploc = np.where(abs(diffs)>30)[0]+1
    #for ii in wraploc:
    if len(wraploc)>0:
        if lons[0]>0: #goes from 180 -> -180
            lons[wraploc[0]:]+=360
        else: #goes form -180 -> 180
            lons[wraploc[0]:]-=360
        
    return lons    
