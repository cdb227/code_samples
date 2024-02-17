import numpy as np
import glob
import xarray as xr
import random
from sklearn.utils import shuffle
import tensorflow as tf
from tensorflow.keras.layers import Input, Dense, Dropout, Concatenate, BatchNormalization
from tensorflow.keras.models import Model
from keras.callbacks import EarlyStopping, ModelCheckpoint
from numpy.lib import stride_tricks
from scipy.ndimage.filters import gaussian_filter1d


def patch_func(arr,patch_size,overlap, threed=False):
	
    h,w = arr.shape[0],arr.shape[1]
	if threed:
		shape = ((h - patch_size)//(patch_size) + 1 , (w - patch_size)//(patch_size-overlap) + 1, patch_size, patch_size,  arr.shape[2])
		r,c,z = arr.strides
		strides = ((patch_size)*r,(patch_size-overlap)*c,r,c,z)
	else:
		shape = ( (h - patch_size)//(patch_size) + 1 , (w - patch_size)//(patch_size-overlap) + 1, patch_size, patch_size)
		r,c = arr.strides
		strides = ((patch_size)*r,(patch_size-overlap)*c,r,c)
    blocks=stride_tricks.as_strided(arr, shape=shape, strides=strides)
    return blocks


def rolling_window(a, window_size):
    shape = (a.shape[0] - window_size + 1, window_size) + a.shape[1:]
    strides = (a.strides[0],) + a.strides
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)


############
#DATAPREP
timestamp = '03UTC'
threshold = 14e-4 #twp threshold for what we consider clear or cloudy
NN_outputpath = './NN_models/PREFIRE_cloudmask/modelvariable_noise/'

#has shape: (nlat, nlon, nchannel)
cldsky_radiances = xr.open_dataset('./TIRS_SRF_v0.10.4/{timestamp}/TIRS_radiance_20160801_{timestamp}.h5').rad
clrsky_radiances = xr.open_dataset('./TIRS_SRF_v0.10.4_clrsky/{timestamp}/TIRS_radiance_20160801_{timestamp}.h5').rad


lwp = xr.open_dataset('./GFDL_sim_wps/GFDL_lwp_{timestamp}.nc4').lwp
iwp = xr.open_dataset('./GFDL_sim_wps/GFDL_iwp_{timestamp}.nc4').iwp

#if desired, we can select only polar regions very easily.
#polar_rad = cldsky_radiances.sel(latitude=slice(-90,-60)+slice(60,90))
#polar_iwp = iwp.sel(latitude=slice(-90,-60)+slice(60,90))
#polar_lwp = lwp.sel(latitude=slice(-90,-60)+slice(60,90))


radiances = np.array(cldsky_radiances) # has shape (2048,12288, 54), 3km resolution

#define patches to introduce inhomogeneity, 3x3 blocks from regular grid
patch_size = 3 #3x3
overlap = 2 #how much overlap from previous patch in lon direction (this is how TIRS works)
radiances = patch_func(radiances,patch_size=patch_size,overlap=overlap, threed=True)

radiances = radiances.mean(axis=(2,3)) #take mean of patch to represent inhomogeneous footprint sat would observe
radiances = np.swapaxes(radiances,0,1).reshape((-1,54), order = 'F') #we'll essentially just flatten this to (nray, nchannel)

N_radiances = len(radiances) #nray

#the above are 'perfect' observations, lets introduce some measurement uncertainty, we'll assume gaussian noise
#the sigma value for the noise at each channel (63)
noise_xr = xr.open_dataset('./TIRS_ancillary/PREFIRE_SRF_v0.10.4_360_2021-03-28.nc')

#the std of noise for each channel
sigma_noise= np.array(noise_xr.NEDR)
#help to determine which channels are always masked (63 -> 54) 0 or 1 filters are masked
clear_channel = np.where(noise_xr.filter_number > 1)
sigma_noise = sigma_noise[clear_channel[0]][:,0] #select only those that aren't masked by bad detectors, gives shape (54,)

#we remove the first two channels since they're SW and we can't model them correctly right now
#apply noise random noise with mu=0 to our coarsened radiances.
radiances = radiances[:,2:] + (np.random.normal(0,1,size=(N_radiances,len(sigma_noise[2:])))*sigma_noise[None,2:])


#ADD MODEL VARIABLES
#we'll also include estimates of surface temp and column water vapor to our features
ts = np.array(xr.open_dataset(glob.glob('./GFDL_fields_3km/ts/ts*{}*'.format(timestamp))[0]).ts) - 273.15
pwv=np.array(xr.open_dataset('./GFDL_data/20160801_{}_GFDL_pwv.nc'.format(timestamp)).pwv*1000.)[3,:,:]

#Make patches with ts.
ts = patch_func(ts, patch_size = patch_size, overlap=overlap)
ts = ts.mean(axis=(2,3))
ts = np.swapaxes(ts,0,1).reshape((-1,1), order = 'F')

#Make patches with column water vapor
pwv = patch_func(pwv, patch_size = patch_size, overlap=overlap)
pwv = pwv.mean(axis=(2,3))
pwv = np.swapaxes(pwv,0,1).reshape((-1,1), order = 'F')

#append these to our radiances, each which also have noise (1K for ts, 10% relative noise for cwv)
radiances = np.hstack((radiances,ts + np.random.normal(0,1,size=(N_radiances)).reshape((-1,1), order = 'F')))
radiances = np.hstack((radiances,pwv+ np.random.normal(0,pwv*0.1).reshape((-1,1), order = 'F' )))


#we'll use values of twp (iwp+lwp) to determine what we consider 'cloud' or 'clear'
cloud = lwp + iwp
#essentially repeat procedure as above but with clouds. 
cloud = patch_func(np.array(cloud),patch_size=patch_size,overlap=overlap)
cloud = cloud.mean(axis=(2))
cloud = np.swapaxes(cloud[:,:,2],0,1).reshape((-1), order = 'F')

#we'll feed in three patches at a time, each has some redundant information
#we only predict that which is overlapped by three footprints.
#see Bertossa et al. 2023 for a full explanation.

window = patch_size
cloud = rolling_window(cloud,window)[:,2]
#if twp>threshold, make it 'cloud'(1) otherwise 'clear' (0)
cloud = np.array(xr.where(cloud>threshold, 1., 0.))

#set of 3 radiances which have common overlap
radiances = rolling_window(radiances,window)


#weight our classes so that clear and cloud predictions are STATISTICALLY equally important
clear_ct = len(np.where(cloud == 0)[0])
cloud_ct = len(np.where(cloud == 1)[0])
total_ct = clear_ct + cloud_ct

weight_for_0 = (1. / clear_ct)*(total_ct)/2.0 
weight_for_1 = (1. / cloud_ct)*(total_ct)/2.0
class_weight = {0: weight_for_0, 1: weight_for_1}

print('Weight for class 0: {:.2f}'.format(weight_for_0))
print('Weight for class 1: {:.2f}'.format(weight_for_1))

#shuffle
ran_shuffle_seed = random.randint(0,10000)
cloud, radiances = shuffle(cloud,radiances, random_state = ran_shuffle_seed)   

#define shape of input (should be 54, in this case)
nfeature = radiances.shape[-1]
input1 = Input(shape=(nfeature,)) #each of our three footprints
input2 = Input(shape=(nfeature,))
input3 = Input(shape=(nfeature,))
inputs = Concatenate()([input1, input2,input3])
#batchnorm to help with globalization
inputs = BatchNormalization()(inputs)
#2 hidden layers, each with dropouts to help with overfitting
hidden = Dense(256, activation = 'relu')(inputs)
hidden = Dropout(0.2)(hidden)
hidden = Dense(256, activation = 'relu')(hidden)
hidden = Dropout(0.3)(hidden)
#final output results in probability of clear, probability of cloud
output = Dense(units = 2, activation='softmax')(hidden )
model = Model([input1,input2,input3], output)
#scc for loss
model.compile(optimizer= 'adam',loss='sparse_categorical_crossentropy', metrics= ['acc'])

epochs = 200
batch_size = 10000

#only save the best model, not the final. 
es = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=25)
mc = ModelCheckpoint( NN_outputpath+'overlapping_modelvar',
	monitor='val_loss', mode='min', verbose=1, save_best_only=True)

#split 25% of data for validation set
model.fit([radiances[:,0,:], radiances[:,1,:], radiances[:,2,:] ], cloud, 
		  batch_size=batch_size,epochs=epochs,verbose = 1, 
		  callbacks = [es,mc], class_weight=class_weight, validation_split=0.25)
