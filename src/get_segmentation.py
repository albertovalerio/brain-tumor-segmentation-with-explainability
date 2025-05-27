"""
Reports generation executable pipeline.
"""
import os, sys, random
from sys import platform
_base_path = '\\'.join(os.getcwd().split('\\')) + '\\' if platform == 'win32' else '/'.join(os.getcwd().split('/')) + '/'
sys.path.append(_base_path)
from monai.utils import set_determinism
from src.helpers.utils import make_dataset, get_device
from src.modules.training import train_test_splitting, predict_model
from src.helpers.config import get_config
from src.modules.preprocessing import get_transformations
from src.models.segresnet import SegResNet
from src.models.unet import UNet
from src.models.swinunetr import SwinUNETR


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


if __name__ == "__main__":

	# ensure reproducibility
	set_determinism(seed=3)
	random.seed(3)

	# load and splitting data
	data_path = make_dataset(dataset='glioma', verbose=False, base_path=_base_path)
	_, _, test_data = train_test_splitting(data_path, reports_path=reports_path, load_from_file=True)

	# set model
	for m in _models.keys():

		model = _models[m]

		print(get_device())

		# get data transformations pipelines
		(
			_,
			eval_transform,
			post_test_transform,
			_
		) = get_transformations(roi_size=(128, 128, 128) if model.name == 'SwinUNETR' else (224, 224, 144))

		# making predictions
		for k, t in enumerate(test_data):
			if k % 10 == 0:
				print(model.name.upper() + '_INFERENCE: ', str(k+1)+'/'+str(len(test_data)))
			test_metrics, _ = predict_model(
				model = model,
				data = [t],
				transforms = [eval_transform, post_test_transform],
				device = get_device(),
				paths = [saved_path, reports_path, preds_path, logs_path],
				ministep = 1,
				num_workers = 0,
				save_sample = 0,
				verbose = False
			)

	sys.exit(0)