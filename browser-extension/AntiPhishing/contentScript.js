const {
    hostname
} = new URL(location.href);

var checkstatus = 'processing';

// Wait for the page to have loaded before trying to count the password fields
window.addEventListener('load', function () {
    var inputs = document.querySelectorAll("input[type=password]");
    if (!hostname.includes("google.") && !hostname.includes("chrome://") && !hostname.includes("bit.ly") && hostname.includes(".") && inputs.length > 0) {
        chrome.runtime.sendMessage({
            url: chrome.runtime.url
        }, function (response) {
            // No response
            // Will be through separate message
        });
    }

    // add listeners to password fields
    for (var i = 0; i < inputs.length; i++) {
        inputs[i].addEventListener("focusin", () => {

            if (checkstatus == 'processing'){
                var tooltipWrap = document.createElement("div"); //creates div
                tooltipWrap.className = "tooltipphish"; //adds class

                var tooltipText = document.createElement("span"); //creates div
                tooltipText.className = "tooltiptext"; //adds class
                tooltipText.innerHTML = "CAUTION: do not enter your details! The anti-phishing plug-in is still running!";

                tooltipWrap.appendChild(tooltipText);
                var firstChild = document.body.firstChild; //gets the first element after body
                firstChild.parentNode.insertBefore(tooltipWrap, firstChild);

                var padding = 30;
                var fieldProps = event.target.getBoundingClientRect();
                var tooltipProps = tooltipWrap.getBoundingClientRect();
                var topPos = fieldProps.top - (tooltipProps.height + padding);
                tooltipWrap.style.cssText =
                    "left:" +
                    fieldProps.left +
                    "px;top:" +
                    topPos +
                    "px;position:absolute;z-index:100;background: #F4FF47;border-radius:6px;padding: 6px 12px;font-family: arial;font-size: 12px;text-shadow: 0px 1px 1px #000;color: #011a15;";
            }
        });

        inputs[i].addEventListener("focusout", () => {
            document.querySelector(".tooltipphish").remove();
        });
    }
    });
        
chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
    if (request.status == "phishing") {
        checkstatus = 'phishing';
        // Check if still on same domain, if yes then display warning
        var hostname1 = new URL(location.href).hostname;
        var hostname2 = new URL(request.url).hostname;
        if (hostname1 == hostname2) {
            //alert("The anti-phishing browser extension has detected the page with URL: " + request.url + " as a phishing website. We recommend you proceed with exterme caution!");

            if (document.getElementById("antiphishingpopup") == null) {
                var alertPopup = document.createElement("div");
                alertPopup.setAttribute("id", "antiphishingpopup");
                alertPopup.innerHTML +=
                    '<div style="padding: 10%;"><div style="width: 150px; float: left; margin-right: 20px;"><img style="width:100%;" src="https://upload.wikimedia.org/wikipedia/commons/8/81/Stop_sign.png" /></div><div style="float:left;"><h1 style="color:#fff; border-bottom: 1px solid white; font-size: xxx-large; margin:10px;padding:20px 10px; text-align:left;">Phishing Detected!</h1><p style="color:#fff;font-weight: bold;font-size: large;margin:10px;padding:20px 10px;text-align:left;">The website you are trying to visit has been reported a phishing site by your Anti-Phishing browser plugin.</p><p style="color:#fff;font-weight: bold;font-size: large;margin:10px;padding:20px 10px;text-align:left;">Phishing websites are designed to trick you into revealing personal or financial information by imitating sources your may trust.</p><p style="color:#fff;font-weight: bold;font-size: large;margin:10px;padding:20px 10px;text-align:left;">Entering any information on this web page may result in identity theft or other fraud.<br><br><br><br>Please close this window now.</p><br/><br/><button style="cursor:pointer;float:right;text-decoration:underline;background:none;color:#000;border:none;" onClick="document.getElementById(&quot;antiphishingpopup&quot;).style.display = &quot;none&quot;;">Ignore this warning</button><br/><button id="whitelistwarning" style="cursor:pointer;float:right;text-decoration:underline;background:none;color:#000;border:none;" onClick="document.getElementById(&quot;antiphishingpopup&quot;).style.display = &quot;none&quot;;">Whitelist this page</button></div></div>';
                alertPopup.style.cssText =
                    "position:fixed;top:0;left:0;width:100%;height:100%;z-index:2147483647;background:#772222;";
                document.body.appendChild(alertPopup);
                document.getElementById('whitelistwarning').addEventListener('click', () => {
                    whitelistPhish();
                })
            }
        }
    } else if (request.status == 'not phishing') {
        checkstatus = 'nophishing';
        document.querySelector(".tooltipphish").remove();        
    } 
});

function whitelistPhish() {
    chrome.storage.local.get({
        urlCacheIds: []
    }, function (result) {
        var i;
        for (i = 0; i < result.urlCacheIds.length; i++) {
            if (result.urlCacheIds[i].urlId == location.href) {
                result.urlCacheIds[i].status = 'not phishing';

                chrome.storage.local.set({
                    urlCacheIds: result.urlCacheIds
                }, function (result) {

                });
                break;
            }
        }

    });
}
