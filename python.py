from re import search
import datetime
import json
import jsonpickle
import gspread
from oauth2client.service_account import ServiceAccountCredentials

with open('data.json') as stored_data:
    _data = json.load(stored_data)
    short_namer = _data['names']
    long_namer = _data['full_names']
    cells = _data['cells']
    paths = _data['paths']
    sheets = _data['sheets']

class Team(object):
    def __init__(self, name, record="", points=""):
        """A class that holds information regarding each team's name, statistics, and players."""
        global short_namer, long_namer
        record_list = list(map(int, search(r'(\d+)-(\d+)-(\d+)-(\d+)', record).groups()))
        calc_points_list = [a * b for a, b in zip([3, 2, 1, 0], record_list)]
        if sum(calc_points_list) != points:
            raise TeamException("Points are not equal to record, check schedule data.")
        self.name = short_namer[name]
        self.full_name = long_namer.get(name, None)
        self.record = record
        self.points = points
        self.wins, self.overtime_wins, self.overtime_losses, self.losses = record_list
        self.players = []

    def __str__(self):
        return "[{name}] with record {rec}".format(name=self.name, rec=self.record)

    def __repr__(self):
        return str(self)

class Player(object):
    def __init__(self, name, **kwargs):
        """A class that holds information regarding player statistics."""
        self.name = name
        self.position = kwargs.get('position', None)
        self.role = kwargs.get('role', None)
        self.points = kwargs.get('points', None)
        self.goals = kwargs.get('goals', None)
        self.assists = kwargs.get('assists', None)
        self.ppg = kwargs.get('ppg', None)
        self.plusminus = kwargs.get('plusminus', None)
        self.gwg = kwargs.get('gwg', None)
        self.goalpercent = kwargs.get('goalpercent', None)
        self.shots = kwargs.get('shots', None)
        self.saves = kwargs.get('saves', None)
        self.savepercent = kwargs.get('savepercent', None)
        self.spg = kwargs.get('spg', None)
        self.ga = kwargs.get('ga', None)
        self.gaa = kwargs.get('gaa', None)
        self.gp = kwargs.get('gp', None)
        self.gp_goalie = kwargs.get('gp_goalie', None)
        self.wins = kwargs.get('wins', None)
        self.shutouts = kwargs.get('shutouts', None)
        self.toi = kwargs.get('toi', None)

class TeamException(Exception):
    pass

def grab_worksheet(keys=None):
    credentials = ServiceAccountCredentials \
        .from_json_keyfile_name('GSpread Project-8646fd91a5c4.json',
            ['https://spreadsheets.google.com/feeds'])
    gc = gspread.authorize(credentials)

    if isinstance(keys, list):
        return [gc.open_by_key(key) for key in keys]
    elif isinstance(keys, str):
        return gc.open_by_key(keys)

def get_teams(wks, league, wks_stats=None):
    global cells
    wks = wks.get_worksheet(0)
    if wks_stats is not None:
        wks_stats = wks_stats.get_worksheet(0)
    teams = []

    for team, record, point in zip(wks.range(cells[league][0]), wks.range(cells[league][1]), wks.range(cells[league][2])):
        out_team = Team(team.value, record.value, int(point.value))
        if wks_stats is not None:
            player_list = []
            for player in wks_stats.range(cells[team.value]):
                row = wks_stats.row_values(player.row)
                usr_player = Player(player.value, position=row[player.col + 1],
                                    role=row[player.col + 2],
                                    points=row[player.col + 3],
                                    goals=row[player.col + 4],
                                    assists=row[player.col + 5],
                                    ppg=row[player.col + 6],
                                    plusminus=row[player.col + 7],
                                    gwg=row[player.col + 8],
                                    goalpercent=row[player.col + 9],
                                    shots=row[player.col + 10],
                                    saves=row[player.col + 11],
                                    savepercent=row[player.col + 12],
                                    spg=row[player.col + 13],
                                    ga=row[player.col + 14],
                                    gaa=row[player.col + 15],
                                    gp=row[player.col + 16],
                                    gp_goalie=row[player.col + 17],
                                    wins=row[player.col + 18],
                                    shutouts=row[player.col + 19],
                                    toi=row[player.col + 20])
                player_list.append(usr_player)
            out_team.players = player_list
        teams.append(out_team)
    with open('stats_{d.month}{d.day}{d.year}-{league}.json'.format(d=datetime.date.today(), league=league), 'w') as outfile:
        outfile.write(jsonpickle.encode(teams))
    return teams

def grab_games(row, col, cell, wks):
    """Internal function to do the heavy lifting of iterating inside the worksheet."""
    games = []
    times = []
    while wks.cell(row, col).value != "":
        cell1 = wks.cell(row, col)
        times.append(cell1.value)
        times.append("null")
        cell1 = wks.cell(row, col + 1)
        cell2 = wks.cell(row, col + 4)
        if len(cell1.value) >= 3 and len(cell2.value) >= 3:
            games.append(cell1.value)
            games.append(cell2.value)
        else:
            raise Exception("No teams scheduled for this date.")
        row += 1
        col = cell.col + 2
    return list(zip(times, games))

def get_schedule(wks):
    """Takes current worksheet and returns a list of all of today's HQM games."""
    search_str = '{today.month}/{today.day}/{today.year}'.format(today=datetime.date.today())
    wks = wks.get_worksheet(0)
    try:
        origin_cell = wks.find(search_str)
        init_row = origin_cell.row
        init_col = origin_cell.col + 2
        return grab_games(init_row, init_col, origin_cell, wks)
    except gspread.CellNotFound:
        raise

def modify_json_standings(lst_teams, league):
    # First section: Modify standings in league-specific intro.
    global paths
    logo_path = paths['left_logo_path']
    json_path = paths['json_path']
    sch_path = paths['sch_path']

    with open(sch_path + "{}_Stand.txt".format(league.upper()), "w+") as standings:
        standings.write("\n".join([i.record for i in lst_teams]) + "\n")
    with open(sch_path + "{}_Pts.txt".format(league.upper()), "w+") as standings:
        standings.write("\n".join([str(i.points) for i in lst_teams]) + "\n")
    with open(json_path + "HQM_{}.json".format(league.upper()), "r+") as json_file:
        data = json.load(json_file)
        for i, team in enumerate(lst_teams):
            # tuple unpacking - confirms we have only 1 match in data['sources']
            item, = filter(lambda x: "{league} {index}".format(league=league.upper(), index=i + 1)
                           in x['name'], data['sources'])
            item["settings"]["file"] = "{start}/{lg}/{name}.png" \
                .format(lg=league.upper(), name=team.name, start=logo_path)
        json_file.seek(0)
        json_file.write(json.dumps(data))
        json_file.truncate()
        return

def modify_json_schedule(lst_sched, league):
    global paths
    logos = [paths['left_logo_path'], paths['right_logo_path']]
    json_path = paths['json_path']
    sch_path = paths['sch_path']
    try:
        with open(sch_path + "{}_Sched.txt".format(league.upper()), "w+") as sch_file:
            sch_file.write("\n\n".join([i[0] for i in lst_sched[0::2]]) + "\n\n")
        with open(json_path + "HQM_{}.json".format(league.upper()), "r+") as json_file:
            data = json.load(json_file)
            for i, game in enumerate(lst_sched):
                item, = filter(lambda x: "{league} Spot {index}".format(league=league.upper(), index=i + 1)
                               in x['name'], data['sources'])
                item["settings"]["file"] = "{start}/{lg}/{name}.png" \
                    .format(lg=league.upper(), name=game[1], start=logos[i % 2])
            json_file.seek(0)
            json_file.write(json.dumps(data))
            json_file.truncate()
        return

    except gspread.CellNotFound:
        raise

def main():
    global sheets
    (jsl, rsl, lhl, lhl_stats) = grab_worksheet([sheets['jsl'], sheets['rsl'], sheets['lhl'], sheets['lhl_stats']])
    modify_json_standings(get_teams(jsl, "jsl"), "jsl")
    modify_json_standings(get_teams(rsl, "rsl"), "rsl")
    modify_json_standings(get_teams(lhl, "lhl", lhl_stats), "lhl")
    try:
        response = input("Which league (JSL, RSL, LHL)? ").upper()
        if response == "JSL" or response == "RSL":
            modify_json_schedule(get_schedule(jsl), "jsl")
            modify_json_schedule(get_schedule(rsl), "rsl")

        elif response == "LHL":
            modify_json_schedule(get_schedule(lhl), "lhl")

        else:
            print("Wrong response.")
    except gspread.CellNotFound:
        print("No " + response + " games today.")

if __name__ == '__main__':
    main()
