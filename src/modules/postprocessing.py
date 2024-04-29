"""
Definitions of postprocessing utility functions.
"""
import numpy as np
import nibabel as nib
import siibra, json, torch, os
from monai.metrics import DiceMetric, HausdorffDistanceMetric


__all__ = ['get_affected_areas', 'write_json_prompt']


def get_affected_areas(parcellation, volume, top=5, verbose=False):
	"""
	Computes the most affected Atlas regions and their relative percentages.
	Args:
		parcellation (str): the parcellation/Atlas name.
		volume (siibra.locations.pointset.PointSet): a set of points indicating the segmentation mask.
		top (int): number of most affected area to return.
		verbose (bool): whether or not to print general information about Atlas.
	Returns:
		results (dict): the list of brain regions and their relative percentages.
	"""
	atlas = siibra.atlases['human']
	julichbrain = atlas.get_parcellation(parcellation=parcellation)
	if verbose:
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
		json_data = {'MRI_Scan': {'Tumor_Details': {'Spatial_Distribution': []}}}

		# setting brain areas details
		for k, v in enumerate(areas.values()):
			json_data['MRI_Scan']['Tumor_Details']['Spatial_Distribution'].append({
				'Region': list(areas.keys())[k],
				'Percentage_of_Tumor': v['Percentage_of_Tumor'],
				'Percentage_of_Region_Affected': v['Percentage_of_Region_Affected']
			})

		# setting semantic segmentation details
		json_data['MRI_Scan']['Tumor_Details']['Semantic_Segmentation'] = {'Tumor_Core': {'Color': 'red'}, 'Peritumoral_Edema': {'Color': 'yellow'}, 'GD_Enhancing_Tumor': {'Color': 'green'}}

		# setting metrics
		pred = nib.load(os.path.join(preds_path, example + '_pred.nii.gz'))
		truth = nib.load(os.path.join(preds_path, example + '_label.nii.gz'))
		dice_metric_batch = DiceMetric(include_background=True, reduction='mean_batch')
		hausdorff_metric_batch = HausdorffDistanceMetric(include_background=True, reduction='mean_batch', percentile=95)
		dice_metric_batch(y_pred=[torch.tensor(pred.get_fdata())], y=[torch.tensor(truth.get_fdata())])
		hausdorff_metric_batch(y_pred=[torch.tensor(pred.get_fdata())], y=[torch.tensor(truth.get_fdata())])
		dice = [i.item() for i in dice_metric_batch.aggregate()]
		hausdorff = [i.item() for i in hausdorff_metric_batch.aggregate()]
		dice_metric_batch.reset()
		hausdorff_metric_batch.reset()
		json_data['MRI_Scan']['Tumor_Details']['Segmentation_Confidence'] = {}
		json_data['MRI_Scan']['Tumor_Details']['Segmentation_Confidence']['Dice_Score'] = {}
		json_data['MRI_Scan']['Tumor_Details']['Segmentation_Confidence']['Hausdorff_Distance'] = {}
		for i, m in enumerate(['Enhancing_Tumor', 'Tumor_Core', 'Whole_Tumor', 'Average']):
			if m == 'Average':
				json_data['MRI_Scan']['Tumor_Details']['Segmentation_Confidence']['Dice_Score'][m] = round((sum(dice) / len(dice)), 2)
				json_data['MRI_Scan']['Tumor_Details']['Segmentation_Confidence']['Hausdorff_Distance'][m] = round((sum(hausdorff) / len(hausdorff)), 2)
			else:
				json_data['MRI_Scan']['Tumor_Details']['Segmentation_Confidence']['Dice_Score'][m] = round(dice[i], 2)
				json_data['MRI_Scan']['Tumor_Details']['Segmentation_Confidence']['Hausdorff_Distance'][m] = round(hausdorff[i], 2)

		# setting model name
		json_data['MRI_Scan']['Tumor_Details']['Model_Used'] = example.split('_')[0]

		# write data to json file
		with open(os.path.join(json_path, example + '.json'), 'w') as js:
			json.dump(json_data, js, indent = '\t')
