from csgo.parser import DemoParser

demo_parser = DemoParser(
    demofile='dataset/demos-64041-64141/Liga-Gamers-Club-2021-Serie-A-April-Cup-santos-vs-sws-bo3/santos-vs-sws-m2-overpass.dem',
    demo_id='Liga-Gamers-Club-2021-Serie-A-April-Cup-santos-vs-sws-bo3-overpass',
    parse_rate=128
)
data = demo_parser.parse(return_type='df')

print(data['MatchId'])
print(data['Rounds'])
print(data['Kills'])
print(data['Damages'])
print(data['Grenades'])
print(data['Flashes'])
print(data['BombEvents'])
