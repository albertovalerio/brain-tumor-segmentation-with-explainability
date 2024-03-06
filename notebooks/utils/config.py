"""
The collection of global configurations
"""
CONFIG = {
	'DATA_FOLDER':			'data/',
	'SYN_IDS':				{
		'glioma':		'syn51514105',
		'africa':		'syn51514109',
		'meningioma':	'syn51514106',
		'metastasis':	'syn51514107',
		'pediatric':	'syn51514108'
	}
}


def get_config():
	"""
	The getter method
	"""
	return CONFIG


def set_config(key, value):
	"""
	The setter method
	"""
	CONFIG.update({key: value})