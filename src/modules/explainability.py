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


__all__ = ['get_explanations']


def get_explanations(
		lang,
		model_key,
		prompt_id,
		output_length = 1024,
		write_prompt_to_file = False,
		write_metrics_to_file = True,
		base_path = '',
		verbose = True
	):
	"""
	Computes the explanations of the model output.
	Args:
		lang (str): the language of the experiment.
		model_key (str): the model ID according to HuggingFace API (See: https://huggingface.co/models).
		prompt_id (str/int): the ID of the prompt. Possible options are '1' or '2'.
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
	prompt = _get_prompt(lang, prompt_id, json_path)
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
			file = os.path.join(reports_path, 'LLM_metrics.csv'),
			metrics = metrics
		)
	if verbose:
		print(readable_output.replace('. ', '. \n'))
	del tokenizer, model, inputs, outputs
	return readable_output, metrics


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


def _get_prompt(lang, prompt_id, json_path, sample_id = 2):
	"""
	Returns the full input prompt.
	Args:
		lang (str): the language of the experiment.
		prompt_id (str/int): the ID of the prompt. Possible options are '1' or '2'.
		json_path (str): the folder where to find the JSON description files.
		sample_id (str/int): the test sample id. Possible options are '1', '2' or '3'.
	Returns:
		prompt (str): the full input prompt.
	"""
	_prompt = get_prompt()
	prompt = _prompt.get(lang).get('prompt_' + str(prompt_id))
	with open(os.path.join(json_path, 'SegResNet_sample_' + str(sample_id) + '_' + lang.upper() + '.json'), 'r') as f:
		d = json.load(f)
		prompt += str(d)
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
	ref_similarities = cosine_similarity(emb, reference_embeddings)
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
