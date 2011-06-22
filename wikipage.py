import urllib2
import re
import time

def getRandomPage():
    #time.sleep(1)
    #uncomment the above line if you want to wait 1 second every time you grab a random page
    request = urllib2.Request('http://en.wikipedia.org/wiki/Special:Random') #if you want to start on a specific page just change "Special:Random" to the name of the page you want to start on
    request.add_header('User-agent','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.100 Safari/534.30')
    response = urllib2.urlopen(request)
    return response

def matchTable(string,index): #give it a string and the index where "<table" shows up in the string, and it will find the matching "</table>" in the HTML
    currentIndex = index+1
    tableCount = 1
    while tableCount > 0:
        nextStartTable = string.find('<table',currentIndex)
        nextEndTable = string.find('</table>',currentIndex)
        if nextStartTable < nextEndTable and nextStartTable != -1:
            tableCount = tableCount+1
            currentIndex = nextStartTable+1
        else:
            tableCount = tableCount-1
            currentIndex = nextEndTable+1
    return currentIndex-1

def matchDiv(string,index): #give it a string and the index where "<div class="thumb tright"" or "<div class="thumb tleft"" and it will find the matching "</div>" in the HTML
    currentIndex = index+1
    divCount = 1
    while divCount > 0:
        nextStartDiv = string.find('<div',currentIndex)
        nextEndDiv = string.find('</div>',currentIndex)
        if nextStartDiv < nextEndDiv and nextStartDiv != -1:
            divCount = divCount+1
            currentIndex = nextStartDiv+1
        else:
            divCount = divCount-1
            currentIndex = nextEndDiv+1
    return currentIndex-1
        

def matchParen(string,index): #give it a string and the index of an open parenthesis and it will find the matching closed parenthesis if there is one. If the parentheses are mismatched it gives the index of the end of the paragraph. If there is no end of the paragraph, it gives the end of the document.
    currentIndex = index+1
    parenCount = 1
    while parenCount > 0:
        nextOpen = string.find('(',currentIndex)
        nextClosed = string.find(')',currentIndex)
        endPara = string.find('</p>',currentIndex)
        if endPara < nextClosed and endPara != -1:
            return endPara+3
        elif nextOpen < nextClosed and nextOpen != -1:
            parenCount = parenCount+1
            currentIndex = nextOpen+1
        elif nextClosed < nextOpen and nextClosed != -1:
            parenCount = parenCount-1
            currentIndex = nextClosed+1
        elif nextClosed == -1 and endPara != -1:
            return endPara+3
        else:
            return len(string)-1
    return currentIndex-1

def findNextLink(response): #given a wikipedia page, it finds the first non-italic, non-parenthetical link in the article text
    wikipage = response.read()

    tableIndex = wikipage.find('<table') #find the first table

    while tableIndex != -1: #cut all the tables out
        endtableIndex = matchTable(wikipage,tableIndex)
        wikipage = wikipage[:tableIndex]+wikipage[endtableIndex+8:]
        tableIndex = wikipage.find('<table',tableIndex+1)

    divIndex = wikipage.find('<div class="thumb tright">') #find the first right sidebar

    while divIndex != -1: #cut all the right sidebars out
        enddivIndex = matchDiv(wikipage,divIndex)
        wikipage = wikipage[:divIndex]+wikipage[enddivIndex+6:]
        divIndex = wikipage.find('<div class="thumb tright">',divIndex+1)

    divIndex = wikipage.find('<div class="thumb tleft">') #find the first left sidebar

    while divIndex != -1: #cut all the left sidebars out
        enddivIndex = matchDiv(wikipage,divIndex)
        wikipage = wikipage[:divIndex]+wikipage[enddivIndex+6:]
        divIndex = wikipage.find('<div class="thumb tleft">',divIndex+1)

    pattern = re.compile('<a href=.*?><i>.*?</i></a>') #regex for italic links (in otherwise non-italic text)
    match = pattern.search(wikipage) 

    while match != None: #cut all italic links (in otherwise non-italic text) out
        currentIndex = match.start()
        wikipage = pattern.sub('',wikipage)
        match = pattern.search(wikipage,currentIndex)
        
    pattern = re.compile('<i>.*?</i>') #regex for italic text
    match = pattern.search(wikipage)
    
    while match != None: #cut all italic text out
        currentIndex = match.start()
        wikipage = pattern.sub('',wikipage)
        match = pattern.search(wikipage,currentIndex)
    
    startIndex = wikipage.find('<p>') #we don't care about anything before the first paragraph
    body = wikipage[startIndex:]
    pattern = re.compile('[^_]\(') #we want to cut out parentheticals but not ones that occur inside links, such as County_(US)
    match = pattern.search(body)
    while match != None: #cuts out parentheticals
        openIndex = match.start()+1
        closeIndex = matchParen(body,openIndex)
        body = body[:openIndex]+body[closeIndex+1:]
        match = pattern.search(body,openIndex)
    
    pattern = re.compile('<a href="(/wiki/[^:]*?)"') #regex for a link that does not contain ":" as files uploaded to wikipedia would have
    match = pattern.search(body) #find the first such link
    if match == None: #detects if there is no such link
        print 'no link'
        return None

    urlend = match.group(1) 
    #time.sleep(1)
    #uncomment the above line if you want it to wait 1 second before going to any new link
    request = urllib2.Request('http://en.wikipedia.org'+urlend)
    request.add_header('User-agent','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.100 Safari/534.30')
    response = urllib2.urlopen(request)
    return response

def getName(response): #pass in the wikipedia page, returns the name of the page (according to the URL)
    url = response.geturl()
    wikiIndex = url.find('wiki/')
    titleIndex = wikiIndex + 5
    name = url[titleIndex:]
    return name

def addEdge(currentPage,nextPage): #adds the edge between one page and the next to the .csv file
    f = open(EdgeFile,'a')
    f.write(getName(currentPage)+';'+getName(nextPage)+'\n')
    print getName(currentPage)+';'+getName(nextPage)
    f.close()

def alreadySeen(pageName): #detects if we've already been to the page, based on name
    return pageName in nodeList
    
def makeGraphData(): #picks a random page to start and keeps finding the next link until it hits a page that has already been seen. runLength is the number of chains you want it to find.
    currentPage = getRandomPage()

    for i in range(runLength):
        print '\n'+'chain '+str(i)+'\n' #prints what chain it's on
        while alreadySeen(getName(currentPage)): #if the first page it picked has already been seen it keeps picking random ones until it finds one it hasn't seen.
            currentPage = getRandomPage()
        
        while not alreadySeen(getName(currentPage)): #keeps finding the next link until it's already seen the current page.
            nodeList.append(getName(currentPage)) #keep track of what pages it's been to
            nextPage = findNextLink(currentPage) #finding the next page
            if nextPage != None: #if it found a page
                addEdge(currentPage,nextPage) #add the edge
            else:
                nextPage = getRandomPage() #this is what happens if it couldn't find a link on a page -- it goes to another random page and doesn't add an edge
            currentPage = nextPage

def makeList(): #reads in all the pages it's been to when you've run this in the past and adds it to the list of already seen pages.
    g = open(EdgeFile,'a')
    g.close()
    f = open(EdgeFile,'r')
    wikilist = f.read()
    edgelist = wikilist.split('\n')
    for i in range(len(edgelist)):
        index = edgelist[i].find(';')
        nodeList.append(edgelist[i][:index])

EdgeFile = 'blahblah.csv' #the file you want it to add the edges to
nodeList = []
runLength = 10 #the number of chains you want to find
makeList() #populate the already-seen list
makeGraphData() #find new graph data

