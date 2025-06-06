"""
A set of plotting functions
"""
import os, random
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from nilearn import plotting
import nibabel as nib
from src.helpers.utils import get_colored_mask, get_slice, get_brats_classes, compute_bootstrap_ci, compute_sd_iqr, compute_statistical_test
from src.helpers.config import get_config
import itertools


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


def results(folder, rnd = 4, ci = 95):
	"""
	Plot all metrics calculated over the testing set.
	Args:
		folder (str): the path of the folder containing the csv reports.
		rnd (int): number of rounding digits.
		ci (int): confidence level (e.g., 95 for 95% CI).
	Returns:
		None.
	"""
	try:
		p = os.path.join(folder, 'results.csv')
		df = pd.read_csv(p)
		for metric in ['dice', 'hausdorff']:
			print(''.join(['> ' for i in range(50)]))
			print(f'\n{"":<20}{metric.upper()+"_ET":<20}{metric.upper()+"_TC":<20}{metric.upper()+"_WT":<20}{metric.upper()+"_AVG":<20}\n')
			print(''.join(['> ' for i in range(50)]))
			for model in df['model'].unique():
				if metric is 'dice':
					et = df[df["model"] == model]["dice_score_et"].to_numpy()
					et_mean, et_lower, et_upper = compute_bootstrap_ci(et, ci=ci)
					et_s = '[' + str(round(et_lower, rnd)) + ',' + str(round(et_upper, rnd)) + ']'
					tc = df[df["model"] == model]["dice_score_tc"].to_numpy()
					tc_mean, tc_lower, tc_upper = compute_bootstrap_ci(tc, ci=ci)
					tc_s = '[' + str(round(tc_lower, rnd)) + ',' + str(round(tc_upper, rnd)) + ']'
					wt = df[df["model"] == model]["dice_score_wt"].to_numpy()
					wt_mean, wt_lower, wt_upper = compute_bootstrap_ci(wt, ci=ci)
					wt_s = '[' + str(round(wt_lower, rnd)) + ',' + str(round(wt_upper, rnd)) + ']'
					mn = df[df["model"] == model]["dice_score_mean"].to_numpy()
					mn_mean, mn_lower, mn_upper = compute_bootstrap_ci(mn, ci=ci)
					mn_s = '[' + str(round(mn_lower, rnd)) + ',' + str(round(mn_upper, rnd)) + ']'
					if model == 'SegResNet':
						print(f'\033[1m{model:<24}{str(round(et_mean, rnd)):<20}{str(round(tc_mean, rnd)):<20}{str(round(wt_mean, rnd)):<20}{str(round(mn_mean, rnd)):<20}\033[0m')
						print(f'\033[1m{model+"_CI_"+str(ci)+"%":<20}{et_s:<20}{tc_s:<20}{wt_s:<20}{mn_s:<20}\033[0m')
					else:
						print(f'{model:<24}{str(round(et_mean, rnd)):<20}{str(round(tc_mean, rnd)):<20}{str(round(wt_mean, rnd)):<20}{np.mean([et_mean, tc_mean, wt_mean]):<20.4f}')
						print(f'{model+"_CI_"+str(ci)+"%":<20}{et_s:<20}{tc_s:<20}{wt_s:<20}{mn_s:<20}')
				else:
					et = round(df[df["model"] == model][metric+"_score_et"].mean(), rnd)
					tc = round(df[df["model"] == model][metric+"_score_tc"].mean(), rnd)
					wt = round(df[df["model"] == model][metric+"_score_wt"].mean(), rnd)
					mn = round(np.mean([et, tc, wt]), rnd)
					if model == 'SegResNet':
						print(f'\033[1m{model:<20}{et:<20}{tc:<20}{wt:<20}{mn:<20}\033[0m')
					else:
						print(f'{model:<20}{et:<20}{tc:<20}{wt:<20}{mn:<20}')
		print(''.join(['> ' for i in range(50)]))
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


def llms_metrics(report_path, report_source = 'hf'):
	"""
	Plot metrics related to LLMs.
	Args:
		report_path (str): absolute path where metrics data are saved.
		report_source (str): the data source (`hf` for HuggingFace, `groq` for Groq).
	Returns:
		None.
	"""
	_config = get_config()
	llm_params = _config.get('LLM_PARAMS').get(report_source)
	llm_params = {k: int(v[:-1]) for k, v in llm_params.items()}
	llm_params = {k: v for k, v in sorted(llm_params.items(), key = lambda item: item[1], reverse = False)}
	df = pd.read_csv(os.path.join(report_path, 'LLM_metrics_' + report_source.upper() + '.csv'))
	llm_times = df.loc[:, (df.columns != 'lang') & (df.columns != 'sample_id')].groupby('model').mean()['inference_time'].to_dict()
	llm_times = {k: v for k, v in sorted(llm_times.items(), key = lambda item: item[1], reverse = False)}
	fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 6))
	rects = ax1.barh(list(llm_params.keys()), list(llm_params.values()), align='center', height=0.5)
	ax1.bar_label(rects, [str(i) + 'B' for i in list(llm_params.values())], padding=-30, color='white', fontsize=16, fontweight='bold')
	ax1.set_xticks(np.arange(0, max(list(llm_params.values())) + 1, (5 if max(list(llm_params.values())) > 10 else 2)))
	ax1.set_yticks(ticks=list(llm_params.keys()), labels=list(llm_params.keys()), fontsize=14)
	ax1.xaxis.grid(True, linestyle='--', which='major', color='grey', alpha=.25)
	ax1.set_title('Number of params', fontsize=20, fontweight='bold')
	ax1.set_xlabel('Number of params (in billions)', fontsize=14)
	rects = ax2.barh(list(llm_times.keys()), list(llm_times.values()), align='center', height=0.5)
	ax2.bar_label(rects, [str(int(i)) + 's' for i in list(llm_times.values())], padding=-48, color='white', fontsize=16, fontweight='bold')
	ax2.set_xticks(np.arange(0, max(list(llm_times.values())) + 1, (50 if max(list(llm_times.values())) > 100 else 2)))
	ax2.set_yticks(ticks=list(llm_times.keys()), labels=list(llm_times.keys()), fontsize=14)
	ax2.xaxis.grid(True, linestyle='--', which='major', color='grey', alpha=.25)
	ax2.set_title('Inference times', fontsize=20, fontweight='bold')
	ax2.set_xlabel('Inference times (in seconds)', fontsize=14)
	fig.tight_layout()
	plt.show()



def llms_textual_metrics(
		metrics,
		titles,
		report_path,
		report_source = 'hf',
		dynamic_padding_rate = 10
	):
	"""
	Plot metrics related to LLMs textual outputs.
	Args:
		metrics (list): two numerical metrics to plot included in the report file.
		titles (list): two titles to associate to the selected metrics.
		report_path (str): absolute path where metrics data are saved.
		report_source (str): the data source (`hf` for HuggingFace, `groq` for Groq).
		dynamic_padding_rate (int): plotted lines padding expressed as percentage.
	Returns:
		None.
	"""
	df = pd.read_csv(os.path.join(report_path, 'LLM_metrics_' + report_source.upper() + '.csv'))
	df = df.loc[:, df.columns != 'sample_id']
	llm_en = df[df['lang'] == 'EN']['model'].unique()
	llm_it = df[df['lang'] == 'IT']['model'].unique()
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


def llms_average_metrics(report_path, report_source = 'hf', lang = 'all', rounding = 2):
	"""
	Plot all metrics by averaging their values.
	Args:
		report_path (str): absolute path where metrics data are saved.
		report_source (str): the data source (`hf` for HuggingFace, `groq` for Groq)
		lang (str): the language by which aggregate the results. Deafult `all` do not filter by language.
		rounding (int): number of decimal digits.
	Returns:
		None.
	"""
	df = pd.read_csv(os.path.join(report_path, 'LLM_metrics_' + report_source.upper() + '.csv'))
	metrics = [m for m in df.columns if m not in ['model', 'lang', 'sample_id', 'prompt_id']]
	llms = df['model'].unique() if lang == 'all' else df[df['lang'] == lang]['model'].unique()
	print(''.join(['> ' for i in range(55)]))
	sm = 'METRIC' + ''.join([' ' for i in range(20)])
	for m in llms:
		sm += m.upper() + ''.join([' ' for i in range(28 - len(m))])
	print('\n', sm, '\n')
	print(''.join(['> ' for i in range(55)]))
	for m in metrics:
		if lang.lower() == 'all':
			data = [compute_sd_iqr(df.loc[df['model'] == l][m].to_numpy()) for l in llms]
			means = [i['mean'] for i in data]
		else:
			data = [compute_sd_iqr(df.loc[(df['model'] == l) & (df['lang'] == lang.upper())][m].to_numpy()) for l in llms]
			means = [i['mean'] for i in data]
		s, q, q13 = '', '', ''
		for k, d in enumerate(data):
			ds = str(round(means[k], rounding)) + ' ± ' + str(round(data[k]['std_dev'], rounding)) + '(SD)'
			dq = 'IQR: ' + str(round(d['iqr'], rounding))
			dq13 = '(Q1=' + str(round(d['q1'], rounding)) + ', Q3=' + str(round(d['q3'], rounding)) + ')'
			s += ''.join([' ' for i in range(24 - len(ds))])
			q += ''.join([' ' for i in range(24 - len(dq))]) + dq
			q13 += ''.join([' ' for i in range(24 - len(dq13))]) + dq13
			if m == 'inference_time' or m == 'diversity_MAAS':
				s += ('\033[1m\033[91m'+ds+'\033[0m' if k == np.argmax(means) else ('\033[1m\033[92m'+ds+'\033[0m' if k ==  np.argmin(means) else ds))
			else:
				s += ('\033[1m\033[92m'+ds+'\033[0m' if k == np.argmax(means) else ('\033[1m\033[91m'+ds+'\033[0m' if k ==  np.argmin(means) else ds))
		print(f'{m:<24}{s:>14}')
		print(f'{"":<24}{q:>14}')
		print(f'{"":<24}{q13:>14}\n')


def evaluation_error(
	folder,
	report_name = 'error_eval_tc.csv'
):
	"""
	Plot evaluation error report.
	Args:
		folder (str): the path of the folder containing data.
		report_name (str): csv file name where data report are saved.
	Returns:
		None.
	"""
	df = pd.read_csv(os.path.join(folder, report_name), encoding='UTF-8')
	diff_regions = df[df['type'] == 'Different_Regions']
	diff_regions_not_true = df[df['type'] == 'Different_Regions_Not_True']
	diff_tumor = df[df['type'] == 'Different_Percentage_of_Tumor']
	pr_all_2, pr_all_5, pr_all_all, prnt_all_1, prnt_all_2, prnt_all_all, pt_all = [], [], [], [], [], [], []
	for i in range(30, 0, -1):
		differences_regions = diff_regions[str(i)].dropna().to_numpy()
		qty = np.unique(differences_regions, return_counts=True)[1]
		percent_regions = sum(qty[1:]) * 100 / sum(qty)
		pr_all_2.append(percent_regions)
		percent_regions = sum(qty[2:]) * 100 / sum(qty)
		pr_all_5.append(percent_regions)
		percent_regions = sum(qty[3:]) * 100 / sum(qty)
		pr_all_all.append(percent_regions)
		differences_regions_not_true = diff_regions_not_true[str(i)].dropna().to_numpy()
		qty = np.unique(differences_regions_not_true, return_counts=True)[1]
		percent_regions = sum(qty[1:]) * 100 / sum(qty)
		prnt_all_1.append(percent_regions)
		percent_regions = sum(qty[2:]) * 100 / sum(qty)
		prnt_all_2.append(percent_regions)
		percent_regions = sum(qty[3:]) * 100 / sum(qty)
		prnt_all_all.append(percent_regions)
		differences_tumor = diff_tumor[str(i)].dropna().to_numpy()
		percent_tumor = sum(differences_tumor) / len(differences_tumor)
		pt_all.append(percent_tumor)
	fig, ax = plt.subplots(1, 1, figsize=(18, 8))
	categories = list(range(30, 0, -1))
	line1 = ax.plot(categories, pr_all_2, label='At least 1 mismatch', color='blue', marker='o', linestyle='-', linewidth=2)
	line2 = ax.plot(categories, pr_all_5, label='At least 2 mismatches', color='red', marker='o', linestyle='-', linewidth=2)
	line3 = ax.plot(categories, pr_all_all, label='At least 3 mismatches', color='green', marker='o', linestyle='-', linewidth=2)
	for i in range(len(categories)):
		ax.text(categories[i], pr_all_2[i] + 1, f'{pr_all_2[i]:.1f}%', ha='center', va='bottom', color='blue', fontsize=10)
		ax.text(categories[i], pr_all_5[i] + 1, f'{pr_all_5[i]:.1f}%', ha='center', va='bottom', color='red', fontsize=10)
		ax.text(categories[i], pr_all_all[i] - 2, f'{pr_all_all[i]:.1f}%', ha='center', va='bottom', color='green', fontsize=10)
	plt.xticks(categories)
	plt.gca().invert_xaxis()
	plt.xlabel('NR. OF REGIONS', labelpad=20, fontsize=12)
	plt.ylabel('PERCENTAGE OF ERROR', labelpad=20, fontsize=12)
	plt.title('REGIONS MISMATCH', fontsize=14)
	plt.legend()
	fig.tight_layout()
	plt.show()
	fig, ax = plt.subplots(1, 1, figsize=(18, 8))
	categories = list(range(30, 0, -1))
	line1 = ax.plot(categories, prnt_all_1, label='At least 1 wrong region', color='blue', marker='o', linestyle='-', linewidth=2)
	line2 = ax.plot(categories, prnt_all_2, label='At least 2 wrong regions', color='red', marker='o', linestyle='-', linewidth=2)
	line3 = ax.plot(categories, prnt_all_all, label='At least 3 wrong regions', color='green', marker='o', linestyle='-', linewidth=2)
	for i in range(len(categories)):
		ax.text(categories[i], prnt_all_1[i] + 1.5, f'{prnt_all_1[i]:.1f}%', ha='center', va='bottom', color='blue', fontsize=10)
		ax.text(categories[i], prnt_all_2[i] + .3, f'{prnt_all_2[i]:.1f}%', ha='center', va='bottom', color='red', fontsize=10)
		ax.text(categories[i], prnt_all_all[i] - 2, f'{prnt_all_all[i]:.1f}%', ha='center', va='bottom', color='green', fontsize=10)
	plt.xticks(categories)
	plt.gca().invert_xaxis()
	plt.xlabel('NR. OF REGIONS', labelpad=20, fontsize=12)
	plt.ylabel('PERCENTAGE OF ERROR', labelpad=20, fontsize=12)
	plt.title('WRONG REGIONS', fontsize=14)
	plt.legend()
	fig.tight_layout()
	plt.show()


def statistical_test(report_path, report_source = 'hf', lang = 'all'):
	"""
	Plot the results of the statistical test for each pair of LLMs in report file.
	Args:
		report_path (str): absolute path where metrics data are saved.
		report_source (str): the data source (`hf` for HuggingFace, `groq` for Groq)
		lang (str): the language by which aggregate the results. Deafult `all` do not filter by language.
	Returns:
		None.
	"""
	df = pd.read_csv(os.path.join(report_path, 'LLM_metrics_' + report_source.upper() + '.csv'))
	metrics = [m for m in df.columns if m not in ['model', 'lang', 'sample_id', 'prompt_id', 'inference_time']]
	llms = df['model'].unique() if lang == 'all' else df[df['lang'] == lang]['model'].unique()
	pairs = list(itertools.combinations(llms, 2))
	for p in pairs:
		print('\n')
		print(''.join(['> ' for i in range(55)]))
		print(f'\n{p[0].upper()+"-"+p[1].upper():>40}\n')
		print(f'\n{"METRIC":<25}{"TEST":<25}{"P-VALUE":<10}{"SIGNIFICANT":<10}\n')
		print(''.join(['> ' for i in range(55)]))
		for m in metrics:
			metric_a = df[df["model"] == p[0]][m].to_numpy()
			metric_b = df[df["model"] == p[1]][m].to_numpy()
			results = compute_statistical_test(metric_a, metric_b)
			print(f'{m:<25}{results["test_name"]:<25}{results["p_value"]:<10.4f}{str(results["significant"]):<10}')
