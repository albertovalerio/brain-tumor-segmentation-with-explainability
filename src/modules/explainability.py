"""
Definitions of explainability utility functions.
"""
import os
from src.helpers.utils import get_device
from transformers import AutoModelForCausalLM, AutoTokenizer


__all__ = ['get_explanations']


def get_explanations(model_id, prompt, write_to_file=True, output_path='', output_length=1024, verbose=True):
	"""
	Computes the explanations of the model output.
	Args:
		model_id (str): the model ID according to HuggingFace API (See: https://huggingface.co/models).
		prompt (str): the ("user") input prompt.
		write_to_file (bool): whether or not to save the output to file.
		output_path (str): the folder's path where to save the output. Required if `write_to_file` is `True`.
		output_length (int): the number of output's tokens.
		verbose (bool): whether or not to print the output.
	Returns:
		readable_output (str): the explanation output.
	"""
	os.environ['TOKENIZERS_PARALLELISM'] = 'false'
	device = get_device()
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
	if write_to_file:
		if output_path == '':
			print('\n' + ''.join(['> ' for i in range(30)]))
			print('\nERROR: Parameter \033[95m `output_path`\033[0m must be specified.\n')
			print(''.join(['> ' for i in range(30)]) + '\n')
			return ''
		else:
			with open(os.path.join(output_path, model_id.split('/')[-1] + '.md'), 'a') as f:
				f.write('\n\n# **Prompt**\n\n')
				f.write(prompt)
				f.write('\n\n# **Output**\n\n')
				f.write(readable_output)
	if verbose:
		print(readable_output.replace('. ', '. \n'))
	del tokenizer, model, inputs, outputs
	return readable_output