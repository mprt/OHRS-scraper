# OHRS-scraper
Python script to find available mountain huts using the Open Hut Reservation System

To Do:
- add option to allow group splitting over various rooms
- find out if it's possible to ensure people sharing an actual room (not just the room type)
- Fix geolocation / distance calculation thing
- add clickable links to commandline output
- add more information (e.g. about room types) to commandline output
- internationalization
- parse room types from html (for i in {0..700}; do wget https://www.alpsonline.org/reservation/calendar?hut_id=$i -O- 2>/dev/null; done) | awk 'BEGIN { i = ""; } /id="bedCategoryLabel0-/ { match($2, "-([0-9]*)", a); i = a[1] } /<\/label>/ { if (i != "") { match($0, "([^ ].*)<", a); print i "," a[1]; i = "" } }' | sort -n | uniqf. 
