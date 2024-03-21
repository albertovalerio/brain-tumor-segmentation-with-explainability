"""
Definitions of data preprocessing pipelines.
"""
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
from helpers.utils import get_brats_classes


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

def get_transformations(roi_size):
	"""
	Get data transformation pipelines.
	Args:
		roi_size (tuple): input roi size.
	Returns:
		train_transform (monai.transforms.Compose): pipeline for the training input data.
		eval_transform (monai.transforms.Compose): pipeline for the evaluation input data.
		test_transform (monai.transforms.Compose): pipeline for the testing input data.
		post_test_transforms (monai.transforms.Compose): pipeline for the testing output data.
		post_trans (monai.transforms.Compose): pipeline for the training output data.
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
		),
		RandSpatialCropd(keys=['image', 'label'], roi_size=roi_size, random_size=False),
		RandFlipd(keys=['image', 'label'], prob=0.5, spatial_axis=0),
		RandFlipd(keys=['image', 'label'], prob=0.5, spatial_axis=1),
		RandFlipd(keys=['image', 'label'], prob=0.5, spatial_axis=2),
		NormalizeIntensityd(keys='image', nonzero=True, channel_wise=True),
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
		),
		NormalizeIntensityd(keys='image', nonzero=True, channel_wise=True),
	])
	test_transform = Compose([
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
	])
	post_test_transforms = Compose([
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
	])
	post_trans = Compose([
		Activations(sigmoid=True),
		AsDiscrete(threshold=0.5)
	])
	return train_transform, eval_transform, test_transform, post_test_transforms, post_trans
