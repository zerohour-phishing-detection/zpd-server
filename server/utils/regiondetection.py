import cv2
import pytesseract
import os.path
import sys
import sqlite3
import jellyfish as jf
import time
import numpy as np
import scipy.stats as ss
from PIL import Image
from scipy.stats.mstats_basic import kurtosis
from pywt import dwt2
import random
import math

# Setup logging
from utils.customlogger import CustomLogger
main_logger = CustomLogger().main_logger


def count_colours(src):
    unique, counts = np.unique(src.reshape(-1, src.shape[-1]), axis=0, return_counts=True)
    return (len(unique), np.amax(counts, initial=0)/max(1,np.sum(counts))*100)

def intensity_hist(src):
    return 1

def getText( region , invert=True):
    main_logger.debug("Starting OCR")
    ocr_config = r'-c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ! --psm 4'
    gray = cv2.cvtColor(region,cv2.COLOR_BGR2GRAY)
    cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU,gray)
    if invert:
        cv2.bitwise_not(gray,gray)

    text = pytesseract.image_to_string(gray, config=ocr_config)

    main_logger.debug("Extracted: '" + text + "'")
    return text

def checkBlacklist( word , similaritythreshold):
    for badword in blacklist:
        dist = jf.levenshtein_distance(word.upper(), badword.upper())
        if (dist < similaritythreshold):
            main_logger.debug("Similarity ( " + str(dist) + " ) below threshold ( " + str(similaritythreshold) + " ) of a forbidden word: '" + word + "' looks like '" + badword +  "'")
            return True
    return False

def regioncontraints(region, margin, x, y, height_image, width_image):
    "performs checks to see if the region is a candidate"
    return True
    # Example of using Height/Width/Area as filter
    h, w, c = region.shape
    h_percent = h / height_image * 100
    w_percent = w / width_image * 100
    x_percent = x / width_image * 100
    y_percent = y / height_image * 100

    if (h_percent < 2.865 or h_percent > 78.125):
        return False
    if (w_percent < 2.148 or w_percent > 58.594):
        return False
    if (h_percent*w_percent < 0.1 or h_percent*w_percent > 3.697):
        return False
    if (x_percent > 87.891): #x_percent < 5.859 or 
        return False
    if (y_percent > 95.052): #y_percent < 2.604 or
        return False

    # Example of the colour count and dominant colour percentage
    ccnt, pct = count_colours(region)
    if pct < 4 or pct > 82:
        return False
    if ccnt < 30 or ccnt > 8572:
        return False

    # OCR can be added to the filter like this:
    regionT = region[margin:-margin, margin:-margin]
    text = getText(regionT).strip()
    if len(text) > 2:
        if checkBlacklist(text, 3):
            return False

    text = getText(regionT,False).strip()
    if len(text) > 2:
        if checkBlacklist(text, 3):
            return False
    return True

def _findregions(image, imgpath, draw=True, highlightname="Highlight", invert=True):
    "Finds ALL regions in the linked image"

    if draw:
        drawimg = np.copy(image)

    main_logger.debug("Obtaining grayscale version of image")
    img = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    if draw:
        cv2.imwrite(f"{highlightname}-0-grey.png", img)
        
    main_logger.debug("Thresholding the image")
    if invert:
        cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU,img)
    else:
        cv2.threshold(img, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU,img)
    
    if draw:
        cv2.imwrite(f"{highlightname}-0-tresh.png", img)

    main_logger.debug("Dilating")
    img = cv2.dilate(img, cv2.getStructuringElement(cv2.MORPH_RECT, (7, 5)), iterations=1);
    if draw:
        cv2.imwrite(f"{highlightname}-1-dilating.png", img)

    main_logger.debug("Morphing to merge close area's")
    #img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (7, 4)))
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (5,5)))
    if draw:
        cv2.imwrite(f"{highlightname}-2-inter.png", img)

    main_logger.debug("Eroding")
    img = cv2.erode(img, cv2.getStructuringElement(cv2.MORPH_RECT, (4, 4)), iterations=1);
    if draw:
        cv2.imwrite(f"{highlightname}-3-eroding.png", img)

    main_logger.debug("Finding contours")
    contours, hier = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    main_logger.debug("Storing valid contours")
    roi = []
    count = 0
    if len(contours) != 0:
        for i,c in enumerate(contours):
            [x,y,w,h] = cv2.boundingRect(c)

            # Adding small padding to image for slight context and better search accuracy
            margin=5
            r = image[y-margin:y+h+margin, x-margin:x+w+margin]

            image_width, image_height = Image.open(imgpath).size

            if(regioncontraints(r, margin, x, y, image_height, image_width)):
                ccnt, pct = count_colours(r)
                # also get a greyscale version of the region for the other attributes
                # (see paper by Evdoxios Baratis and Euripides G.M. Petrakis why this is)

                if (r.size == 0):
                    continue
                r_grey = cv2.cvtColor(r, cv2.COLOR_BGR2GRAY)

                # Image info
                mean = np.mean(r_grey, axis=None)
                std = np.std(r_grey, axis=None)
                skew = ss.skew(r_grey, axis=None)
                kurtosis = ss.kurtosis(r_grey, axis=None)
                entropy = ss.entropy(r_grey, axis=None)

                #Otsu threshold
                otsu = 0
                if invert:
                    otsu = cv2.threshold(r_grey, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)[0]
                else:
                    otsu = cv2.threshold(r_grey, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)[0]

                # Energy
                _, (cH, cV, cD) = dwt2(r_grey.T, 'db1')
                energy = (cH**2 + cV**2 + cD**2).sum()/r_grey.size
                if math.isnan(energy):
                    energy = 0.0
                # Number of shades of grey
                int_hist = cv2.calcHist([r_grey], [0], None, [256], [0, 256]).flatten()
                occupied_bins = np.count_nonzero(int_hist)
                if draw:
                    cv2.rectangle(drawimg,(x-margin,y-margin),(x+w+margin,y+h+margin),(0,0,255),1)

                if len(hier) > 0:
                    roi.append((r, i, x, y, ccnt, pct, hier[0][i], invert, mean, std, skew, kurtosis, entropy, otsu, energy, occupied_bins))
                else:
                    roi.append((r, i, x, y, ccnt, pct, [-2, -2, -2, -2], invert, mean, std, skew, kurtosis, entropy, otsu, energy, occupied_bins))
                count += 1
    if draw:
        cv2.imwrite(f"{highlightname}.png", drawimg)
        main_logger.debug("Wrote image highlighting the regions to: " + highlightname)
    return roi

def findregions( imgpath, draw=True, recursivedraw=False, subregiondraw=False, highlightname="Highlight"):
    main_logger.debug("Loading image: " + imgpath)
    image = cv2.imread(imgpath, 1)
    imgdata = [count_colours(image), image.shape[0], image.shape[1]]

    regions = _findregions(image, imgpath, draw=(draw & recursivedraw), highlightname=f"{highlightname}.allregions.1", invert=True)
    regions += _findregions(image, imgpath, draw=(draw & recursivedraw), highlightname=f"{highlightname}.allregions.2", invert=False)

    roi = []
    # Find containers only
    for idx, region in enumerate(regions):
        h, w, _ = region[0].shape
        child = False
        for idx2, region2 in enumerate(regions):
            #don't need to check against itself
            if idx==idx2:
                continue
            h2, w2, _ = region2[0].shape
            if region[2] >= region2[2] and (region[2]+w <= region2[2]+w2):
                # On x axis region1 is contained within region2
                if region[3] >= region2[3] and (region[3]+h <= region2[3]+h2):
                    # On y axis region 1 is contained within region2
                    #child = True
                    continue
        if not child:
            roi.append(region)

    if draw:
        drawimg = np.copy(image)
        for idx, region in enumerate(roi):
            main_logger.debug("Drawing region #{idx}")
            h,w,_ = region[0].shape
            x = region[2]
            y = region[3]
            color_int = random.randint(1, 3)
            color = (0,0,0)
            if color_int == 1:
                color = (0,0,255)
            elif color_int == 2:
                color = (0,255,0)
            else:
                color = (255,0,0)
            flip = (random.randint(0, 1) == 1)
            cv2.rectangle(drawimg,(x-5,y-5),(x+w-5,y+h-5),color,1)
            if region[7]:
                text = "-" + str(region[1])
            else:
                text = str(region[1])
            if flip:
                cv2.putText(drawimg, text, (x+w-random.randint(-5, 5), y+h-random.randint(-5, 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            else:
                cv2.putText(drawimg, text, (x-random.randint(-5, 5), y-random.randint(-5, 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            if subregiondraw:
                cv2.imwrite(f"{highlightname}.subregion.{idx}.png", region[0])
        cv2.imwrite(os.path.join(os.path.dirname(os.path.realpath(imgpath)),f"{highlightname}.png"), drawimg)
    return roi, imgdata

blacklist = ['Sign', 'Support', 'rememberme', 'encryption', 'SecurityPolicy', 'copyright', 'SignOut', 'Inloggen', 'Send', 'Okay', 'Password', 'Accept', 'Login', 'Pay', 'Akkoord', 'Next', 'Continue', 'Logon', 'Gettheapp', 'news', 'weiter', 'search', 'sign on', 'email', 'confirm', 'createnewaccount', 'get started', 'submit', 'einloggen', 'sign up', 'learn more', 'join', 'enter here', 'enterpassword', 'share', 'home', 'register', 'download', 'joinnow', 'enroll', 'enrollnow', 'Agree', 'tell me more', 'freedownload', 'share', 'suivant', 'emailaddress']