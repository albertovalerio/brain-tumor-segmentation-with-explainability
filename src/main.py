"""
Main executable pipeline.
"""
import os, sys, random
from sys import platform
import requests
from dotenv import dotenv_values
from monai.utils import set_determinism
from helpers.utils import make_dataset, get_device
from modules.training import train_test_splitting, training_model, predict_model
from helpers.config import get_config
from modules.preprocessing import get_transformations
from models.segresnet import SegResNet
from models.unet import UNet
from models.swinunetr import SwinUNETR


# defining paths
_base_path = '\\'.join(os.getcwd().split('\\')) + '\\' if platform == 'win32' else '/'.join(os.getcwd().split('/')) + '/'
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
	'SegResNet': SegResNet(
		init_filters=16,
		in_channels=4,
		out_channels=3,
		dropout_prob=0.2
	),
	'UNet': UNet(
        spatial_dims=3,
        in_channels=4,
        out_channels=3,
        channels=(16, 32, 64, 128, 256),
        strides=(2, 2, 2, 2)
    ),
	'SwinUNETR': SwinUNETR(
        img_size=(128, 128, 128),
        in_channels=4,
        out_channels=3,
        feature_size=48
    )
}

if __name__ == "__main__":

    # set model
	model = _models['SwinUNETR']

	# ensure reproducibility
	set_determinism(seed=3)
	random.seed(3)

	# load and splitting data
	data_path = make_dataset(dataset='glioma', verbose=False, base_path=_base_path)
	train_data, eval_data, test_data = train_test_splitting(data_path)

	# get data transformations pipelines
	(
		train_transform,
		eval_transform,
		test_transform,
		post_test_transforms,
		post_trans
	) = get_transformations(roi_size=(128, 128, 128) if model.name == 'SwinUNETR' else (224, 224, 144))

	# training model
	_ = training_model(
		model = model,
		data = [train_data, eval_data],
		transforms = [train_transform, eval_transform, post_trans],
		epochs = 100,
		device = get_device(),
		paths = [saved_path, reports_path, logs_path],
		num_workers=0,
		ministep=8,
		verbose=True
	)

	# making predictions
	_ = predict_model(
		model = model,
		data = test_data,
		transforms = [test_transform, post_test_transforms],
		device = get_device(),
		paths = [saved_path, reports_path, preds_path, logs_path],
		ministep=8,
		verbose=True
	)

	# shutdown the machine
	requests.patch(
		'https://api.paperspace.com/v1/machines/' + _env.get('MACHINE_ID') + '/stop',
		headers={'Authorization': 'Bearer ' + _env.get('API_KEY')}
	)

	sys.exit(0)