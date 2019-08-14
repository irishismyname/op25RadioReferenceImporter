import csv
from zeep import Client
import re
import sys

if len(sys.argv) == 1:
    rrSystemId = int(input("What system ID would you like to download?"))

else:
    for j in range(1,len(sys.argv)):
        rrSystemId = sys.argv[j]
    
        #parameters
        op25OutputPath = '/home/pi/Downloads/op25/op25/gr-op25_repeater/apps/'
        sdrtOutputPath = 'off'
        
        #radio reference authentication
        client = Client('http://api.radioreference.com/soap2/?wsdl&v=15&s=rpc')
        auth_type = client.get_type('ns0:authInfo')
        myAuthInfo = auth_type(username='youusername', password='yourpassword', appKey='yourapikey', version='15', style='rpc')
        
        #prompt user for system ID
        
        sysName = client.service.getTrsDetails(rrSystemId, myAuthInfo).sName
        print(sysName + ' system selected.')
        
        #download talkgroups for given sysid
        Talkgroups_type = client.get_type('ns0:Talkgroups')
        result = Talkgroups_type(client.service.getTrsTalkgroups(rrSystemId, 0, 0 ,0, myAuthInfo))
        #print(result)
        #abbreviate the system name
        wordsInSysName = (len(sysName.split()))
        
        sysNameAbb = ''
        if wordsInSysName >= 2:
            for i in range(wordsInSysName):
                sysNameAbb = sysNameAbb + sysName.split()[i][0]
            regex = re.compile('[^a-zA-Z]')
            #First parameter is the replacement, second parameter is your input string
            sysNameAbb = regex.sub('', sysNameAbb)
        else:
            sysNameAbb = sysName
        
        print('Abbreviating ' + sysName + ' as ' + sysNameAbb)
        
        #construct the talkgroup and blacklist lists
        talkgroups = []
        blacklist = []
        for row in result:
            if row.enc == 0:
                talkgroups.append([row.tgDec,sysNameAbb + ' ' + row.tgDescr])
            else:
                blacklist.append(row.tgDec)
                
        #output tsv files
        csv.register_dialect('tsvDialect', delimiter='\t', quoting=csv.QUOTE_NONE)        
        #with open(op25OutputPath + sysNameAbb + '_talkgroups.tsv' , 'w', newline='') as op25OutputFile:
        with open(op25OutputPath + sysNameAbb.lower() + '_talkgroups.tsv' , 'wb') as op25OutputFile:
            writer = csv.writer(op25OutputFile, dialect='tsvDialect')
            writer.writerows(talkgroups)
            
        with open(op25OutputPath + sysNameAbb.lower() + '_blacklist.tsv' , 'w') as op25BlacklistFile:
            for row in blacklist:
                op25BlacklistFile.write("%s\n" % row)
                
        #construct xml file for sdrtrunk
        def decStringToHexString(decString):
            return format(int(decString),'X')
        
        sdrtList = []
        for row in result:
                sdrtList.append('  <alias name="' + sysNameAbb + ' ' + row.tgDescr + '" list="' + sysName + '"' + ' iconName="No Icon" color="-16777216" group="'+sysName+'">')
                sdrtList.append('      <id type="talkgroupID" talkgroup="'+decStringToHexString(row.tgDec)+'"/>')
                sdrtList.append('  </alias>')
                
        #write xml file for sdrtrunk
        if sdrtOutputPath != 'off':
            with open(sdrtOutputPath + 'output.xml' , 'w') as sdrtOutputFile:
                    for Element in sdrtList:
                        sdrtOutputFile.write("%s\n" % Element)
