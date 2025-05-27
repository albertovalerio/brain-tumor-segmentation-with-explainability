"""
Reports generation executable pipeline.
"""
import os, sys, random
from sys import platform
_base_path = '\\'.join(os.getcwd().split('\\')) + '\\' if platform == 'win32' else '/'.join(os.getcwd().split('/')) + '/'
sys.path.append(_base_path)
import siibra
import nibabel as nib
import numpy as np
from nilearn import datasets, image
from monai.utils import set_determinism
from src.helpers.utils import make_dataset, get_device
from src.modules.training import train_test_splitting, predict_model
from src.helpers.config import get_config
from src.modules.preprocessing import get_transformations
from src.models.segresnet import SegResNet
from src.models.unet import UNet
from src.models.swinunetr import SwinUNETR
from src.modules.postprocessing import get_affected_areas, write_json_prompt
from src.modules.explainability import get_explanations_via_groq


# defining paths
_config = get_config()
saved_path = os.path.join(_base_path, _config.get('SAVED_FOLDER'))
reports_path = os.path.join(_base_path, _config.get('REPORT_FOLDER'))
preds_path = os.path.join(_base_path, _config.get('PRED_FOLDER'))
logs_path = os.path.join(_base_path, _config.get('LOG_FOLDER'))
json_path = os.path.join(_base_path, _config.get('JSON_FOLDER'))
if platform == 'win32':
	saved_path = saved_path.replace('/', '\\')
	reports_path = reports_path.replace('/', '\\')
	preds_path = preds_path.replace('/', '\\')
	logs_path = logs_path.replace('/', '\\')
	json_path = json_path.replace('/', '\\')

# defining models
_models = {
	'SegResNet': SegResNet(in_channels = 4, out_channels = 3),
	'UNet': UNet(in_channels = 4, out_channels = 3),
	'SwinUNETR': SwinUNETR(in_channels = 4, out_channels = 3)
}

# defining brain atlas
atlas = siibra.atlases['human']
parcellations = list(atlas.parcellations)

# defining Groq LLMs
llms = ['groq_llama', 'groq_mixtral', 'groq_gemma']


if __name__ == "__main__":

	args = sys.argv[1:]
	if len(args) == 0:
		print('\n' + ''.join(['> ' for i in range(25)]))
		print('\nWARNING: missing required parameters!')
		print('\n' + ''.join(['> ' for i in range(25)]))
		print(f'\n{"PARAM":<16}{"VALUE RANGE":<18}\n')
		print(''.join(['> ' for i in range(25)]))
		print(f'{"--model":<16}{str(list(_models.keys())):<18}')
		print(''.join(['> ' for i in range(25)]) + '\n')
	else:
		keys = [i.split('=')[0].upper()[2:] for i in args]
		values = [i.split('=')[1] for i in args]
		model_name = values[keys.index('MODEL')]

		if model_name in _models.keys():

			# ensure reproducibility
			set_determinism(seed=3)
			random.seed(3)

			# set model
			model = _models[model_name]

			print(get_device())

			# load and splitting data
			data_path = make_dataset(dataset='glioma', verbose=False, base_path=_base_path)
			_, _, test_data = train_test_splitting(data_path, reports_path=reports_path, load_from_file=True)

			# get data transformations pipelines
			(
				_,
				eval_transform,
				post_test_transform,
				_
			) = get_transformations(roi_size=(128, 128, 128) if model.name == 'SwinUNETR' else (224, 224, 144))

			# making predictions
			_, _ = predict_model(
				model = model,
				data = test_data,
				transforms = [eval_transform, post_test_transform],
				device = 'cpu', # get_device(),
				paths = [saved_path, reports_path, preds_path, logs_path],
				write_to_file = False,
				save_sample = len(test_data),
				return_prediction = True,
				verbose = True
			)

			# generating reports
			subjects = np.unique(sorted([s.split('_')[1] for s in os.listdir(os.path.join(_base_path, preds_path)) if 'SegResNet_BraTS' in s]))
			for k, s in enumerate(subjects):

				print('GENERATING REPORT: ', str(k + 1) + '/' + str(len(subjects)))

				# brain atlas registration
				example_name = model_name + '_' + s
				mask = nib.load(os.path.join(preds_path, example_name + '_pred.nii.gz'))
				tc = mask.get_fdata()[1]
				mni_template = datasets.load_mni152_template()
				pred = nib.Nifti1Image(np.rot90(tc, 2), affine=mni_template.affine)
				pred_norm = image.resample_to_img(pred, mni_template)
				points = siibra.PointSet(tuple(zip(*np.where(pred_norm.get_fdata() == 1))), space='mni152', sigma_mm=5).transform(mni_template.affine, space='mni152')

				# top 5 regions extraction
				areas = get_affected_areas(
					parcellation=parcellations[12].name,
					volume=points,
					top=5,
					verbose=0
				)

				# json generation
				write_json_prompt(
					example=example_name,
					areas=areas,
					paths=[preds_path, json_path]
				)

				# get reports and saving metrics
				for l in llms:
					_, _ = get_explanations_via_groq(
						lang = 'EN',
						model_key = l,
						prompt_id = '2',
						sample_id = s,
						output_length = 1024,
						write_prompt_to_file = False,
						write_metrics_to_file = True,
						base_path = _base_path,
						verbose = False
					)

		else:
			print('\n' + ''.join(['> ' for i in range(25)]))
			print('\nWARNING: out-of-bound parameters!')
			print('\n' + ''.join(['> ' for i in range(25)]))
			print(f'\n{"PARAM":<16}{"VALUE RANGE":<18}\n')
			print(''.join(['> ' for i in range(25)]))
			print(f'{"--model":<16}{str(list(_models.keys())):<18}')
			print(''.join(['> ' for i in range(25)]) + '\n')

	sys.exit(0)