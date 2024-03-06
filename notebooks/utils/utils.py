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


def make_dataset(dataset):
	"""Import the dataset from a remote source and extract the data.
	NOTE: 	A valid Synapse authentication token required in .env file.
			Please see: https://www.synapse.org/#!PersonalAccessTokens:
	Args:
		dataset (str): the dataset name (See SYN_IDS keys in config.py).
	Returns:
		train_path (str): the full path of the training set.
		eval_path (str): the full path of the evaluation set.
	"""
	_base_path = '\\'.join(os.getcwd().split('\\')[:-1]) + '\\' if platform == 'win32' else '/'.join(os.getcwd().split('/')[:-1]) + '/'
	_config = get_config()
	_env = dotenv_values(os.path.join(_base_path, '.env'))
	_syn_id = _config.get('SYN_IDS')[dataset]
	_data_path = os.path.join(_base_path, _config.get('DATA_FOLDER'), dataset)
	if platform == 'win32':
		_data_path = _data_path.replace('/', '\\')
	if _env.get('AUTH_TOKEN') is not None:
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
			return paths[0], paths[1]
		except OSError as e:
			print(e)
	else:
		print('\n' + ''.join(['> ' for i in range(30)]))
		print('\nERROR: missing auth token! Please check your\033[95m .env\033[0m file.\n')
		print(''.join(['> ' for i in range(30)]) + '\n')
