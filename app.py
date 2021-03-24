# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for
from lighthouse import LighthouseRunner
from threading import Timer, Thread
from os import listdir, urandom
from os.path import isfile, join, exists
from urllib.parse import urlparse
import webbrowser
import json
import datetime
import math

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.secret_key = urandom(42)
app.config.update(
    TESTING=True,
    TEMPLATES_AUTO_RELOAD=True,
    DEBUG=False
)

results_path = 'results/'

# FILTERS
@app.template_filter()
def ms2s(value):
    """Convert milliseconds into seconds."""
    seconds = round((value/1000)%60, 2)
    return str(seconds)+'s'

@app.template_filter()
def format_bytes(size_bytes):
    """Format a bytes integer."""
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


# ROUTES
@app.route('/', methods = ['GET', 'POST'])
def hello():
    if request.method == 'GET':
        return render_template('index.html')

    if request.method == 'POST':
        data = request.form
        batch_name = data['name']
        links = data['links'].split('\r\n')
        is_mobile = request.form.get('mobile') != None
        now = datetime.datetime.now()

        jsonOutput = {}
        jsonOutput['name'] = batch_name
        jsonOutput['done'] = False
        jsonOutput['date'] = now.strftime("%d/%m/%Y %H:%M:%S")
        jsonOutput['mobile'] = is_mobile

        writepath = results_path+batch_name+'-'+now.strftime("%d-%m-%Y__%H-%M-%S")+'.json'
        mode = 'a' if exists(writepath) else 'w'

        with open(writepath, mode) as outfile:
            json.dump(jsonOutput, outfile)

        thread = Thread(target=process_list, args=(writepath, links, is_mobile))
        thread.daemon = True
        thread.start()

        return render_template('index.html', msg = 'Processing for '+batch_name+' started! For more details see console or wait for process results at the results page (refresh required).')


def process_list(path, links, is_mobile):
    with open(path) as json_file:
        data = json.load(json_file)

    print('-----------------------')
    print('STARTING BATCH!')
    results = {}
    factor = 'mobile' if is_mobile else 'desktop'
    length = len(links)
    for idx, link in enumerate(links):
        if link:
            parsed_url = urlparse(link)
            if not parsed_url.scheme:
                link = join('https://', link)
            print('(%s/%s) processing %s' % (idx+1,length,link))
            try:
                report = LighthouseRunner(link, form_factor=factor, quiet=True).report
                results[link] = report.score
                results[link]['metrics'] = report.metrics
            except:
                print('(%s/%s) Lighthouse error: %s' % (idx+1,length,link))
        else:
            print('(%s/%s) invalid empty link: %s' % (idx+1,length,link))

    data['links'] = results
    data['done'] = True


    with open(path, 'w') as json_file:
        json.dump(data, json_file)

    print('END OF BATCH! RESULTS UPDATED')
    print('-----------------------')


@app.route('/results', methods = ['GET'])
def results():
    all_files = [pos_json for pos_json in listdir(results_path) if pos_json.endswith('.json')]
    results = []

    for result_file in all_files:
        with open(join(results_path, result_file)) as json_file:
            data = json.load(json_file)
            data['file'] = result_file
            results.append(data)

    return render_template('results.html', results = results)


@app.route('/results/<file_name>', methods = ['GET'])
def results_details(file_name):
    file_path = join(results_path, file_name)

    if not isfile(file_path):
        return redirect(url_for('results'))

    with open(file_path) as json_file:
        data = json.load(json_file)

    avg = {}

    if data.get('links') != None:
        performance = []
        accessibility = []
        best_practices = []
        seo = []
        pwa = []
        first_meaningful_paint = []
        largest_contentful_paint = []
        interactive = []
        speed_index = []
        page_size = []
        cumulative_layout_shift = []
        total_blocking_time = []

        for link in data['links']:
            values = data['links'][link]
            performance.append(values['performance'])
            accessibility.append(values['accessibility'])
            best_practices.append(values['best-practices'])
            seo.append(values['seo'])
            pwa.append(values['pwa'])
            first_meaningful_paint.append(values['metrics']['first-meaningful-paint'])
            largest_contentful_paint.append(values['metrics']['largest-contentful-paint'])
            interactive.append(values['metrics']['interactive'])
            speed_index.append(values['metrics']['speed-index'])
            page_size.append(values['metrics']['page-size'])
            cumulative_layout_shift.append(values['metrics']['cumulative-layout-shift'])
            total_blocking_time.append(values['metrics']['total-blocking-time'])

        avg['performance'] = calc_average(performance)
        avg['accessibility'] = calc_average(accessibility)
        avg['best_practices'] = calc_average(best_practices)
        avg['seo'] = calc_average(seo)
        avg['pwa'] = calc_average(pwa)
        avg['first-meaningful-paint'] = calc_average(first_meaningful_paint)
        avg['largest-contentful-paint'] = calc_average(largest_contentful_paint)
        avg['interactive'] = calc_average(interactive)
        avg['speed-index'] = calc_average(speed_index)
        avg['page-size'] = calc_average(page_size)
        avg['cumulative-layout-shift'] = calc_average(cumulative_layout_shift, True)
        avg['total-blocking-time'] = calc_average(total_blocking_time)

    return render_template('result_details.html', data = data, avg = avg)


def calc_average(list, is_index = False):
    decimals = 3 if is_index else 2
    return round(sum(list) / len(list), decimals)


def open_browser():
    if not app.debug:
        webbrowser.open('http://localhost:5000/')


if __name__ == '__main__':
    Timer(1, open_browser).start();
    app.run()