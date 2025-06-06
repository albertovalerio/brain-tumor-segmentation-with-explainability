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
	'REMOTE_DATA': 'https://unibari-my.sharepoint.com/:u:/g/personal/a_valerio31_studenti_uniba_it/EU0C24jfgUZHqolXloD_K30BpZRdt3TI1L3MAWtkJO0zCg?e=BGHc9n&download=1',
	'LLM':				{
		'biomistral': 'BioMistral/BioMistral-7B',
		'llama': 'meta-llama/Meta-Llama-3-8B-Instruct',
		'mistral': 'mistralai/Mistral-7B-Instruct-v0.2',
		'minerva': 'sapienzanlp/Minerva-1B-base-v1.0',
		'llamantino2': 'swap-uniba/LLaMAntino-2-chat-7b-hf-UltraChat-ITA',
		'llamantino3': 'swap-uniba/LLaMAntino-3-ANITA-8B-Inst-DPO-ITA',
		'groq_llama': 'llama3-70b-8192',
		'groq_mixtral': 'mistral-saba-24b',
		'groq_gemma': 'gemma2-9b-it'
	},
	'LLM_PARAMS':				{
		'hf': {
			'biomistral': '7B',
			'llama': '8B',
			'mistral': '7B',
			'minerva': '1B',
			'llamantino2': '7B',
			'llamantino3': '8B'
		},
		'groq': {
			'gemma': '9B',
			'llama': '70B',
			'mixtral': '24B',
		}
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