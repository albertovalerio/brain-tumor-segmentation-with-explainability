"""
A set of plotting functions
"""
import matplotlib.pyplot as plt
import random
import os
from nilearn import plotting
import nibabel as nib
from utils.utils import get_colored_mask, get_slice


def plot_random_samples(folder, n_samples, axis):
	"""Plot sample data.
	Args:
		folder (str): the path of the folder containing data.
		n_samples (int): number of samples to plot. Min value is 2.
		axis (int): axis of the spatial image. Values are: 0=X_axis, 1=Y_axis, 2=Z_axis.
	Returns:
		None.
	"""
	if n_samples > 1 and axis < 3:
		samples = random.sample(os.listdir(folder), n_samples)
		fig, axs = plt.subplots(n_samples, 5, figsize=(18, n_samples * 4))
		for i, axl in enumerate(axs):
			images = sorted(os.listdir(os.path.join(folder, samples[i])))
			images.append(images.pop(images.index(images[0])))
			if i == 0:
				axl[0].set_title('post-contrast T1-weighted')
				axl[1].set_title('T1-native')
				axl[2].set_title('T2-FLAIR')
				axl[3].set_title('T2-weighted')
				axl[4].set_title('Segmented')
			for j, ax in enumerate(axl):
				if j == 0:
					ax.set_ylabel(samples[i])
				brain_vol = nib.load(os.path.join(os.path.join(folder, samples[i]), images[j]))
				isocenter = list(map(int, plotting.find_xyz_cut_coords(brain_vol)))
				if j == len(images) - 1:
					mask_colored = get_colored_mask(get_slice(brain_vol, axis, isocenter[axis]))
					brain_vol = nib.load(os.path.join(os.path.join(folder, samples[i]), images[j - 1]))
					ax.imshow(get_slice(brain_vol, axis, isocenter[axis]), cmap='gist_yarg')
					ax.imshow(mask_colored)
				else:
					ax.imshow(get_slice(brain_vol, axis, isocenter[axis]), cmap='gist_yarg')
				ax.spines['top'].set_visible(False)
				ax.spines['right'].set_visible(False)
				ax.spines['bottom'].set_visible(False)
				ax.spines['left'].set_visible(False)
				a = {0:'X',1:'Y',2:'Z'}
				ax.set_xlabel(a[axis]+'='+str(isocenter[axis]))
				ax.get_xaxis().set_ticks([])
				ax.get_yaxis().set_ticks([])
		fig.tight_layout()
		plt.show()
	else:
		print('\n' + ''.join(['> ' for i in range(40)]))
		print('\nERROR: \033[95m n_samples\033[0m must be greater that \033[95m 1\033[0m and \033[95m axis\033[0m bust be lower that \033[95m 2\033[0m.\n')
		print(''.join(['> ' for i in range(40)]) + '\n')


def plot_single_sample(folder):
	"""Plot sample data.
	Args:
		folder (str): the path of the folder containing data.
	Returns:
		None.
	"""
	samples = random.sample(os.listdir(folder), 1)
	images = sorted(os.listdir(os.path.join(folder, samples[0])))
	images.append(images.pop(images.index(images[0])))
	fig, axs = plt.subplots(3, 5, figsize=(18, 12))
	for i, axl in enumerate(axs):
		if i == 0:
			axl[0].set_title('post-contrast T1-weighted')
			axl[1].set_title('T1-native')
			axl[2].set_title('T2-FLAIR')
			axl[3].set_title('T2-weighted')
			axl[4].set_title('Segmented')
		for j, ax in enumerate(axl):
			brain_vol = nib.load(os.path.join(os.path.join(folder, samples[0]), images[j]))
			isocenter = list(map(int, plotting.find_xyz_cut_coords(brain_vol)))
			if j == len(images) - 1:
				mask_colored = get_colored_mask(get_slice(brain_vol, i, isocenter[i]))
				brain_vol = nib.load(os.path.join(os.path.join(folder, samples[0]), images[j - 1]))
				ax.imshow(get_slice(brain_vol, i, isocenter[i]), cmap='gist_yarg')
				ax.imshow(mask_colored)
			else:
				ax.imshow(get_slice(brain_vol, i, isocenter[i]), cmap='gist_yarg')
			ax.spines['top'].set_visible(False)
			ax.spines['right'].set_visible(False)
			ax.spines['bottom'].set_visible(False)
			ax.spines['left'].set_visible(False)
			a = {0:'X',1:'Y',2:'Z'}
			ax.set_xlabel(a[i]+'='+str(isocenter[i]))
			ax.get_xaxis().set_ticks([])
			ax.get_yaxis().set_ticks([])
	brain_vol = nib.load(os.path.join(os.path.join(folder, samples[0]), images[j - 1]))
	brain_mask = nib.load(os.path.join(os.path.join(folder, samples[0]), images[j]))
	plotting.plot_epi(brain_vol, display_mode='z', cmap='hot_white_bone', title=images[j - 1])
	plotting.plot_epi(brain_mask, display_mode='z', cmap='hot_white_bone', title=images[j])
	fig.tight_layout()
	fig.suptitle(samples[0], fontsize=18)
	plt.show()
