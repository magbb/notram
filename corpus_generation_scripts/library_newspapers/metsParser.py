import os
import argparse
import glob
import ftfy
import langid

from os import path
#from sandboxLogger import SandboxLogger

from xmlHandler import xmlHandler
#s=SandboxLogger("myLogger","logging_config.config")

import json

class parseMets:
    articles = []
    metshandler = None
    altopapermetsfile=""
    paperDir = ""
    currentUrn=""
    year=0
    docworksVersion = ""
    abbyyVersion = ""
    detected_language = ""
    xmlfileinuse=""
    xmlfilehandler=None
    globalOcrWordConfidence=0
    globalPercentageWords98=0
    averageNumberOfWordInArticle=0
    NumberOfArticles=0
    globalNumberOfWords=0
    outputPath = ""
    month = 0
    day = 0
    papername = ""
    errorLogged = False
    filelist = []
    scandate=""


    def __init__(self):
        self.articles = []
        self.metshandler = None
        self.paperDir = ""
        self.altopapermetsfile = ""
        self.currentUrn = ""
        self.year = 0
        self.docworksVersion = ""
        self.abbyyVersion = ""
        self.detected_language = ""
        self.xmlfileinuse = ""
        self.xmlfilehandler = None
        self.globalOcrWordConfidence = 0
        self.globalPercentageWords98 = 0
        self.averageNumberOfWordInArticle = 0
        self.NumberOfArticles = 0
        self.globalNumberOfWords = 0
        self.outputPath = ""
        self.month = 0
        self.day = 0
        self.papername = ""
        self.errorLogged = False
        self.filelist = []
        self.scandate = ""

    def getFileNameFromblockId(self,blockid):
        pageno=blockid.split("_")[0]
        nodigits=len(pageno)
        page=int(pageno[1:])
        return self.filelist[page-1]
        #print(blockid)
        #print(nodigits)
        #print(pageno)
        pageid=""
        if (nodigits == 2):
            pageid="00" + pageno[1:]
        if (nodigits == 3):
            pageid = "0" + pageno[1:]
        if (nodigits == 4):
            pageid = pageno[1:]
        criterium="/*_" + pageid + "_[a-z]*.xml"
        #print(criterium)
        filename=glob.glob(self.paperDir + criterium )
        if len(filename) == 0:
            if (nodigits == 2):
                pageid = "0" + pageno[1:]
            if (nodigits == 3):
                pageid =  pageno[1:]
            criterium = "/*_" + pageid + "_[a-z]*.xml"
            #print(criterium)
            filename = glob.glob(self.paperDir + criterium)
        #print(pageid + " " + self.paperDir + criterium)
        #print(filename)
        return filename[0].split("/")[-1]


    def buildArticleReferences(self,metsfilename):
        NSMETS = 'http://www.loc.gov/METS/'
        self.articles = []
        cnt=0
        structmaps = self.metshandler.findAllNodes("{%s}structMap[@TYPE='LOGICAL']/{%s}div/{%s}div/{%s}div/{%s}div/{%s}div" % (NSMETS, NSMETS, NSMETS, NSMETS, NSMETS, NSMETS))
        for s in structmaps:
            #cnt += 1
            #print(str(cnt) + " " + str(len(structmaps)))
            if s.attrib["TYPE"] == 'ARTICLE':
                ref = self.metshandler.findInSub(s, ".//{%s}area" % (NSMETS))
                label = ""
                if "LABEL" in s.attrib:
                    label = str(s.attrib["LABEL"])
                else:
                    label = "<null>"
                for r in ref:
                    # print (s.attrib["DMDID"] + ":" +r.attrib["BEGIN"] + ":" + r.attrib["FILEID"])
                    thestring = ""
                    begin = str(r.attrib["BEGIN"])
                    if "_TB" in begin:
                        if (self.findFileNamefromAltoReference(r.attrib["FILEID"]) ==""):
                            filename=self.getFileNameFromblockId(str(r.attrib["BEGIN"]))
                            thestring = str(s.attrib["DMDID"]) + ";;;;;" + label + ";;;;;" + str(
                                r.attrib["BEGIN"]) + ";;;;;" + filename
                        else:
                            thestring = str(s.attrib["DMDID"]) + ";;;;;" + label + ";;;;;" + str(
                                r.attrib["BEGIN"]) + ";;;;;" + str(self.findFileNamefromAltoReference(r.attrib["FILEID"]))
                    # print(thestring)
                    self.articles.append(thestring)


    def findFileNamefromAltoReference(self,altoreference):

        NSMETS = 'http://www.loc.gov/METS/'
        NSXLINK = 'http://www.w3.org/TR/xlink'
        attribKey = "{%s}href" % (NSXLINK)

        #self.handler2 = xmlHandler(self.altopapermetsfile, rootNodeName="alto")
        Flocat = self.metshandler.findAllNodes("{%s}fileSec/{%s}fileGrp[@ID='ALTOGRP']/{%s}file[@ID='%s']/{%s}FLocat" % (NSMETS, NSMETS, NSMETS, altoreference, NSMETS))
        if "{%s}href" % (NSXLINK) not in Flocat[0].attrib:
            NSXLINK = 'http://www.w3.org/1999/xlink'
            attribKey = "{%s}href" % (NSXLINK)

        #print(self.paperDir + "/" + Flocat[0].attrib[attribKey].rsplit('/', 1)[-1])
        if path.exists(self.paperDir + "/" + Flocat[0].attrib[attribKey].rsplit('/', 1)[-1]) == False:
            #print("Not exists: " + Flocat[0].attrib[attribKey])
            #print("Mets file: " + self.altopapermetsfile)
            #print(self.altopapermetsfile.split("-")[0])
            if self.errorLogged == False:
                f=open("NewspaperError.log","a+")
                f.write("Mets File: " + self.altopapermetsfile.rsplit('/', 1)[-1] + " has illegal file references.\n")
                f.close()
                self.errorLogged = True

            part1=self.altopapermetsfile.split("-")[0]
            part2=Flocat[0].attrib[attribKey].split("-")[1]
            newname=part1 + "-" + part2
            return newname.rsplit('/', 1)[-1]

        return (Flocat[0].attrib[attribKey].rsplit('/', 1)[-1])

    def findWCForBlockId(self, blockid, filename):
        handler = None
        if filename==self.xmlfileinuse:
            handler=self.xmlfilehandler
        else:
            handler = xmlHandler(inputXmlFile=filename, rootNodeName="alto")
            self.xmlfileinuse = filename
            self.xmlfilehandler =handler

        if self.docworksVersion == "":
            docworksVersionNode = handler.findAllNodes(
                "Description/OCRProcessing/preProcessingStep/processingSoftware/softwareVersion")
            self.docworksVersion = docworksVersionNode[0].text
        if self.abbyyVersion == "":
            abbyyVersionNode = handler.findAllNodes(
                "Description/OCRProcessing/ocrProcessingStep/processingSoftware/softwareVersion")
            if abbyyVersionNode != []:
                self.abbyyVersion = abbyyVersionNode[0].text
            else:
                self.abbyyVersion = "none"

        blockid = blockid.replace(';', '')
        # print(blockid, filename)

        TBNodes = handler.findAllNodes("Layout/Page/PrintSpace/TextBlock[@ID='%s']" % (blockid))

        contentnodes = handler.findInSub(TBNodes[0], ".//String")
        thestr = ""
        localConfidence = 0
        cnt = 0
        cnt98 = 0
        for c in contentnodes:
            if "SUBS_TYPE" in c.attrib and c.attrib["SUBS_TYPE"] == "HypPart1":
                localConfidence += float(c.attrib["WC"])
                cnt += 1
                if localConfidence >= 0.98:
                    cnt98+=1
            else:
                localConfidence += float(c.attrib["WC"])
                cnt += 1
                if localConfidence >= 0.98:
                    cnt98+=1
        if cnt == 0:
            return 0,0
        else:
            return localConfidence / cnt , cnt98/cnt

    def findContentForBlockId(self,blockid,filename):
        #print(filename)
        blockid=blockid.replace(';', '')
        #print(blockid, filename)
        handler = None
        if filename==self.xmlfileinuse:
            handler=self.xmlfilehandler
        else:
            handler = xmlHandler(inputXmlFile=filename, rootNodeName="alto")
            self.xmlfileinuse = filename
            self.xmlfilehandler =handler

        TBNodes = handler.findAllNodes("Layout/Page/PrintSpace/TextBlock[@ID='%s']" % (blockid))

        contentnodes = handler.findInSub(TBNodes[0], ".//String" )
        thestr=""

        for c in contentnodes:
            if "SUBS_TYPE" in c.attrib and c.attrib["SUBS_TYPE"] == "HypPart1":
                thestr+=c.attrib["CONTENT"]
            else:
                thestr+= c.attrib["CONTENT"]
                thestr+=" "
        #print(thestr.rstrip().lstrip())
        return  thestr


    def writeArticleTofile(self,articleText,filename,articlewc,percentageOver98):
        noOfWords=len(articleText.split())
        self.NumberOfArticles += 1
        self.globalNumberOfWords+=noOfWords
        f = open(filename+".txt", "w+")
        #rint ("File Written:" + filename+".txt")
        #print(str(len(articleText.split())))
        f.write(articleText)
        f.close()
        self.detectLanguage(articleText)
        self.metaWriter(filename,articlewc,percentageOver98,noOfWords)


    def detectLanguage(self,inputext):
        res = str(langid.classify(inputext))
        # res = langid.classify("File with path to all books")
        # print(res)
        self.detected_language = res.split(",")[0].replace("(", "").replace("'", "")

    def writeMasterMetafile(self):

        if self.NumberOfArticles == 0:
            gowc=0
            gpwc=0
            anowc=0
        else:
            gowc = str(round(self.globalOcrWordConfidence/self.NumberOfArticles, 2))
            gpwc = str(round(self.globalPercentageWords98/self.NumberOfArticles, 2))
            anowc = str(round(self.globalNumberOfWords/self.NumberOfArticles,2))

        jsonrecord = {
            "urn": self.currentUrn,
            "publishYear": self.year,
            "docworksVersion": str(self.docworksVersion),
            "abbyyVersion": str(self.abbyyVersion),
            "scandate": str(self.scandate),
            "globalOcrWordconfidence": gowc,
            "globalPercentageWords98confidence": gpwc,
            "numberOfArticles":str(self.NumberOfArticles),
            "avrageNumberOfWordsInArticle": anowc
        }
        filenameMeta = self.outputPath + "/" + self.currentUrn + "-master.meta"
        print("Writing master meta file:" + filenameMeta)
        currfptrMeta = open(filenameMeta, "w+")
        json.dump(jsonrecord, currfptrMeta)
        currfptrMeta.flush()
        currfptrMeta.close()

    def metaWriter(self,filename,articlewc,percentageOver98,noWords):
        jsonrecord = {
            "urn": self.currentUrn,
            "publishYear": self.year,
            "languageDetected": self.detected_language,
            "docworksVersion": str(self.docworksVersion),
            "abbyyVersion": str(self.abbyyVersion),
            "scandate":str(self.scandate),
            "ocrWordconfidence": str(round(articlewc, 2)),
            "percentageWords98confidence": str(round(percentageOver98, 2)),
            "numberOfWordsInArticle": str(noWords)
        }

        #print(jsonrecord)
        filenameMeta = filename + ".meta"
        currfptrMeta = open(filenameMeta, "w+")
        json.dump(jsonrecord, currfptrMeta)
        # print(jsonrecord)
        currfptrMeta.flush()
        currfptrMeta.close()

    def writeArticles(self):
        print("writearticles")
        i = 0
        prevarticleid = ""
        articleText = ""
        filename = ""
        # print(args.avisdir)
        parts=0
        partWC=0
        percentOver98=0
        articleid = ""
        while i < len(self.articles):
            # print(articles[i])
            count = len(self.articles[i].split(";;;;;"))
            if (count < 4):
                i += 1
                continue

            articleid, title, blockid, filename = self.articles[i].split(";;;;;")
            #print("ArticleID:"+articleid+ " Title:" + title + " Blockid:" + blockid + " Filename" + filename)
            if articleid != prevarticleid and prevarticleid == "":
                articleText = self.findContentForBlockId(blockid, self.paperDir + "/" +filename)
                partWC,percentageOver98= self.findWCForBlockId(blockid, self.paperDir + "/" + filename)
                percentOver98=percentageOver98
                prevarticleid = articleid
                parts = 1
            elif articleid == prevarticleid:
                articleText += self.findContentForBlockId(blockid, self.paperDir + "/" +filename)
                blockWC,percentageOver98= self.findWCForBlockId(blockid, self.paperDir + "/" + filename)
                partWC+=float(blockWC)
                percentOver98+=float(percentageOver98)
                parts+=1
            else:
                if (parts == 0):
                    parts=1
                if articleid == None or articleid == "":
                    articleid = "noarticleid_noarticleid"
                outputfilename = self.outputPath +"/" + filename.split(".")[0] + "_" + articleid.split("_")[1]

                self.writeArticleTofile(articleText, outputfilename,partWC/parts,percentOver98/parts)
                self.globalOcrWordConfidence += (partWC/parts)
                self.globalPercentageWords98 += (percentOver98/parts)
                percentOver98=0
                prevarticleid = articleid
                articleText = self.findContentForBlockId(blockid, self.paperDir + "/" +filename)
                partWC,percentageOver98 = self.findWCForBlockId(blockid, self.paperDir + "/" + filename)
                parts = 1
            i += 1

        # print("********************************** LAST *******************************")
        if (parts == 0):
            parts = 1
        if articleid == None or articleid == "":
            articleid = "noarticleid_noarticleid"
        outputfilename = self.outputPath +"/" + filename.split(".")[0] + "_" + articleid.split("_")[1]
        self.writeArticleTofile(articleText, outputfilename,partWC/parts,percentOver98/parts)

    def processNewspaper(self,paperDir,outputDir):
        NSMETS = 'http://www.loc.gov/METS/'
        self.paperDir=paperDir
        self.errorLogged = False
        for file in glob.glob(self.paperDir+"/*.xml"):
            if "mets.xml" not in file:
                self.filelist.append(file.split("/")[-1])
            else:
                self.altopapermetsfile = file
        self.filelist.sort()
        #print(self.filelist)
        #print(self.filelist[1])
        files = glob.glob(paperDir +"/*mets.xml")
        file=files[0]
        #for file in glob.glob(paperDir +"/*mets.xml"):
            #print(file)
        relativefilename=file.split("/")[-1]
        self.currentUrn=relativefilename.split("_")[0] + "_" + relativefilename.split("_")[3]
        self.altopapermetsfile = file
        self.outputPath=outputDir
        #print("mets file: " + self.altopapermetsfile)
        yearmonthday = relativefilename.split("_")[3]
        year=yearmonthday[0:4]
        self.year=year
        self.month=yearmonthday[4:6]
        self.day = yearmonthday[6:8]
        self.papername=relativefilename.split("_")[0]
        self.outputPath = outputDir + "/" +str(self.year) + "/" +str(self.month) + "/" +str(self.day)  + "/"+ str(self.papername)
        if not os.path.exists(self.outputPath):
            os.makedirs(self.outputPath)
        self.metshandler = xmlHandler(inputXmlFile=file, rootNodeName="alto")
        metsHdr =self.metshandler.findAllNodes("{%s}metsHdr" % (NSMETS))
        dateonly=metsHdr[0].attrib["CREATEDATE"].split("T")

        self.scandate=dateonly[0].split("-")[2]+dateonly[0].split("-")[1]+dateonly[0].split("-")[0]
        #print(self.scandate)

        r = self.metshandler.getRootNode()
        #self.metshandler.printElement(r)
        #NSXLINK = "http://www.loc.gov/METS/ //Produksjon8.nb.no/docWORKS/schema/mets-metae.xsd"
        #attribKey = "{%s}xlink" % (NSXLINK)
        # print(r.attrib[attribKey])
        #print("before")
        self.buildArticleReferences(file)
        #print("after")
        self.writeArticles()
        self.writeMasterMetafile()

if __name__ == '__main__':

        parser = argparse.ArgumentParser()
        parser.add_argument('paperdir', help='Avis dir')
        parser.add_argument('outputdir', help='Dir to place output articles')
        args = parser.parse_args()
        p=parseMets()
        p.processNewspaper(args.paperdir,args.outputdir)











