from pprint import pprint
from skimage.measure import block_reduce
import matplotlib.pyplot as plt
import numpy as np
import os


def downsample_2d(img, block_size=(4, 4)):
    """
    Downsamples a 2D array/image using averaging.
    img: 2D numpy array.
    block_size: tuple (m, n) representing the block size to average over.
    Returns: 
        downsampled_image: 2D numpy array.
    """
    return block_reduce(img, block_size=block_size, func=np.mean)


def fit_lines(img_data):
    """
    Fits lines to a 2D array.
    img_data: 2D numpy array where rows are y-values and column indices are x-values.
    Returns: 
        individual_fits: Nx2 array where each row is [slope, intercept] for that image row.
        average_fit: 1x2 array [slope, intercept] for all data points combined.
    """
    rows, cols = img_data.shape
    x = np.arange(cols)

    # Individual line fits (one for each row)
    # np.polyfit can handle multiple y-columns if we transpose img_data
    individual_fits = np.polyfit(x, img_data.T, 1).T

    # Average line fit (pooled data points)
    x_all = np.tile(x, rows)
    y_all = img_data.flatten()
    average_fit = np.polyfit(x_all, y_all, 1)

    return individual_fits, average_fit


dir = r'C:\Users\Gregory\OneDrive - UHN\Projects\Art\2'
#img_file=os.path.join(dir,'BW_tRANSFORMED_8X6.png')
img_orig_file = os.path.join(dir,'BW_tRANSFORMED2.png')

print(os.path.isdir(dir), os.path.isfile(img_orig_file))

img =plt.imread(img_orig_file)
if len(img.shape)>2:
    assert (np.sum(np.abs(img[:, :, 1] - img[:, :, 0])) == 0)
    img = img[:,:,0]



f,ax = plt.subplots(7,1)
ax[0].imshow(img/np.max(img),cmap='gray')
y_vals1 = img[-80:,:]
#ind_fits, avg_fits = fit_lines(y_vals1)
y_vals2 = img[10:80,:]
y_vals = np.vstack((y_vals1, y_vals2))
#ind_fits, avg_fits = fit_lines(y_vals2)
ind_fits,avg_fits = fit_lines(y_vals)


"""
print("Individual Fits (Slope, Intercept):")
for i, (m, c) in enumerate(ind_fits):
    print(f"Row {i}: y = {m:.6f}x + {c:.3f}")
print(f"\nAverage Fit (All points):")
print(f"y = {avg_fits[0]:.6f}x + {avg_fits[1]:.3f}")
"""

for i in range(y_vals1.shape[0]):
    ax[1].plot(y_vals1[i,:])
y_avg = avg_fits[0]*np.arange(0,y_vals1.shape[1]) + avg_fits[1]
ax[1].plot(y_avg,'-+k')


"""
print("Individual Fits (Slope, Intercept):")
for i, (m, c) in enumerate(ind_fits):
    print(f"Row {i}: y = {m:.6f}x + {c:.3f}")
print(f"\nAverage Fit (All points):")
print(f"y = {avg_fits[0]:.6f}x + {avg_fits[1]:.3f}")
"""

for i in range(y_vals2.shape[0]):
    ax[2].plot(y_vals2[i,:])
ax[2].plot(y_avg,'-+k')
img_norm = img/y_avg
img_norm = img_norm/np.max(img_norm)

ax[3].imshow(img_norm/np.max(img_norm),cmap='gray')

yn_vals1 = img_norm[-80:,:]
#ind_fits, avg_fits = fit_lines(y_vals1)
yn_vals2 = img_norm[10:80,:]

for i in range(yn_vals2.shape[0]):
    ax[4].plot(yn_vals2[i,:])


vy_vals = np.hstack((img_norm[:,:40], img_norm[:,-40:]))
for i in range(vy_vals.shape[1]):
    #print(vy_vals[:,i])
    ax[5].plot(vy_vals[:,i])
plt.show()
#normalize image for illumination distortion across image
f,ax = plt.subplots(2,1)
ax[0].imshow(img,cmap='gray')

ax[1].imshow(img_norm,cmap='gray')
plt.show()


#img8x6bit = (plt.imread(img_file))#*255).astype(np.uint8)
size = np.array(img_norm.shape)/np.array([6,8])
# Downsample by a factor of 4 in both dimensions using mean averaging
block_size = (int(size[0]), int(size[1]))
img = img_norm
img8x6bit = downsample_2d(img, block_size=block_size)


f,ax=plt.subplots(4, 1)



ax[0].imshow(img,cmap='gray')
ax[0].axis('off')
ax[1].hist(img.flatten(), bins=255)
ax[2].imshow(img8x6bit,cmap='gray')
ax[2].axis('off')
ax[3].hist(img8x6bit.flatten(), bins=255)
plt.tight_layout()
plt.show()


plt.figure()
plt.hist(img8x6bit.flatten(), bins=256)
plt.figure()
nbins = 7
plt.hist(img8x6bit.flatten(), bins=nbins)
hist, edges = np.histogram(img8x6bit.flatten(), bins=nbins)
#edges[0] = -1

#edges[-1] = 1
count = np.zeros(7)
xnvalues = img8x6bit.flatten() #copy
for i in range(len(xnvalues)):
    for j in range(len(edges)-1):
        if xnvalues[i] >= edges[j] and xnvalues[i] <= edges[j+1]:
            xnvalues[i] = j
            count[j]+=1

assert( np.sum(np.abs(count-hist))==0 )



xnvalues = xnvalues.reshape(img8x6bit.shape)
xnvalues = xnvalues.astype(int)
f,ax = plt.subplots(3,1)
ax[0].imshow(img_norm,cmap='gray')
ax[1].imshow(xnvalues,cmap='gray')

ax[2].imshow(img8x6bit,cmap='gray')
plt.axis('off')
img_ravel = img8x6bit.ravel()
print(pprint(img8x6bit))
print(pprint(xnvalues))
xset = set(xnvalues.ravel())
xset = [int(x) for x in xset]
print(xset)
plt.show()

