"""
A set of plotting functions
"""
import os, random
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from nilearn import plotting
import nibabel as nib
from src.helpers.utils import get_colored_mask, get_slice, get_brats_classes
from src.helpers.config import get_config


def random_samples(folder, n_samples, axis):
	"""
	Plot a comparison between different n data examples.
	Args:
		folder (str): the path of the folder containing data.
		n_samples (int): number of samples to plot. Min value is 2.
		axis (int): axis of the spatial image. Values are: 0=X_axis, 1=Y_axis, 2=Z_axis.
	Returns:
		None.
	"""
	_config = get_config()
	channels = _config.get('CHANNELS')
	if n_samples > 1 and axis < 3:
		samples = random.sample(os.listdir(folder), n_samples)
		fig, axs = plt.subplots(n_samples, 5, figsize=(18, n_samples * 4))
		for i, axl in enumerate(axs):
			images = sorted(os.listdir(os.path.join(folder, samples[i])))
			images.append(images.pop(images.index(images[0])))
			if i == 0:
				for k in range(5):
					axl[k].set_title(channels[k])
			for j, ax in enumerate(axl):
				if j == 0:
					ax.set_ylabel(samples[i])
				brain_vol = nib.load(os.path.join(os.path.join(folder, samples[i]), images[j]))
				isocenter = list(map(int, plotting.find_xyz_cut_coords(brain_vol)))
				if j == len(images) - 1:
					mask_colored, _ = get_colored_mask(get_slice(brain_vol, axis, isocenter[axis]))
					brain_vol = nib.load(os.path.join(os.path.join(folder, samples[i]), images[j - 1]))
					ax.imshow(get_slice(brain_vol, axis, isocenter[axis]), cmap='gist_yarg')
					ax.imshow(mask_colored)
				else:
					ax.imshow(get_slice(brain_vol, axis, isocenter[axis]), cmap='gist_yarg')
				ax.spines['top'].set_visible(False)
				ax.spines['right'].set_visible(False)
				ax.spines['bottom'].set_visible(False)
				ax.spines['left'].set_visible(False)
				a = {0:'X',1:'Y',2:'Z'}
				ax.set_xlabel(a[axis]+'='+str(isocenter[axis]))
				ax.get_xaxis().set_ticks([])
				ax.get_yaxis().set_ticks([])
		fig.tight_layout()
		plt.show()
	else:
		print('\n' + ''.join(['> ' for i in range(40)]))
		print('\nERROR: \033[95m n_samples\033[0m must be greater that \033[95m 1\033[0m and \033[95m axis\033[0m bust be lower that \033[95m 2\033[0m.\n')
		print(''.join(['> ' for i in range(40)]) + '\n')


def single_sample(folder, session=None):
	"""
	Plot different views of a single sample data.
	Args:
		folder (str): the path of the folder containing data.
		session (str): a session ID, if not provided a random ID will be selected.
	Returns:
		None.
	"""
	_config = get_config()
	channels = _config.get('CHANNELS')
	sample = session if session else random.sample(os.listdir(folder), 1)[0]
	images = sorted(os.listdir(os.path.join(folder, sample)))
	images.append(images.pop(images.index(images[0])))
	fig, axs = plt.subplots(3, 5, figsize=(18, 12))
	for i, axl in enumerate(axs):
		if i == 0:
			for k in range(5):
				axl[k].set_title(channels[k])
		for j, ax in enumerate(axl):
			brain_vol = nib.load(os.path.join(os.path.join(folder, sample), images[j]))
			isocenter = list(map(int, plotting.find_xyz_cut_coords(brain_vol)))
			if j == len(images) - 1:
				mask_colored, _ = get_colored_mask(get_slice(brain_vol, i, isocenter[i]))
				brain_vol = nib.load(os.path.join(os.path.join(folder, sample), images[j - 1]))
				ax.imshow(get_slice(brain_vol, i, isocenter[i]), cmap='gist_yarg')
				ax.imshow(mask_colored)
			else:
				ax.imshow(get_slice(brain_vol, i, isocenter[i]), cmap='gist_yarg')
			ax.spines['top'].set_visible(False)
			ax.spines['right'].set_visible(False)
			ax.spines['bottom'].set_visible(False)
			ax.spines['left'].set_visible(False)
			a = {0:'X',1:'Y',2:'Z'}
			ax.set_xlabel(a[i]+'='+str(isocenter[i]))
			ax.get_xaxis().set_ticks([])
			ax.get_yaxis().set_ticks([])
	brain_vol = nib.load(os.path.join(os.path.join(folder, sample), images[j - 1]))
	brain_mask = nib.load(os.path.join(os.path.join(folder, sample), images[j]))
	plotting.plot_epi(brain_vol, display_mode='z', cmap='hot_white_bone', title=images[j - 1])
	plotting.plot_epi(brain_mask, display_mode='z', cmap='hot_white_bone', title=images[j])
	fig.tight_layout()
	fig.suptitle(sample, fontsize=18)
	plt.show()
	return sample


def counter(folder):
	"""
	Plot data counters.
	Args:
		folder (str): the path of the folder containing data.
	Returns:
		None.
	"""
	mr_sessions = sorted([f.split('-')[2] for f in os.listdir(folder)])
	n_subjects = len(list(set(mr_sessions)))
	mr_sessions = len(mr_sessions)
	fig, ax = plt.subplots(1, 1, figsize=(18, 8))
	bar_labels = ['MRI Sessions (n.'+str(mr_sessions)+')', 'Nr. Subjects (n.'+str(n_subjects)+')']
	bars = ax.bar(['MRI Sessions', 'Nr. Subjects'], height=[mr_sessions, n_subjects], label=bar_labels, color=['#8fce00', '#ff8200'])
	for rect in bars:
		height = rect.get_height()
		plt.text(rect.get_x() + rect.get_width() / 2.0, height, f'{height:.0f} ({height/mr_sessions*100:.2f}%)', ha='center', va='bottom')
	plt.xlabel('DATA', labelpad=20)
	plt.ylabel('COUNT', labelpad=20)
	plt.title('EXPLORING DATA')
	plt.legend()
	fig.tight_layout()
	plt.show()


def brats_classes(folder, session=None, axis=2):
	"""
	Plot data labels and data classes according to BraTS-2023.
	Args:
		folder (str): the path of the folder containing data.
		session (str): a session ID, if not provided a random ID will be selected.
		axis (int): axis of the spatial image. Values are: 0=X_axis, 1=Y_axis, 2=Z_axis.
	Returns:
		None.
	"""
	_config = get_config()
	labels = _config.get('LABELS')
	classes = _config.get('CLASSES')
	sample = session if session else random.sample(os.listdir(folder), 1)[0]
	images = sorted(os.listdir(os.path.join(folder, sample)))
	fig, axs = plt.subplots(2, 3, figsize=(18, 12))
	brain_mask = nib.load(os.path.join(os.path.join(folder, sample), images[0]))
	brain_vol = nib.load(os.path.join(os.path.join(folder, sample), images[1]))
	print(f"Image shape: {brain_vol.shape}")
	isocenter = list(map(int, plotting.find_xyz_cut_coords(brain_mask)))
	_, label_masks = get_colored_mask(get_slice(brain_mask, axis, isocenter[axis]))
	brain_classes = get_brats_classes(brain_mask)
	for i, axl in enumerate(axs):
		for j, ax in enumerate(axl):
			if i == 0:
				ax.imshow(get_slice(brain_vol, axis, isocenter[axis]), cmap='gist_yarg')
				ax.imshow(label_masks[j])
				ax.set_title('Label '+str(j+1)+': '+labels[j])
			else:
				ax.imshow(get_slice(brain_classes[j], axis, isocenter[axis]), cmap='gray')
				ax.set_title('Class '+str(j+1)+': '+classes[j])
			ax.axis('off')
	fig.tight_layout()
	plt.show()


def input_output(example):
	"""
	Plot data input after preprocessing and data output according to BraTS-2023.
	Args:
		example (dict): an example returned from Dataloader.
	Returns:
		None.
	"""
	_config = get_config()
	classes = _config.get('CLASSES')
	channels = _config.get('CHANNELS')
	axes_l = ['X=100', 'Y=100', 'Z=60']
	brain_vol = example['image'].detach().cpu().numpy()
	brain_mask = example['label'].detach().cpu().numpy()
	brain_vol3d = nib.Nifti1Image(brain_vol[0], affine=np.eye(4))
	brain_mask3d = nib.Nifti1Image(brain_mask[0], affine=np.eye(4))
	isocenter_vol = list(map(int, plotting.find_xyz_cut_coords(brain_vol3d)))
	isocenter_mask = list(map(int, plotting.find_xyz_cut_coords(brain_mask3d)))
	plt.figure('image-t1c', (18, 6))
	for i in range(3):
		plt.subplot(1, 3, i + 1)
		plt.title(axes_l[i])
		plt.axis('off')
		plt.imshow(get_slice(brain_vol[0], i, isocenter_vol[i]), cmap='gray')
	plt.show()
	plt.figure('image', (18, 6))
	for i in range(4):
		plt.subplot(1, 4, i + 1)
		plt.title(channels[i])
		plt.axis('off')
		plt.imshow(get_slice(brain_vol[i], 2, isocenter_vol[2]), cmap='gray')
	plt.show()
	plt.figure('label', (18, 6))
	for i in range(3):
		plt.subplot(1, 3, i + 1)
		plt.title(classes[i])
		plt.axis('off')
		plt.imshow(get_slice(brain_mask[i], 2, isocenter_mask[2]))
	plt.show()


def training_values(folder):
	"""
	Plot losses and metrics over training phase.
	Args:
		folder (str): the path of the folder containing the csv reports.
	Returns:
		None.
	"""
	trainings = sorted([i for i in os.listdir(folder) if '_training.csv' in i])
	labels = [l.split('_')[0] for l in trainings]
	if len(trainings):
		fig, axs = plt.subplots(len(trainings), 2, figsize=(18, 6 * len(trainings)))
		for k, ax_row in enumerate(axs):
			df = pd.read_csv(os.path.join(folder, trainings[k]))
			run_id = sorted(df['id'].unique())[0]
			data_df = df[df['id'] == run_id]
			best_epoch = data_df.iloc[data_df['dice_score'].idxmax()]['epoch']
			x = [i + 1 for i in range(len(data_df))]
			ax_row[0].plot(x, data_df['train_dice_loss'].to_numpy(), label='training_loss')
			ax_row[0].plot(x, data_df['eval_dice_loss'].to_numpy(), label='evaluation_loss')
			ax_row[0].set_xticks([i for i in range(0, len(data_df), 5)])
			ax_row[0].axvline(best_epoch, color='red')
			ax_row[0].text(best_epoch - 3.2, data_df['train_dice_loss'].max() / 2, 'best_run', rotation=0)
			ax_row[0].set_xlabel('EPOCHS', fontsize=14)
			ax_row[0].set_ylabel('DICE LOSS', fontsize=14)
			ax_row[0].set_title(labels[k], fontsize=18)
			ax_row[0].legend(loc='upper center')
			ax_row[1].plot(x, data_df['dice_score_et'].to_numpy(), label='enhancing_tumor')
			ax_row[1].plot(x, data_df['dice_score_tc'].to_numpy(), label='tumor_core')
			ax_row[1].plot(x, data_df['dice_score_wt'].to_numpy(), label='whole_tumor')
			ax_row[1].set_xticks([i for i in range(0, len(data_df), 5)])
			ax_row[1].set_yticks(np.round(np.linspace(.0, 1., 10), 1))
			ax_row[1].axvline(best_epoch, color='red')
			ax_row[1].text(best_epoch - 3.2, data_df['dice_score_wt'].max() / 2, 'best_run', rotation=0)
			ax_row[1].set_xlabel('EPOCHS', fontsize=14)
			ax_row[1].set_ylabel('DICE SCORE', fontsize=14)
			ax_row[1].set_title(labels[k], fontsize=18)
			ax_row[1].legend(loc='lower center')
		fig.tight_layout()
		plt.show()
	else:
		print('\n' + ''.join(['> ' for i in range(30)]))
		print('\nERROR: no model report found.\n')
		print(''.join(['> ' for i in range(30)]) + '\n')


def prediction(model_name, folder):
	"""
	Plot original image data, groundtruth label and predicted mask.
	Args:
		model_name (str): the model name. `model_name` is case sensitive.
		folder (str): the path of the folder containing the csv reports.
	Returns:
		None.
	"""
	_config = get_config()
	classes = _config.get('CLASSES')
	channels = _config.get('CHANNELS')
	images = [i for i in os.listdir(folder) if '.nii' in i]
	ids = list(set([int(i.split('_')[2]) for i in images]))
	if len(ids) > 1:
		n = random.sample(ids, 1)[0]
		kind = ['image', 'label', 'pred']
		for i, k in enumerate(kind):
			brain_vol = nib.load(os.path.join(folder, model_name + '_sample_' + str(n) + '_' + k + '.nii.gz'))
			brain_vol3d = nib.Nifti1Image(brain_vol.get_fdata()[0], affine=np.eye(4))
			isocenter = list(map(int, plotting.find_xyz_cut_coords(brain_vol3d)))
			brain_vol_data = brain_vol.get_fdata()
			plt.figure('image', (18, 6))
			for j in range(4 if i == 0 else 3):
				plt.subplot(1, 4 if i == 0 else 3, j + 1)
				plt.title(k + '_' + str(n) + ' - ' + (channels[j] if i == 0 else classes[j]))
				plt.axis('off')
				img = brain_vol_data[j, :, :, isocenter[2]]
				if i == 0:
					plt.imshow(img, cmap = 'gray')
				else:
					plt.imshow(np.rot90(img, 2), cmap = 'viridis')
			plt.show()
	else:
		print('\n' + ''.join(['> ' for i in range(30)]))
		print('\nERROR: sample predictions for\033[95m '+model_name+'\033[0m not found.\n')
		print(''.join(['> ' for i in range(30)]) + '\n')


def results(folder):
	"""
	Plot all metrics calculated over the testing set.
	Args:
		folder (str): the path of the folder containing the csv reports.
	Returns:
		None.
	"""
	try:
		p = os.path.join(folder, 'results.csv')
		df = pd.read_csv(p)
		for metric in ['dice', 'hausdorff']:
			print(''.join(['> ' for i in range(40)]))
			print(f'\n{"":<20}{metric.upper()+"_ET":<15}{metric.upper()+"_TC":<15}{metric.upper()+"_WT":<15}{metric.upper()+"_AVG":<15}\n')
			print(''.join(['> ' for i in range(40)]))
			for model in df['model']:
				et = df[df["model"] == model][metric+"_score_et"].values[0]
				tc = df[df["model"] == model][metric+"_score_tc"].values[0]
				wt = df[df["model"] == model][metric+"_score_wt"].values[0]
				if model == 'SegResNet':
					print(f'\033[1m{model:<20}{et:<15.4f}{tc:<15.4f}{wt:<15.4f}{np.mean([et, tc, wt]):<15.4f}\033[0m')
				else:
					print(f'{model:<20}{et:<15.4f}{tc:<15.4f}{wt:<15.4f}{np.mean([et, tc, wt]):<15.4f}')
		print(''.join(['> ' for i in range(40)]))
	except OSError as e:
		print('\n' + ''.join(['> ' for i in range(30)]))
		print('\nERROR: file\033[95m  reports.csv\033[0m not found.\n')
		print(''.join(['> ' for i in range(30)]) + '\n')


def available_llms():
	"""
	Printing all available llms as defined in `src.helpers.config`.
	Args:
		None.
	Returns:
		None.
	"""
	_config = get_config()
	llms = _config.get('LLM')
	print(''.join(['> ' for i in range(35)]))
	print(f'\n{"MODEL_KEY":<15}{"MODEL_NAME":<25}\n')
	print(''.join(['> ' for i in range(35)]))
	for k in llms.keys():
		print(f'\033[1m{k:<15}\033[0m{llms[k].split("/")[-1]:<25}')


def llms_metrics(report_path):
	"""
	Plot metrics related to LLMs.
	Args:
		report_path (str): absolute path where metrics data are saved.
	Returns:
		None.
	"""
	_config = get_config()
	llm_params = _config.get('LLM_PARAMS')
	llm_params = {k: int(v[:-1]) for k, v in llm_params.items()}
	llm_params = {k: v for k, v in sorted(llm_params.items(), key = lambda item: item[1], reverse = False)}
	df = pd.read_csv(os.path.join(report_path, 'LLM_metrics.csv'))
	llm_times = df.loc[:, df.columns != 'lang'].groupby('model').mean()['inference_time'].to_dict()
	llm_times = {k: v for k, v in sorted(llm_times.items(), key = lambda item: item[1], reverse = False)}
	fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 6))
	rects = ax1.barh(list(llm_params.keys()), list(llm_params.values()), align='center', height=0.5)
	ax1.bar_label(rects, [str(i) + 'B' for i in list(llm_params.values())], padding=-30, color='white', fontsize=16, fontweight='bold')
	ax1.set_xticks(np.arange(0, max(list(llm_params.values())) + 1))
	ax1.set_yticks(ticks=list(llm_params.keys()), labels=list(llm_params.keys()), fontsize=14)
	ax1.xaxis.grid(True, linestyle='--', which='major', color='grey', alpha=.25)
	ax1.set_title('Number of params', fontsize=20, fontweight='bold')
	ax1.set_xlabel('Number of params (in billions)', fontsize=14)
	rects = ax2.barh(list(llm_times.keys()), list(llm_times.values()), align='center', height=0.5)
	ax2.bar_label(rects, [str(int(i)) + 's' for i in list(llm_times.values())], padding=-48, color='white', fontsize=16, fontweight='bold')
	ax2.set_xticks(np.arange(0, max(list(llm_times.values())) + 10, 50))
	ax2.set_yticks(ticks=list(llm_times.keys()), labels=list(llm_times.keys()), fontsize=14)
	ax2.xaxis.grid(True, linestyle='--', which='major', color='grey', alpha=.25)
	ax2.set_title('Inference times', fontsize=20, fontweight='bold')
	ax2.set_xlabel('Inference times (in seconds)', fontsize=14)
	fig.tight_layout()
	plt.show()



def llms_textual_metrics(metrics, titles, report_path, dynamic_padding_rate = 10):
	"""
	Plot metrics related to LLMs textual outputs.
	Args:
		metrics (list): two numerical metrics to plot included in the report file.
		titles (list): two titles to associate to the selected metrics.
		report_path (str): absolute path where metrics data are saved.
		dynamic_padding_rate (int): plotted lines padding expressed as percentage.
	Returns:
		None.
	"""
	df = pd.read_csv(os.path.join(report_path, 'LLM_metrics.csv'))
	llm_en = ['biomistral', 'llama', 'mistral']
	llm_it = ['llama', 'mistral', 'llamantino2', 'llamantino3', 'minerva']
	left_ylabels = ['English', 'Italian']
	left_score = df.groupby(['model', 'lang', 'prompt_id']).mean()[metrics[0]].to_dict()
	left_score_en = [[v for k, v in left_score.items() if k[0] == m and k[1] == 'EN' ] for m in llm_en]
	left_score_it = [[v for k, v in left_score.items() if k[0] == m and k[1] == 'IT' ] for m in llm_it]
	right_score = df.groupby(['model', 'lang', 'prompt_id']).mean()[metrics[1]].to_dict()
	right_score_en = [[v for k, v in right_score.items() if k[0] == m and k[1] == 'EN' ] for m in llm_en]
	right_score_it = [[v for k, v in right_score.items() if k[0] == m and k[1] == 'IT' ] for m in llm_it]

	fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 12))
	axs = [ax1, ax2, ax3, ax4]
	data = [left_score_en, right_score_en, left_score_it, right_score_it]
	for j, ax in enumerate(axs):
		llms = llm_en if j < 2 else llm_it
		ticks = [i for i in range(len(llms))]
		ax.plot(ticks, data[j], label=['Prompt_1', 'Prompt_2'], marker='D', markersize=12, linewidth=3)
		ax.plot(ticks, [np.mean(i) for i in data[j]], label='mean', color='red', marker='o', markersize=8, linestyle='dotted', linewidth=2)
		ax.set_xticks(ticks=ticks, labels=llms, fontsize=14)
		ax.yaxis.grid(True, linestyle='--', which='major', color='grey', alpha=.25)
		ax.legend(fontsize=12, labelspacing=1)
		if j < 2:
			ax.set_title(titles[j], fontsize=20, fontweight='bold', pad=20)
		if j % 2 == 0:
			ax.set_ylabel(left_ylabels[int(j/2)], fontsize=16, fontweight='bold')
			dyn_pad = (max(left_score.values()) - min(left_score.values())) * dynamic_padding_rate / 100
			ax.set_ylim([min(left_score.values()) - dyn_pad, max(left_score.values()) + dyn_pad])
		else:
			dyn_pad = (max(right_score.values()) - min(right_score.values())) * dynamic_padding_rate / 100
			ax.set_ylim([min(right_score.values()) - dyn_pad, max(right_score.values()) + dyn_pad])
	fig.tight_layout()
	plt.show()


def llms_average_metrics(report_path, lang = 'all'):
	"""
	Plot all metrics by averaging their values.
	Args:
		report_path (str): absolute path where metrics data are saved.
		lang (str): the language by which aggregate the results. Deafult `all` do not filter by language.
	Returns:
		None.
	"""
	df = pd.read_csv(os.path.join(report_path, 'LLM_metrics.csv'))
	metrics = [m for m in df.columns if m not in ['model', 'lang', 'prompt_id']]
	llms = {
		'en': ['biomistral', 'llama', 'mistral'],
		'it': ['llama', 'mistral', 'llamantino2', 'llamantino3', 'minerva'],
		'all': ['biomistral', 'llama', 'mistral', 'llamantino2', 'llamantino3', 'minerva']
	}
	print(''.join(['> ' for i in range(55)]))
	if lang.lower() == 'en':
		print(f'\n{"METRIC":<24}{"BIOMISTRAL":>14}{"LLAMA":>14}{"MISTRAL":>14}\n')
	elif lang.lower() == 'it':
		print(f'\n{"METRIC":<24}{"LLAMA":>14}{"MISTRAL":>14}{"LLAMANTINO2":>14}{"LLAMANTINO3":>14}{"MINERVA":>14}\n')
	else:
		print(f'\n{"METRIC":<24}{"BIOMISTRAL":>14}{"LLAMA":>14}{"MISTRAL":>14}{"LLAMANTINO2":>14}{"LLAMANTINO3":>14}{"MINERVA":>14}\n')
	print(''.join(['> ' for i in range(55)]))
	for m in metrics:
		if lang.lower() == 'all':
			data = [df.loc[df['model'] == l][m].mean() for l in llms[lang.lower()]]
		else:
			data = [df.loc[(df['model'] == l) & (df['lang'] == lang.upper())][m].mean() for l in llms[lang.lower()]]
		s = ''
		for k, d in enumerate(data):
			ds = str(round(d, 2))
			s += ''.join([' ' for i in range(14 - len(ds))])
			if m == 'inference_time' or m == 'diversity_MAAS':
				s += ('\033[1m\033[91m'+ds+'\033[0m' if k == np.argmax(data) else ('\033[1m\033[92m'+ds+'\033[0m' if k ==  np.argmin(data) else ds))
			else:
				s += ('\033[1m\033[92m'+ds+'\033[0m' if k == np.argmax(data) else ('\033[1m\033[91m'+ds+'\033[0m' if k ==  np.argmin(data) else ds))
		print(f'{m:<24}{s:>14}')
