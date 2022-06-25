#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import json
from datetime import datetime

import requests
import yaml
from bs4 import BeautifulSoup
from jinja2 import Template

# import traceback


def pagerender(name, tags, stations, lat, lng, reg):
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open("template.html", "r", encoding="utf8") as tfile:
        template = tfile.read()
    t = Template(template)
    res = t.render(name=name, tags=tags, stations=stations, lat=lat, lng=lng,
                   reg=reg, date=date)
    return res


def main():
    """
    main loop
    """
    args = parse_arguments()

    # load config file
    try:
        with open(args.config, "r") as config:
            config = yaml.safe_load(config)
    except Exception as e:
        print("Cannot load config: {}".format(e))

    url = args.url
    response = requests.get(url, timeout=15)
    soup = BeautifulSoup(response.content, 'lxml-xml')

    # process data from url
    data = {}
    data2 = {}
    nodata = set()
    for country in soup.markers:
        if country['country'] == "PL":
            try:
                city_id = country.city['uid']
                data[city_id] = {'stations': {}, 'geo': {}}
                data2[city_id] = {'name': country.city['name'], 'data': []}
                for city in country.city:
                    data[city_id]['stations'][city['name']] = city['bikes']
                    data[city_id]['geo']['lat'] = city['lat']
                    data[city_id]['geo']['lng'] = city['lng']
                    data2[city_id]['data'].append(
                        {'station': city['name'], 'uid': city['uid'], 'bike_count': city['bikes']})
            except Exception as e:
                print("Error occured for {}: {}".format(city_id, e))
                # print(traceback.format_exc())

    for city_str in data:
        city = int(city_str)
        stations = data[city_str]['stations']
        lat = data[city_str]['geo'].get('lat')
        lng = data[city_str]['geo'].get('lng')
        if config.get('cities').get(city):
            filename = args.path + str(config['cities'][city].get('filename')) + '/index.html'
            tags = config['cities'][city].get('tags')
            name = config['cities'][city].get('name')
            geo = config['cities'][city].get('geo.region')
            with open(str(filename), "w", encoding="utf-8") as file:
                body = pagerender(name, tags, stations, lat, lng, geo)
                file.write(body)
        else:
            nodata.add(int(city))

    # dump json to file
    json_file = args.path + 'json/output.json'
    with open(json_file, 'w') as outfile:
        json.dump(data2, outfile)
    print(len(nodata), nodata)


def parse_arguments():
    """
    parsing arguments
    """
    parser = argparse.ArgumentParser(
        description='Nextbike for cities in Poland')

    parser.add_argument(
        '--url', required=False,
        default='https://nextbike.net/maps/nextbike-official.xml',
        help='RSS URL to fetch')
    parser.add_argument(
        '--config', required=False,
        default='config.yaml',
        help='config with cities data')
    parser.add_argument(
        '--path', required=False,
        default='/var/www/nextbike/',
        help='path to directories with files')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()
