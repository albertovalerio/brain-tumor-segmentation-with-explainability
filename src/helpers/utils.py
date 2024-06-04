"""
A set of utility functions
"""
import os, zipfile, csv
from sys import platform
from datetime import datetime
import numpy as np
import torch
import nibabel as nib
from monai.data.meta_tensor import MetaTensor
from src.helpers.config import get_config
from dotenv import dotenv_values
import synapseclient
import synapseutils


__all__ = ['make_dataset', 'get_colored_mask', 'get_brats_classes', 'get_slice', 'get_device', 'get_date_time']


def make_dataset(dataset, verbose=True, base_path=''):
	"""
	Import the dataset from a remote source and extract the data.
	NOTE: 	A valid Synapse authentication token is required in .env file.
			Please see: https://www.synapse.org/#!PersonalAccessTokens:
	Args:
		dataset (str): the dataset name (See SYN_IDS keys in config.py).
		verbose (bool): whether or not print information.
		base_path (str): project root directory's path.
	Returns:
		data_path (str): the full path of the dataset folder.
	"""
	if base_path == '':
		_base_path = '\\'.join(os.getcwd().split('\\')[:-1]) + '\\' if platform == 'win32' else '/'.join(os.getcwd().split('/')[:-1]) + '/'
	else:
		_base_path = base_path
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
	"""
	Convert 2D segmentation mask into RGBA image.
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
	"""
	Convert labels to multi channels based on BraTS-2023 classes:
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
	if type(mask) is nib.nifti1.Nifti1Image:
		mask = mask.get_fdata()
		base_class = np
	else:
		base_class = torch
	result = []
	# label 3 is ET
	result.append(mask == 3.)
	# merge label 1 and label 3 to construct TC
	result.append(base_class.logical_or(mask == 1., mask == 3.))
	# merge labels 1, 2 and 3 to construct WT
	result.append(base_class.logical_or(base_class.logical_or(mask == 2., mask == 3.), mask == 1.))
	classes_imgs = base_class.stack(result, axis=0).astype(int) if base_class is np else MetaTensor(base_class.stack(result, axis=0).float())
	return classes_imgs


def get_slice(spatial_image, axis, offset):
	"""
	Get a 2D slice of a spatial image.
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


def get_device():
	"""
	Returns the device available on the current machine.
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


def get_date_time():
	"""
	Convert the current date in a standard datetime format.
	Args:
		None.
	Returns:
		str: the datetime formatted.
	"""
	ts = datetime.timestamp(datetime.now())
	date_time = datetime.fromtimestamp(ts)
	return date_time.strftime("%Y-%m-%d %H:%M:%S")


def save_results(file, metrics):
	"""Save the metrics to csv file.
	Args:
		file (str): the file path where to save data.
		metrics (dict): the metrics of the experiment.
	Returns:
		None.
	"""
	if os.path.isfile(file):
		with open(file, 'a', encoding='utf-8') as outfile:
			csvwriter = csv.writer(outfile, delimiter=',')
			csvwriter.writerow(metrics.values())
	else:
		with open(file, 'w', encoding='utf-8') as outfile:
			csvwriter = csv.writer(outfile, delimiter=',')
			csvwriter.writerow(metrics)
			csvwriter.writerow(metrics.values())
