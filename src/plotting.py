"""
A set of plotting functions
"""
import os, random
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from nilearn import plotting
import nibabel as nib
from utils import get_colored_mask, get_slice, get_brats_classes
from config import get_config


def plot_random_samples(folder, n_samples, axis):
	"""
	Plot a comparison between different n data examples.
	Args:
		folder (str): the path of the folder containing data.
		n_samples (int): number of samples to plot. Min value is 2.
		axis (int): axis of the spatial image. Values are: 0=X_axis, 1=Y_axis, 2=Z_axis.
	Returns:
		None.
	"""
	_config = get_config()
	channels = _config.get('CHANNELS')
	if n_samples > 1 and axis < 3:
		samples = random.sample(os.listdir(folder), n_samples)
		fig, axs = plt.subplots(n_samples, 5, figsize=(18, n_samples * 4))
		for i, axl in enumerate(axs):
			images = sorted(os.listdir(os.path.join(folder, samples[i])))
			images.append(images.pop(images.index(images[0])))
			if i == 0:
				for k in range(5):
					axl[k].set_title(channels[k])
			for j, ax in enumerate(axl):
				if j == 0:
					ax.set_ylabel(samples[i])
				brain_vol = nib.load(os.path.join(os.path.join(folder, samples[i]), images[j]))
				isocenter = list(map(int, plotting.find_xyz_cut_coords(brain_vol)))
				if j == len(images) - 1:
					mask_colored, _ = get_colored_mask(get_slice(brain_vol, axis, isocenter[axis]))
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


def plot_single_sample(folder, session=None):
	"""
	Plot different views of a single sample data.
	Args:
		folder (str): the path of the folder containing data.
		session (str): a session ID, if not provided a random ID will be selected.
	Returns:
		None.
	"""
	_config = get_config()
	channels = _config.get('CHANNELS')
	sample = session if session else random.sample(os.listdir(folder), 1)[0]
	images = sorted(os.listdir(os.path.join(folder, sample)))
	images.append(images.pop(images.index(images[0])))
	fig, axs = plt.subplots(3, 5, figsize=(18, 12))
	for i, axl in enumerate(axs):
		if i == 0:
			for k in range(5):
				axl[k].set_title(channels[k])
		for j, ax in enumerate(axl):
			brain_vol = nib.load(os.path.join(os.path.join(folder, sample), images[j]))
			isocenter = list(map(int, plotting.find_xyz_cut_coords(brain_vol)))
			if j == len(images) - 1:
				mask_colored, _ = get_colored_mask(get_slice(brain_vol, i, isocenter[i]))
				brain_vol = nib.load(os.path.join(os.path.join(folder, sample), images[j - 1]))
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
	brain_vol = nib.load(os.path.join(os.path.join(folder, sample), images[j - 1]))
	brain_mask = nib.load(os.path.join(os.path.join(folder, sample), images[j]))
	plotting.plot_epi(brain_vol, display_mode='z', cmap='hot_white_bone', title=images[j - 1])
	plotting.plot_epi(brain_mask, display_mode='z', cmap='hot_white_bone', title=images[j])
	fig.tight_layout()
	fig.suptitle(sample, fontsize=18)
	plt.show()
	return sample


def plot_counter(folder):
	"""
	Plot data counters.
	Args:
		folder (str): the path of the folder containing data.
	Returns:
		None.
	"""
	mr_sessions = sorted([f.split('-')[2] for f in os.listdir(folder)])
	n_subjects = len(list(set(mr_sessions)))
	mr_sessions = len(mr_sessions)
	fig, ax = plt.subplots(1, 1, figsize=(18, 8))
	bar_labels = ['MRI Sessions (n.'+str(mr_sessions)+')', 'Nr. Subjects (n.'+str(n_subjects)+')']
	bars = ax.bar(['MRI Sessions', 'Nr. Subjects'], height=[mr_sessions, n_subjects], label=bar_labels, color=['#8fce00', '#ff8200'])
	for rect in bars:
		height = rect.get_height()
		plt.text(rect.get_x() + rect.get_width() / 2.0, height, f'{height:.0f} ({height/mr_sessions*100:.2f}%)', ha='center', va='bottom')
	plt.xlabel('DATA', labelpad=20)
	plt.ylabel('COUNT', labelpad=20)
	plt.title('EXPLORING DATA')
	plt.legend()
	fig.tight_layout()
	plt.show()


def plot_brats_classes(folder, session=None, axis=2):
	"""
	Plot data labels and data classes according to BraTS-2023.
	Args:
		folder (str): the path of the folder containing data.
		session (str): a session ID, if not provided a random ID will be selected.
		axis (int): axis of the spatial image. Values are: 0=X_axis, 1=Y_axis, 2=Z_axis.
	Returns:
		None.
	"""
	_config = get_config()
	labels = _config.get('LABELS')
	classes = _config.get('CLASSES')
	sample = session if session else random.sample(os.listdir(folder), 1)[0]
	images = sorted(os.listdir(os.path.join(folder, sample)))
	fig, axs = plt.subplots(2, 3, figsize=(18, 12))
	brain_mask = nib.load(os.path.join(os.path.join(folder, sample), images[0]))
	brain_vol = nib.load(os.path.join(os.path.join(folder, sample), images[1]))
	print(f"Image shape: {brain_vol.shape}")
	isocenter = list(map(int, plotting.find_xyz_cut_coords(brain_mask)))
	_, label_masks = get_colored_mask(get_slice(brain_mask, axis, isocenter[axis]))
	brain_classes = get_brats_classes(brain_mask)
	for i, axl in enumerate(axs):
		for j, ax in enumerate(axl):
			if i == 0:
				ax.imshow(get_slice(brain_vol, axis, isocenter[axis]), cmap='gist_yarg')
				ax.imshow(label_masks[j])
				ax.set_title('Label '+str(j+1)+': '+labels[j])
			else:
				ax.imshow(get_slice(brain_classes[j], axis, isocenter[axis]), cmap='gray')
				ax.set_title('Class '+str(j+1)+': '+classes[j])
			ax.axis('off')
	fig.tight_layout()
	plt.show()


def plot_input_output(example):
	"""
	Plot data input after preprocessing and data output according to BraTS-2023.
	Args:
		example (dict): an example returned from Dataloader.
	Returns:
		None.
	"""
	_config = get_config()
	classes = _config.get('CLASSES')
	channels = _config.get('CHANNELS')
	axes_l = ['X=100', 'Y=100', 'Z=60']
	plt.figure('image-t1c', (18, 6))
	for i in range(3):
		plt.subplot(1, 3, i + 1)
		plt.title(axes_l[i])
		plt.axis('off')
		plt.imshow(get_slice(example['image'][0].detach().cpu(), i, 60 if i == 2 else 100), cmap='gray')
	plt.show()
	plt.figure('image', (18, 6))
	for i in range(4):
		plt.subplot(1, 4, i + 1)
		plt.title(channels[i])
		plt.axis('off')
		plt.imshow(example['image'][i, :, :, 60].detach().cpu(), cmap='gray')
	plt.show()
	plt.figure('label', (18, 6))
	for i in range(3):
		plt.subplot(1, 3, i + 1)
		plt.title(classes[i])
		plt.axis('off')
		plt.imshow(example['label'][i, :, :, 80].detach().cpu())
	plt.show()


def plot_training_values(model_name, folder):
	"""
	Plot losses and metrics over training phase.
	Args:
		model_name (str): the model name. `model_name` is case sensitive.
		folder (str): the path of the folder containing the csv reports.
	Returns:
		None.
	"""
	try:
		p = os.path.join(folder, model_name + '_training.csv')
		df = pd.read_csv(p)
		run_id = sorted(df['id'].unique())[0]
		data_df = df[df['id'] == run_id]
		best_epoch = data_df.iloc[data_df['dice_score'].idxmax()]['epoch']
		x = [i + 1 for i in range(len(data_df))]
		fig, ax = plt.subplots(1, 1, figsize=(18, 6))
		ax.plot(x, data_df['train_dice_loss'].to_numpy(), label='training_loss')
		ax.plot(x, data_df['eval_dice_loss'].to_numpy(), label='evaluation_loss')
		ax.set_xticks([i for i in range(0, len(data_df), 5)])
		plt.axvline(best_epoch, color='red')
		plt.text(best_epoch - 3.2, data_df['train_dice_loss'].max() / 2, 'best_run', rotation=0)
		plt.xlabel('EPOCHS', fontsize=14)
		plt.ylabel('DICE LOSS', fontsize=14)
		plt.title('TRAINING LOSSES', fontsize=18)
		plt.legend(fontsize=14)
		fig.tight_layout()
		plt.show()
		fig, ax = plt.subplots(1, 1, figsize=(18, 6))
		ax.plot(x, data_df['dice_score_et'].to_numpy(), label='enhancing_tumor')
		ax.plot(x, data_df['dice_score_tc'].to_numpy(), label='tumor_core')
		ax.plot(x, data_df['dice_score_wt'].to_numpy(), label='whole_tumor')
		ax.set_xticks([i for i in range(0, len(data_df), 5)])
		plt.axvline(best_epoch, color='red')
		plt.text(best_epoch - 3.2, data_df['dice_score_wt'].max() / 2, 'best_run', rotation=0)
		plt.xlabel('EPOCHS', fontsize=14)
		plt.ylabel('DICE METRIC', fontsize=14)
		plt.title('TRAINING METRICS', fontsize=18)
		plt.legend(fontsize=14)
		fig.tight_layout()
		plt.show()
	except OSError as e:
		print('\n' + ''.join(['> ' for i in range(30)]))
		print('\nERROR: model report for\033[95m '+model_name+'\033[0m not found.\n')
		print(''.join(['> ' for i in range(30)]) + '\n')


def plot_prediction(model_name, folder):
	"""
	Plot original image data, groundtruth label and predicted mask.
	Args:
		model_name (str): the model name. `model_name` is case sensitive.
		folder (str): the path of the folder containing the csv reports.
	Returns:
		None.
	"""
	_config = get_config()
	classes = _config.get('CLASSES')
	channels = _config.get('CHANNELS')
	images = [i for i in os.listdir(folder) if '.nii.gz' in i]
	ids = list(set([int(i.split('_')[2]) for i in images]))
	if len(ids) > 1:
		n = random.sample(ids, 1)[0]
		kind = ['image', 'label', 'pred']
		for i, k in enumerate(kind):
			brain_vol = nib.load(os.path.join(folder, model_name + '_sample_' + str(n) + '_' + k + '.nii.gz'))
			brain_vol3d = nib.Nifti1Image(brain_vol.get_fdata()[0], affine=np.eye(4))
			isocenter = list(map(int, plotting.find_xyz_cut_coords(brain_vol3d)))
			brain_vol_data = brain_vol.get_fdata()
			plt.figure('image', (18, 6))
			for j in range(4 if i == 0 else 3):
				plt.subplot(1, 4 if i == 0 else 3, j + 1)
				plt.title(k + '_' + str(n) + ' - ' + (channels[j] if i == 0 else classes[j]))
				plt.axis('off')
				plt.imshow(brain_vol_data[j, :, :, isocenter[2]], cmap = 'gray' if i == 0 else 'viridis')
			plt.show()
	else:
		print('\n' + ''.join(['> ' for i in range(30)]))
		print('\nERROR: sample predictions for\033[95m '+model_name+'\033[0m not found.\n')
		print(''.join(['> ' for i in range(30)]) + '\n')


def plot_results(folder):
	"""
	Plot all metrics calculated over the testing set.
	Args:
		folder (str): the path of the folder containing the csv reports.
	Returns:
		None.
	"""
	try:
		p = os.path.join(folder, 'results.csv')
		df = pd.read_csv(p)
		for metric in ['dice', 'hausdorff']:
			print(''.join(['> ' for i in range(40)]))
			print(f'\n{"":<20}{metric.upper()+"_ET":<15}{metric.upper()+"_TC":<15}{metric.upper()+"_WT":<15}{metric.upper()+"_AVG":<15}\n')
			print(''.join(['> ' for i in range(40)]))
			for model in df['model']:
				et = df[df["model"] == model][metric+"_score_et"].values[0]
				tc = df[df["model"] == model][metric+"_score_tc"].values[0]
				wt = df[df["model"] == model][metric+"_score_wt"].values[0]
				print(f'{model:<20}{et:<15.4f}{tc:<15.4f}{wt:<15.4f}{np.mean([et, tc, wt]):<15.4f}')
		print(''.join(['> ' for i in range(40)]))
	except OSError as e:
		print('\n' + ''.join(['> ' for i in range(30)]))
		print('\nERROR: file\033[95m  reports.csv\033[0m not found.\n')
		print(''.join(['> ' for i in range(30)]) + '\n')