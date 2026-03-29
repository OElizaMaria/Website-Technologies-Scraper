
# Website Technologies Scraper

## Content:
## 1. Results
## 2. Pipeline explanation
## 3. How the solution came to be
## 4. Debate Topics

##        Results

    340 technologies found

    10 domains not found (server error)

##        Pipeline

The Scraper: A get request is sent which returns the html file found at the domain name. In case we get a >500 response (server error) it tries multiple different domains with diferent protocols (such as https and http). It sorts the info using BigSoup library so it has a few categories to match against(scripts, links, meta etc). Afterwards it enters the technology detection logic (detect_tech function) where there is a fast guard that checks if the tech name is in the file, if not it doesn't bother to check the other fingerprints. If it doesnt find any fingerprints it falls back on a Hail Marry attempt, it just tries to match the name of the technology anywhere but the content of the page (titles, headers, scripts etc.). If a technology is found through Hail Marry, it is noted when added to the output file. The code is built to be multi-threaded so it handles the large dataset  to be analyzed. For multi-threading I used the asyncio and aiohttp library, limiting at 50 threads.

The Dictionary Builder: The code scrapes the top 500 technologies from a website and looks for them in the wappalyzer dictionary. To properly work with our scraper and to run smoothly, it cleans the strings to keep them in their simplest form. This removes some fingerprints, but  it helps our program run much faster.


##        How the solution came to be
(all articles mentioned can be found in the ResearchBibliography file)

When I first started this project I had no experience with web scrapers, therefore I had to start by studying how such applications work. I read a GeeksForGeeks[1] article and completed an online tutorial[2] to get a basic understanding of the logic. The next step was finding out how to detect a technology from the scraped data. A few articles came in handy ([3] [4]), in which I read about where technology fingerprints hide. That's when I stumbled on the wappalyzer github repository[5]. Initially I had wanted to write my own dictionary, however considering I had only one week at hand and 300+ technologies to find, I decided it would be wiser to scrape the data, but format it to serve my own implementation of the web scraper.

 I first built the code of the scraper on a small hand-written dictionary, but even than I noticed how slow the code was running. I decided to try multi-threading my code since the get request is a blocking call. I looked into the aiohttp and async libraries and found the GeeksforGeeks explanations to be really helpful ([6][7]). After building my first iteration of the DictionaryBuilder I realized some technologies had few fingerprints and might not be found even if they were present. 
 
 That's when I decided to add the Hail Mary case. Although it is not as strong as simple fingerprinting (reason for which I decided to mark it in the output in case it is decided to be discarded) I still believe it brings value. Since we are not checking the content of the page, only the code, the case of a Hail Mary being detected when  it shouldn't be is very low. This adds a few technologies without being too time-consuming. Since the dataset we are working with is made of 200 domains I decided to limit the number of dictionary entries to 500. I looked for articles which ranked most used technologies so I could increase the odds of them being found in the domains. For the implementation of the code I used this ranking [8].
        
        
##        Debate Topics 

1. What were the main issues with your current implementation and how would you tackle them?
    Main issues:

        1. lack of java script rendering

        2. limited dictionary with limited fingerprints

        3. large files being handled


    Fixes:

        1. for next iterations of the code, a library such as Pupeteer can be used to fully render pages before analyzing the content, to make sure this doesn't slow us down it will be used only as a fallback if no technologies have been found

        2. the library can be widened by including more technologies, either by looking for a wider list of ranked technologies or parsing each letter in the wappalyzer dictionary and choosing a set number of technologies at random. To fix the extra time caused by extra matching operations we could increase the number of threads and parallelizing the fingerprint evaluation

        3. some pages might be very large, for future iterations it would be helpful to limit the amount of the page we load or analyze smaller chunks at a time. Instead of loading the dictionary from a .json file we could use small databases such as SQL or Firebase which would be more efficient 


2. How would you scale this solution for millions of domains crawled in a timely manner (1-2 months)?

Easiest fix would be to move from a single-machine implementation to multiple ones. Instead of running the scraper on one computer with limited concurrency, the workload could be divided across multiple computers that process domains in parallel. Containerization tools such as Docker and Kubernetes could help manage the machines, automatically scaling the number of running instances. We could also prioritize faster detection even if it might give some false positives (for example trying cases such as the Hail Marry one first). ANy local saving logic should be completly removed, opting for online databases for easier handling.


3. How would you discover new technologies in the future?

Any unknown patterns found in the scraped websites could be colected and analyzed by a machine learning model which would categorize them by similarity. AI could also help automatically generate fingerprints for new technologies. Once a potential technology is identified, a model could analyze the html data and convert patterns into possible fingerprints.