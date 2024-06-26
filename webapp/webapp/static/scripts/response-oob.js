(function () {

    /** @type {import("../htmx").HtmxInternalApi} */
    var api;

    htmx.defineExtension('response-oob', {
        init: function (apiRef) {
            api = apiRef;
        },
        transformResponse : function(text, xhr, elt) {
            // Gets the ids and swap styles from the response header and adds those
            // to the corresponding elements in the response content.
            textDOM = new DOMParser().parseFromString(text, 'text/html');
            var hxResponseOobHeader = xhr.getResponseHeader('HX-Swap-Oob');
            var newElt = elt.cloneNode(true);
            if (hxResponseOobHeader) {
                var selectors = hxResponseOobHeader.split(',');
                selectors.forEach(function (selector) {
                    selector = selector.trim();
                    var parts = selector.split(':');
                    var elementSelector = parts[0];
                    var elementSwapStyle = typeof (parts[1]) !== "undefined" ? parts[1] : "true";
                    
                    if (elementSelector.charAt(0) !== '#') {
                        console.error("HTMX OOB swap: unsupported selector '" + target + "'. Only ID selectors starting with '#' are supported.");
                        return;
                    }
                    
                    var target = textDOM.querySelector(elementSelector);                    
                    if (!target) {
                        console.error("HTMX OOB swap: element with selector '" + elementSelector + "' not found in response.");
                        return;
                    }
                    target.setAttribute('hx-swap-oob', elementSwapStyle);
                });
            }
        }
    });
})();