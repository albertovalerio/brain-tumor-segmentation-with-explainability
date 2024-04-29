"""
The collection of global configurations
"""
CONFIG = {
	'DATA_FOLDER':			'data/',
	'SAVED_FOLDER': 		'saved/',
	'REPORT_FOLDER':		'reports/',
	'PRED_FOLDER':			'predictions/',
	'LOG_FOLDER':			'logs/',
	'JSON_FOLDER':			'json/',
	'PROMPT_FOLDER':		'prompts/',
	'SYN_IDS':				{
		'glioma':		'syn51514105',
		'africa':		'syn51514109',
		'meningioma':	'syn51514106',
		'metastasis':	'syn51514107',
		'pediatric':	'syn51514108'
	},
	'CHANNELS':			[
		'post-contrast T1-weighted',
		'T1-native',
		'T2-FLAIR',
		'T2-weighted',
		'segmentation mask'
	],
	'LABELS': 			[
		'NCR (necrotic tumor core)',
		'ED (peritumoral edematous/invaded tissue)',
		'ET (GD-enhancing tumor)'
	],
	'CLASSES':			[
		'ET (Enhancing Tumor)',
		'TC (Tumor Core)',
		'WT (Whole Tumor)'
	],
	'REMOTE_DATA': 'https://unibari-my.sharepoint.com/:u:/g/personal/a_valerio31_studenti_uniba_it/EU0C24jfgUZHqolXloD_K30BpZRdt3TI1L3MAWtkJO0zCg?e=BGHc9n&download=1'
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