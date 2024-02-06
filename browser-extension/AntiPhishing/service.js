chrome.runtime.onInstalled.addListener(() => {
    console.log('Installed');

    // generate unique ID for server-side cache if not already exists
    chrome.storage.local.get(['uuid'], function (result) {
        if (result.uuid == "" || result.uuid == null) {
            uuid_val = create_UUID();
            chrome.storage.local.set({
                uuid: uuid_val
            }, function () {
                console.log('uuid set to ' + uuid_val);
            });
        }
    });

});

// Yes, a UUID that is based on Math.random is not a good uuid
// For the purposes it is used, it is more than fine
function create_UUID() {
    var dt = new Date().getTime();
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = (dt + Math.random() * 16) % 16 | 0;
        dt = Math.floor(dt / 16);
        return (c == 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
    return uuid;
}

chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
    //console.log(sender.tab ?
    //    "from a content script: " + sender.tab.url :
    //    "from the extension");

    updateBadge();

    // if tab is not active, we can't get the screenshot
    // So we leave it to the OnActivated listener
    if (!sender.tab.active) {
        return;
    }

    // Get screenshot and call process
    //chrome.tabs.captureVisibleTab(sender.tab.windowId, {"format": "png"}, function(dataUrl) {
    //process(sender.tab.id, sender.tab.url, sender.tab.title, dataUrl);
    //});

    chrome.storage.local.get(['uuid'], function (result) {
        process(sender.tab.id, sender.tab.url, sender.tab.title, "", result.uuid);
    });

});

// Clear local storage on fresh chrome startup
chrome.runtime.onStartup.addListener(() => {
    // Clear on startup?
    //chrome.storage.local.clear(); // doesn't work well as it removes also the UUID
    clearUrlStorage();
    updateBadge();
});

// Called when active tab changes
/*
chrome.tabs.onActivated.addListener(function(activeInfo) {
    chrome.tabs.get(activeInfo.tabId, function(tab) {
        var urlkey = tab.url;
        //console.log("tab with url " + urlkey + " came into view");

        if (tab.status != "complete") {
            // Tab is not ready loading yet. Can't get screenshot yet.
            // Leave it to the content script message or when tab comes
            // into view again.
            return;
        }
        const { hostname } = new URL(tab.url);
        console.log(hostname);

        if (!hostname.includes("google.") && !hostname.includes("chrome://") && hostname.includes(".")) {
            // Get screenshot and call process
            chrome.tabs.captureVisibleTab(activeInfo.windowId, {"format": "png"}, function(dataUrl) {
                process(tab.id, urlkey, tab.title, dataUrl);
            });
        }
    });

});
*/

function process(tabid, urlkey, title, screenshot, uuid) {
    // check if url still needs processing
    chrome.storage.local.get({
        urlCacheIds: []
    }, function (result) {
        var i;
        for (i = 0; i < result.urlCacheIds.length; i++) {
            if (result.urlCacheIds[i].urlId == urlkey) {

                // check status of tab for the icon change
                if ((result.urlCacheIds[i].status == 'queued') || (result.urlCacheIds.status == 'processing')) {
                    chrome.action.setIcon({
                        path: {
                            "16": "/images/waiting_16.png",
                            "32": "/images/waiting_32.png",
                            "64": "/images/waiting_64.png",
                            "128": "/images/waiting_128.png"
                        },
                        tabId: tabid
                    });
                } else if (result.urlCacheIds[i].status == "inconclusive") {
                    chrome.action.setIcon({
                        path: {
                            "16": "/images/questionmark_16.png",
                            "32": "/images/questionmark_32.png",
                            "64": "/images/questionmark_64.png",
                            "128": "/images/questionmark_128.png"
                        },
                        tabId: tabid
                    });
                } else if (result.urlCacheIds[i].status == "phishing") {
                    chrome.action.setIcon({
                        path: {
                            "16": "/images/phishing_16.png",
                            "32": "/images/phishing_32.png",
                            "64": "/images/phishing_64.png",
                            "128": "/images/phishing_128.png"
                        },
                        tabId: tabid
                    });
                } else if (result.urlCacheIds[i].status == "not phishing") {
                    console.log("Icon set to not_phishing");
                    chrome.action.setIcon({
                        path: {
                            "16": "/images/not_phishing_16.png",
                            "32": "/images/not_phishing_32.png",
                            "64": "/images/not_phishing_64.png",
                            "128": "/images/not_phishing_128.png"
                        },
                        tabId: tabid
                    });
                }

                chrome.tabs.sendMessage(tabid, {
                    status: result.urlCacheIds[i].status,
                    url: urlkey
                }, function (response) {
                    // No response
                });
                if ((result.urlCacheIds[i].status != 'queued') && (result.urlCacheIds.status != 'processing')) {
                    return;
                }
            }
        }

        chrome.action.setIcon({
            path: {
                "16": "/images/waiting_16.png",
                "32": "/images/waiting_32.png",
                "64": "/images/waiting_64.png",
                "128": "/images/waiting_128.png"
            },
            tabId: tabid
        });

        // we do still need processing
        //console.log("New URL is " + urlkey + " and title is  " + title + " and screenshot data " + screenshot);

        // add url to cache so we do not process twice before result is known.
        storeResponse(urlkey, "queued");

        var jsonData = JSON.stringify({
            'URL': urlkey,
            'pagetitle': title,
            'image64': screenshot,
            'uuid': uuid
        });
        console.log(jsonData)
        fetch("http://tilbury2.fortiddns.com:5000/api/v1/url", {
                method: "POST",
                body: jsonData,
                headers: {
                    'Content-Type': 'application/json',
                    'Connection': 'close',
                    'Content-Length': jsonData.length
                }
            }).then(res => {
                res.json();
            })
            .then((data) => {
                jsonResp = JSON.stringify(data[0]);
                jsonResp = JSON.parse(jsonResp);
                storeResponse(urlkey, jsonResp.status);
                updateBadge();
                //console.log(jsonResp.status);

                if (jsonResp.status == 'processing') {
                    checkLoop(tabid, urlkey, title, screenshot, uuid, 0);
                } else {
                    // change icon
                    if (jsonResp.status == 'phishing') {
                        chrome.action.setIcon({
                            path: {
                                "16": "/images/phishing_16.png",
                                "32": "/images/phishing_32.png",
                                "64": "/images/phishing_64.png",
                                "128": "/images/phishing_128.png"
                            },
                            tabId: tabid
                        });
                    } else if (jsonResp.status == 'not phishing') {
                        chrome.action.setIcon({
                            path: {
                                "16": "/images/not_phishing_16.png",
                                "32": "/images/not_phishing_32.png",
                                "64": "/images/not_phishing_64.png",
                                "128": "/images/not_phishing_128.png"
                            },
                            tabId: tabid
                        });
                    } else if (jsonResp.status == "inconclusive") {
                        chrome.action.setIcon({
                            path: {
                                "16": "/images/questionmark_16.png",
                                "32": "/images/questionmark_32.png",
                                "64": "/images/questionmark_64.png",
                                "128": "/images/questionmark_128.png"
                            },
                            tabId: tabid
                        });
                    }
                    chrome.tabs.sendMessage(tabid, {
                        status: jsonResp.status,
                        url: jsonResp.url
                    }, function (response) {
                        // No response

                    });
                }
            })
            .catch((err) => {
                // An error occured. This can be the timeout, or some other error.
                console.log(err);
                checkLoop(tabid, urlkey, title, screenshot, uuid, 0)
            });
        /*
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "http://tilbury2.fortiddns.com:5000/api/v1/url", true);
        xhr.setRequestHeader("Content-type", "application/json");
        xhr.setRequestHeader("Content-length", jsonData.length);
        xhr.setRequestHeader("Connection", "close");
        xhr.onreadystatechange = function() {
            if (xhr.readyState == 4) {
                var resp = JSON.parse(xhr.responseText);
                console.log(resp);

                storeResponse(urlkey, resp.status);

                chrome.tabs.sendMessage(tabid, {status: resp.status, url: resp.url}, function(response) {
                    // No response
                });
           }
        }
        xhr.send(jsonData);
        */


    });
}

function checkLoop(tabid, urlkey, title, screenshot, uuid, i) {
    res = checkAgain(tabid, urlkey, title, screenshot, uuid, i);
}

function checkAgain(tabid, urlkey, title, screenshot, uuid, i) {
    var jsonData = JSON.stringify({
        'URL': urlkey,
        'pagetitle': title,
        'image64': screenshot,
        'uuid': uuid
    });
    console.log(jsonData)
    fetch("http://tilbury2.fortiddns.com:5000/api/v1/url", {
            method: "POST",
            body: jsonData,
            headers: {
                'Content-Type': 'application/json',
                'Connection': 'close',
                'Content-Length': jsonData.length
            }
        }).then(res => {
            return res.json();
        })
        .then((data) => {
            jsonResp = JSON.stringify(data[0]);
            jsonResp = JSON.parse(jsonResp);
            storeResponse(urlkey, jsonResp.status);
            updateBadge();
            if (i > 50) {
                //deleteResponse(urlkey)
                // stop checking.. takes too long (server down?)
            } else if (jsonResp.status == 'processing') {
                setTimeout(checkLoop(tabid, urlkey, title, screenshot, uuid, ++i), 2000);
            } else {
                console.log('late response sent to tab')
                // change icon
                if (jsonResp.status == 'phishing') {
                    chrome.action.setIcon({
                        path: {
                            "16": "/images/phishing_16.png",
                            "32": "/images/phishing_32.png",
                            "64": "/images/phishing_64.png",
                            "128": "/images/phishing_128.png"
                        },
                        tabId: tabid
                    });
                } else if (jsonResp.status == 'not phishing') {
                    console.log("Icon set to not_phishing");
                    chrome.action.setIcon({
                        path: {
                            "16": "/images/not_phishing_16.png",
                            "32": "/images/not_phishing_32.png",
                            "64": "/images/not_phishing_64.png",
                            "128": "/images/not_phishing_128.png"
                        },
                        tabId: tabid
                    });
                } else if (jsonResp.status == "inconclusive") {
                    chrome.action.setIcon({
                        path: {
                            "16": "/images/questionmark_16.png",
                            "32": "/images/questionmark_32.png",
                            "64": "/images/questionmark_64.png",
                            "128": "/images/questionmark_128.png"
                        },
                        tabId: tabid
                    });
                }
                chrome.tabs.sendMessage(tabid, {
                    status: jsonResp.status,
                    url: urlkey
                }, function (response) {
                    // No response
                });
            }
        })
        .catch((err) => {
            // An error occured. This can be the timeout, or some other error.
            console.log(err);
            return 'error';
        });
}

function storeResponse(urlkey, response) {
    // Store the url and response in cache
    chrome.storage.local.get({
        urlCacheIds: []
    }, function (result) {
        var found = false;
        for (i = 0; i < result.urlCacheIds.length; i++) {
            if (result.urlCacheIds[i].urlId == urlkey) {
                result.urlCacheIds[i].status = response;
                result.urlCacheIds[i].ack = false;

                chrome.storage.local.set({
                    urlCacheIds: result.urlCacheIds
                }, function (result) {

                });
                found = true;
                break;
            }
        }
        if (!found) {
            var urlCacheIds = result.urlCacheIds;
            urlCacheIds.push({
                urlId: urlkey,
                status: response,
                ack: false
            });

            chrome.storage.local.set({
                urlCacheIds: urlCacheIds
            }, function (result) {

            });
        }
    });
}

function deleteResponse(urlkey) {
    chrome.storage.local.get({
        urlCacheIds: []
    }, function (result) {
        for (i = 0; i < result.urlCacheIds.length; i++) {
            if (result.urlCacheIds[i].urlId == urlkey) {

                // delete entry
                result.urlCacheIds.splice(i, 1);

                // put array back
                chrome.storage.local.set({
                    urlCacheIds: result.urlCacheIds
                }, function (result) {

                });
                break;
            }
        }
    });
}

function updateBadge() {
    chrome.storage.local.get({
        urlCacheIds: []
    }, function (result) {
        var count = 0
        for (i = 0; i < result.urlCacheIds.length; i++) {
            if (result.urlCacheIds[i].status == 'phishing' && result.urlCacheIds[i].ack != true) {
                count++;
            }
        }
        if (count != 0) {
            chrome.action.setBadgeText({
                text: count.toString()
            });
            chrome.action.setBadgeBackgroundColor({
                color: [255, 0, 0, 255]
            })
        } else {
            chrome.action.setBadgeText({
                text: ""
            });
        }
    });

}


// Read all data in local storage
function readAllStorage() {
	chrome.storage.local.get(
		null, 
		//{urlCacheIds: []}
		function(result) {
		// result is an object containing all the key-value pairs in storage
		console.log(result);
	});
}

// Delete all urlCacheIds content in local storage

function clearUrlStorage() {
	chrome.storage.local.remove("urlCacheIds", function() {
		if (chrome.runtime.lastError) {
		  console.error("Error removing item from storage: " + chrome.runtime.lastError);
		} else {
		  console.log("urlCacheIds removed successfully.");
		}
	});
}

// clear all local storage
function clearAllStorage() {
	chrome.storage.local.clear(function() {
		if (chrome.runtime.lastError) {
		  console.error("Error clearing storage: " + chrome.runtime.lastError);
		} else {
		  console.log("Storage cleared successfully.");
		}
	});
}
