# brain-tumor-segmentation-with-explainability

This repository contains the code, and resources associated with the paper:

**From Segmentation to Explanation: Generating Textual Reports from MRI with LLMs**
Authors: [Giovanna Castellano](https://github.com/giocastellano), [Salvatore de Benedictis](https://github.com/salvatoredebenedictis), [Katya Trufanova](https://github.com/katyatrufanova), [Alberto G. Valerio](https://github.com/albertovalerio), [Gennaro Vessio](https://github.com/gvessio)
DOI: [10.2139/ssrn.4974224](https://dx.doi.org/10.2139/ssrn.4974224)

This repository includes all necessary files and instructions to reproduce the main experiments and results presented in the paper. If you find this code useful, please consider citing our paper:

```python
@article{castellano2024segmentation,
  title={From Segmentation to Explanation: Generating Textual Reports from MRI with Llms},
  author={Castellano, Giovanna and de Benedictis, Salvatore and Trufanova, Katya and Valerio, Alberto G and Vessio, Gennaro},
  journal={Available at SSRN 4974224}
  doi={"https://dx.doi.org/10.2139/ssrn.4974224"}
}
```

## Abstract
**Background and Objective**: Artificial Intelligence (AI) has significantly advanced medical imaging, yet the opacity of deep learning models remains challenging, often reducing the trust of medical professionals towards AI-driven diagnoses. As a result, there is a strong focus on making AI models more transparent and interpretable to boost healthcare providers’ confidence in these technologies.
**Methods**: This paper introduces a novel approach to enhance AI explainability in critical medical tasks by integrating state-of-the-art semantic segmentation models with atlas-based mapping and Large Language Models (LLMs) to produce comprehensive, human-readable medical reports. The proposed framework ensures that the generated outputs are factual and context-rich, enhancing the transparency and interpretability of AI systems.
**Results**: Experimental results show that the SegResNet model achieves high segmentation accuracy, while LLMs (Gemma, Llama, and Mixtral) demonstrate diverse strengths in generating explanatory reports. To assess the quality and effectiveness of generated textual explanations, numerous metrics have been employed, such as lexical diversity, readability, coherence, and information coverage.
**Conclusions**: The method has been specifically tested on brain tumor detection for glioma, one of the most aggressive forms of cancer, and later applied to multiple sclerosis lesion detection to further validate its generalizability across medical imaging scenarios, contributing to trustworthiness in healthcare AI applications.


The methodology employed in this work can be broadly divided into four main
stages:
1. Semantic Segmentation
2. Brain Atlas Mapping
3. JSON Construction
4. Prompt Engineering and LLMs Integration

![framework pipeline](/images/pipeline.jpg)


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
#### Example of segmentation models labels
![model output](/images/model_output.png)
#### Example of segmentation models predictions
![model prediction](/images/model_prediction.png)
#### Segmentation models results
![results](/images/metrics.png)

#### Language models generated medical reports

1. **[English outputs](/prompts/en)**
2. **[Italian outputs](/prompts/it)**


## Authors

The present project has been realized by me **[@albertovalerio](https://github.com/albertovalerio)** and my colleague **[@katyatrufanova](https://github.com/katyatrufanova)** as university laboratory activity for the exam in **Deep Learning**, Master's Degree in Computer Science, curriculum studies in Artificial Intelligence, with **Professor Giovanna Castellano** and Assistant Professor **Dr. Gennaro Vessio** at University of Bari "Aldo Moro", Italy.

## Acknowledgments

- Segmentations models and metrics adapted from **[@Project-MONAI](https://monai.io/)** implementation.
- Brain atlas refers to **[@Julich-Brain-Cytoarchitectonic-Atlas](https://julich-brain-atlas.de/)** institute.
- Language models taken from **[@HuggingFace](https://huggingface.co/)** community and **[@Groq](https://groq.com/)** API.
- Dataset from **[@BraTS-2023](https://www.synapse.org/#!Synapse:syn51156910/wiki/622351)** challenge.

#### Further acknowledgments

- **[@NiBabel](https://nipy.org/nibabel/)**
- **[@Nilearn](https://nilearn.github.io/)**
- **[@SIIBrA (Software Interface for Interacting with Brain Atlases)](https://siibra-python.readthedocs.io/)**
- **[@PyTorch](https://pytorch.org/)**
- **[@SpaCy](https://spacy.io/)**
- **[@NumPy](https://numpy.org/)**
- **[@Matplotlib](https://matplotlib.org/)**

## License

Distributed under the [MIT](https://choosealicense.com/licenses/mit/) License. See [LICENSE](/LICENSE) for more information.