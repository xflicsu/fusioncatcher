#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
It downloads the paralog genes from the Ensembl database.



Author: Daniel Nicorici, Daniel.Nicorici@gmail.com

Copyright (c) 2009-2016 Daniel Nicorici

This file is part of FusionCatcher.

FusionCatcher is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

FusionCatcher is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with FusionCatcher (see file 'COPYING.txt').  If not, see
<http://www.gnu.org/licenses/>.

By default, FusionCatcher is running BLAT aligner
<http://users.soe.ucsc.edu/~kent/src/> but it offers also the option to disable
all its scripts which make use of BLAT aligner if you choose explicitly to do so.
BLAT's license does not allow to be used for commercial activities. If BLAT
license does not allow to be used in your case then you may still use
FusionCatcher by forcing not use the BLAT aligner by specifying the option
'--skip-blat'. Fore more information regarding BLAT please see its license.

Please, note that FusionCatcher does not require BLAT in order to find
candidate fusion genes!

This file is not running/executing/using BLAT.
"""
#using biomart in Python
import sys
import os
import socket
# timeout in seconds
timeout = 6000 # one hour
socket.setdefaulttimeout(timeout)
import urllib
import urllib2
import optparse
import time


if __name__ == '__main__':

    #command line parsing

    usage = "%prog [options]"
    description = """It downloads the paralog genes from the Ensembl database."""
    version = "%prog 0.10 beta"

    parser = optparse.OptionParser(usage=usage,description=description,version=version)

    parser.add_option("--organism",
                      action = "store",
                      type = "string",
                      dest = "organism",
                      default = "homo_sapiens",
                      help="""The name of the organism for which the paralog genes are downloaded, e.g. homo_sapiens, mus_musculus, etc. Default is '%default'.""")

    parser.add_option("--output",
                      action="store",
                      type="string",
                      dest="output_directory",
                      default = '.',
                      help="""The output directory where the paralog genes are stored. Default is '%default'.""")

    parser.add_option("--server",
                      action="store",
                      type="string",
                      dest="server",
                      default = "www.ensembl.org",
                      help="""The Ensembl server from where the paralog genes are downloaded, e.g. 'www.ensembl.org', 'uswest.ensembl.org', 'useast.ensembl.org', 'asia.ensembl.org', etc. Default is '%default'.""")

    (options,args) = parser.parse_args()

    # validate options
    if not (options.output_directory
            ):
        parser.print_help()
        sys.exit(1)


    #
    #
    #
    temp_paralogs_filename1=os.path.join(options.output_directory,'temp_paralogs1.txt')
    temp_paralogs_filename2=os.path.join(options.output_directory,'temp_paralogs2.txt')
    paralogs_filename=os.path.join(options.output_directory,'paralogs.txt')
    paralogs_header_filename=os.path.join(options.output_directory,'paralogs_header.txt')
        

                    
    ense = options.organism.lower().split('_',1)
    ensembl_organism = ense[0][0]+ense[1]+'_gene_ensembl'
    org = ense[0][0] + ense[1]

    CHUNK_SIZE=65536 # 2**20 1 MB

    query1 = """<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE Query>
    <Query  virtualSchemaName = "default" formatter = "TSV" header = "0" uniqueRows = "0" count = "" datasetConfigVersion = "0.6" >
        <Dataset name = "%%%organism%%%" interface = "default" >
            <Attribute name = "ensembl_gene_id" />
            <Attribute name = "chromosome_name" />
        </Dataset>
    </Query>
    """.replace('%%%organism%%%',ensembl_organism).replace("\n"," ").strip()

    query2 = """<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE Query>
    <Query  virtualSchemaName = "default" formatter = "TSV" header = "0" uniqueRows = "0" count = "" datasetConfigVersion = "0.7" >
        <Dataset name = "%%%organism%%%" interface = "default" >
            <Filter name = "chromosome_name" value = "%%%chromosome%%%"/>        
            <Attribute name = "ensembl_gene_id" />
            <Attribute name = "%%%org%%%_paralog_ensembl_gene" />
        </Dataset>
    </Query>
    """.replace('%%%organism%%%',ensembl_organism).replace('%%%org%%%',org).replace("\n"," ").strip()



    mydata1=urllib.urlencode( {"query" : query1} )
    headers = {
    'User-agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3',
    'Accept' : 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
    'Accept-Language' : 'en-gb,en;q=0.5'
    }

    print "Starting..."

    s = ""
    ns = 0
    server = "http://%s/biomart/martservice" % (options.server,)
    try:
        req=urllib2.Request(server,mydata1,headers)
        page=urllib2.urlopen(req)

        fid=open(temp_paralogs_filename1,'w')
        size=0
        while True:
            part=page.read(CHUNK_SIZE)
            if not part:
                break
            size=size+len(part)
            fid.write(part)
            amount=size/float(1024*1024)
            sys.stdout.write("\b"*ns)
            sys.stdout.flush()
            s = "Downloaded: %9.2f MB" % amount
            ns = len(s)
            sys.stdout.write(s)
            sys.stdout.flush()
        fid.close()
        print "\nFinished downloading: %9.2f MB\n" % amount
    except urllib2.HTTPError, error:
        print '\nHTTPError = ' + str(error)
        sys.exit(1)
    except urllib2.URLError, error:
        print '\nURLError = ' + str(error)
        sys.exit(1)
    except IOError, error:
        print '\nIOError = ' + str(error)
        sys.exit(1)
    except Exception, error:
        print "\nError: Generic exception!",str(error)
        sys.exit(1)

    # extract chromosomes
    chroms = sorted(set([line.rstrip('\r\n').split('\t')[-1] for line in file(temp_paralogs_filename1,'r').readlines() if line.rstrip("\r\n")]))
    file(temp_paralogs_filename2,'w').write('')

    try:
    
        for crs in chroms:
            time.sleep(3)
            print "chromosome =",crs
            mydata2=urllib.urlencode( {"query" : query2.replace("%%%chromosome%%%",crs)} )
            headers = {
            'User-agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3',
            'Accept' : 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
            'Accept-Language' : 'en-gb,en;q=0.5'
            }
            req=urllib2.Request(server,mydata2,headers)
            page=urllib2.urlopen(req)

            fid=open(temp_paralogs_filename2,'a')
            size=0
            while True:
                part=page.read(CHUNK_SIZE)
                if not part:
                    break
                size=size+len(part)
                fid.write(part)
                amount=size/float(1024*1024)
                sys.stdout.write("\b"*ns)
                sys.stdout.flush()
                s = "Downloaded: %9.2f MB" % amount
                ns = len(s)
                sys.stdout.write(s)
                sys.stdout.flush()
            fid.close()
            print "\nFinished downloading: %9.2f MB\n" % amount
    except urllib2.HTTPError, error:
        print '\nHTTPError = ' + str(error)
        sys.exit(1)
    except urllib2.URLError, error:
        print '\nURLError = ' + str(error)
        sys.exit(1)
    except IOError, error:
        print '\nIOError = ' + str(error)
        sys.exit(1)
    except Exception, error:
        print "\nError: Generic exception!",str(error)
        sys.exit(1)


    # continue as usual
    data=[el.strip('\r\n').split('\t') for el in file(temp_paralogs_filename2,'rt').readlines()]

    data=['\t'.join(sorted(line))+'\n' for line in data if line[1]]
    data=sorted(list(set(data)))

    file(paralogs_filename,'wt').writelines(data)
    
    if options.organism.lower() == "saccharomyces_cerevisiae":
        x = options.organism.upper().split('_')
        templ = "ENS"+x[0][0]+x[1][0:2]+"G"
        data = [line.rstrip("\r\n").split("\t") for line in file(paralogs_filename,"r").readlines() if line.rstrip("\r\n")]
        data = [[templ+line[0].upper(),templ+line[1].upper()] for line in data]
        file(paralogs_filename,"w").writelines(['\t'.join(line)+'\n' for line in data])
    
    
    file(paralogs_header_filename,'w').writelines([el.split('"')[1]+'\n' for el in query2.split('Attribute name =')[1:]])
    os.remove(temp_paralogs_filename1)
    os.remove(temp_paralogs_filename2)
    
    print "End."



