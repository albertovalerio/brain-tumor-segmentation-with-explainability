"""
The collection of input prompts
"""
PROMPTS = {
	'EN': {
		"prompt_1": "Using the provided JSON data from a brain MRI study, please generate a comprehensive report detailing the segmentation results of a brain tumor.\n\nDescribe the tumor's presence in various brain regions according to the Julich-Brain Atlas, noting the percentages of the tumor within each region and the impact on the region. While discussing the confidence of the segmentation and the model used, keep the explanations high-level and avoid overly technical details.\n\nThe goal is to enhance the explainability of the AI segmentation to support clinical decision-making in a manner that can be easily understood by medical professionals.\n\n",

		"prompt_2": "Using the provided JSON data from a brain MRI study, please generate a comprehensive report detailing the segmentation results of a brain tumor. The report should be structured as follows:\n\n1. **Summary of Tumor Segmentation**: Provide an overview of the tumor's distribution across various regions of the brain according to the Julich-Brain Atlas. Discuss the semantic segmentation of the tumor into different categories (tumor core, peritumoral edema, GD-enhancing tumor) and their implications.\n2. **Detailed Regional Impact**: For each region where the tumor is present, describe the percentage of the tumor within the region and the percentage of the region affected by the tumor. Discuss the known roles and functions of these regions in the brain and how the presence of the tumor might impact these functions.\n3. **Semantic Segmentation**: Discuss the different aspects of the tumor identified by the semantic segmentation (tumor core, peritumoral edema, GD-enhancing tumor) and their potential clinical implications.\n4. **Clinical Implications**: Discuss how the insights gained from the segmentation results could guide clinical decision-making, including potential treatment strategies and areas for further investigation.\n\nWhile discussing the confidence of the segmentation and the model used, keep the explanations high-level and avoid overly technical details. The goal is to enhance the explainability of the AI segmentation to support clinical decision-making in a manner that can be easily understood by medical professionals.\n\n"
	},
	'IT': {
		"prompt_1": "Utilizzando i dati JSON derivati da uno studio di risonanza magnetica cerebrale, genera un referto medico completo che illustri i risultati della segmentazione semantica di un tumore cerebrale.\n\n Descrivi la presenza del tumore in varie regioni cerebrali secondo l'Atlante cerebrale di Julich, annotando le percentuali del tumore all'interno di ciascuna regione e l'impatto sulla regione. Durante la discussione del livello di accuratezza della segmentazione semantica e del modello utilizzato, mantieni le spiegazioni ad altro livello ed evita dettagli troppo tecnici.\n\n L'obiettivo è quello di migliorare la spiegabilità della segmentazione semantica effettuata dal modello di intelligenza artificiale per supportare il processo decisionale clinico in un modo che possa essere facilmente compreso dai professionisti del settore medico.\n\n",

		"prompt_2": "Utilizzando i dati JSON derivati da uno studio di risonanza magnetica cerebrale, genera un referto medico che illustri i risultati della segmentazione semantica di un tumore cerebrale. Il referto medico deve essere strutturato come segue:\n\n1. **Sintesi della segmentazione semantica del tumore**: Fornisci una panoramica della distribuzione del tumore nelle varie regioni del cervello secondo l'Atlante cerebrale di Julich. Descrivi la segmentazione semantica del tumore in diverse categorie (nucleo del tumore, edema peritumorale, tumore circostante) e le loro implicazioni.\n2. **Impatto regionale dettagliato**: Per ogni regione in cui è presente il tumore, descrivi la percentuale del tumore all'interno della regione e la percentuale della regione interessata dal tumore. Descrivi i ruoli e le funzioni note di queste regioni nel cervello e come la presenza del tumore potrebbe influire su queste funzioni.\n3. **Segmentazione semantica**: Descrivi i diversi  aspetti del tumore identificati dalla segmentazione semantica (nucleo del tumore, edema peritumorale, tumore circostante) e le loro potenziali implicazioni cliniche.\n4. **Implicazioni cliniche**: Discuti in che modo le informazioni ottenute dai risultati della segmentazione semantica potrebbero guidare il processo decisionale clinico, comprese le potenziali strategie di trattamento e le aree da approfondire.\n\nDurante la discussione del livello di accuratezza della segmentazione semantica e del modello utilizzato, mantieni le spiegazioni ad altro livello ed evita dettagli troppo tecnici. L'obiettivo è migliorare la spiegabilità della segmentazione semantica effettuata dal modello di apprendimento automatico per supportare il processo decisionale clinico in modo che possa essere facilmente compreso dai professionisti del settore medico.\n\n"
	}
}


def get_prompt():
	"""
	The getter method
	"""
	return PROMPTS


def set_prompt(key, value):
	"""
	The setter method
	"""
	PROMPTS.update({key: value})