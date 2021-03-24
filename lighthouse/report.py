# this python file uses the following encoding utf-8

# Python Standard Library
from collections import namedtuple
from datetime import timedelta


AuditResult = namedtuple('AuditResult', ['title', 'score', 'display'])
AuditCategoryResult = namedtuple('AuditCategoryResult', ['passed', 'failed'])

BASE_TIMINGS = [
    'first-contentful-paint',
    'speed-index',
    'interactive',
    'first-meaningful-paint',
    'first-cpu-idle',
    'estimated-input-latency',
    'time-to-first-byte',
]
"""list(str) default list of timings"""


class LighthouseReport(object):
    """
    Lighthouse report abstract

    Should provide more pleasant report then the lighthouse JSON.
    """

    def __init__(self, data, timings=BASE_TIMINGS):
        """
        Args:
            data (dict): JSON loaded lighthouse report
            timings (list(str), optional): list of timings
                to gather
        """

        self.__data = data
        self.__timings = timings

    @property
    def score(self):
        """ Dictionary of lighthouse's category name: score (0 to 1) """

        return {
            k: v.get('score', 0)
            for k, v
            in self.__data['categories'].items()
        }

    @property
    def metrics(self):
        """ Dictionary of lighthouse's selected metrics values (custom and ugly) """

        raw_metrics = self.__data['audits']['metrics']['details']['items'][0]
        resource_details = self.__data['audits']['resource-summary']['details']['items'][0]

        metrics = {}
        metrics['first-meaningful-paint'] = raw_metrics['firstMeaningfulPaint']
        metrics['largest-contentful-paint'] = raw_metrics['largestContentfulPaint']
        metrics['interactive'] = raw_metrics['interactive']
        metrics['speed-index'] = raw_metrics['speedIndex']
        metrics['total-blocking-time'] = raw_metrics['totalBlockingTime']
        metrics['cumulative-layout-shift'] = raw_metrics['cumulativeLayoutShift']
        metrics['page-size'] = resource_details['transferSize']

        return metrics

    @property
    def timings(self):
        """ Dictionary of lighthouse's timings names: timedelta times """

        return {
            k: timedelta(milliseconds=v.get('rawValue'))
            for k, v
            in self.__data['audits'].items()
            if k in self.__timings
        }

    @property
    def audits(self):
        """
        Dictionary of audits as category name: object with passed/failed keys
            with lists attached.
        """
        res = {}

        for category, data in self.__data['categories'].items():
            all_audit_refs = [
                x.get('id')
                for x in data['auditRefs']
            ]
            all_audits = {k: self.__data['audits'][k] for k in all_audit_refs}
            sdm_to_reject = ['manual', 'notApplicable', 'informative']
            passed_audits = [
                AuditResult(**{
                    'title': v['title'],
                    'score': v['score'],
                    'display': v.get('displayValue'),
                })
                for k, v in all_audits.items()
                if v.get('score', 0) == 1 and
                v.get('scoreDisplayMode') not in sdm_to_reject
            ]

            failed_audits = [
                AuditResult(**{
                    'title': v['title'],
                    'score': v['score'],
                    'display': v.get('displayValue'),
                })
                for k, v in all_audits.items()
                if v.get('score', 0) < 1 and
                v.get('scoreDisplayMode') not in sdm_to_reject
            ]

            res[category] = AuditCategoryResult(passed_audits, failed_audits)
        return res
