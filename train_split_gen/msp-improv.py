import json
import numpy as np
import pandas as pd
import pickle, pdb, re

from tqdm import tqdm
from pathlib import Path

# define logging console
import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-3s ==> %(message)s', 
    level=logging.INFO, 
    datefmt='%Y-%m-%d %H:%M:%S'
)


if __name__ == '__main__':

    # data path
    data_path = Path('/media/data/sail-data/MSP-IMPROV/MSP-IMPROV/')
    output_path = Path('/media/data/projects/speech-privacy/emo2vec')

    Path.mkdir(output_path.joinpath('train_split'), parents=True, exist_ok=True)
    train_list, dev_list, test_list = list(), list(), list()
    
    # msp-improv
    evaluation_path = Path(data_path).joinpath('Evalution.txt')
    with open(str(evaluation_path)) as f:
        evaluation_lines = f.readlines()

    label_dict = dict()
    for evaluation_line in evaluation_lines:
        if 'UTD-' in evaluation_line:
            file_name = 'MSP-'+evaluation_line.split('.avi')[0][4:]
            label_dict[file_name] = evaluation_line.split('; ')[1][0]
            
    sentence_file_list = list(label_dict.keys())
    sentence_file_list.sort()
    for sentence_file in tqdm(sentence_file_list, ncols=100, miniters=100):
        sentence_part = sentence_file.split('-')
        recording_type = sentence_part[-2][-1:]
        gender, speaker_id, label = sentence_part[-3][:1], sentence_part[-3], label_dict[sentence_file]
        session_id = int(speaker_id[1:])
        
        # we keep improv data only
        file_path = Path(data_path).joinpath(
            'Audio', f'session{session_id}', sentence_part[2], recording_type, f'{sentence_file}.wav'
        )
        # [key, speaker id, gender, path, label]
        file_data = [sentence_file, f'msp_improv_{speaker_id}', gender, str(file_path), label]

        # append data
        if f'session{session_id}' == 'session6': test_list.append(file_data)
        elif f'session{session_id}' == 'session5': dev_list.append(file_data)
        else: train_list.append(file_data)
        
    return_dict = dict()
    return_dict['train'], return_dict['dev'], return_dict['test'] = train_list, dev_list, test_list
    logging.info(f'-------------------------------------------------------')
    logging.info(f'Split distribution for MSP-IMPROV dataset')
    for split in ['train', 'dev', 'test']:
        logging.info(f'Split {split}: Number of files {len(return_dict[split])}')
    logging.info(f'-------------------------------------------------------')
        
    # dump the dictionary
    jsonString = json.dumps(return_dict, indent=4)
    jsonFile = open(str(output_path.joinpath('train_split', f'msp-improv.json')), "w")
    jsonFile.write(jsonString)
    jsonFile.close()

    