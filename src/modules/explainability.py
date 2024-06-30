"""
Definitions of explainability utility functions.
"""
import os, time, json, math
from sys import platform
from src.helpers.utils import get_device, save_results
from src.helpers.config import get_config
from src.helpers.prompts import get_prompt
from transformers import AutoModelForCausalLM, AutoTokenizer
from spacy.lang.en import English
from spacy.lang.it import Italian
import textstat as ts
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import dotenv_values
from groq import Groq


__all__ = ['get_explanations', 'get_explanations_via_groq']


def get_explanations(
		lang,
		model_key,
		prompt_id,
		sample_id = 2,
		output_length = 1024,
		write_prompt_to_file = False,
		write_metrics_to_file = True,
		base_path = '',
		verbose = True
	):
	"""
	Generates the medical report and its metrics based on segmentation model output.
	Args:
		lang (str): the language of the experiment.
		model_key (str): the model ID according to HuggingFace API (See: https://huggingface.co/models).
		prompt_id (str/int): the ID of the prompt. Possible options are '1' or '2'.
		sample_id (str/int): the ID of an image sample from those available in `json` folder.
		output_length (int): the number of output's tokens.
		write_prompt_to_file (bool): whether or not to save the output to file.
		write_metrics_to_file (bool): whether or not to save the metrics to file.
		base_path (str): project root directory's path.
		verbose (bool): whether or not to print the output.
	Returns:
		readable_output (str): the explanation (medical report) output.
		metrics (dict): the computed metrics.
	"""
	os.environ['TOKENIZERS_PARALLELISM'] = 'false'
	device = get_device()
	_config = get_config()
	model_id = _config.get('LLM').get(model_key)
	output_path, json_path, reports_path = _get_paths(lang, base_path)
	prompt = _get_prompt(lang, prompt_id, json_path, sample_id)
	start = time.time()
	tokenizer = AutoTokenizer.from_pretrained(model_id)
	model = AutoModelForCausalLM.from_pretrained(model_id).to(device)
	inputs = tokenizer.apply_chat_template(
		[{'role': 'user', 'content': prompt}],
		add_generation_prompt = True,
		return_tensors = 'pt'
	).to(device)
	outputs = model.generate(
		inputs,
		max_new_tokens = output_length,
		eos_token_id = [
			tokenizer.eos_token_id,
			tokenizer.convert_tokens_to_ids('<|eot_id|>')
		],
		pad_token_id = tokenizer.eos_token_id,
		do_sample = True,
		temperature = 0.6,
		top_p = 0.9,
	)
	readable_output = tokenizer.decode(outputs[0][inputs.shape[-1]:], skip_special_tokens=True)
	end = time.time()
	metrics = _get_metrics(model_key, lang, prompt_id, prompt, readable_output)
	metrics['inference_time'] = end - start
	if write_prompt_to_file:
		with open(os.path.join(output_path, model_id.split('/')[-1] + '.md'), 'a') as f:
			f.write('\n\n# **Prompt**\n\n')
			f.write(prompt)
			f.write('\n\n# **Output**\n\n')
			f.write(readable_output)
	if write_metrics_to_file:
		save_results(
			file = os.path.join(reports_path, 'LLM_metrics_HF.csv'),
			metrics = metrics
		)
	if verbose:
		print(readable_output.replace('. ', '. \n'))
	del tokenizer, model, inputs, outputs
	return readable_output, metrics


def get_explanations_via_groq(
		lang,
		model_key,
		prompt_id,
		sample_id = 2,
		output_length = 1024,
		write_prompt_to_file = False,
		write_metrics_to_file = True,
		base_path = '',
		verbose = True
	):
	"""
	Generates the medical report and its metrics based on segmentation model output.
	LLM inference provided by Groq API (See: https://console.groq.com/docs).
	Args:
		lang (str): the language of the experiment.
		model_key (str): the model ID according to Groq API (See: https://console.groq.com/docs/models).
		prompt_id (str/int): the ID of the prompt. Possible options are '1' or '2'.
		sample_id (str/int): the ID of an image sample from those available in `json` folder.
		output_length (int): the number of output's tokens.
		write_prompt_to_file (bool): whether or not to save the output to file.
		write_metrics_to_file (bool): whether or not to save the metrics to file.
		base_path (str): project root directory's path.
		verbose (bool): whether or not to print the output.
	Returns:
		readable_output (str): the explanation (medical report) output.
		metrics (dict): the computed metrics.
	"""
	_env = dotenv_values(os.path.join(base_path, '.env'))
	if _env.get('GROQ_API_KEY') is not None:
		_config = get_config()
		model_id = _config.get('LLM').get(model_key)
		output_path, json_path, reports_path = _get_paths(lang, base_path)
		prompt = _get_prompt(lang, prompt_id, json_path, sample_id)
		start = time.time()
		client = Groq(api_key=_env.get('GROQ_API_KEY'))
		chat_completion = client.chat.completions.create(
			messages=[{'role': 'user', 'content': prompt}],
			model=model_id,
			temperature = 0.6,
			max_tokens=output_length,
			top_p = 0.9
		)
		readable_output = chat_completion.choices[0].message.content
		end = time.time()
		metrics = _get_metrics(model_key, lang, prompt_id, prompt, readable_output)
		metrics['inference_time'] = end - start
		if write_prompt_to_file:
			with open(os.path.join(output_path, model_id.split('/')[-1] + '.md'), 'a') as f:
				f.write('\n\n# **Prompt**\n\n')
				f.write(prompt)
				f.write('\n\n# **Output**\n\n')
				f.write(readable_output)
		if write_metrics_to_file:
			save_results(
				file = os.path.join(reports_path, 'LLM_metrics_GROQ.csv'),
				metrics = metrics
			)
		if verbose:
			print(readable_output.replace('. ', '. \n'))
		return readable_output, metrics
	else:
		print('\n' + ''.join(['> ' for i in range(40)]))
		print('\nERROR: missing auth token! Please check your\033[95m .env\033[0m file.\n')
		print(''.join(['> ' for i in range(40)]) + '\n')
		return ''


def _get_paths(lang, base_path=''):
	"""
	Returns all the useful paths.
	Args:
		lang (str): the language of the experiment.
		base_path (str): project root directory's path.
	Returns:
		output_path (str): the folder where to save the medical report.
		json_path (str): the folder where to find the JSON description files.
		reports_path (str): the folder where to save the computed metrics.
	"""
	if base_path == '':
		_base_path = '\\'.join(os.getcwd().split('\\')[:-1]) + '\\' if platform == 'win32' else '/'.join(os.getcwd().split('/')[:-1]) + '/'
	else:
		_base_path = base_path
	_config = get_config()
	output_path = os.path.join(_base_path, _config.get('PROMPT_FOLDER'), lang.lower())
	json_path = os.path.join(_base_path, _config.get('JSON_FOLDER'))
	reports_path = os.path.join(_base_path, _config.get('REPORT_FOLDER'))
	if platform == 'win32':
		output_path = output_path.replace('/', '\\')
		json_path = json_path.replace('/', '\\')
		reports_path = reports_path.replace('/', '\\')
	return output_path, json_path, reports_path


def _get_prompt(lang, prompt_id, json_path, sample_id):
	"""
	Returns the full input prompt.
	Args:
		lang (str): the language of the experiment.
		prompt_id (str/int): the ID of the prompt. Possible options are '1' or '2'.
		json_path (str): the folder where to find the JSON description files.
		sample_id (str/int): the test sample ID from those available in `json` folder.
	Returns:
		prompt (str): the full input prompt.
	"""
	_prompt = get_prompt()
	prompt = _prompt.get(lang).get('prompt_' + str(prompt_id))
	sample_name = 'SegResNet_sample_' + str(sample_id) + '_' + lang.upper() + '.json'
	if sample_name in os.listdir(json_path):
		with open(os.path.join(json_path, sample_name), 'r') as f:
			d = json.load(f)
			prompt += str(d)
	else:
		print('\n' + ''.join(['> ' for i in range(30)]))
		print('\nERROR: sample_id \033[95m '+sample_id+'\033[0m not found.\n')
		print(''.join(['> ' for i in range(30)]) + '\n')
		prompt = ''
	return prompt


def _get_metrics(model_key, lang, prompt_id, prompt, output):
	"""
	Returns the full prompt.
	Args:
		model_key (str): the LLM identifier.
		lang (str): the language of the experiment.
		prompt_id (str): the ID of the prompt. Possible options are '1' or '2'.
		prompt (str): the full input prompt.
		output (str): the LLM output to evaluate.
	Returns:
		metrics (dict): the computed metrics.
	"""

	# Diversity measures
	nlp = English() if lang.lower() == 'en' else Italian()
	tokens = [t.text for t in nlp(output)]
	ttr = len(list(set(tokens))) / len(tokens)
	maas = (math.log(len(tokens)) - math.log(len(list(set(tokens))))) / (math.log(len(tokens)) ** 2)

	# Readability measure
	readability = ts.flesch_reading_ease(output) if lang.lower() == 'en' else ts.gulpease_index(output)

	# Coherence measure
	model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
	sentences = output.replace('.\n\n', '. ').replace('\n\n', '').replace('\n', '. ').split('. ')
	emb = model.encode(sentences)
	similarities = [cosine_similarity([emb[i]], [emb[i+1]])[0][0] for i in range(len(emb)-1)]
	coherence_score = (sum(similarities) / len(similarities)) if len(similarities) else 0.0

	# Coverage of information measures
	reference_texts = prompt.replace('.\n\n', '. ').replace('\n\n', '').replace('\n', '. ').split('. ')
	reference_embeddings = model.encode(reference_texts)
	text_embeddings = model.encode([output])
	ref_similarities = cosine_similarity(text_embeddings, reference_embeddings)
	coverage_embedding_based = sum(ref_similarities[0]) / len(reference_texts)

	text_input = [t.text.lower() for t in nlp(prompt.replace('\n', ' ')) if not (t.is_punct or t.is_stop)]
	text_input = list(filter(lambda x: x != ' ', text_input))
	text_output = [t.text.lower() for t in nlp(output.replace('\n', ' ')) if not (t.is_punct or t.is_stop)]
	text_output = list(filter(lambda x: x != ' ', text_output))
	coverage_token_based = len(list(set(text_input).intersection(text_output))) / len(list(set(text_input).union(text_output)))

	return {
		'model': model_key,
		'lang': lang,
		'prompt_id': prompt_id,
		'diversity_TTR': ttr,
		'diversity_MAAS': maas,
		'readability_score': readability,
		'coherence_score': coherence_score,
		'coverage_embedding_based': coverage_embedding_based,
		'coverage_token_based': coverage_token_based
	}
