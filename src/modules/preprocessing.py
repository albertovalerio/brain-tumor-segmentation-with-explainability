"""
Definitions of data preprocessing pipelines.
"""
from monai.transforms import (
    Activations,
    Activationsd,
    AsDiscrete,
    AsDiscreted,
    Compose,
    EnsureChannelFirstd,
    EnsureTyped,
    Invertd,
    LoadImaged,
    MapTransform,
    Orientationd,
	RandAxisFlipd,
    RandScaleIntensityd,
    RandShiftIntensityd,
    RandSpatialCropd,
	Resized,
	ScaleIntensityd,
    Spacingd,
	SpatialPadd
)
from src.helpers.utils import get_brats_classes


class ConvertToMultiChannelBasedOnBratsClassesd(MapTransform):
	"""
	Convert labels to multi channels based on BraTS-2023 classes.
	(See src.utils.get_brats_classes() for more details)
	"""
	def __call__(self, data):
		d = dict(data)
		for key in self.keys:
			d[key] = get_brats_classes(d[key])
		return d


def get_transformations(size):
	"""
	Get data transformation pipelines.
	Args:
		size (int): max size for input image. Final input shape will be (size, size, size).
	Returns:
		train_transform (monai.transforms.Compose): pipeline for the training input data.
		eval_transform (monai.transforms.Compose): pipeline for the evaluation/testing input data.
		post_test_transform (monai.transforms.Compose): pipeline for the testing output data.
		post_transform (monai.transforms.Compose): pipeline for the training output data.
	"""
	train_transform = Compose([
		LoadImaged(keys=['image', 'label']),
		EnsureChannelFirstd(keys='image'),
		EnsureTyped(keys=['image', 'label']),
		ConvertToMultiChannelBasedOnBratsClassesd(keys='label'),
		Orientationd(keys=['image', 'label'], axcodes='RAS'),
		Spacingd(
			keys=['image', 'label'],
			pixdim=(1.0, 1.0, 1.0),
			mode=('bilinear', 'nearest'),
			align_corners=True,
			scale_extent=True
		),
		ScaleIntensityd(keys='image', channel_wise=True),
		RandSpatialCropd(keys=['image', 'label'], roi_size=(220, 220, 140), random_size=False),
		RandAxisFlipd(keys=['image', 'label'], prob=0.5),
		Resized(
			keys=['image', 'label'],
			spatial_size=size,
			size_mode='longest',
			mode=('bilinear', 'nearest')
		),
		SpatialPadd(keys=['image', 'label'], spatial_size=(size, size, size)),
		RandScaleIntensityd(keys='image', factors=0.1, prob=1.0),
		RandShiftIntensityd(keys='image', offsets=0.1, prob=1.0)
	])
	eval_transform = Compose([
		LoadImaged(keys=['image', 'label']),
		EnsureChannelFirstd(keys='image'),
		EnsureTyped(keys=['image', 'label']),
		ConvertToMultiChannelBasedOnBratsClassesd(keys='label'),
		Orientationd(keys=['image', 'label'], axcodes='RAS'),
		Spacingd(
			keys=['image', 'label'],
			pixdim=(1.0, 1.0, 1.0),
			mode=('bilinear', 'nearest'),
			align_corners=True,
			scale_extent=True
		),
		ScaleIntensityd(keys='image', channel_wise=True),
		Resized(
			keys=['image', 'label'],
			spatial_size=size,
			size_mode='longest',
			mode=('bilinear', 'nearest')
		),
		SpatialPadd(keys=['image', 'label'], spatial_size=(size, size, size)),
		RandScaleIntensityd(keys='image', factors=0.1, prob=1.0),
		RandShiftIntensityd(keys='image', offsets=0.1, prob=1.0)
	])
	post_test_transform = Compose([
		Invertd(
			keys='pred',
			transform=eval_transform,
			orig_keys='image',
			meta_keys='pred_meta_dict',
			orig_meta_keys='image_meta_dict',
			meta_key_postfix='meta_dict',
			nearest_interp=False,
			to_tensor=True,
			device='cpu',
		),
		Invertd(
			keys='label',
			transform=eval_transform,
			orig_keys='label',
			meta_keys='label_meta_dict',
			orig_meta_keys='image_meta_dict',
			meta_key_postfix='meta_dict',
			nearest_interp=False,
			to_tensor=True,
			device='cpu',
		),
		Invertd(
			keys='image',
			transform=eval_transform,
			orig_keys='image',
			meta_keys='image_meta_dict',
			orig_meta_keys='image_meta_dict',
			meta_key_postfix='meta_dict',
			nearest_interp=False,
			to_tensor=True,
			device='cpu',
		),
		Activationsd(keys='pred', sigmoid=True),
		AsDiscreted(keys='pred', threshold=0.5)
	])
	post_transform = Compose([
		Activations(sigmoid=True),
		AsDiscrete(threshold=0.5)
	])
	return train_transform, eval_transform, post_test_transform, post_transform
