"""
Main executable pipeline.
"""
import os, sys, random
from sys import platform
from monai.transforms import (
    Activations,
    Activationsd,
    AsDiscrete,
    AsDiscreted,
    Compose,
    Invertd,
    LoadImaged,
    MapTransform,
    NormalizeIntensityd,
    Orientationd,
    RandFlipd,
    RandScaleIntensityd,
    RandShiftIntensityd,
    RandSpatialCropd,
    Spacingd,
    EnsureTyped,
    EnsureChannelFirstd,
)
from monai.utils import set_determinism
from utils import make_dataset, get_device, get_brats_classes
from training import train_test_splitting, training_model, predict_model
from config import get_config
from models import SegResNet, UNet, SwinUNETR
import requests
from dotenv import dotenv_values


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
	'SegResNet': SegResNet(init_filters=16, in_channels=4, out_channels=3, dropout_prob=0.2),
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

# defining image transformations
class ConvertToMultiChannelBasedOnBratsClassesd(MapTransform):
	"""
	Convert labels to multi channels based on BraTS-2023 classes.
	(See src.utils.get_brats_classes)
	"""
	def __call__(self, data):
		d = dict(data)
		for key in self.keys:
			d[key] = get_brats_classes(d[key])
		return d
train_transform = Compose(
    [
        LoadImaged(keys=['image', 'label']),
        EnsureChannelFirstd(keys='image'),
        EnsureTyped(keys=['image', 'label']),
        ConvertToMultiChannelBasedOnBratsClassesd(keys='label'),
        Orientationd(keys=['image', 'label'], axcodes='RAS'), #(Left, Right),(Posterior, Anterior),(Inferior, Superior)
        Spacingd(
            keys=['image', 'label'],
            pixdim=(1.0, 1.0, 1.0),
            mode=('bilinear', 'nearest'),
        ),
        RandSpatialCropd(keys=['image', 'label'], roi_size=[128, 128, 128], random_size=False),
        RandFlipd(keys=['image', 'label'], prob=0.5, spatial_axis=0),
        RandFlipd(keys=['image', 'label'], prob=0.5, spatial_axis=1),
        RandFlipd(keys=['image', 'label'], prob=0.5, spatial_axis=2),
        NormalizeIntensityd(keys='image', nonzero=True, channel_wise=True),
        RandScaleIntensityd(keys='image', factors=0.1, prob=1.0),
        RandShiftIntensityd(keys='image', offsets=0.1, prob=1.0),
    ]
)
eval_transform = Compose(
    [
        LoadImaged(keys=['image', 'label']),
        EnsureChannelFirstd(keys='image'),
        EnsureTyped(keys=['image', 'label']),
        ConvertToMultiChannelBasedOnBratsClassesd(keys='label'),
        Orientationd(keys=['image', 'label'], axcodes='RAS'),
        Spacingd(
            keys=['image', 'label'],
            pixdim=(1.0, 1.0, 1.0),
            mode=('bilinear', 'nearest'),
        ),
        NormalizeIntensityd(keys='image', nonzero=True, channel_wise=True),
    ]
)
test_transform = Compose(
    [
        LoadImaged(keys=['image', 'label']),
        EnsureChannelFirstd(keys=['image']),
        ConvertToMultiChannelBasedOnBratsClassesd(keys='label'),
        Orientationd(keys=['image'], axcodes='RAS'),
        Spacingd(
			keys=['image'],
			pixdim=(1.0, 1.0, 1.0),
			mode='bilinear'
		),
        NormalizeIntensityd(keys='image', nonzero=True, channel_wise=True),
    ]
)
post_test_transforms = Compose(
    [
        Invertd(
            keys='pred',
            transform=test_transform,
            orig_keys='image',
            meta_keys='pred_meta_dict',
            orig_meta_keys='image_meta_dict',
            meta_key_postfix='meta_dict',
            nearest_interp=False,
            to_tensor=True,
            device='cpu',
        ),
        Activationsd(keys='pred', sigmoid=True),
        AsDiscreted(keys='pred', threshold=0.5),
    ]
)
post_trans = Compose(
	[
		Activations(sigmoid=True),
		AsDiscrete(threshold=0.5)
	]
)


if __name__ == "__main__":

    # set model
	model = _models['SwinUNETR']

	# ensure reproducibility
	set_determinism(seed=3)
	random.seed(3)

	# load and splitting data
	data_path = make_dataset(dataset='glioma', verbose=False, base_path=_base_path)
	train_data, eval_data, test_data = train_test_splitting(data_path)

	# training model
	# _ = training_model(
	# 	model = model,
	# 	data = [train_data, eval_data],
	# 	transforms = [train_transform, eval_transform, post_trans],
	# 	epochs = 10,
	# 	device = get_device(),
	# 	paths = [saved_path, reports_path, logs_path],
	# 	ministep=8,
	# 	verbose=True
	# )

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