from pprint import pprint
from skimage.measure import block_reduce
import matplotlib.pyplot as plt
import numpy as np
import os



dir = r'C:\Users\Gregory\OneDrive - UHN\Projects\Art\2'
img_file=os.path.join(dir,'BW_tRANSFORMED_8X6.png')
img_orig_file = os.path.join(dir,'BW_tRANSFORMED2.png')
img =plt.imread(img_orig_file)
if len(img.shape)>2:
    assert (np.sum(np.abs(img[:, :, 1] - img[:, :, 0])) == 0)
    img = img[:,:,0]



f,ax = plt.subplots(3,1)
ax[0].imshow(img)
y_vals = img[-80:,:]
for i in range(y_vals.shape[0]):
    ax[1].plot(y_vals[i,:])

y_vals = img[10:80,:]
for i in range(y_vals.shape[0]):
    ax[2].plot(y_vals[i,:])

plt.show()





img8x6bit = (plt.imread(img_file))#*255).astype(np.uint8)

# Downsample by a factor of 4 in both dimensions using mean averaging
block_size = (4, 4)

downsampled_image_avg = block_reduce(img, block_size=block_size, func=np.mean)


f,ax=plt.subplots(4, 1)



ax[0].imshow(img,cmap='gray')
ax[0].axis('off')
ax[1].hist(img.flatten(), bins=255)
ax[2].imshow(img8x6bit,cmap='gray')
ax[2].axis('off')
ax[3].hist(img8x6bit.flatten(), bins=255)
plt.tight_layout()
plt.show
plt.figure()
plt.hist(img8x6bit.flatten(), bins=256)
plt.figure()
nbins = 8
plt.hist(img8x6bit.flatten(), bins=nbins)
hist, edges = np.histogram(img8x6bit.flatten(), bins=nbins)
xnvalues = img8x6bit.flatten() #copy
for i in range(len(xnvalues)):
    for j in range(len(edges)-1):
        if xnvalues[i] >= edges[j] and xnvalues[i] < edges[j+1]:
            xnvalues[i] = j

xnvalues = xnvalues.reshape(img8x6bit.shape)
xnvalues = xnvalues.astype(int)
plt.figure()
plt.imshow(xnvalues,cmap='gray')
plt.axis('off')
img_ravel = img8x6bit.ravel()
print(pprint(xnvalues))
xset = set(xnvalues.ravel())
xset = [int(x) for x in xset]
print(xset)
plt.show()

