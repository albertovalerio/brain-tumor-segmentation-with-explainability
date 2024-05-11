# brain-tumor-segmentation-with-explainability

Starting from a literature review of explainable AI techniques applied to the analysis and classification of brain diseases, a dataset of medical images (MRI) relating to specific brain diseases was selected, in particular, brain tumors of the glioma type were considered.

On this dataset, various state-of-the-art models and methodologies were applied for the segmentation of the brain areas affected at different levels of severity by the disease and, subsequently, a framework was proposed for the explainability of the AI models, the which, starting from the definition of a series of objective descriptors extracted from the overlap of the segmentation mask with a "brain atlas", constituted the input of different linguistic models for the generation of a medical report with the aim of giving support, that it was explainable and interpretable, for experts in the sector, and subordinately for the improvement of diagnostic and therapeutic practices in the field of neuroscience and medicine.


## Requirements
* **Global requirements**: Python >= 3.8 (tested on 3.11.4 and 3.11.7)

* **System requirements**: see [requirements.txt](/requirements.txt)

```python
pip install -r requirements.txt
```
* **Environment variables (if needed)**: see [.env.example](/.env.example)

```python
cp .env.example .env
```

## Project organization

```

├── data                          <- Dataset of MR images.
│
├── images                        <- Examples images, screenshots and graphs results.
│
├── json                          <- JSON files containing the descriptors of XAI framework.
│
├── logs                          <- Logs saved during the executions of training and testing phases.
│
├── notebooks
│   ├── 1-data-exploration.ipynb  <- Explorative data analysys.
│   ├── 2-training.ipynb          <- Execution of training phase and results.
│   ├── 3-post-processing.ipynb   <- XAI descriptors extraction.
│   └── 4-explainability.ipynb    <- Testing prompts and descriptors on LLMs.
│
├── predictions                   <- Saved random examples during the testing phase, for each model.
|
├── prompts                       <- Saved output prompts for each LLM and for each language.
│   ├── en
│   └── it
│
├── reports                       <- Saved training and testing splitting and metrics.
|
├── saved                         <- Best models serialization files.
│
├── src
│   ├── helpers                   <- Configuration files and utilities functions.
│   │   ├── config.py
│   │   └── utils.py
│   │
│   ├── models                   <- Segmentation models implementation.
│   │   ├── segresnet.py
│   │   ├── swinunetr.py
│   │   └── unet.py
│   │
│   ├── modules                  <- Python modules.
│   │   ├── explainability.py
│   │   ├── plotting.py
│   │   ├── postprocessing.py
│   │   ├── preprocessing.py
│   │   └── training.py
│   │
│   └── main.py                  <- Python script for the execution of the whole pipeline.
│
├── .env.example                 <- Environment variables.
├── .gitignore                   <- Specifications of files to be ignored by Git.
├── LICENCE                      <- Licence file.
├── README.md                    <- The top-level README for developers using this project.
├── requirements.txt             <- The project requirements to be installed.

```

## Resources

Segmentation models training was carried out on the following resources:

* CPU: 1 x Intel(R) Xeon(R) Gold 5317 CPU @ 3.00GHz (12 cores).
* GPU: 1 x NVIDIA A100 PCIe 80GB.
* RAM: 90 GB.

LLM prompting was carried out on the following resources:

* CPU: 1 x Apple M2 Max (12 cores).
* GPU: 1 x Apple M2 Max (38 cores).
* RAM: 64 GB.


## Results

#### Example of segmentation models 4-channels input
![model input](/images/model_input.png)
#### Example of segmentation models label
![model output](/images/model_output.png)
#### Example of segmentation models prediction
![model prediction](/images/model_prediction.png)
#### Segmentation models results
![results](/images/metrics.png)
#### Language models explainable medical reports
- **[BioMistral-7B.md](/prompts/en/BioMistral-7B.md)**
- **[Meta-Llama-3-8B-Instruct.md](/prompts/en/Meta-Llama-3-8B-Instruct.md)**
- **[Mistral-7B-Instruct-v0.2.md](/prompts/en/Mistral-7B-Instruct-v0.2.md)**


## Authors

The present project has been realized by me **[@albertovalerio](https://github.com/albertovalerio)** and my colleague **[@katyatrufanova](https://github.com/katyatrufanova)** as university laboratory activity for the exam in **Deep Learning**, Master's Degree in Computer Science, curriculum studies in Artificial Intelligence, with **Professor Giovanna Castellano** and Assistant Professor **Dr. Gennaro Vessio** at University of Bari "Aldo Moro", Italy.

## Acknowledgments

- Segmentations models and metrics adapted from **[@Project-MONAI](https://monai.io/)** implementation.
- Brain atlas refers to **[@Julich-Brain-Cytoarchitectonic-Atlas](https://julich-brain-atlas.de/)** institute.
- Language models taken from **[@HuggingFace](https://huggingface.co/)** community.
- Dataset from **[@BraTS-2023](https://www.synapse.org/#!Synapse:syn51156910/wiki/622351)** challenge.

#### Further acknowledgments

- **[@NiBabel](https://nipy.org/nibabel/)**
- **[@Nilearn](https://nilearn.github.io/)**
- **[@SIIBrA (Software Interface for Interacting with Brain Atlases)](https://siibra-python.readthedocs.io/)**
- **[@PyTorch](https://pytorch.org/)**
- **[@NumPy](https://numpy.org/)**
- **[@Matplotlib](https://matplotlib.org/)**

## License

Distributed under the [MIT](https://choosealicense.com/licenses/mit/) License. See [LICENSE](/LICENSE) for more information.