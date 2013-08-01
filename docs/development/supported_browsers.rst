Adhocracy today depends on Javascript and the use of a modern browser.
We have spent some efforts (sometimes more, sometimes less) to resolve
IE-related problems, and even chose technology which supports old-style
browsers (e.g. Openlayers and Knockout, but not D3JS or Polymaps), but
still not everything is working correctly.

A quick look at last 3 month’s browser stats on https://adhocracy.de (as
of 2012-10-18) reveals that IE 8 is still widely in use (on par with IE
9). IE6 is far behind, and IE7 even more. Concerning other browsers, Fx
3.6 is somewhat above IE6 usage, and Fx <= 3.5 and Safari <= 5.0 are
below.

-  Officially supported browser versions which we actively test: IE 9
   and current Firefox, Chrome and Safari.

-  browser versions, which we don’t actively test, but try to maintain
   functionally working if we’re receiving bug reports: IE 8 (XP),
   Firefox 3.6-15, Safari 4-5 and similarly modern browsers (but main
   work will be IE 8 here).
