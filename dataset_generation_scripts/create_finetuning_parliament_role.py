####################################################################################
# Cleaning up parliament speech files
# Output is an UTF-8 file with one article per line
####################################################################################

import sys, glob, os, re, argparse
import pandas as pd
from collections import Counter
import random 
from itertools import islice

#Norwegian Spacy
import spacy
from spacy.lang.nb.examples import sentences
nlp = spacy.load('nb_core_news_sm')

def main(args):
    num_samples = 3000
    print(f'Starting to read csv-file')
    
    #Read the file
    df = pd.read_csv(args.input_file, encoding='utf-8', dtype='string')


    print(f'Finished reading csv-fil.\nNumber of valid articles: {len(df)}')
    
    
    rolelist = []
    data = pd.DataFrame(columns=['date', 'role', 'text'])

    for index, row in df.iterrows():
        article = row['text']
        role = row['party_role']
        date = row['date']
        rolelist.append(role)

        
       #Add to dataframe if more than 5 words and start with capital letter
        if len(article.split()) > 5 and article[0].isupper():
            firstparagraph = article.split("\n")[0]
            data = data.append({'date': date, 'role': role, 'text': firstparagraph}, ignore_index=True)

        if index%1000 == 0:
            print(f'Processing row {index}')
    
    print("Finished loading everything into Pandas")

    cabinet = data['role'] == "Cabinet"
    support = data['role'] == "Support"
    opposition = data['role'] == "Opposition"
    
    print("Some stats:")
    r = Counter(rolelist) 
    print(r.items())
  
    support_sample = data[support].sample(n=num_samples, random_state=1)
    cabinet_sample = data[cabinet].sample(n=num_samples, random_state=1)
    opposition_sample = data[opposition].sample(n=num_samples, random_state=1)
   
    final_data = pd.concat([support_sample, cabinet_sample, opposition_sample], ignore_index=True).sample(frac=1).reset_index(drop=True)

   
    final_data.to_csv(args.output_file, index=False)


    print(f'A total number of {num_samples} for both bokmål and nynorsk is written to file {args.output_file}')



def parse_args():
    # Parse commandline
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', required=True, type=str, help='Input file')
    parser.add_argument('--output_file', required=True, type=str, help='Output file')
    args = parser.parse_args()
    return args
    
if __name__ == "__main__":
    args = parse_args()
    main(args)

