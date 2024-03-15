"""
A set of utility functions
"""
import os
import random
from sys import platform
from dotenv import dotenv_values
import zipfile
from utils.config import get_config
import synapseclient
import synapseutils
import numpy as np
import torch
import nibabel as nib


def make_dataset(dataset, verbose=True):
	"""Import the dataset from a remote source and extract the data.
	NOTE: 	A valid Synapse authentication token required in .env file.
			Please see: https://www.synapse.org/#!PersonalAccessTokens:
	Args:
		dataset (str): the dataset name (See SYN_IDS keys in config.py).
		verbose (bool): whether or not print information.
	Returns:
		data_path (str): the full path of the dataset folder.
	"""
	_base_path = '\\'.join(os.getcwd().split('\\')[:-1]) + '\\' if platform == 'win32' else '/'.join(os.getcwd().split('/')[:-1]) + '/'
	_config = get_config()
	_env = dotenv_values(os.path.join(_base_path, '.env'))
	_syn_id = _config.get('SYN_IDS')[dataset]
	_data_path = os.path.join(_base_path, _config.get('DATA_FOLDER'), dataset)
	if platform == 'win32':
		_data_path = _data_path.replace('/', '\\')
	if _env.get('AUTH_TOKEN') is not None:
		if not os.path.isdir(_data_path):
			os.makedirs(_data_path)
		if len(os.listdir(_data_path)) == 0:
			syn = synapseclient.Synapse()
			syn.login(authToken=_env.get('AUTH_TOKEN'))
			print('Downloading files...')
			files = synapseutils.syncFromSynapse(syn, _syn_id, path=_data_path)
			train_path = os.path.join(_data_path, [f.name for f in files if 'training' in f.name.lower()][0])
			try:
				print('Extracting files...')
				with zipfile.ZipFile(train_path, 'r') as zip_ref:
					zip_ref.extractall(_data_path)
				print('Finalizing...')
				for i in os.listdir(_data_path):
					full = os.path.join(_data_path, i)
					if os.path.isfile(full):
						os.unlink(full)
				print('Operation completed!')
				return train_path[:-4]
			except OSError as e:
				print(e)
		else:
			paths = [f for f in os.listdir(_data_path) if os.path.isdir(os.path.join(_data_path, f))]
			train_path = os.path.join(_data_path, [f for f in paths if 'training' in f.lower()][0])
			if verbose:
				print('\n' + ''.join(['> ' for i in range(40)]))
				print('\nWARNING: \033[95m '+dataset+'\033[0m directory not empty.\n')
				print('DATA_PATH: \033[95m '+'/'.join(train_path.split('/')[-2:])+'\033[0m\n')
				print(''.join(['> ' for i in range(40)]) + '\n')
			return train_path if len(paths) == 1 else ''
	else:
		print('\n' + ''.join(['> ' for i in range(40)]))
		print('\nERROR: missing auth token! Please check your\033[95m .env\033[0m file.\n')
		print(''.join(['> ' for i in range(40)]) + '\n')
		return ''


def get_colored_mask(mask):
	"""Convert 2D segmentation mask into RGBA image.
	Args:
		mask (numpy.ndarray): the 2D mask.
	Returns:
		mask_colored (numpy.ndarray): the RGBA colored mask.
		labels_colored (list): the RGBA colored mask by single label.
	"""
	mask_colored = np.zeros((mask.shape[0], mask.shape[1], 4), dtype='uint8')
	labels_colored = [
		np.zeros((mask.shape[0], mask.shape[1], 4), dtype='uint8'),
		np.zeros((mask.shape[0], mask.shape[1], 4), dtype='uint8'),
		np.zeros((mask.shape[0], mask.shape[1], 4), dtype='uint8')
	]
	for i in range(mask.shape[0]):
		for j in range(mask.shape[1]):
			if mask[i][j] == 1.:
				mask_colored[i][j] = [255, 0, 0, 255]
				labels_colored[0][i][j] = [255, 0, 0, 255]
			if mask[i][j] == 2.:
				mask_colored[i][j] = [255, 255, 0, 255]
				labels_colored[1][i][j] = [255, 255, 0, 255]
			if mask[i][j] == 3.:
				mask_colored[i][j] = [0, 255, 0, 255]
				labels_colored[2][i][j] = [0, 255, 0, 255]
	return mask_colored, labels_colored


def get_brats_classes(mask):
	"""Convert labels to multi channels based on BraTS-2023 classes:
    	- label 1 (NCR): the necrotic tumor core
    	- label 2 (ED): the peritumoral edematous/invaded tissue
    	- label 3 (ET): the GD-enhancing tumor
    The sub-regions considered for evaluation are:
    	- "enhancing tumor" (ET)
        - "tumor core" (TC)
        - "whole tumor" (WT)
	Args:
		mask (nibabel.nifti1.Nifti1Image): the 3D segmentation mask.
	Returns:
		classes_imgs (numpy.ndarray): the 4D matrix, 1-dim correspond to different classes.
	"""
	mask = mask.get_fdata()
	classes_imgs = np.zeros((3, mask.shape[0], mask.shape[1], mask.shape[2]), dtype='uint8')
	for i in range(mask.shape[0]):
		for j in range(mask.shape[1]):
			for k in range(mask.shape[2]):
				# label 3 is ET
				if mask[i][j][k] == 3.:
					classes_imgs[0][i][j][k] = 1
				# merge label 1 and label 3 to construct TC
				if mask[i][j][k] == 1. or mask[i][j][k] == 3.:
					classes_imgs[1][i][j][k] = 1
				# merge labels 1, 2 and 3 to construct WT
				if mask[i][j][k] != 0.:
					classes_imgs[2][i][j][k] = 1
	return classes_imgs


def get_slice(spatial_image, axis, offset):
	"""Get a 2D slice of a spatial image.
	Args:
		spatial_image (nibabel.nifti1.Nifti1Image/numpy.ndarray): the spatial image.
		axis (int/str): axis of the spatial image. Values are: 0=X_axis, 1=Y_axis, 2=Z_axis.
		offset (int): offset from the origin of the axis, where to cut the slice.
	Returns:
		slice (numpy.ndarray): the 2D slice.
	"""
	if type(spatial_image) is nib.nifti1.Nifti1Image:
		spatial_image = spatial_image.get_fdata()
	slice = np.array([])
	match int(axis):
		case 0:
			slice = np.rot90(spatial_image[offset,:,:], 1)
		case 1:
			slice = np.rot90(spatial_image[:,offset,:], 1)
		case 2:
			slice = np.rot90(spatial_image[:,:,offset], 3)
		case _:
			raise Exception('Axis not valid. Possible values are: 0, 1, 2')
	return slice


def train_test_splitting(folder, train_ratio=.8, verbose=True):
	"""Splitting train/test.
	Args:
		folder (str): the path of the folder containing data.
		train_ratio (float): ratio of the training set, value between 0 and 1.
		verbose (bool): whether or not print information.
	Returns:
		train_data (list): the training data ready to feed monai.data.Dataset
		test_data (list): the testing data ready to feed monai.data.Dataset.
		(see https://docs.monai.io/en/latest/data.html#monai.data.Dataset).
	"""
	sessions = [s.split('-')[2] for s in os.listdir(folder)]
	subjects = list(set(sessions))
	random.shuffle(subjects)
	split = int(len(subjects) * train_ratio)
	train_subjects, test_subjects = subjects[:split], subjects[split:]
	train_sessions = [os.path.join(folder, s) for s in os.listdir(folder) if s.split('-')[2] in train_subjects]
	test_sessions = [os.path.join(folder, s) for s in os.listdir(folder) if s.split('-')[2] in test_subjects]
	train_labels = [os.path.join(s, s.split('/')[-1] + '-seg.nii.gz') for s in train_sessions]
	test_labels = [os.path.join(s, s.split('/')[-1] + '-seg.nii.gz') for s in test_sessions]
	modes = ['t1c', 't1n', 't2f', 't2w']
	train_data, test_data = {}, {}
	train_data = [dict({
		'image': [os.path.join(s, s.split('/')[-1] + '-' + m + '.nii.gz') for m in modes],
		'label':train_labels[i]
	}) for i, s in enumerate(train_sessions)]
	test_data = [dict({
		'image': [os.path.join(s, s.split('/')[-1] + '-' + m + '.nii.gz') for m in modes],
		'label':test_labels[i]
	}) for i, s in enumerate(test_sessions)]
	if verbose:
		print(''.join(['> ' for i in range(30)]))
		print(f'\n{"":<20}{"TRAINING":<20}{"TESTING":<20}\n')
		print(''.join(['> ' for i in range(30)]))
		tsb1 = str(len(train_subjects)) + ' (' + str(round((len(train_subjects) * 100 / len(subjects)), 1)) + ' %)'
		tsb2 = str(len(test_subjects)) + ' (' + str(round((len(test_subjects) * 100 / len(subjects)), 1)) + ' %)'
		tss1 = str(len(train_sessions)) + ' (' + str(round((len(train_sessions) * 100 / len(sessions)), 2)) + ' %)'
		tss2 = str(len(test_sessions)) + ' (' + str(round((len(test_sessions) * 100 / len(sessions)), 2)) + ' %)'
		print(f'\n{"subjects":<20}{tsb1:<20}{tsb2:<20}\n')
		print(f'{"sessions":<20}{tss1:<20}{tss2:<20}\n')
	return train_data, test_data


def get_device():
	"""Returns the device available on the current machine
	Args: None
	Returns:
		device (str): name of the device available.
	"""
	device = 'cpu'
	if torch.backends.mps.is_available():
		device = 'mps'
	elif torch.cuda.is_available():
		device = 'cuda'
	return device