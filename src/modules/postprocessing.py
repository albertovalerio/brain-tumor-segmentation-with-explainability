"""
Definitions of postprocessing utility functions.
"""
import numpy as np
import siibra


__all__ = ['get_affected_areas']


def get_affected_areas(parcellation, volume, top=5, verbose=False):
	"""
	Computes the most affected Atlas region and the relative percentage.
	Args:
		parcellation (str): the parcellation/Atlas name.
		volume (siibra.locations.pointset.PointSet): a set of points indicating the segmentation mask.
		top (int): number of most affected area to return.
		verbose (bool): whether or not to print general information about Atlas.
	Returns:
		region (list): the list of brain regions.
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
	for i, v in enumerate(top_r.index):
		p_map = julich_pmaps.fetch(region=v)
		n_vox = np.unique(p_map.get_fdata(), return_counts=True)[1][1]
		print(f'{str(v):>40}{(top_r[i] / len(assignments) * 100):>15.2f}{(top_r[i] / n_vox * 100):>15.2f}')
	return list(top_r.index)