"""
Functions for training the models.
"""
import os, random, time, datetime, calendar, csv
from sys import platform
import torch
import numpy as np
from monai.data import DataLoader, decollate_batch, CacheDataset
from monai.losses import DiceLoss
from monai.inferers import sliding_window_inference
from monai.metrics import DiceMetric
from monai.transforms import Activations, AsDiscrete, Compose


def train_test_splitting(folder, train_ratio=.8, verbose=True):
	"""
	Splitting train/eval/test.
	Args:
		folder (str): the path of the folder containing data.
		train_ratio (float): ratio of the training set, value between 0 and 1.
		verbose (bool): whether or not print information.
	Returns:
		train_data (list): the training data ready to feed monai.data.Dataset
		eval_data (list): the evaluation data ready to feed monai.data.Dataset
		test_data (list): the testing data ready to feed monai.data.Dataset.
		(see https://docs.monai.io/en/latest/data.html#monai.data.Dataset).
	"""
	sessions = [s.split('-')[2] for s in os.listdir(folder)]
	subjects = list(set(sessions))
	random.shuffle(subjects)
	split_train = int(len(subjects) * train_ratio)
	train_subjects, test_subjects = subjects[:split_train], subjects[split_train:]
	split_eval = int(len(train_subjects) * .8)
	eval_subjects = train_subjects[split_eval:]
	train_subjects = train_subjects[:split_eval]
	train_sessions = [os.path.join(folder, s) for s in os.listdir(folder) if s.split('-')[2] in train_subjects]
	eval_sessions = [os.path.join(folder, s) for s in os.listdir(folder) if s.split('-')[2] in eval_subjects]
	test_sessions = [os.path.join(folder, s) for s in os.listdir(folder) if s.split('-')[2] in test_subjects]
	train_labels = [os.path.join(s, s.split('/')[-1] + '-seg.nii.gz') for s in train_sessions]
	eval_labels = [os.path.join(s, s.split('/')[-1] + '-seg.nii.gz') for s in eval_sessions]
	test_labels = [os.path.join(s, s.split('/')[-1] + '-seg.nii.gz') for s in test_sessions]
	modes = ['t1c', 't1n', 't2f', 't2w']
	train_data, eval_data, test_data = {}, {}, {}
	train_data = [dict({
		'image': [os.path.join(s, s.split('/')[-1] + '-' + m + '.nii.gz') for m in modes],
		'label': train_labels[i]
	}) for i, s in enumerate(train_sessions)]
	eval_data = [dict({
		'image': [os.path.join(s, s.split('/')[-1] + '-' + m + '.nii.gz') for m in modes],
		'label': eval_labels[i]
	}) for i, s in enumerate(eval_sessions)]
	test_data = [dict({
		'image': [os.path.join(s, s.split('/')[-1] + '-' + m + '.nii.gz') for m in modes],
		'label': test_labels[i]
	}) for i, s in enumerate(test_sessions)]
	if verbose:
		print(''.join(['> ' for i in range(40)]))
		print(f'\n{"":<20}{"TRAINING":<20}{"EVALUATION":<20}{"TESTING":<20}\n')
		print(''.join(['> ' for i in range(40)]))
		tsb1 = str(len(train_subjects)) + ' (' + str(round((len(train_subjects) * 100 / len(subjects)), 0)) + ' %)'
		tsb2 = str(len(eval_subjects)) + ' (' + str(round((len(eval_subjects) * 100 / len(subjects)), 0)) + ' %)'
		tsb3 = str(len(test_subjects)) + ' (' + str(round((len(test_subjects) * 100 / len(subjects)), 0)) + ' %)'
		tss1 = str(len(train_sessions)) + ' (' + str(round((len(train_sessions) * 100 / len(sessions)), 2)) + ' %)'
		tss2 = str(len(eval_sessions)) + ' (' + str(round((len(eval_sessions) * 100 / len(sessions)), 2)) + ' %)'
		tss3 = str(len(test_sessions)) + ' (' + str(round((len(test_sessions) * 100 / len(sessions)), 2)) + ' %)'
		print(f'\n{"subjects":<20}{tsb1:<20}{tsb2:<20}{tsb3:<20}\n')
		print(f'{"sessions":<20}{tss1:<20}{tss2:<20}{tss3:<20}\n')
	return train_data, eval_data, test_data


def training_model(
		model,
		data,
		transforms,
		epochs,
		val_interval,
		device,
		paths,
		ministep=10,
		write_to_file=True,
		verbose=False
	):
	"""
	Standard Pythorch training program.
	Args:
		model (torch.nn.Module): the model to be trained.
		data (list): the training and evalutaion data.
		transform (list): transformation sequence for training and evaluation data.
		epochs (int): max number of epochs.
		val_interval (int): validation interval.
		device (str): device's name.
		paths (list): folders where to save results and model's dump.
		write_to_file (bool): whether to write results to csv file.
		verbose (bool): whether to print minimal or extended information.
	Returns:
		None.
	"""
	# define Dice loss, Adam optimizer, mean Dice metric, Cosine Annealing scheduler
	loss_function = DiceLoss(smooth_nr=0, smooth_dr=1e-5, squared_pred=True, to_onehot_y=False, sigmoid=True)
	optimizer = torch.optim.Adam(model.parameters(), 1e-4, weight_decay=1e-5)
	lr_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
	dice_metric = DiceMetric(include_background=True, reduction="mean")
	dice_metric_batch = DiceMetric(include_background=True, reduction="mean_batch")
	post_trans = Compose([Activations(sigmoid=True), AsDiscrete(threshold=0.5)])
	scaler = torch.cuda.amp.GradScaler() # use Automatic Pixed Precision to accelerate training
	torch.backends.cudnn.benchmark = True # enable cuDNN benchmark

	# define metric/loss collectors
	best_metric, best_metric_epoch = -1, -1
	best_metrics_epochs_and_time = [[], [], []]
	epoch_loss_values, epoch_time_values = [[], []], []
	metric_values, metric_values_et, metric_values_tc, metric_values_wt = [], [], [], []

	# unfolds grouped data
	train_data, eval_data = data
	train_transform, eval_transform = transforms
	device = torch.device(device)
	saved_path, reports_path = paths

	ts = calendar.timegm(time.gmtime())
	total_start = time.time()
	for epoch in range(epochs):
		epoch_start = time.time()
		print(''.join(['> ' for i in range(30)]))
		print(f"epoch {epoch + 1}/{epochs}")
		model.train()
		epoch_loss_train, epoch_loss_eval = 0, 0
		step_train, step_eval = 0, 0
		ministeps_train = np.linspace(0, len(train_data), ministep).astype(int)
		ministeps_eval = np.linspace(0, len(eval_data), ministep).astype(int)

		# start training
		for i in range(len(ministeps_train) - 1):
			train_ds = CacheDataset(train_data[ministeps_train[i]:ministeps_train[i+1]], transform=train_transform, cache_rate=1.0, num_workers=None, progress=False)
			train_loader = DataLoader(train_ds, batch_size=1, shuffle=True, num_workers=4)
			for batch_data in train_loader:
				step_start = time.time()
				step_train += 1
				inputs, labels = (batch_data['image'].to(device), batch_data['label'].to(device))
				optimizer.zero_grad()
				with torch.cuda.amp.autocast():
					outputs = model(inputs)
					loss = loss_function(outputs, labels)
				scaler.scale(loss).backward()
				scaler.step(optimizer)
				scaler.update()
				epoch_loss_train += loss.item()
				if verbose:
					print(
						f"{step_train}/{len(train_data) // train_loader.batch_size}"
						f", train_loss: {loss.item():.4f}"
						f", step time: {str(datetime.timedelta(seconds=int(time.time() - step_start)))}"
					)
		lr_scheduler.step()
		epoch_loss_train /= step_train
		epoch_loss_values[0].append(epoch_loss_train)
		print(f"epoch {epoch + 1} average training loss: {epoch_loss_train:.4f}")

		# start validation
		if (epoch + 1) % val_interval == 0:
			model.eval()
			with torch.no_grad():
				for i in range(len(ministeps_eval) - 1):
					eval_ds = CacheDataset(eval_data[ministeps_eval[i]:ministeps_eval[i+1]], transform=eval_transform, cache_rate=1.0, num_workers=None, progress=False)
					eval_loader = DataLoader(eval_ds, batch_size=1, shuffle=True, num_workers=4)
					for val_data in eval_loader:
						step_eval += 1
						val_inputs, val_labels = (val_data['image'].to(device), val_data['label'].to(device))
						val_outputs = _inference(val_inputs, device, model)
						val_loss = loss_function(val_outputs, val_labels)
						epoch_loss_eval += val_loss.item()
						val_outputs = [post_trans(i) for i in decollate_batch(val_outputs)]
						dice_metric(y_pred=val_outputs, y=val_labels)
						dice_metric_batch(y_pred=val_outputs, y=val_labels)
				epoch_loss_eval /= step_eval
				epoch_loss_values[1].append(epoch_loss_eval)

				# calculate metrics
				metric = dice_metric.aggregate().item()
				metric_values.append(metric)
				metric_batch = dice_metric_batch.aggregate()
				metric_et = metric_batch[0].item()
				metric_values_et.append(metric_et)
				metric_tc = metric_batch[1].item()
				metric_values_tc.append(metric_tc)
				metric_wt = metric_batch[2].item()
				metric_values_wt.append(metric_wt)
				dice_metric.reset()
				dice_metric_batch.reset()

				# save best performing model
				if metric > best_metric:
					best_metric = metric
					best_metric_epoch = epoch + 1
					best_metrics_epochs_and_time[0].append(best_metric)
					best_metrics_epochs_and_time[1].append(best_metric_epoch)
					best_metrics_epochs_and_time[2].append(time.time() - total_start)
					torch.save(model.state_dict(), os.path.join(saved_path, model.name + '_best.pth'))
					print("saved new best model")
				print(
					f"current epoch: {epoch + 1} current mean dice: {metric:.4f}"
					f" tc: {metric_tc:.4f} wt: {metric_wt:.4f} et: {metric_et:.4f}"
					f"\nbest mean dice: {best_metric:.4f}"
					f" at epoch: {best_metric_epoch}"
				)
		print(f"time consuming of epoch {epoch + 1} is: {str(datetime.timedelta(seconds=int(time.time() - epoch_start)))}")
		epoch_time_values.append(time.time() - epoch_start)

		# save results to file
		if write_to_file:
			_save_results(
				file = os.path.join(reports_path, model.name + '_training.csv'),
				metrics = {
					'id': model.name.upper() + '_' + str(ts),
					'epoch': epoch + 1,
					'model': model.name,
					'train_loss': epoch_loss_train,
					'eval_loss': epoch_loss_eval,
					'exec_time': time.time() - epoch_start,
					'metric': metric,
					'metric_et': metric_et,
					'metric_tc': metric_tc,
					'metric_wt': metric_wt
				}
			)
	print(f"\n\nTrain completed! Best_metric: {best_metric:.4f} at epoch: {best_metric_epoch}, total time: {str(datetime.timedelta(seconds=int(time.time() - total_start)))}.")
	return [
		epoch_loss_values[0],
		epoch_loss_values[1],
		epoch_time_values,
		metric_values,
		metric_values_et,
		metric_values_tc,
		metric_values_wt
	]


def _inference(input, device, model):
	"""
	Define inference method.
	"""
	def _compute(input):
		return sliding_window_inference(
			inputs=input,
			roi_size=(240, 240, 160),
			sw_batch_size=1,
			predictor=model,
			overlap=0.5,
		)
	if device.type == 'cuda':
		with torch.cuda.amp.autocast():
			return _compute(input)
	else:
		return _compute(input)


def _save_results(file, metrics):
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
