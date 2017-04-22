# HQMStreamHelper
A repository containing code to assist in the automation of gathering and assembling stream assets.

python.py contains code that helps with 3 things, given you set up the paths in the data.json correctly and your OBS has media sources defined with the correct names:
1. Updates the standings in OBS - the pictures for the teams in order of standings, the points for each team, and the record
2. Updates the schedule for any games being played today in OBS - pictures and times
3. Confirms that the standings match the points generated for each team. Will raise exception otherwise.

# Requirements
Tested on Python 3. You'll need to get a [Google Service Account](https://developers.google.com/identity/protocols/OAuth2ServiceAccount#creatinganaccount) to interface with the Google Spreadsheet 
and change the name of the JSON credentials file in python.py.

# Future
- Grab players for each team with statistics, store them in JSON files with the full team name so they can be displayed as needed from 
some C# memoryreader as the players join the ice to start the game.
- Get team statistics from the rosters sheets, store in JSON to be accessed by OBS / shown somewhere.
- Idk make suggestions or help me out fam
