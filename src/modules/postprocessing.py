"""
Definitions of postprocessing utility functions.
"""
import numpy as np
import siibra, json, os
import pandas as pd
import nibabel as nib
from nilearn import datasets, image
from src.helpers.utils import get_device
from src.modules.training import predict_model


__all__ = ['get_affected_areas', 'write_json_prompt', 'write_evaluation_report']


def get_affected_areas(parcellation, volume, top=5, verbose=0):
	"""
	Computes the most affected Atlas regions and their relative percentages.
	Args:
		parcellation (str): the parcellation/Atlas name.
		volume (siibra.locations.pointset.PointSet): a set of points indicating the segmentation mask.
		top (int): number of most affected area to return.
		verbose (int): set the level of verbosity. Possible values: 0,1,2.
	Returns:
		results (dict): the list of brain regions and their relative percentages.
	"""
	atlas = siibra.atlases['human']
	julichbrain = atlas.get_parcellation(parcellation=parcellation)
	if verbose > 1:
		print(f'Name:     {julichbrain.name}')
		print(f'Id:       {julichbrain.id}')
		print(f'Modality: {julichbrain.modality}\n')
		print(f'{julichbrain.description}\n')
		for p in julichbrain.publications:
			print(p['citation'])
		print('\n\n')
	julich_pmaps = siibra.get_map(
		parcellation=julichbrain,
		space=siibra.spaces.get('mni152'),
		maptype=siibra.MapType.LABELLED
	)
	assignments = julich_pmaps.assign(volume)
	top_r = assignments['region'].value_counts()[:top]
	if verbose >= 1:
		print(''.join(['> ' for i in range(40)]))
		print(f'\n{"REGION":>40}{"%_of_TUMOR":>15}{"%_of_REGION":>15}\n')
		print(''.join(['> ' for i in range(40)]))
	results = {}
	for i, v in enumerate(top_r.index):
		p_map = julich_pmaps.fetch(region=v)
		n_vox = np.unique(p_map.get_fdata(), return_counts=True)[1][1]
		results[str(v)] = {}
		results[str(v)]['Percentage_of_Tumor'] = round((top_r[i] / len(assignments) * 100), 2)
		results[str(v)]['Percentage_of_Region_Affected'] = round((top_r[i] / n_vox * 100), 2)
		if verbose >= 1:
			print(f'{str(v):>40}{(top_r[i] / len(assignments) * 100):>15.2f}{(top_r[i] / n_vox * 100):>15.2f}')
	return results


def write_json_prompt(example, areas, paths):
	"""
	Write example's details to a json file that will serve as a prompt.
	Args:
		example (str): the example's name.
		areas (dict): the list of brain regions and their relative percentages.
		paths (list): the paths where to find the `example` and where to save json file.
	Returns:
		None.
	"""
	preds_path, json_path = paths
	if not os.path.isdir(preds_path) or not os.path.isdir(json_path):
		print('\n' + ''.join(['> ' for i in range(30)]))
		print('\nERROR: Path \033[95m' + (preds_path if not os.path.isdir(preds_path) else json_path) + '\033[0m is not a valid path.\n')
		print(''.join(['> ' for i in range(30)]) + '\n')
	else:
		json_data_en = {'MRI_Scan': {'Tumor_Details': {'Spatial_Distribution': []}}}
		json_data_it = {'MRI_Scan': {'Dettagli_Tumore': {'Distribuzione_Spaziale': []}}}

		# setting brain areas details
		for k, v in enumerate(areas.values()):
			json_data_en['MRI_Scan']['Tumor_Details']['Spatial_Distribution'].append({
				'Region': list(areas.keys())[k],
				'Percentage_of_Tumor': v['Percentage_of_Tumor'],
				'Percentage_of_Region_Affected': v['Percentage_of_Region_Affected']
			})
			json_data_it['MRI_Scan']['Dettagli_Tumore']['Distribuzione_Spaziale'].append({
				'Regione': list(areas.keys())[k],
				'Percentuale_del_Tumore': v['Percentage_of_Tumor'],
				'Percentuale_della_Regione_Affetta': v['Percentage_of_Region_Affected']
			})

		# setting semantic segmentation details
		json_data_en['MRI_Scan']['Tumor_Details']['Semantic_Segmentation'] = {'Tumor_Core': {'Color': 'red'}, 'Peritumoral_Edema': {'Color': 'yellow'}, 'GD_Enhancing_Tumor': {'Color': 'green'}}
		json_data_it['MRI_Scan']['Dettagli_Tumore']['Segmentazione_Semantica'] = {'Nucleo_del_tumore': {'Colore': 'rosso'}, 'Edema_Peritumorale': {'Colore': 'giallo'}, 'Tumore_Circostante': {'Colore': 'verde'}}

		# setting metrics
		json_data_en['MRI_Scan']['Tumor_Details']['Segmentation_Confidence'] = {'Dice_Score': {'Enhancing_Tumor': 0.88, 'Tumor_Core': 0.91, 'Whole_Tumor': 0.93, 'Average': 0.91}, 'Hausdorff_Distance': {'Enhancing_Tumor': 3.69, 'Tumor_Core': 4.35, 'Whole_Tumor': 4.99, 'Average': 4.34}}
		json_data_it['MRI_Scan']['Dettagli_Tumore']['Accuratezza_Segmentazione'] = {'Indice_di_similarit\u00e0_di_S\u00f8rensen': {'Enhancing_Tumor': 0.88, 'Tumor_Core': 0.91, 'Whole_Tumor': 0.93, 'Average': 0.91},'Distanza_di_Hausdorff': {'Enhancing_Tumor': 3.69, 'Tumor_Core': 4.35, 'Whole_Tumor': 4.99, 'Average': 4.34}}

		# setting model name
		json_data_en['MRI_Scan']['Tumor_Details']['Model_Used'] = example.split('_')[0]
		json_data_it['MRI_Scan']['Dettagli_Tumore']['Modello_Utilizzato'] = example.split('_')[0]

		# write data to json file
		with open(os.path.join(json_path, example + '_EN.json'), 'w') as js:
			json.dump(json_data_en, js, indent = '\t')
		with open(os.path.join(json_path, example + '_IT.json'), 'w') as js:
			json.dump(json_data_it, js, indent = '\t')


def write_evaluation_report(
	data,
	model,
	transforms,
	paths,
	write_to_file = False,
	tumor_class = 1,
	report_name = 'error_eval_tc.csv',
	verbose = True
):
	"""
	Execute error evaluation report, and save results to file.
	Args:
		data (list): the testing data.
		model (torch.nn.Module): the trained model.
		transform (list): transformation sequence for evaluation and post-evaluation.
		paths (list): list of useful paths.
		write_to_file (bool): whether to write results to csv file.
		tumor_class (int): the BraTS tumor class. `0`=`ET`, `1`=`TC`, `2`=`WT`,
		report_name (str): csv file name where to save data report.
		verbose (bool): whether to print status information.
	Returns:
		df (pd.Dataframe): stored report information.
	"""
	if write_to_file:
		df = pd.DataFrame({'subject':[],'type':[],'30':[],'29':[],'28':[],'27':[],'26':[],'25':[],'24':[],'23':[],'22':[],'21':[],'20':[],'19':[],'18':[],'17':[],'16':[],'15':[],'14':[],'13':[],'12':[],'11':[],'10':[],'9':[],'8':[],'7':[],'6':[],'5':[],'4':[],'3':[],'2':[],'1':[]})
		for t in data:
			df = pd.concat([df, pd.DataFrame([
				{'subject': t['image'][0].split('/')[-2], 'type': 'Different_Regions'},
				{'subject': t['image'][0].split('/')[-2], 'type': 'Different_Regions_Not_True'},
				{'subject': t['image'][0].split('/')[-2], 'type': 'Different_Percentage_of_Tumor'}
			])], ignore_index=True)
		df.to_csv(os.path.join(paths[1], report_name), index=False, encoding='UTF-8')
	df = pd.read_csv(os.path.join(paths[1], report_name), encoding='UTF-8')
	parcellations = list(siibra.atlases['human'].parcellations)
	for k, t in enumerate(data):
		_, prediction = predict_model(
			model = model,
			data = [t],
			transforms = transforms,
			device = 'cpu', # get_device(), MPS not supported
			paths = paths,
			num_workers = 0,
			write_to_file = False,
			save_sample = 0,
			return_prediction = True
		)
		mask_data = prediction[0]['pred'].detach().cpu().numpy()
		truth_data = prediction[0]['label'].detach().cpu().numpy()
		mni_template = datasets.load_mni152_template()
		pred = nib.Nifti1Image(np.rot90(mask_data[tumor_class], 2), affine=mni_template.affine)
		label = nib.Nifti1Image(np.rot90(truth_data[tumor_class], 2), affine=mni_template.affine)
		pred_norm = image.resample_to_img(pred, mni_template)
		label_norm = image.resample_to_img(label, mni_template)
		points_pred = siibra.PointSet(tuple(zip(*np.where(pred_norm.get_fdata() == 1))), space='mni152', sigma_mm=5).transform(mni_template.affine, space='mni152')
		points_label = siibra.PointSet(tuple(zip(*np.where(label_norm.get_fdata() == 1))), space='mni152', sigma_mm=5).transform(mni_template.affine, space='mni152')
		areas_pred = get_affected_areas(parcellation=parcellations[12].name, volume=points_pred, top=30)
		areas_label = get_affected_areas(parcellation=parcellations[12].name, volume=points_label, top=30)
		percentage_pred = [a['Percentage_of_Tumor'] for a in areas_pred.values()]
		percentage_label = [a['Percentage_of_Tumor'] for a in areas_label.values()]
		for i in range(min(len(areas_pred), len(areas_label)), 0, -1):
			set_pred = set(list(areas_pred)[:i])
			set_label = set(list(areas_label)[:i])
			diff = set_pred.difference(set_label)
			diff_true = set(list(diff)).difference(set(list(areas_label)))
			percentage_diff = sum(abs(percentage_pred[j] - percentage_label[j]) for j in range(i))
			df.loc[(df['subject'] == t['image'][0].split('/')[-2]) & (df['type'] == 'Different_Regions'), str(i)] = len(diff)
			df.loc[(df['subject'] == t['image'][0].split('/')[-2]) & (df['type'] == 'Different_Regions_Not_True'), str(i)] = len(diff_true)
			df.loc[(df['subject'] == t['image'][0].split('/')[-2]) & (df['type'] == 'Different_Percentage_of_Tumor'), str(i)] = percentage_diff
			if write_to_file:
				df.to_csv(os.path.join(paths[1], report_name), index=False, encoding='UTF-8')
		if k % 30 == 0 and verbose == True:
			print(f'Run: {k}/{len(data)}')
	return df
