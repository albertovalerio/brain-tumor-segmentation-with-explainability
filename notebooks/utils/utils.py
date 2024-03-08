"""
A set of utility functions
"""
import os
from sys import platform
from dotenv import dotenv_values
import zipfile
from utils.config import get_config
import synapseclient
import synapseutils
import numpy as np


def make_dataset(dataset):
	"""Import the dataset from a remote source and extract the data.
	NOTE: 	A valid Synapse authentication token required in .env file.
			Please see: https://www.synapse.org/#!PersonalAccessTokens:
	Args:
		dataset (str): the dataset name (See SYN_IDS keys in config.py).
	Returns:
		paths (list): the full path of the training and evaluation sets.
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
			paths = [
				os.path.join(_data_path, [f.name for f in files if 'training' in f.name.lower()][0]),
				os.path.join(_data_path, [f.name for f in files if 'validation' in f.name.lower()][0])
			]
			try:
				print('Extracting files...')
				for p in paths:
					with zipfile.ZipFile(p, 'r') as zip_ref:
						zip_ref.extractall(_data_path)
				print('Finalizing...')
				for i in os.listdir(_data_path):
					full = os.path.join(_data_path, i)
					if os.path.isfile(full):
						os.unlink(full)
				print('Operation completed!')
				return [paths[0][:-4], paths[1][:-4]]
			except OSError as e:
				print(e)
		else:
			paths = [f for f in os.listdir(_data_path) if os.path.isdir(os.path.join(_data_path, f))]
			paths = [
				os.path.join(_data_path, [f for f in paths if 'training' in f.lower()][0]),
				os.path.join(_data_path, [f for f in paths if 'validation' in f.lower()][0])
			]
			print('\n' + ''.join(['> ' for i in range(30)]))
			print('\nWARNING: \033[95m '+dataset+'\033[0m directory not empty.\n')
			print('TRAIN_PATH: \033[95m '+'/'.join(paths[0].split('/')[-2:])+'\033[0m')
			print('EVAL_PATH: \033[95m '+'/'.join(paths[1].split('/')[-2:])+'\033[0m \n')
			print(''.join(['> ' for i in range(30)]) + '\n')
			return paths if len(paths) == 2 else ['', '']
	else:
		print('\n' + ''.join(['> ' for i in range(30)]))
		print('\nERROR: missing auth token! Please check your\033[95m .env\033[0m file.\n')
		print(''.join(['> ' for i in range(30)]) + '\n')
		return ['','']


def get_colored_mask(mask):
	"""Convert 2D segmentation mask into RGBA image.
	Args:
		mask (numpy.ndarray): the 2D mask.
	Returns:
		mask_colored (numpy.ndarray): the RGBA colored mask.
	"""
	mask_colored = np.zeros((mask.shape[0], mask.shape[1], 4), dtype='uint8')
	for i in range(mask.shape[0]):
		for j in range(mask.shape[1]):
			match mask[i][j]:
				case 0.:
					mask_colored[i][j] = [255, 255, 255, 0]
				case 1.:
					mask_colored[i][j] = [255, 0, 0, 255]
				case 2.:
					mask_colored[i][j] = [255, 255, 0, 255]
				case 3.:
					mask_colored[i][j] = [0, 255, 0, 255]
	return mask_colored


def get_slice(spatial_image, axis, offset):
	"""Get a 2D slice of a spatial image.
	Args:
		spatial_image (nibabel.nifti1.Nifti1Image): the spatial image.
		axis (int): axis of the spatial image. Values are: 0=X_axis, 1=Y_axis, 2=Z_axis.
		offset (int): offset value where to cut the slice.
	Returns:
		slice (numpy.ndarray): the 2D slice.
	"""
	spatial_image_data = spatial_image.get_fdata()
	slice = np.array([])
	match axis:
		case 0:
			slice = np.rot90(spatial_image_data[offset,:,:], 1)
		case 1:
			slice = np.rot90(spatial_image_data[:,offset,:], 1)
		case 2:
			slice = np.rot90(spatial_image_data[:,:,offset], 3)
		case _:
			raise Exception('Axis not valid. Possible values are: 0, 1, 2')
	return slice
