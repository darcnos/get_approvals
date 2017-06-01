import requests, json, time, os, sys, configparser


#Detect current path of the script
dir_path = os.path.dirname(os.path.realpath(__file__))

#Define where our config inis are located
configobject = configparser.ConfigParser()
configobject.read(dir_path + '\\get_approvals.ini')
savepath = configobject['LawsonCSV_Settings']['path']
myheaders = {'content-type': 'application/json'}
problematic_fileId =  []



#Grab system time, use it for csv nrame
currenttime = time.strftime("%Y%m%d-%H%M%S")
filename = currenttime + '_approved.csv'
problematic_fileId_log = currenttime + '_errors.txt'

#Print stuff to the console
print("Program's current location is: " + dir_path)
print("Approved items discovered this run will be saved to: " + savepath + '\\' + filename)
print('')


def login():
    login_url = 'https://applications.filebound.com/v3/login?fbsite=https://burriswebdocs.filebound.com'
    data = {
        'username': 'approver',
        'password': 'SECRETPASSWORDTHATISNOTTHISSTRING'
    }
    r = requests.post(login_url, data)
    guid = r.json()
    return(guid)

guid = login()




def get_approvals():
    """
    The meat of our program. Queries all files in ProjectID 54 with a Field19 value of 'ReadyForLawson'
    If there is more than one, process the files and build an upload file.
    As files are processed, 'ReadyForLawson' is updated to 'UploadedToLawson' so it doesn't get pulled again.
    """

    #First some variables to make stringing together URIs easier
    appsite_files = 'https://applications.filebound.com/v4/files/?filter=ProjectID_54,F19_ReadyForLawson&'
    filebound_site = 'fbsite=https://burriswebdocs.filebound.com&guid=' + guid
    url = appsite_files + filebound_site
    #print(url)

    #Print that the server is going to be queried, save the response as a var named 'r'
    print('Querying the site for any newly added approvals')
    r = requests.get(url)

    #If the response was successful, do this stuff
    if r.status_code == 200:
        print('Successful connection!')
        print('')
        #response = requests.get(url)
        #Convert the response data to JSON
        json_data = json.loads(r.text)

        #If the response contains no files, end now
        if len(json_data) == 0:
            print('No files have been marked as approved since last runtime.')
            print('Exiting program now.')
            time.sleep(5)
            sys.exit(0)
        num = 0

        #If the successful response data contains files, go on to do the following things
        if len(json_data) >= 1:
            global newstuff
            newstuff = True
            #If the savepath in the INI doesn't exist, create it
            if not os.path.exists(savepath):
                os.makedirs(savepath)

            #Now entering a loop involving our output file
            with open(savepath + '\\' + filename, 'a') as out:
            #Header stuff
                headerstuff = '"Company","Level","Distrib Date","Batch #","Vendor","Invoice #","Invoice Type","Invoice Date","Due Date","Inv Amount","","Line","Distrib Company","Acct Unit","Account","Sub-Acct","Distrib Amt","Results from BU20.1","Reference"\n'
                out.write(headerstuff)
            #out.write('"Company","Level","Distrib Date","Batch #","Vendor","Invoice #","Invoice Type","Invoice Date","Due Date","Inv Amount","Reason Code","Distrib Company","Acct Unit","Account","Sub-Acct","Distrib Amt","Units","Reference"\n')
            #For each of the files in the successful response data, do the following things
                for i in range(len(json_data)):
                    #Save off each field's value into some variable
                    field1 = json_data[num]['field'][1]
                    field2 = json_data[num]['field'][2]
                    field3 = json_data[num]['field'][3]
                    field4 = json_data[num]['field'][4]
                    field5 = json_data[num]['field'][5]
                    field6 = json_data[num]['field'][6]
                    field7 = json_data[num]['field'][7]
                    field8 = json_data[num]['field'][8]
                    field9 = json_data[num]['field'][9]
                    #We now try to interpret the Invoice Amount as an interger, floats are okay input
                    try:
                        intvalue = int(float(field9))
                        #If the invoice is negative, set it to Credit
                        if intvalue < 0:
                            invoicetype = 'C'
                            #We will assume most transactions are '' since they are debit
                        else:
                            invoicetype = ''
                    except:
                        #On the off chance you have something crazy, Invoice is likely a debit anyway
                        invoicetype = ''
                        print('Invoice Amount is blank or a non-number.')

                    #Lets grab the rest of the fields since we already have the data
                    field10 = json_data[num]['field'][10]
                    field11 = json_data[num]['field'][1]
                    field12 = json_data[num]['field'][12]
                    field12 = field12.zfill(4)
                    field13 = json_data[num]['field'][13]
                    field14 = json_data[num]['field'][14]
                    field15 = json_data[num]['field'][15]
                    field16 = json_data[num]['field'][16]
                    field17 = json_data[num]['field'][17]
                    field18 = json_data[num]['field'][18]
                    field19 = json_data[num]['field'][19]
                    field20 = json_data[num]['field'][20]


                    #Get the current fileId. This is needed in the update_exportstate function call
                    currentfileId = json_data[num]['fileId']
                    result = update_exportstate(currentfileId)
                    if result == 200:
                        #Assemble the string which shall be a line of the Lawson upload file
                        #values = '"' + field1 + '","' + field2 + '","' + field3 + '","' + field4 + '","' + field5 + '","' + field6 + '","' + invoicetype + '","' + field7 + '","' + field8 + '","' + field9 + '","' + field10 + '","' + field11 + '","' + field12 + '","' +  field13 + '","' + field14 + '","' + field15 + '","' + field16 + '","' + field17 + '"\n'
                        values = '"' + field1 + '","' + field2 + '","' + field3 + '","' + field4 + '","' + field5 + '","' + field6 + '","' + invoicetype + '","' + field7 + '","' + field8 + '","' + field9 + '","' + '' + '","' + 'A' + '","' + field11 + '","' + field12 + '","' +  field13 + '","' + field14 + '","' + field15 + '","' + "" + '","' + '"' + '\n'



                        #Only if the status is updated on the site successfully should we write the line to the Lawson upload file
                        out.write(values)

                        #Bump the counter up by one, run the next iteration of the loop if there is any
                        num = num + 1
                    if result != 200:
                        bee = ': logging as a problematic file to *NOT* upload to Lawson.'
                        print("Problem updating FileID " + str(currentfileId) + bee)
                        errors = '"' + field5 + '","' + field6 + '","' + str(currentfileId) + '"\n'
                        problematic_fileId.append(errors)
                        continue
            if newstuff == True:
                print('----')
                print('Wrote all newly approved Corp AP Invoice items to ' + savepath + '\\' + filename)
                out.close()
            if newstuff != True:
                print('')
                print('No new approvals this run, so no Lawson CSV file has been made.')
            if len(problematic_fileId) >= 1:
                print('')
                print('Problematic files found in this run. They have been logged to: ' + savepath + '\\' + problematic_fileId_log)
                with open(savepath + '\\' + problematic_fileId_log, 'a') as elog:
                    error_headers = '"VendorNumber","InvoiceNumber","FileID"\n'
                    elog.write(error_headers)
                    for i in problematic_fileId:
                        elog.write(i)
                    elog.close()


    else:
        print('Connection error. Please try again, check network connection or account credentials, or contact WebDocs Development (dcarson@dmi-inc.com).')





def update_exportstate(fileId):
    """
    Reads in a string, returns nothing, only does stuff.
    The input is the fileId of a given file, to which it updates the 'ExportState'
    """
    url = 'https://applications.filebound.com/v4/files/' + str(fileId) + '?fbsite=https://burriswebdocs.filebound.com&guid=' + guid
    #print(url)
    r = requests.get(url)
    jsonobject = json.loads(r.text)
    jsonobject['field'][19] = 'UploadedToLawson'
    finalstring = json.dumps(jsonobject)
    boom = requests.post(url, finalstring, headers = myheaders)
    if boom.status_code == 200:
        print('Successfully updated file with ID ' + str(fileId))
        return(boom.status_code)
    if boom.status_code != 200:
        #print("Couldn't update this record. Skipping for now.")
        return(boom.status_code)
    print(boom.text)
    print(boom)




get_approvals()
time.sleep(5)
sys.exit(0)
#exit