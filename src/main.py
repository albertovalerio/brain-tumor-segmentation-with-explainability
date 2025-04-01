"""
Main executable pipeline.
"""
import os, sys, random, requests
from sys import platform
_base_path = '\\'.join(os.getcwd().split('\\')) + '\\' if platform == 'win32' else '/'.join(os.getcwd().split('/')) + '/'
sys.path.append(_base_path)
from dotenv import dotenv_values
from monai.utils import set_determinism
from src.helpers.utils import make_dataset, get_device
from src.modules.training import train_test_splitting, training_model, predict_model
from src.helpers.config import get_config
from src.modules.preprocessing import get_transformations
from src.models.segresnet import SegResNet
from src.models.unet import UNet
from src.models.swinunetr import SwinUNETR


# defining paths
_env = dotenv_values(os.path.join(_base_path, '.env'))
_config = get_config()
saved_path = os.path.join(_base_path, _config.get('SAVED_FOLDER'))
reports_path = os.path.join(_base_path, _config.get('REPORT_FOLDER'))
preds_path = os.path.join(_base_path, _config.get('PRED_FOLDER'))
logs_path = os.path.join(_base_path, _config.get('LOG_FOLDER'))
if platform == 'win32':
	saved_path = saved_path.replace('/', '\\')
	reports_path = reports_path.replace('/', '\\')
	preds_path = preds_path.replace('/', '\\')
	logs_path = logs_path.replace('/', '\\')

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
	train_data, eval_data, test_data = train_test_splitting(data_path, reports_path=reports_path, load_from_file=True)

	for m in _models.keys():

		# set model
		model = _models[m]

		# get data transformations pipelines
		(
			train_transform,
			eval_transform,
			post_test_transform,
			post_transform
		) = get_transformations(roi_size=(128, 128, 128) if model.name == 'SwinUNETR' else (224, 224, 144))

		# training model
		_ = training_model(
			model = model,
			data = [train_data, eval_data],
			transforms = [train_transform, eval_transform, post_transform],
			epochs = 100,
			device = get_device(),
			paths = [saved_path, reports_path, logs_path],
			verbose = False
		)

		# making predictions
		_, _ = predict_model(
			model = model,
			data = test_data,
			transforms = [eval_transform, post_test_transform],
			device = get_device(),
			paths = [saved_path, reports_path, preds_path, logs_path],
			verbose = True
		)

	# shutdown the machine
	# requests.patch(
	# 	'https://api.paperspace.com/v1/machines/' + _env.get('MACHINE_ID') + '/stop',
	# 	headers={'Authorization': 'Bearer ' + _env.get('API_KEY')}
	# )

	sys.exit(0)