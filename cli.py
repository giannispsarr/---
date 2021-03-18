import config
import socket
import hashlib
import requests
import pickle
import time
import json
import os
import pdfplumber
import pandas as pd

from argparse import ArgumentParser
from flask import Flask, Blueprint, jsonify, request
from PyInquirer import style_from_dict, Token, prompt
from PyInquirer import Validator, ValidationError
from texttable import Texttable
from time import sleep
from datetime import datetime, date


style = style_from_dict({
    Token.QuestionMark: '#E91E63 bold',
    Token.Selected: '#673AB7 bold',
    Token.Instruction: '',
    Token.Answer: '#2196f3 bold',
    Token.Question: '',
})


def HomeOrExit():
    HomeOrExit_q = [
        {
            'type': 'list',
            'name': 'option',
            'message': 'What do you want to do?',
            'choices': ['Home', 'Exit'],
            'filter': lambda val: val.lower()
        }]
    HomeOrExit_a = prompt(HomeOrExit_q)['option']
    return HomeOrExit_a


def GenerateAkomaNtosoXML(ada):
    doc_url = "https://diavgeia.gov.gr/doc/"+ada
    meta_url="https://diavgeia.gov.gr/luminapi/opendata/decisions/"+ada+".json"
    json_metadata = requests.get(meta_url)
    if(json_metadata.status_code==404):
        print("Error 404 - Δε βρέθηκε Πράξη με ΑΔΑ: "+str(ada))
    elif(json_metadata.status_code==400):
        print("Error 400 - Bad Request")
    elif(json_metadata.status_code!=200):
        print("Error - Status code: "+str(json_metadata.status_code))
    else:
        json_metadata=json_metadata.json()
        #get useful metadata from json
        subject = json_metadata['subject']
        ada = json_metadata['ada']
        print("ΑΔΑ: "+str(ada))
        status=json_metadata['status']
        protocolNumber=json_metadata['protocolNumber']
        isd = float(json_metadata['issueDate'])/1000 #divide by 1000 to get timestamp in s, not ms
        issueDate = date.fromtimestamp(isd)
        decisionID = json_metadata['decisionTypeId']
        decision_info = requests.get("https://diavgeia.gov.gr/luminapi/opendata/types/"+str(decisionID)+".json").json()
        if 'label' in decision_info:
            decision_name = decision_info['label']
        else: decision_name=""
        print("Decision type: "+str(decision_name))


        
        unitIDs = json_metadata['unitIds']
        print("Unit ids:"+str(unitIDs))

        organizationID = json_metadata['organizationId']
        print("Organization ID:"+str(organizationID))


        organization_info = requests.get("https://diavgeia.gov.gr/luminapi/opendata/organizations/"+str(organizationID)+".json").json()
        organization_name = organization_info['label']
        print("Organization name: "+str(organization_name))


        unit_names=[]
        #idiotites=[]
        if unitIDs:
            for unit_id in unitIDs:
                unit_info = requests.get("https://diavgeia.gov.gr/luminapi/opendata/units/"+str(unit_id)+".json").json()
                unit_names.append(unit_info['label'])
        print("Unit names:"+str(unit_names))
        #print(idiotites)

        signerIds = json_metadata['signerIds']

        issuer_ranks=[]
        issuer_names=[]
        issuer_units=[]
        print("Issuer IDs:"+str(signerIds))
        for sid in signerIds:
            signer_info = requests.get("https://diavgeia.gov.gr/luminapi/opendata/signers/"+str(sid)+".json").json()
            fullname=signer_info['firstName']+" "+signer_info['lastName']
            issuer_names.append(fullname)
            signer_units=signer_info['units']
            #Ψαξε στα units στα οποία φαίνεται να είναι καταχωρημένος ο signer
            rank_found=False
            for s_unit in signer_units:
                for uid in unitIDs:
                    #Aν βρεις κάποιο που να ταιριάζει με τα units της πράξης, πέρασε ως ιδιότητα του signer την ιδιότητα που έχει σε αυτό το unit
                    if uid == s_unit['uid']:
                        issuer_ranks.append(s_unit['positionLabel'])
                        issuer_units.append(requests.get("https://diavgeia.gov.gr/luminapi/opendata/units/"+str(uid)+".json").json()['label'])
                        rank_found=True
                        break
            #Αν δε βρεις κανένα unit του signer, πέρασέ του ως ιδιότητα την ιδιότητα που έχει στο πρώτο unit του (το οποίο λογικά είναι και το πιο σημαντικό).
            if not rank_found:
                signer_unit=requests.get("https://diavgeia.gov.gr/luminapi/opendata/signers/"+str(sid)+".json").json()['units'][0]
                signer_unit_id = signer_unit['uid']
                issuer_ranks.append(signer_unit['positionLabel'])
                issuer_units.append(requests.get("https://diavgeia.gov.gr/luminapi/opendata/units/"+str(signer_unit_id)+".json").json()['label'])
        print("Issuer Names: "+str(issuer_names))
        print("Issuer Ranks:"+str(issuer_ranks))
        print("Issuer Units:"+str(issuer_units))
        


        hasPrivateData = json_metadata['privateData']
        lmd = float(json_metadata['submissionTimestamp'])/1000 #divide by 1000 to get timestamp in s, not ms
        lastModifiedDateTime = datetime.fromtimestamp(isd).date()
        
        version = json_metadata['versionId']
        attachments=json_metadata['attachments']
        extraFieldValues = json_metadata['extraFieldValues']

        
        with open('akomantoso_template.xml','r', encoding='utf-8') as template:
            filedata = template.read()

        template.close()

        filedata = filedata.replace("SUBJECT",str(subject))
        filedata = filedata.replace("DOC_URL", doc_url )
        filedata = filedata.replace("DATE_PUBLISHED",str(issueDate))
        filedata = filedata.replace("DATE_LAST_MODIFIED",str(lastModifiedDateTime))
        filedata = filedata.replace("ADA",str(ada))
        filedata = filedata.replace("NOW_DATE",str(datetime.now().date()))
        filedata = filedata.replace("PROTOCOL_NUMBER",str(protocolNumber))
        filedata = filedata.replace("DECISION_TYPE_ID",str(decisionID))
        filedata = filedata.replace("DECISION_TYPE_NAME",str(decision_name))
        filedata = filedata.replace("ORGANIZATION_ID",str(organizationID))
        filedata = filedata.replace("ORGANIZATION_NAME",str(organization_name))


        text=""
        for uid in unitIDs:
            text = text+str(uid)+","
        text=text[:-1]
        filedata = filedata.replace("UNIT_IDS",text)
        text=""
        for un in unit_names:
            text = text+str(un)+","
        text=text[:-1]
        filedata = filedata.replace("UNIT_NAMES",text)

        text=""
        for ir in issuer_ranks:
            text = text+str(ir)+"|"
        text=text[:-1]
        filedata = filedata.replace("ISSUER_RANKS",text)

        filedata = filedata.replace("YEAR",str(datetime.now().date())[0:4])

        text=""
        for i_n in issuer_names:
            text = text+str(i_n)+","
        text=text[:-1]
        filedata = filedata.replace("ISSUER_NAMES",text)

        filedata = filedata.replace("UNIT_NAME",str(unit_names[0]))

        text=""
        for i,i_n in enumerate(issuer_names):
            text = text+i_n+", "+issuer_ranks[i].upper()+","+issuer_units[i]+"|"
        text=text[:-1]
        filedata = filedata.replace("ISSUERRANKSNAMES",text)




        filedata = filedata.replace("ADA",str(ada))

        output_file = str(ada)+"_AkomaNtoso.xml"
        f = open(output_file, 'w', encoding='utf-8') 
        f.write(filedata)
        f.close()


def client():
    print('Loading...\n')
    sleep(2)
    print("Μηχανισμός Άντλησης Δεδομένων Δι@υγειας.\n")
    while True:
        print("----------------------------------------------------------------------")
        method_q = [
            {
                'type': 'list',
                'name': 'method',
                'message': 'Ενέργεια:',
                'choices': ['Άντληση/Προεπισκόπηση δεδομένων', 'Έξοδος']
            }]
        method_a = prompt(method_q, style=style)["method"]
        os.system('cls||clear')
        if method_a == 'Άντληση/Προεπισκόπηση δεδομένων':
            print("Άντληση/Προεπισκόπηση δεδομένων")
            print("----------------------------------------------------------------------")
            insert_q = [
                {
                    'type': 'input',
                    'name': 'ada',
                    'message': 'ΑΔΑ:',
                    'filter': lambda val: str(val)
                }]
            insert_a = prompt(insert_q, style=style)
            print("\nΕπιβεβαίωση αναζήτησης:")
            insert_confirm_q = [
                {
                    'type': 'confirm',
                    'name': 'confirm_search',
                    'message': 'Αναζήτηση του: ' + insert_a["ada"] + ' ;',
                    'default': False
                }
            ]
            insert_confirm_a = prompt(insert_confirm_q)["confirm_search"]
            if insert_confirm_a:
                ada = insert_a["ada"]
                GenerateAkomaNtosoXML(ada)
                if HomeOrExit() == 'exit':
                    break
                else:
                    os.system('cls||clear')

        elif method_a == 'Έξοδος':
            print("Έξοδος από την Μηχανή Άντλησης Δεδομένων...")
            print("----------------------------------------------------------------------\n")
            break

        else:
            break



if __name__ == '__main__':
    client()