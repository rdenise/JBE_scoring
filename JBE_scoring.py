#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys
import time
import argparse
from textwrap import dedent
import requests

import pandas as pd
import seaborn as sns; sns.set(); sns.set_style("ticks")
from io import StringIO
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from imageio import imread



##########################################################################################
##########################################################################################
##
##								Function
##
##########################################################################################
##########################################################################################

def create_folder(mypath):

	"""
	Created the folder that I need to store my result if it doesn't exist

	:param mypath: path where I want the folder (write at the end of the path)
	:type: string
	:return: Nothing
	"""

	try:
		os.makedirs(mypath)
	except OSError:
		pass

	return

##########################################################################################
##########################################################################################

def beautify_h1(message) :

	"""
	Will write the heading for text as wanted

	:param message: the heading to write
	:type: str
	:return: Nothing
	"""

	number_letter = len(message)

	print("\n{}".format("#"*(number_letter+2)))
	print("# {}".format(message))
	print("{}\n".format("#"*(number_letter+2)))

	return

##########################################################################################
##########################################################################################


def grab_spreadsheet_info(URL, names_columns, all_register_email) :
    
    """
	Function that will grab all the informations about all the google spreadsheet link to the google form

	:params URL: URL of the google spreadsheet
	:type: str
	:params names_columns: Names of the speaker in the same order with the google form apparition
	:type: list
	:params all_register_email: list with the email of all the attendents to YRLS
	:type: list
	:return: The formated dataframe to be used for the scoring 
	:rtype: pandas.DataFrame
    """
    
    names_columns = [i for i in names_columns if i != 'nan']    
    
    # Grab the information from the google spreadsheet
    response = requests.get("{}/export?format=csv".format(URL))
    response.encoding = "utf-8"
    voting = response.text
    voting = pd.read_csv(StringIO(voting))
    
    columns_score = [i for i in voting.columns if not "Feedback" in i ]
    voting = voting[columns_score]

    # Let's delete the column time
    voting = voting.iloc[:,1:]
    
    # Remove not good mail address
    voting = voting[voting['Email Address'].isin(all_register.Email)]
    
    # Changing the index by the mail addresses
    voting.set_index("Email Address", inplace=True)
    
    # Be sure to have only number 
    voting = voting.replace("5 (Excellent)", 5) # Poster max
    voting = voting.replace("10 (Excellent)", 10) # Talk max
    voting = voting.replace("1 (Poor)", 1) # Talk and poster min
    
    voting.columns = names_columns
    
    return voting

##########################################################################################
##########################################################################################

def merge_results(allRegister, csvInput, number) :
    
    """
	Function that will merge the information of all the google spreadsheet of votes into one for talk and the other for poster

	:params allRegister: dataframe with all the registration for YRLS 
	:type: pandas.DataFrame
	:params csvInput: Dataframe with all the link to the google spreadsheet of votes
	:type: pandas.DataFrame
	:params number: minimal number to be in list to the winner contest
	:type: int
	:return: The dataframe with the point for the talks and the dataframe with the point for the posters
	:rtype: pandas.DataFrame
    """
    
    df_Talk = pd.DataFrame(index=allRegister.Email)
    df_Poster = pd.DataFrame(index=allRegister.Email)
    
    for index, subtab in csvInput.iterrows() :
        tmp_df = grab_spreadsheet_info(subtab.Speadsheet_url, str(subtab.Names_talk).split(";") + str(subtab.Names_poster).split(";"), allRegister.Email)
        
        # Verify to get the columns with only 5 votes
        tmp_df.loc[:,tmp_df.apply(lambda x : True if x[~x.isna()].shape[0] >= number else False, axis=0)]
        
        df_Poster = pd.concat([df_Poster, tmp_df], axis=1)
    
    return df_Poster


##########################################################################################
##########################################################################################

def winners_pdf(winner_Talk, winner_Poster, folder, backgroung_template, name, fontsize=12, figsize=[8, 12]):

	"""
    Function that will create the pdf file with the names of the winner

    :param winner_Talk: name of the winner of YRLS talk
    :type: str
    :param winner_Poster: name of the winner of YRLS poster
    :type: str
    :param folder: path to the output folder
    :type: str
    :param backgroung_template: path to the template file
    :type: str   
    :param name: name of the file to write
    :type: str
    :return: noting
	"""

	# Open a pdf file with matplotlib
	pp = PdfPages(os.path.join(folder, name)) 
	fig, ax = plt.subplots(figsize=figsize)

	# read an image to a numpy array
	f = imread(backgroung_template)
	# tranform an image that into a numpy array to an image 
	plt.imshow(f, aspect="auto") 

	# To write the text
	plt.text(0.065, 0.7, 'The winner for the talks :', ha='left', va='center', transform=ax.transAxes, fontsize=fontsize)
	plt.text(0.5, 0.65, '{}'.format(winner_Talk), ha='center', va='center', transform=ax.transAxes,fontsize=fontsize)
	plt.text(0.065, 0.5, 'The winner for the poster :', ha='left', va='center', transform=ax.transAxes, fontsize=fontsize)
	plt.text(0.5, 0.45, '{}'.format(winner_Poster), ha='center', va='center', transform=ax.transAxes, fontsize=fontsize)

	a = plt.gca()
	a.get_xaxis().set_visible(False) # We don't need axis ticks
	a.get_yaxis().set_visible(False)

	sns.despine(left=True, bottom=True)

	pp.savefig(bbox_inches='tight', dpi=300)
	pp.close()

	return

##########################################################################################
##########################################################################################


def compute_score(df_Poster, folder, backgroung_template, FlashTalks) :
    
    """
    Function that will compute the mean (could be change) to find the winner

    :param df_Poster: the dataframe with all the notation for each poster (that have at leat 3 votes)
    :type: pandas.DataFrame
    :param folder: path to the output folder
    :type: str
    :param backgroung_template: path to the template file
    :type: str  
    :param FlashTalks: dataframe with the correspondance between id and name
    :type: pandas.DataFrame
    :return: Nothing     
    """
    
    score_Poster = df_Poster.mean(axis=0).sort_values()
    score_Poster.to_csv(os.path.join(folder, "Results_Poster_JBE{}_{}.txt".format(time.strftime("%Y"), time.strftime("%Y%m%d"))), sep="\t")
    winner_Poster = " and ".join([" ".join(score_Poster[score_Poster.ID_poster == IDPoster].loc[:,["First name", "Last name"]].tolist()) for IDPoster in score_Poster[score_Poster == score_Poster.max()].index.tolist()])

    beautify_h1("Poster")
    print("The name of the winner for JBE{} : {}".format(time.strftime("%Y"), winner_Poster))

    # For the page
    winners_pdf(winner_Talk, winner_Poster, folder, backgroung_template, name="Winner_JBE{}_{}.pdf".format(time.strftime("%Y"), time.strftime("%Y%m%d")))
    

   	# For the slide
    winners_pdf(winner_Talk, winner_Poster, folder, backgroung_template, name="Winner_slide_JBE{}_{}.pdf".format(time.strftime("%Y"), time.strftime("%Y%m%d")), figsize=[16, 9])
    
    return


##########################################################################################
##########################################################################################
##
##								Main
##
##########################################################################################
##########################################################################################


parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
     description=dedent("""
     *            *               *                   *
*           *               *   *   *  *    **                *   *
  **     *    *   *  *     *                    *               *
||       _ ____  ______    _____                    
||      | |  _ \|  ____|  / ____|                   
||      | | |_) | |__    | (___   ___ ___  _ __ ___ 
||  _   | |  _ <|  __|    \___ \ / __/ _ \| '__/ _ \\
|| | |__| | |_) | |____   ____) | (_| (_) | | |  __/
||  \____/|____/|______| |_____/ \___\___/|_|  \___|                                                                                                                                                                    
 *      *   * *     *   **         *   *  *           *
  *      *         *        *    *              *
             *                           *  *           *     *

""") )

general_option = parser.add_argument_group(title = "General input dataset options")
general_option.add_argument("-url",'--url_info_csv',
							metavar="<URL>",
							dest="url_info_csv",
							help="Shared URL to the google spreandsheet with all the registration and google form [if you don't provide the csv file]")
general_option.add_argument("-csv",'--file_info_csv',
							metavar="<FILE>",
							dest="file_info_csv",
							help="CSV with all the registration and google form [if you don't provide the url]")
general_option.add_argument("-t",'--template',
							metavar="<FILE>",
							dest="template",
							help="Png file with the tamplate to use for the slide and the page that will contain the winners",
              				required=True) # for later could be two files
general_option.add_argument("-o",'--output',
 							default=None,
							dest="output",
							metavar='<OUTPUT>',
							help="Using <OUTPUT> for output files (default: template folder)")
general_option.add_argument("-min",'--minimum_votes',
 							default=3,
							dest="minimum_votes",
							metavar='<INT>',
							help="Minimal number of vote to stay in the competition")

args = parser.parse_args()

TEMPLATE = args.template

if args.output:
	OUTPUT = args.output
else :
	OUTPUT = os.path.join(os.path.abspath(os.path.dirname(TEMPLATE)),"YRLS{}_results_{}".format(time.strftime("%Y"), time.strftime("%y%m%d")))
		
create_folder(OUTPUT)

#  We take the information directly on the spreadsheet if the information is online
if args.url_info_csv :
	response = requests.get("{}/export?format=csv".format(args.url_info_csv)) #functon that allow to take information from website + adding /export?format=csv to a google spreadsheet link allow to export as csv
	response.encoding = "utf-8"
	csv_input = response.text
	csv_input = pd.read_csv(StringIO(csv_input)) # StringIO allow to transform string to flux, so we can read the csv with pandas
elif args.file_info_csv :
	csv_input = pd.read_csv(args.file_info_csv)
else :
	print(dedent("""usage: YRLS_scoring.py [-h] [-url <URL>] [-csv <FILEE>] -t <FILE>
                       [-o <OUTPUT>] [-min <INT>]
			YRLS_scoring.py: error: the following arguments are required: -url/--url_info_csv or -csv/--file_info_csv"""))
	sys.exit(0)


print(dedent("""
  -------------------------------------------------------------
||       _ ____  ______  __          ___                       
||      | |  _ \|  ____| \ \        / (_)                      
||      | | |_) | |__     \ \  /\  / / _ _ __  _ __   ___ _ __ 
||  _   | |  _ <|  __|     \ \/  \/ / | | '_ \| '_ \ / _ \ '__|
|| | |__| | |_) | |____     \  /\  /  | | | | | | | |  __/ |   
||  \____/|____/|______|     \/  \/   |_|_| |_|_| |_|\___|_|                                                         
  -------------------------------------------------------------
"""))

# We split the dataframe about the registration information
response = requests.get("{}/export?format=csv&gid={}".format(csv_input.iloc[0].Speadsheet_url, csv_input.iloc[0].gid))
response.encoding = "utf-8"
all_register = response.text
all_register = pd.read_csv(StringIO(all_register))

# We take the informations to convert the name of the winner
response = requests.get("{}/export?format=csv&gid={}".format(csv_input.iloc[0].Speadsheet_url, csv_input.iloc[0].gid))
response.encoding = "utf-8"
flash_talk = response.text
flash_talk = pd.read_csv(StringIO(flash_talk))

# We split the dataframe with only the google spreadsheets of the votes
csv_input = csv_input.iloc[2:,:]

dfPoster = merge_results(all_register,csv_input, int(args.minimum_votes))

compute_score(dfPoster, OUTPUT, TEMPLATE, flash_talk)

