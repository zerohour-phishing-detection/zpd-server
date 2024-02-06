# python -m pip install tldextract
import tldextract
import time
import requests
import random
import csv

def read_urls(path=None):

    if not path:
        # list of test URLs [URL,title]
        urls = [
        ['https://versicherung.ge-be-in.de/startseite', "Sterbegeldversicherung seit 1923 - GE·BE·IN Versicherungen"], 
        ['https://idsrv.lv1871.de/Login', '"Lebensversicherung von 1871 a. G. München"'],
        ['http://www.rogerebert.com/reviews/reservoir-dogs-1992', 'Reservoir Dogs movie review &amp; film summary (1992) | Roger Ebert'],
        ['http://www.kuselit.de/', ':: Kuselit Verlag :: Rechtsbibliografie'],
        ['http://www.ullapoolholidayhomes.com/', 'Holiday Accommodation Self Catering Cottages | Ullapool Scotland NC500'],
        ['http://www.art-und-tat.de/', 'Veronika Jakob Grafikdesign'],
        ['http://www.tuffies.co.uk/', 'Buy Luxury Dog Beds UK Online | British Handmade Heavy Duty &amp; Chew Proof Dog Beds | Tuffies'],
        # ['http://www.comune.pietraperzia.en.it/', 'Comune di Pietraperzia'],
        ['http://www.traditieialomita.ro/', 'Tradiție și Modernism – Centrul Județean pentru Conservarea și Promovarea Culturii Tradiționale Ialomița'],
        ['http://www.theglenlyngorge.co.uk/', '\n']
        #['http://www.kronos.co.uk/', 'Workforce Management and HCM Cloud Solutions | Kronos UK']
        ]

        return urls

    urls = []

    with open(path, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',') # encoding='utf-8'
        next(reader) # skip header    
        for row in reader:
            # print("Reading: " + ', '.join(row))
            url_pair = [row[0],row[1]]
            urls.append(url_pair)

    return urls

def write_sample(fake_urls,benign_urls):
    with open('./' + 'data/fake_urls.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(['url','title'])
        writer.writerows(fake_urls)

    with open('./' + 'data/benign_urls.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(['url','title'])
        writer.writerows(benign_urls)

def get_starting_url(file):
    f = open(file, "r")
    return f.read()

def set_starting_url(file,index,close=True):
    f = open(file, "w")
    f.write(index)
    if close:
        f.close()

def split_list(a_list):
    half = len(a_list)//2
    return a_list[:half], a_list[half:]

def evaluate(urls, index_writer, fake=True, starting_url=0, test=False):
    nof_skipped_samples = 0

    i = 0 if not starting_url else int(starting_url)
    # if not starting_url:
    #     i = 0
    # else:
    #     i = int(starting_url)

    # for url in urls:
    for url in urls[i:len(urls)]:
        if not url[1].strip():
            print("Stripped title of " + url[0] + " is empty. Going on.")
            nof_skipped_samples = nof_skipped_samples + 1
            i = i + 1
            continue
        else:
            url[1] = url[1].strip()
            #strip from quotes
            url[1] = url[1].strip('\"')

        # i = i + 1
        # create json:
        if fake: #request for fake phishing site
            current_json = {
            "URL": url[0],
            "uuid": str(client_uuid),
            "pagetitle": url[1],
            # "image64": "",
            "phishURL" : "http://bogusurl" + str(i) + ".co.uk"
            }
        else: #request for benign site
            current_json = {
            "URL": url[0],
            "uuid": str(client_uuid),
            "pagetitle": url[1],
            # "image64": "",
            "phishURL" : ""
            }

        # test_json = {
        # "URL": "https://idsrv.lv1871.de/Login",
        # "uuid": "63054094-01c4-11ed-b939-0242ac120002",
        # "pagetitle": "Lebensversicherung von 1871 a. G. München",
        # "image64": "",
        # "phishURL" : "http://bogusurl1.co.uk"
        # }

        if fake:
            print(str(i) + ': Sent request for ' + url[0] + ' with fakeURL ' + str(current_json["phishURL"]))
        else:
            print(str(i) + ': Sent request for ' + url[0] + ' with benignURL ' + str(current_json["URL"]))

        try:
            res = requests.post('http://192.168.56.100:5000/api/v1/url', json=current_json, timeout = 1200)
        except requests.Timeout as err:
            print(str(url[0]) + " timed out. Going on.")
            print(err)
            nof_skipped_samples = nof_skipped_samples + 1
            i = i +1
            continue
        except requests.RequestException as err:
            print("Error with requets: ")
            print(err)
            print(url[0] + " got error. Going on.")
            nof_skipped_samples = nof_skipped_samples + 1
            i = i + 1 
            continue

        print('Response from antiPhish server: ', res.text)

        #write current processed index to file
        if not test:
            set_starting_url(path_fake_counter,str(i)) if fake else set_starting_url(path_benign_counter,str(i))
        else:
            set_starting_url("data/test_starting.txt",str(i))

        # sleep every x calls to not trigger Google limiting
        if i % 3 == 0:
            sleep_time = random.randint(20,30)
            sleep_time = 1
            print("Sleeping " + str(sleep_time) + " seconds.")
            time.sleep(sleep_time)
        
        # go to next URL
        i = i + 1

    #write last processed index to file again when finished
    if not test:
        set_starting_url(path_fake_counter,str(i)) if fake else set_starting_url(path_benign_counter,str(i))
    else:
        set_starting_url("data/test_starting.txt",str(i))

## global constants ##
test = False
write_samples = False

path_urls = "data/urls.csv" if not test else None
path_fake_urls = "data/fake_urls.csv"# if not test else None
path_benign_urls = "data/benign_urls.csv"# if not test else None
path_fake_counter = "data/last_fake_url.txt"
path_benign_counter = "data/last_benign_url.txt"

fake_starting_url = get_starting_url(path_fake_counter) if not test else 0
benign_starting_url = get_starting_url(path_benign_counter) if not test else 0


# client_uuid = "73054094-01c4-11ed-b939-0242ac120002" #first attempt
# client_uuid = "simulation-" + time.strftime("%H:%M:%S %a, %d-%b-%Y", time.gmtime())
client_uuid = "simulation_1"
# total number of urls to evaluate (split 50/50 for fake/benign)
#urls_to_process = 2274 if not test else None
urls_to_process = None
    
def main():
    startTime = time.time()
    print("Starting time: " + time.strftime("%H:%M:%S %a, %d-%b-%Y", time.gmtime()))

    # get all available urls
    urls = read_urls(path_urls)
    print("Read " + str(len(urls)) + " URLs from " + str(path_urls))

    if not urls_to_process:
        nof_urls = len(urls)
    else:
        nof_urls = urls_to_process
    print("Total number of URLs to evaluate: " + str(nof_urls) + "\n")

    if not test:
        if not write_samples:
            # read fake phish and benign urls
            print("Reading already sampled URLs.")
            fake_urls = read_urls(path_fake_urls)
            print("Read " + str(len(fake_urls)) + " fake URLs from " + str(path_fake_urls))

            benign_urls = read_urls(path_benign_urls)
            print("Read " + str(len(benign_urls)) + " benign URLs from " + str(path_benign_urls))
        else:
            # sample 50% fake_urls and 50% benign_urls
            sampled_urls = random.sample(urls,nof_urls)
            fake_urls, benign_urls = split_list(sampled_urls)
            write_sample(fake_urls,benign_urls)

        # evaluate
        print("Starting fake url:  " + str(fake_starting_url))
        print("Beginning to evaluate " + str(len(fake_urls) - int(fake_starting_url)) + " fake URLs.")

        f = open(path_fake_counter, "w")
        evaluate(fake_urls, f, True, fake_starting_url)
        f.close()

        # sleep 5 min before starting the benign urls
        #time.sleep(300)

        print("Starting benign url:  " + str(benign_starting_url))
        print("Beginning to evaluate " + str(len(benign_urls) - int(benign_starting_url)) + " benign URLs.\n")

        f = open(path_benign_counter, "w")
        evaluate(benign_urls, f, False, benign_starting_url)
        f.close()
    else:
        test_starting_url = get_starting_url("data/test_starting.txt")
        print("Starting test url:  " + str(test_starting_url))
        print("Running test with " + str(nof_urls - int(test_starting_url)) + " URLs \n")

        f = open("data/test_starting.txt", "w")
        evaluate(urls, f, False, test_starting_url, True)
        f.close()

    stopTime = time.time()
    print("Ending time: " + time.strftime("%H:%M:%S %a, %d-%b-%Y", time.gmtime()))
    print(f"Finished. Time elapsed for complete evaluation is {round((stopTime - startTime)/60, 2)} min\n")

if __name__ == '__main__':
    main()